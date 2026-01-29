"""
Main CLI entry point for AiCippy.

Provides all command-line commands using Typer with Rich UI.
Features auto-update checks and 12-hour session timeout login prompts.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Final, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from aicippy import __version__
from aicippy.config import Settings, get_settings
from aicippy.utils.logging import setup_logging, get_logger
from aicippy.utils.correlation import CorrelationContext

# Session and version management
from aicippy.installer import (
    CURRENT_VERSION,
    SessionManager,
    check_latest_version,
    needs_login as check_needs_login,
)
from aicippy.installer.session_manager import SESSION_MISSING

# Human verification
from aicippy.cli.human_verify import (
    HumanVerifier,
    is_likely_automated,
    require_human_verification,
)

# Constants
UPDATE_CHECK_ENABLED: Final[bool] = True
SESSION_CHECK_ENABLED: Final[bool] = True
HUMAN_VERIFICATION_ENABLED: Final[bool] = True

# Initialize Typer app with Rich
app = typer.Typer(
    name="aicippy",
    help="Enterprise-grade multi-agent CLI system powered by AWS Bedrock",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=False,
)

# Rich console for output
console = Console()
error_console = Console(stderr=True)

# Logger
logger = get_logger(__name__)

# Session manager instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get or create session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def check_for_updates_async(silent: bool = True) -> bool:
    """
    Check for updates and optionally perform silent upgrade.

    Args:
        silent: If True, run silently without UI output.

    Returns:
        True if update was performed, False otherwise.
    """
    if not UPDATE_CHECK_ENABLED:
        return False

    try:
        version_info = await check_latest_version()

        if version_info.update_available:
            if silent:
                # Silent auto-upgrade
                from aicippy.installer import perform_upgrade
                success, _ = await perform_upgrade()
                return success
            else:
                # Show update notification (only when explicitly requested)
                console.print(
                    Panel(
                        f"[yellow]Update available![/yellow]\n"
                        f"Current: {version_info.current}\n"
                        f"Latest: {version_info.latest}\n\n"
                        f"Run [bold cyan]aicippy upgrade[/bold cyan] to update.",
                        title="Update Available",
                        border_style="yellow",
                    )
                )
        return False
    except Exception:
        # Silently ignore update check failures
        return False


def check_for_updates(silent: bool = True) -> None:
    """Synchronous wrapper for update check (silent by default)."""
    try:
        asyncio.run(check_for_updates_async(silent=silent))
    except Exception:
        pass


def check_session_and_prompt_login() -> bool:
    """
    Check if session is valid, prompt for login if expired.

    Returns:
        True if session is valid or user successfully logged in.
    """
    if not SESSION_CHECK_ENABLED:
        return True

    try:
        session_mgr = get_session_manager()
        validation = session_mgr.validate()

        if not validation.needs_login:
            # Session is valid - silently refresh activity
            session_mgr.touch()
            return True

        # Session expired, invalid, or missing - trigger login directly
        # No verbose messages about 12hr timeout
        return perform_interactive_login()

    except Exception as e:
        logger.warning("session_check_failed", error=str(e))
        return False  # Block access on session check failure


def perform_interactive_login() -> bool:
    """
    Perform interactive login flow using manual code entry.

    Returns:
        True if login successful, exits to terminal on invalid code.
    """
    try:
        from aicippy.auth.cognito import CognitoAuth
        from aicippy.cli.mascot import animate_welcome_compact

        auth = CognitoAuth()
        result = asyncio.run(auth.manual_code_login())

        if result.success:
            # Create session after successful auth
            session_mgr = get_session_manager()
            success, _ = session_mgr.login(
                user_id=result.user_id or "unknown",
                username=result.username or result.user_email.split("@")[0],
                email=result.user_email,
            )

            if success:
                # Show colored Zozoo welcome animation
                username = result.username or result.user_email.split("@")[0]
                asyncio.run(animate_welcome_compact(console, username))
                return True

        # Invalid code - exit to terminal
        console.print()
        raise typer.Exit(1)

    except ImportError:
        # Auth module not available - create mock session
        logger.warning("auth_module_not_available")

        # Create a demo session for development
        session_mgr = get_session_manager()
        session_mgr.login(
            user_id="offline-user",
            username="Developer",
            email="developer@localhost",
        )
        return True

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("login_failed", error=str(e))
        # Exit to terminal on login error
        raise typer.Exit(1)


def display_welcome_banner() -> None:
    """Display the welcome banner (silent - no output)."""
    # Welcome animation is shown during login success
    # This function is kept for compatibility but produces no output
    pass


# Human verification state
_human_verifier: HumanVerifier | None = None
_human_verified: bool = False


def get_human_verifier() -> HumanVerifier:
    """Get or create human verifier singleton."""
    global _human_verifier
    if _human_verifier is None:
        _human_verifier = HumanVerifier(console=console)
    return _human_verifier


def check_automation_and_verify() -> bool:
    """
    Check for automation and perform human verification.

    Returns:
        True if human verified, False if blocked.
    """
    global _human_verified

    if not HUMAN_VERIFICATION_ENABLED:
        return True

    # Skip if already verified this session
    if _human_verified:
        return True

    # Quick automation check first
    if is_likely_automated():
        verifier = get_human_verifier()
        result = verifier.check_automation()
        if result:
            # Automation detected - block access
            console.print(Panel(
                Text(
                    f"🤖 Automated Access Blocked\n\n"
                    f"Reason: {result.reason}\n\n"
                    f"AiCippy is designed for interactive human use only.\n"
                    f"Automated scripts, bots, and CI/CD pipelines are not permitted.",
                    style="red",
                ),
                title="[bold red]Access Denied[/bold red]",
                border_style="red",
            ))
            return False

    return True


def perform_human_verification_after_login() -> bool:
    """
    Perform human verification with puzzle question after login.

    Returns:
        True if verified as human, False otherwise.
    """
    global _human_verified

    if not HUMAN_VERIFICATION_ENABLED:
        _human_verified = True
        return True

    if _human_verified:
        return True

    verifier = get_human_verifier()
    result = verifier.verify()

    _human_verified = result.is_human
    return result.is_human


def version_callback(value: bool) -> None:
    """Display version information and exit."""
    if value:
        console.print(
            Panel(
                f"[bold blue]AiCippy[/bold blue] v{__version__}\n"
                f"Enterprise Multi-Agent CLI System\n\n"
                f"[dim]Copyright (c) 2024-2026 AiVibe Software Services Pvt Ltd[/dim]\n"
                f"[dim]ISO 27001:2022 | NVIDIA Inception | AWS Activate[/dim]",
                title="Version",
                border_style="blue",
            )
        )
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Enable verbose logging",
        ),
    ] = False,
    config_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--config-dir",
            "-c",
            help="Custom configuration directory",
        ),
    ] = None,
    skip_update_check: Annotated[
        bool,
        typer.Option(
            "--skip-update-check",
            help="Skip automatic update check",
            hidden=True,
        ),
    ] = False,
    skip_login: Annotated[
        bool,
        typer.Option(
            "--skip-login",
            help="Skip login check (offline mode)",
            hidden=True,
        ),
    ] = False,
) -> None:
    """
    AiCippy - Enterprise-grade multi-agent CLI system.

    Run without arguments to start an interactive session.
    Use --help to see all available commands.

    Features:
    - Auto version update checks on launch
    - 12-hour session timeout with automatic re-login prompt
    - Enterprise-grade security with AWS Cognito authentication
    """
    # Initialize settings
    settings = get_settings()

    # Setup logging based on verbose flag
    if verbose:
        import os
        os.environ["AICIPPY_LOG_LEVEL"] = "DEBUG"
        # Clear cached settings to reload with new log level
        get_settings.cache_clear()
        settings = get_settings()

    setup_logging(settings)

    # FIRST: Check for automation/robot access
    if not check_automation_and_verify():
        logger.warning("automation_blocked", reason="automated_access_detected")
        raise typer.Exit(1)

    # Auto update check (runs silently in background conceptually)
    if not skip_update_check:
        check_for_updates()

    # Session validation - silent until login needed
    if not skip_login:
        session_valid = check_session_and_prompt_login()
        if not session_valid:
            logger.warning("session_invalid_access_denied")
            raise typer.Exit(1)
        else:
            # Perform human verification after successful login
            if not perform_human_verification_after_login():
                logger.warning("human_verification_failed")
                raise typer.Exit(1)

    # If no subcommand is provided, start interactive session
    if ctx.invoked_subcommand is None:
        # Display welcome banner with session info
        display_welcome_banner()

        from aicippy.cli.interactive import start_interactive_session
        asyncio.run(start_interactive_session())


@app.command()
def login(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force re-authentication even if already logged in",
        ),
    ] = False,
) -> None:
    """
    Authenticate with AiCippy using device/browser OAuth flow.

    Opens a browser window for secure authentication via AWS Cognito.
    Tokens are stored securely in the OS keychain.
    Session expires after 12 hours of inactivity.

    After successful login, a human verification question will be asked
    to prevent automated/bot access.
    """
    with CorrelationContext() as ctx:
        logger.info("login_started", correlation_id=ctx.correlation_id)

        # First check for automation
        if not check_automation_and_verify():
            logger.warning("automation_blocked_at_login")
            raise typer.Exit(1)

        try:
            session_mgr = get_session_manager()

            # Check if already logged in with valid session
            if not force:
                validation = session_mgr.validate()
                if not validation.needs_login:
                    console.print(
                        Panel(
                            f"[green]Already logged in![/green]\n"
                            f"User: {validation.session.username}\n"
                            f"Email: {validation.session.email}\n"
                            f"Session expires in: {validation.session.hours_remaining:.1f} hours",
                            title="Session Active",
                            border_style="green",
                        )
                    )
                    console.print("Use --force to re-authenticate.")
                    return

            # Perform interactive login
            success = perform_interactive_login()

            if not success:
                raise typer.Exit(1)

            # Human verification after successful login
            console.print()  # Spacing
            if not perform_human_verification_after_login():
                logger.warning("human_verification_failed_at_login")
                console.print("[red]Human verification failed. Login cancelled.[/red]")
                # Invalidate the session since verification failed
                session_mgr.logout()
                raise typer.Exit(1)

        except typer.Exit:
            raise
        except Exception as e:
            logger.exception("login_failed", error=str(e))
            error_console.print(f"[red]Login error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def logout() -> None:
    """
    Log out from AiCippy and clear stored credentials.

    Removes tokens from the OS keychain and invalidates the session.
    """
    with CorrelationContext() as ctx:
        logger.info("logout_started", correlation_id=ctx.correlation_id)

        try:
            # Invalidate local session first
            session_mgr = get_session_manager()
            username, _ = session_mgr.get_user()

            session_success, session_msg = session_mgr.logout()

            # Try to logout from auth provider as well
            try:
                from aicippy.auth.cognito import CognitoAuth
                auth = CognitoAuth()
                auth.logout()
            except ImportError:
                pass  # Auth module not available
            except Exception:
                pass  # Ignore auth logout failures

            if session_success:
                console.print(
                    Panel(
                        f"[green]Successfully logged out![/green]\n"
                        f"Goodbye{', ' + username if username else ''}!",
                        title="Logged Out",
                        border_style="green",
                    )
                )
            else:
                console.print(f"[yellow]{session_msg}[/yellow]")

        except Exception as e:
            logger.exception("logout_failed", error=str(e))
            error_console.print(f"[red]Logout error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to initialize (defaults to current directory)",
        ),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing aicippy.md file",
        ),
    ] = False,
) -> None:
    """
    Initialize AiCippy in a project directory.

    Scans the repository, detects tech stack, and creates an aicippy.md
    file with project context for the AI agents.
    """
    from aicippy.knowledge.project_scanner import ProjectScanner

    with CorrelationContext() as ctx:
        logger.info("init_started", path=str(path), correlation_id=ctx.correlation_id)

        target_path = path.resolve()
        aicippy_md = target_path / "aicippy.md"

        if aicippy_md.exists() and not force:
            error_console.print(
                f"[yellow]aicippy.md already exists at {target_path}[/yellow]"
            )
            console.print("Use --force to overwrite.")
            raise typer.Exit(1)

        console.print(f"[blue]Scanning project at {target_path}...[/blue]")

        try:
            scanner = ProjectScanner(target_path)
            with console.status("[bold blue]Analyzing project structure..."):
                project_info = scanner.scan()

            # Write aicippy.md
            aicippy_md.write_text(project_info.to_markdown())

            console.print(
                Panel(
                    f"[green]Project initialized![/green]\n\n"
                    f"Created: {aicippy_md}\n"
                    f"Tech Stack: {', '.join(project_info.tech_stack)}\n"
                    f"Files Scanned: {project_info.files_count}",
                    title="Initialization Complete",
                    border_style="green",
                )
            )

        except Exception as e:
            logger.exception("init_failed", error=str(e))
            error_console.print(f"[red]Initialization error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def chat(
    message: Annotated[
        str,
        typer.Argument(
            help="Message to send to the AI assistant",
        ),
    ],
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="AI model to use (opus, sonnet, llama)",
        ),
    ] = None,
) -> None:
    """
    Send a single message to AiCippy and get a response.

    For interactive sessions, use the 'aicippy' command without arguments.
    """
    from aicippy.agents.orchestrator import AgentOrchestrator

    with CorrelationContext() as ctx:
        logger.info("chat_started", correlation_id=ctx.correlation_id)

        try:
            settings = get_settings()
            model_id = settings.get_model_id(model)

            console.print(f"[dim]Using model: {model or settings.default_model}[/dim]")

            orchestrator = AgentOrchestrator(model_id=model_id)

            with console.status("[bold blue]Thinking..."):
                response = asyncio.run(orchestrator.chat(message))

            console.print(Markdown(response.content))

            # Show token usage
            if response.usage:
                console.print(
                    f"\n[dim]Tokens: {response.usage.input_tokens} in / "
                    f"{response.usage.output_tokens} out[/dim]"
                )

        except Exception as e:
            logger.exception("chat_failed", error=str(e))
            error_console.print(f"[red]Chat error: {e}[/red]")
            raise typer.Exit(1)


@app.command(name="run")
def run_task(
    task: Annotated[
        str,
        typer.Argument(
            help="Task description for the agents to execute",
        ),
    ],
    agents: Annotated[
        int,
        typer.Option(
            "--agents",
            "-a",
            help="Number of parallel agents (1-10)",
            min=1,
            max=10,
        ),
    ] = 3,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="AI model to use (opus, sonnet, llama)",
        ),
    ] = None,
) -> None:
    """
    Execute a task using multiple parallel agents.

    Spawns specialized agents that collaborate to complete the task.
    """
    from aicippy.agents.orchestrator import AgentOrchestrator

    with CorrelationContext() as ctx:
        logger.info(
            "run_task_started",
            task=task,
            agents=agents,
            correlation_id=ctx.correlation_id,
        )

        try:
            settings = get_settings()
            model_id = settings.get_model_id(model)

            console.print(
                Panel(
                    f"Task: {task}\n"
                    f"Agents: {agents}\n"
                    f"Model: {model or settings.default_model}",
                    title="Starting Task Execution",
                    border_style="blue",
                )
            )

            orchestrator = AgentOrchestrator(
                model_id=model_id,
                max_agents=agents,
            )

            # Run with progress display
            asyncio.run(orchestrator.run_task_with_progress(task, console))

        except Exception as e:
            logger.exception("run_task_failed", error=str(e))
            error_console.print(f"[red]Task execution error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def config(
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            "-s",
            help="Show current configuration",
        ),
    ] = True,
    edit: Annotated[
        bool,
        typer.Option(
            "--edit",
            "-e",
            help="Open configuration in editor",
        ),
    ] = False,
) -> None:
    """
    Show or edit AiCippy configuration.

    Configuration is stored in ~/.aicippy/config.toml
    """
    settings = get_settings()

    if edit:
        import subprocess
        import os

        config_file = settings.local_config_dir / "config.toml"

        # Create default config if it doesn't exist
        if not config_file.exists():
            config_file.write_text(
                "# AiCippy Configuration\n"
                "# See documentation for available options\n\n"
                "[general]\n"
                f"default_model = \"{settings.default_model}\"\n"
                f"max_parallel_agents = {settings.max_parallel_agents}\n"
            )

        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(config_file)])
        return

    # Show configuration
    table = Table(title="AiCippy Configuration", border_style="blue")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("AWS Account ID", settings.aws_account_id)
    table.add_row("AWS Region", settings.aws_region)
    table.add_row("Default Model", settings.default_model)
    table.add_row("Max Parallel Agents", str(settings.max_parallel_agents))
    table.add_row("Session TTL", f"{settings.session_ttl_hours} hours")
    table.add_row("Config Directory", str(settings.local_config_dir))
    table.add_row("WebSocket URL", settings.websocket_url)
    table.add_row("Cognito Domain", settings.cognito_domain)

    console.print(table)


@app.command()
def status() -> None:
    """
    Show current session and agent status.

    Displays active agents, connection status, and session information.
    """
    from aicippy.agents.status import get_agent_status

    with CorrelationContext():
        try:
            status_info = asyncio.run(get_agent_status())

            # Session info
            session_table = Table(title="Session Status", border_style="blue")
            session_table.add_column("Property", style="cyan")
            session_table.add_column("Value", style="green")

            session_table.add_row("Session ID", status_info.session_id or "Not started")
            session_table.add_row(
                "Connection",
                "[green]Connected[/green]" if status_info.connected else "[red]Disconnected[/red]",
            )
            session_table.add_row("Active Agents", str(status_info.active_agents))
            session_table.add_row("Total Tokens Used", f"{status_info.total_tokens:,}")

            console.print(session_table)

            # Agent list if any are active
            if status_info.agents:
                agent_table = Table(title="Active Agents", border_style="green")
                agent_table.add_column("ID", style="cyan")
                agent_table.add_column("Type", style="blue")
                agent_table.add_column("Status", style="yellow")
                agent_table.add_column("Progress")

                for agent in status_info.agents:
                    status_color = {
                        "running": "green",
                        "thinking": "yellow",
                        "error": "red",
                        "idle": "dim",
                    }.get(agent.status, "white")

                    agent_table.add_row(
                        agent.id,
                        agent.type,
                        f"[{status_color}]{agent.status}[/{status_color}]",
                        f"{agent.progress}%",
                    )

                console.print(agent_table)

        except Exception as e:
            logger.exception("status_failed", error=str(e))
            error_console.print(f"[red]Status error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def usage(
    detail: Annotated[
        bool,
        typer.Option(
            "--detail",
            "-d",
            help="Show detailed per-agent breakdown",
        ),
    ] = False,
) -> None:
    """
    Show token usage statistics.

    Displays usage for the current session and historical data.
    """
    from aicippy.agents.usage import get_usage_stats

    with CorrelationContext():
        try:
            stats = asyncio.run(get_usage_stats())

            # Summary table
            summary_table = Table(title="Token Usage Summary", border_style="blue")
            summary_table.add_column("Period", style="cyan")
            summary_table.add_column("Input Tokens", style="green", justify="right")
            summary_table.add_column("Output Tokens", style="green", justify="right")
            summary_table.add_column("Total", style="yellow", justify="right")

            summary_table.add_row(
                "Current Session",
                f"{stats.session_input:,}",
                f"{stats.session_output:,}",
                f"{stats.session_total:,}",
            )
            summary_table.add_row(
                "Today",
                f"{stats.today_input:,}",
                f"{stats.today_output:,}",
                f"{stats.today_total:,}",
            )
            summary_table.add_row(
                "This Month",
                f"{stats.month_input:,}",
                f"{stats.month_output:,}",
                f"{stats.month_total:,}",
            )

            console.print(summary_table)

            if detail and stats.per_agent:
                agent_table = Table(title="Per-Agent Breakdown", border_style="green")
                agent_table.add_column("Agent", style="cyan")
                agent_table.add_column("Model", style="blue")
                agent_table.add_column("Tokens", style="yellow", justify="right")

                for agent_stat in stats.per_agent:
                    agent_table.add_row(
                        agent_stat.agent_type,
                        agent_stat.model,
                        f"{agent_stat.total_tokens:,}",
                    )

                console.print(agent_table)

        except Exception as e:
            logger.exception("usage_failed", error=str(e))
            error_console.print(f"[red]Usage error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def upgrade(
    check_only: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Only check for updates, don't install",
        ),
    ] = False,
) -> None:
    """
    Upgrade AiCippy to the latest version from PyPI.

    Checks for available updates and optionally installs them.
    """
    from aicippy.installer import upgrade_aicippy

    with console.status("[bold blue]Checking for updates..."):
        try:
            success, message, version_info = asyncio.run(
                upgrade_aicippy(console=console, check_only=check_only)
            )

            if check_only:
                if version_info.update_available:
                    console.print(
                        Panel(
                            f"[yellow]Update available![/yellow]\n\n"
                            f"Current version: {version_info.current}\n"
                            f"Latest version: {version_info.latest}\n\n"
                            f"Run [bold cyan]aicippy upgrade[/bold cyan] to update.",
                            title="Update Available",
                            border_style="yellow",
                        )
                    )
                else:
                    console.print(
                        Panel(
                            f"[green]You're up to date![/green]\n\n"
                            f"Current version: {version_info.current}",
                            title="No Updates Available",
                            border_style="green",
                        )
                    )
                return

            if success:
                console.print(
                    Panel(
                        f"[green]{message}[/green]\n\n"
                        f"Restart your terminal to use the new version.",
                        title="Upgrade Complete",
                        border_style="green",
                    )
                )
            else:
                error_console.print(f"[red]Upgrade failed: {message}[/red]")
                raise typer.Exit(1)

        except Exception as e:
            logger.exception("upgrade_failed", error=str(e))
            error_console.print(f"[red]Upgrade error: {e}[/red]")
            raise typer.Exit(1)


@app.command(name="help")
def show_help() -> None:
    """
    Show detailed help and usage information.
    """
    help_text = """
# AiCippy Help

## Commands

| Command | Description |
|---------|-------------|
| `aicippy` | Start interactive session |
| `aicippy login` | Authenticate with Cognito |
| `aicippy logout` | Clear credentials |
| `aicippy session` | View/manage session |
| `aicippy init` | Initialize project |
| `aicippy chat <msg>` | Single query mode |
| `aicippy run <task>` | Execute with agents |
| `aicippy config` | Show/edit config |
| `aicippy status` | Agent status |
| `aicippy usage` | Token usage |
| `aicippy upgrade` | Self-update |
| `aicippy install` | Run/verify installation |

## Session Management

Sessions expire after **12 hours** of inactivity. When your session expires:
- You will be prompted to login again
- Use `aicippy session --refresh` to extend your session

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/model <name>` | Switch model |
| `/mode <name>` | Change mode |
| `/agents spawn <n>` | Spawn agents |
| `/agents list` | List agents |
| `/agents stop` | Stop agents |
| `/kb sync` | Sync to KB |
| `/tools list` | List tools |
| `/usage` | Token usage |
| `/clear` | Clear conversation |
| `/quit` | Exit |

## Environment Variables

- `AICIPPY_AWS_REGION` - AWS region (default: us-east-1)
- `AICIPPY_DEFAULT_MODEL` - Default model (opus/sonnet/llama)
- `AICIPPY_LOG_LEVEL` - Log level (DEBUG/INFO/WARNING/ERROR)
- `AICIPPY_HOME` - Installation directory
- `AICIPPY_CONFIG` - Configuration directory
- `AICIPPY_CACHE` - Cache directory

## Support

- Documentation: https://docs.aicippy.io
- Issues: https://github.com/aivibe/aicippy/issues
- Email: support@aivibe.in
"""
    console.print(Markdown(help_text))


@app.command()
def install(
    show_progress: Annotated[
        bool,
        typer.Option(
            "--progress",
            "-p",
            help="Show animated progress display",
        ),
    ] = True,
    verify_only: Annotated[
        bool,
        typer.Option(
            "--verify",
            "-v",
            help="Only verify installation, don't install",
        ),
    ] = False,
) -> None:
    """
    Run or verify AiCippy installation.

    Sets up directories, permissions, and environment variables.
    Use --verify to check existing installation without modifications.
    """
    from aicippy.installer import install_aicippy, verify_installation

    with CorrelationContext() as ctx:
        logger.info("install_started", correlation_id=ctx.correlation_id)

        try:
            if verify_only:
                console.print("[blue]Verifying installation...[/blue]")
                success, issues = verify_installation()

                if success:
                    console.print(
                        Panel(
                            "[green]Installation verified successfully![/green]\n\n"
                            "All components are properly configured.",
                            title="Verification Passed",
                            border_style="green",
                        )
                    )
                else:
                    console.print(
                        Panel(
                            "[yellow]Installation issues found:[/yellow]\n\n"
                            + "\n".join(f"• {issue}" for issue in issues),
                            title="Verification Issues",
                            border_style="yellow",
                        )
                    )
                    console.print("\nRun [cyan]aicippy install[/cyan] to fix issues.")
                    raise typer.Exit(1)
                return

            # Run installation
            result = asyncio.run(
                install_aicippy(console=console, show_progress=show_progress)
            )

            if result.success:
                console.print(
                    Panel(
                        f"[green]Installation successful![/green]\n\n"
                        f"Version: {result.version}\n"
                        f"Phases completed: {len(result.phases_completed)}\n\n"
                        + (
                            "[yellow]Note: Restart your terminal for PATH changes.[/yellow]\n\n"
                            if result.requires_restart
                            else ""
                        )
                        + "Run [cyan]aicippy[/cyan] to start.",
                        title="Installation Complete",
                        border_style="green",
                    )
                )

                if result.warnings:
                    console.print("\n[yellow]Warnings:[/yellow]")
                    for warning in result.warnings:
                        console.print(f"  • {warning}")

            else:
                console.print(
                    Panel(
                        "[red]Installation failed![/red]\n\n"
                        + "\n".join(f"• {error}" for error in result.errors),
                        title="Installation Failed",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

        except typer.Exit:
            raise
        except Exception as e:
            logger.exception("install_failed", error=str(e))
            error_console.print(f"[red]Installation error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def session(
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            "-s",
            help="Show current session info",
        ),
    ] = True,
    refresh: Annotated[
        bool,
        typer.Option(
            "--refresh",
            "-r",
            help="Refresh session (extend timeout)",
        ),
    ] = False,
) -> None:
    """
    View or manage your AiCippy session.

    Sessions expire after 12 hours of inactivity.
    Use --refresh to extend your session timeout.
    """
    with CorrelationContext() as ctx:
        logger.info("session_command", correlation_id=ctx.correlation_id)

        try:
            session_mgr = get_session_manager()
            validation = session_mgr.validate()

            if refresh:
                if validation.needs_login:
                    console.print("[yellow]No active session to refresh.[/yellow]")
                    console.print("Run [cyan]aicippy login[/cyan] to start a new session.")
                    return

                success, message = session_mgr.refresh()
                if success:
                    console.print("[green]Session refreshed![/green]")
                    console.print("Session extended for another 12 hours.")
                else:
                    console.print(f"[yellow]Could not refresh: {message}[/yellow]")
                return

            # Show session info
            if validation.needs_login:
                console.print(
                    Panel(
                        f"[yellow]{validation.message}[/yellow]\n\n"
                        f"Status: {validation.status}\n\n"
                        f"Run [cyan]aicippy login[/cyan] to authenticate.",
                        title="No Active Session",
                        border_style="yellow",
                    )
                )
            else:
                session = validation.session
                hours_remaining = session.hours_remaining

                # Determine status color
                if hours_remaining > 6:
                    status_style = "green"
                elif hours_remaining > 2:
                    status_style = "yellow"
                else:
                    status_style = "red"

                session_table = Table.grid(padding=(0, 2))
                session_table.add_column(style="cyan")
                session_table.add_column(style="white")

                session_table.add_row("User:", session.username)
                session_table.add_row("Email:", session.email)
                session_table.add_row("Created:", session.created_at.strftime("%Y-%m-%d %H:%M UTC"))
                session_table.add_row("Last Activity:", session.last_activity.strftime("%Y-%m-%d %H:%M UTC"))
                session_table.add_row(
                    "Expires In:",
                    f"[{status_style}]{hours_remaining:.1f} hours[/{status_style}]"
                )
                session_table.add_row("Device ID:", session.device_id[:8] + "...")

                console.print(
                    Panel(
                        session_table,
                        title="Session Information",
                        border_style="blue",
                    )
                )

                if hours_remaining < 2:
                    console.print(
                        "\n[yellow]Your session is expiring soon. "
                        "Run [cyan]aicippy session --refresh[/cyan] to extend.[/yellow]"
                    )

        except Exception as e:
            logger.exception("session_failed", error=str(e))
            error_console.print(f"[red]Session error: {e}[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
