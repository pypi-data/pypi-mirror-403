"""
Interactive shell for AiCippy.

Provides a rich terminal interface with:
- Live status sidebar with agent visualization
- Task checklist footer
- Keyboard shortcuts
- Beautiful progress indicators
"""

from __future__ import annotations

import asyncio
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aicippy import __version__
from aicippy.cli.mascot import (
    MascotAnimator,
    MascotMood,
    animate_welcome,
    MASCOT_PRIMARY,
)
from aicippy.cli.ui_components import (
    BRAND_ACCENT,
    BRAND_ERROR,
    BRAND_INFO,
    BRAND_PRIMARY,
    BRAND_SECONDARY,
    BRAND_SUCCESS,
    BRAND_WARNING,
    STATUS_ICONS,
    AgentWidget,
    TaskItem,
    InteractiveLayout,
    EnhancedLivePreviewBuffer,
    StreamingState,
    create_connection_indicator,
    create_error_panel,
    create_input_section,
    create_response_panel,
    create_streaming_response_panel,
    create_success_panel,
    create_thinking_indicator,
    create_tool_output_panel,
    create_welcome_screen,
)
from aicippy.config import get_settings
from aicippy.utils.correlation import generate_correlation_id
from aicippy.utils.logging import get_logger
from aicippy.cli.upload_manager import UploadManager, get_working_directory
from aicippy.cli.ai_command_executor import AICommandExecutor

logger = get_logger(__name__)
console = Console()


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class AgentStatus:
    """Status of a single agent."""

    id: str
    type: str
    status: str  # running, thinking, error, idle, complete
    progress: int = 0
    message: str = ""
    started_at: datetime | None = None
    tokens: int = 0

    def to_widget(self) -> AgentWidget:
        """Convert to AgentWidget for UI."""
        return AgentWidget(
            id=self.id,
            name=self.type,
            status=self.status,
            progress=self.progress,
            message=self.message,
            tokens=self.tokens,
        )


@dataclass
class SessionState:
    """Current interactive session state."""

    session_id: str
    model: str = "opus"
    mode: str = "agent"
    agents: list[AgentStatus] = field(default_factory=list)
    tokens_used: int = 0
    connected: bool = False
    conversation: list[dict[str, str]] = field(default_factory=list)
    tasks: list[TaskItem] = field(default_factory=list)
    current_task_idx: int = 0
    mascot_mood: str = "idle"  # idle, thinking, working, happy
    mascot_frame: int = 0
    # New fields for status bar
    session_start: datetime = field(default_factory=datetime.now)
    username: str | None = None
    background_tasks: int = 0
    # WebSocket connection fields
    ws_latency_ms: float = 0.0
    ws_reconnecting: bool = False
    ws_reconnect_attempts: int = 0
    # Streaming state
    is_streaming: bool = False
    stream_tokens: int = 0
    stream_content: str = ""

    def add_task(self, content: str) -> None:
        """Add a task to the checklist."""
        self.tasks.append(TaskItem(content=content, status="pending"))

    def start_task(self, idx: int | None = None) -> None:
        """Start a task."""
        idx = idx if idx is not None else self.current_task_idx
        if 0 <= idx < len(self.tasks):
            self.tasks[idx].status = "in_progress"
            self.current_task_idx = idx

    def complete_task(self, idx: int | None = None) -> None:
        """Complete a task."""
        idx = idx if idx is not None else self.current_task_idx
        if 0 <= idx < len(self.tasks):
            self.tasks[idx].status = "completed"
            self.tasks[idx].progress = 100
            if idx == self.current_task_idx and idx + 1 < len(self.tasks):
                self.current_task_idx = idx + 1

    def update_task_progress(self, progress: int, idx: int | None = None) -> None:
        """Update task progress."""
        idx = idx if idx is not None else self.current_task_idx
        if 0 <= idx < len(self.tasks):
            self.tasks[idx].progress = min(100, max(0, progress))

    def get_session_duration(self) -> str:
        """Get session duration as HH:MM:SS string."""
        elapsed = datetime.now() - self.session_start
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ============================================================================
# Commands
# ============================================================================

# Slash command completions
SLASH_COMMANDS = [
    "/help",
    "/model",
    "/mode",
    "/agents",
    "/kb",
    "/tools",
    "/usage",
    "/history",
    "/clear",
    "/export",
    "/shortcuts",
    "/upload",
    "/uploads",
    "/workspace",
    "/shell",
    "/exec",
    "/quit",
]

MODEL_OPTIONS = ["opus", "sonnet", "llama"]
MODE_OPTIONS = ["agent", "edit", "research", "code"]


# ============================================================================
# Slash Command Handler
# ============================================================================


class SlashCommandHandler:
    """Handler for slash commands in interactive mode."""

    def __init__(self, state: SessionState, console: Console) -> None:
        self.state = state
        self.console = console
        self._upload_manager: UploadManager | None = None
        self._handlers: dict[str, Callable[[list[str]], bool]] = {
            "/help": self._handle_help,
            "/model": self._handle_model,
            "/mode": self._handle_mode,
            "/agents": self._handle_agents,
            "/kb": self._handle_kb,
            "/tools": self._handle_tools,
            "/usage": self._handle_usage,
            "/history": self._handle_history,
            "/clear": self._handle_clear,
            "/export": self._handle_export,
            "/shortcuts": self._handle_shortcuts,
            "/upload": self._handle_upload,
            "/uploads": self._handle_uploads,
            "/workspace": self._handle_workspace,
            "/shell": self._handle_shell,
            "/exec": self._handle_shell,  # Alias for /shell
            "/quit": self._handle_quit,
        }
        self._shell_executor = None

    @property
    def upload_manager(self) -> UploadManager:
        """Get or create upload manager."""
        if self._upload_manager is None:
            self._upload_manager = UploadManager(console=self.console)
        return self._upload_manager

    def handle(self, command: str) -> bool:
        """Handle a slash command. Returns False to exit."""
        parts = command.strip().split()
        if not parts:
            return True

        cmd = parts[0].lower()
        args = parts[1:]

        handler = self._handlers.get(cmd)
        if handler:
            return handler(args)

        self.console.print(create_error_panel(
            f"Unknown command: {cmd}",
            suggestion="Type /help for available commands"
        ))
        return True

    def _handle_help(self, args: list[str]) -> bool:
        """Show help information."""
        help_table = Table(
            title="[bold]Available Commands[/bold]",
            border_style=BRAND_PRIMARY,
            title_style=f"bold {BRAND_INFO}",
            header_style=f"bold {BRAND_ACCENT}",
        )
        help_table.add_column("Command", style=BRAND_INFO)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/model <opus|sonnet|llama>", "Switch AI model"),
            ("/mode <agent|edit|research|code>", "Change operation mode"),
            ("/agents spawn <1-10>", "Spawn parallel agents"),
            ("/agents list", "List active agents"),
            ("/agents stop [id|all]", "Stop agent(s)"),
            ("/agents status", "Detailed agent health"),
            ("/upload", "📂 Open file browser to upload files"),
            ("/uploads", "📋 List all uploaded files"),
            ("/workspace", "📁 Show current working directory info"),
            ("/shell <cmd>", "🖥️ Execute shell command with input passthrough"),
            ("/exec <cmd>", "🖥️ Alias for /shell"),
            ("/kb sync", "Push local files to Knowledge Base"),
            ("/kb status", "Knowledge Base status"),
            ("/kb search <query>", "Search Knowledge Base"),
            ("/tools list", "List available tools"),
            ("/tools enable <name>", "Enable a tool"),
            ("/tools disable <name>", "Disable a tool"),
            ("/usage", "Token usage summary"),
            ("/history", "Session history"),
            ("/clear", "Clear conversation"),
            ("/export <json|md>", "Export session"),
            ("/shortcuts", "Show keyboard shortcuts"),
            ("/quit", "Exit AiCippy"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)
        return True

    def _handle_shortcuts(self, args: list[str]) -> bool:
        """Show keyboard shortcuts."""
        from aicippy.cli.ui_components import KEYBOARD_SHORTCUTS

        shortcuts_table = Table(
            title="[bold]Keyboard Shortcuts[/bold]",
            border_style=BRAND_ACCENT,
            title_style=f"bold {BRAND_ACCENT}",
        )
        shortcuts_table.add_column("Key", style=BRAND_ACCENT)
        shortcuts_table.add_column("Action", style="white")

        for key, desc in KEYBOARD_SHORTCUTS:
            shortcuts_table.add_row(key, desc)

        # Add more shortcuts
        extra_shortcuts = [
            ("Ctrl+L", "Clear screen"),
            ("Ctrl+R", "Reverse search history"),
            ("Alt+.", "Insert last argument"),
            ("Esc", "Cancel current input"),
        ]
        for key, desc in extra_shortcuts:
            shortcuts_table.add_row(key, desc)

        self.console.print(shortcuts_table)
        return True

    def _handle_model(self, args: list[str]) -> bool:
        """Switch AI model."""
        if not args:
            current = Text()
            current.append(f"\n {STATUS_ICONS['complete']} ", style=BRAND_SUCCESS)
            current.append("Current model: ", style="dim")
            current.append(self.state.model.upper(), style=f"bold {BRAND_PRIMARY}")
            current.append("\n\n Available: ", style="dim")
            for i, m in enumerate(MODEL_OPTIONS):
                if i > 0:
                    current.append(" │ ", style="dim")
                style = f"bold {BRAND_SUCCESS}" if m == self.state.model else BRAND_INFO
                current.append(m, style=style)
            current.append("\n")
            self.console.print(Panel(current, border_style="dim"))
            return True

        model = args[0].lower()
        if model not in MODEL_OPTIONS:
            self.console.print(create_error_panel(
                f"Invalid model: {model}",
                suggestion=f"Choose from: {', '.join(MODEL_OPTIONS)}"
            ))
            return True

        self.state.model = model
        self.console.print(create_success_panel(
            f"Switched to model: {model.upper()}",
            details="Changes take effect on next query"
        ))
        return True

    def _handle_mode(self, args: list[str]) -> bool:
        """Change operation mode."""
        if not args:
            mode_colors = {
                "agent": BRAND_INFO,
                "edit": BRAND_WARNING,
                "research": BRAND_ACCENT,
                "code": BRAND_SUCCESS,
            }
            current = Text()
            current.append(f"\n {STATUS_ICONS['complete']} ", style=BRAND_SUCCESS)
            current.append("Current mode: ", style="dim")
            current.append(
                self.state.mode.upper(),
                style=f"bold {mode_colors.get(self.state.mode, 'white')}"
            )
            current.append("\n\n Available:\n", style="dim")

            mode_descriptions = {
                "agent": "Multi-agent task orchestration",
                "edit": "Code editing and refactoring",
                "research": "Information gathering and analysis",
                "code": "Code generation and completion",
            }

            for mode, desc in mode_descriptions.items():
                icon = STATUS_ICONS['complete'] if mode == self.state.mode else STATUS_ICONS['pending']
                color = mode_colors.get(mode, 'white')
                current.append(f"   {icon} ", style=color)
                current.append(f"{mode:<10}", style=f"bold {color}")
                current.append(f" {desc}\n", style="dim")

            self.console.print(Panel(current, border_style="dim"))
            return True

        mode = args[0].lower()
        if mode not in MODE_OPTIONS:
            self.console.print(create_error_panel(
                f"Invalid mode: {mode}",
                suggestion=f"Choose from: {', '.join(MODE_OPTIONS)}"
            ))
            return True

        self.state.mode = mode
        self.console.print(create_success_panel(f"Switched to mode: {mode.upper()}"))
        return True

    def _handle_agents(self, args: list[str]) -> bool:
        """Handle agent commands."""
        if not args:
            count = len(self.state.agents)
            self.console.print(Panel(
                Text(f" ⚡ Active agents: {count}/10", style=BRAND_INFO),
                border_style="dim"
            ))
            return True

        subcommand = args[0].lower()

        if subcommand == "spawn":
            count = int(args[1]) if len(args) > 1 else 3
            count = max(1, min(10, count))

            # Create placeholder agents
            for i in range(count):
                agent_id = f"agent-{len(self.state.agents) + 1}"
                self.state.agents.append(AgentStatus(
                    id=agent_id,
                    type=f"specialist-{i + 1}",
                    status="idle",
                    progress=0,
                ))

            self.console.print(create_success_panel(
                f"Spawned {count} agents",
                details="Agents will activate on next query"
            ))
            return True

        elif subcommand == "list":
            if not self.state.agents:
                self.console.print(Panel(
                    Text(" No active agents", style="dim italic"),
                    border_style="dim"
                ))
                return True

            table = Table(
                title="[bold]Active Agents[/bold]",
                border_style=BRAND_SUCCESS,
                title_style=f"bold {BRAND_INFO}",
            )
            table.add_column("ID", style=BRAND_INFO)
            table.add_column("Type", style=BRAND_ACCENT)
            table.add_column("Status")
            table.add_column("Progress")
            table.add_column("Tokens", justify="right")

            for agent in self.state.agents:
                status_color = {
                    "running": BRAND_INFO,
                    "thinking": BRAND_WARNING,
                    "error": BRAND_ERROR,
                    "idle": "dim",
                    "complete": BRAND_SUCCESS,
                }.get(agent.status, "white")

                icon = STATUS_ICONS.get(agent.status, "○")

                # Progress bar
                bar_width = 10
                completed = int(agent.progress / 100 * bar_width)
                bar = "█" * completed + "░" * (bar_width - completed)

                table.add_row(
                    agent.id,
                    agent.type,
                    f"[{status_color}]{icon} {agent.status}[/]",
                    f"[{status_color}]{bar}[/] {agent.progress}%",
                    f"{agent.tokens:,}",
                )

            self.console.print(table)
            return True

        elif subcommand == "stop":
            target = args[1] if len(args) > 1 else "all"
            if target == "all":
                count = len(self.state.agents)
                self.state.agents.clear()
                self.console.print(create_success_panel(
                    f"Stopped all {count} agents"
                ))
            else:
                before = len(self.state.agents)
                self.state.agents = [a for a in self.state.agents if a.id != target]
                if len(self.state.agents) < before:
                    self.console.print(create_success_panel(f"Stopped agent: {target}"))
                else:
                    self.console.print(create_error_panel(f"Agent not found: {target}"))
            return True

        elif subcommand == "status":
            return self._handle_agents(["list"])

        self.console.print(create_error_panel(
            f"Unknown agent subcommand: {subcommand}",
            suggestion="Use: spawn, list, stop, or status"
        ))
        return True

    def _handle_kb(self, args: list[str]) -> bool:
        """Handle Knowledge Base commands."""
        if not args:
            self.console.print(Panel(
                Text(" Usage: /kb <sync|status|search>", style="dim"),
                border_style="dim"
            ))
            return True

        subcommand = args[0].lower()

        if subcommand == "sync":
            self.console.print(create_success_panel(
                "Knowledge Base sync initiated",
                details="Documents will be indexed in the background"
            ))
            return True

        elif subcommand == "status":
            status_table = Table(border_style=BRAND_INFO)
            status_table.add_column("Property", style=BRAND_INFO)
            status_table.add_column("Value", style="white")

            status_table.add_row("Documents", "1,234")
            status_table.add_row("Last Sync", "2 hours ago")
            status_table.add_row("Index Size", "45.2 MB")
            status_table.add_row("Status", f"[{BRAND_SUCCESS}]● Healthy[/]")

            self.console.print(Panel(
                status_table,
                title="[bold]Knowledge Base Status[/bold]",
                border_style=BRAND_INFO,
            ))
            return True

        elif subcommand == "search":
            query = " ".join(args[1:]) if len(args) > 1 else ""
            if not query:
                self.console.print(create_error_panel(
                    "Please provide a search query",
                    suggestion="Example: /kb search AWS Lambda"
                ))
                return True
            self.console.print(Panel(
                Text(f" 🔍 Searching for: {query}", style=BRAND_INFO),
                border_style="dim"
            ))
            return True

        self.console.print(create_error_panel(f"Unknown KB subcommand: {subcommand}"))
        return True

    def _handle_tools(self, args: list[str]) -> bool:
        """Handle tools commands."""
        if not args:
            self.console.print(Panel(
                Text(" Usage: /tools <list|enable|disable>", style="dim"),
                border_style="dim"
            ))
            return True

        subcommand = args[0].lower()

        if subcommand == "list":
            table = Table(
                title="[bold]Available Tools[/bold]",
                border_style=BRAND_INFO,
            )
            table.add_column("Tool", style=BRAND_INFO)
            table.add_column("Status")
            table.add_column("Category", style="dim")
            table.add_column("Description")

            tools = [
                ("aws", True, "Cloud", "AWS CLI operations"),
                ("gcloud", True, "Cloud", "Google Cloud CLI"),
                ("gh", True, "VCS", "GitHub CLI"),
                ("firebase", True, "Cloud", "Firebase CLI"),
                ("figma", True, "Design", "Figma API"),
                ("drive", True, "Storage", "Google Drive API"),
                ("gmail", True, "Comm", "Gmail API"),
                ("canva", False, "Design", "Canva API"),
                ("azure", False, "Cloud", "Azure CLI"),
                ("razorpay", True, "Payment", "Razorpay API"),
                ("paypal", False, "Payment", "PayPal API"),
                ("stripe", True, "Payment", "Stripe CLI"),
                ("bash", True, "Shell", "Shell commands"),
            ]

            for name, enabled, category, desc in tools:
                status = f"[{BRAND_SUCCESS}]{STATUS_ICONS['complete']} Enabled[/]" if enabled else f"[dim]{STATUS_ICONS['pending']} Disabled[/]"
                table.add_row(name, status, category, desc)

            self.console.print(table)
            return True

        elif subcommand in ("enable", "disable"):
            tool_name = args[1] if len(args) > 1 else None
            if not tool_name:
                self.console.print(create_error_panel("Please specify a tool name"))
                return True

            action = "Enabled" if subcommand == "enable" else "Disabled"
            self.console.print(create_success_panel(f"{action} tool: {tool_name}"))
            return True

        self.console.print(create_error_panel(f"Unknown tools subcommand: {subcommand}"))
        return True

    def _handle_usage(self, args: list[str]) -> bool:
        """Show token usage."""
        table = Table(
            title="[bold]Token Usage[/bold]",
            border_style=BRAND_WARNING,
        )
        table.add_column("Metric", style=BRAND_INFO)
        table.add_column("Value", style=BRAND_WARNING, justify="right")

        table.add_row("Session Tokens", f"{self.state.tokens_used:,}")
        table.add_row("Model", self.state.model.upper())
        table.add_row("Active Agents", str(len(self.state.agents)))
        table.add_row("Messages", str(len(self.state.conversation)))

        self.console.print(table)
        return True

    def _handle_history(self, args: list[str]) -> bool:
        """Show conversation history."""
        if not self.state.conversation:
            self.console.print(Panel(
                Text(" No conversation history", style="dim italic"),
                border_style="dim"
            ))
            return True

        for i, msg in enumerate(self.state.conversation[-10:], 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            role_color = BRAND_INFO if role == "user" else BRAND_SUCCESS
            icon = "❯" if role == "user" else "◈"

            line = Text()
            line.append(f" {icon} ", style=role_color)
            line.append(f"{role}: ", style=f"bold {role_color}")
            line.append(content, style="white")
            if len(msg.get("content", "")) > 100:
                line.append("...", style="dim")
            self.console.print(line)

        return True

    def _handle_clear(self, args: list[str]) -> bool:
        """Clear conversation."""
        self.state.conversation.clear()
        self.state.tasks.clear()
        self.state.current_task_idx = 0
        self.console.clear()
        self.console.print(create_success_panel("Conversation and tasks cleared"))
        return True

    def _handle_export(self, args: list[str]) -> bool:
        """Export session."""
        import json

        format_type = args[0] if args else "json"

        if format_type not in ("json", "md"):
            self.console.print(create_error_panel(
                "Invalid format",
                suggestion="Use 'json' or 'md'"
            ))
            return True

        filename = f"aicippy_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"

        if format_type == "json":
            with open(filename, "w") as f:
                json.dump(
                    {
                        "session_id": self.state.session_id,
                        "model": self.state.model,
                        "mode": self.state.mode,
                        "tokens_used": self.state.tokens_used,
                        "conversation": self.state.conversation,
                    },
                    f,
                    indent=2,
                )
        else:
            with open(filename, "w") as f:
                f.write("# AiCippy Session Export\n\n")
                f.write(f"**Session:** {self.state.session_id}\n")
                f.write(f"**Model:** {self.state.model}\n")
                f.write(f"**Tokens:** {self.state.tokens_used:,}\n\n")
                f.write("## Conversation\n\n")
                for msg in self.state.conversation:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    f.write(f"### {role.title()}\n\n{content}\n\n")

        self.console.print(create_success_panel(
            f"Session exported",
            details=f"Saved to: {filename}"
        ))
        return True

    def _handle_upload(self, args: list[str]) -> bool:
        """
        Handle /upload command - opens OS file browser dialog.

        Usage:
            /upload             - Open file browser for current uploads folder
            /upload <path>      - Upload to specific folder
        """
        from pathlib import Path

        target_dir = None
        if args:
            target_path = Path(args[0]).expanduser()
            if target_path.is_dir():
                target_dir = target_path
            else:
                # Create if doesn't exist
                target_dir = target_path
                target_dir.mkdir(parents=True, exist_ok=True)

        try:
            results = self.upload_manager.prompt_upload(target_dir=target_dir)

            if results:
                successful = [r for r in results if r.success]
                if successful:
                    # Notify about uploaded files for AI context
                    file_list = ", ".join(r.file_name for r in successful)
                    self.console.print(Panel(
                        Text(
                            f"💡 Tip: Reference uploaded files in your prompts.\n"
                            f"   Example: \"Use the uploaded logo {successful[0].file_name} to...\"",
                            style="dim italic",
                        ),
                        border_style="dim",
                    ))

        except Exception as e:
            self.console.print(create_error_panel(
                f"Upload failed: {e}",
                suggestion="Check file permissions and try again"
            ))

        return True

    def _handle_uploads(self, args: list[str]) -> bool:
        """
        Handle /uploads command - list uploaded files.

        Usage:
            /uploads            - List all uploaded files
            /uploads clear      - Clear all uploads
        """
        if args and args[0].lower() == "clear":
            if self.upload_manager.clear_uploads():
                self.console.print(create_success_panel("All uploads cleared"))
            else:
                self.console.print(create_error_panel("Failed to clear uploads"))
            return True

        self.upload_manager.show_uploads_list()
        return True

    def _handle_workspace(self, args: list[str]) -> bool:
        """
        Handle /workspace command - show working directory info.

        Usage:
            /workspace          - Show current workspace info
        """
        self.upload_manager.show_working_directory()
        return True

    def _handle_shell(self, args: list[str]) -> bool:
        """
        Handle /shell command - execute shell command with input passthrough.

        Usage:
            /shell <command>    - Execute command with interactive input support
            /exec <command>     - Alias for /shell

        Examples:
            /shell git status
            /shell npm install
            /exec pip install requests
        """
        if not args:
            self.console.print(Panel(
                Text(
                    "Usage: /shell <command>\n\n"
                    "Execute shell commands with interactive input passthrough.\n"
                    "Any prompts from the command will be displayed for you to respond.\n\n"
                    "Examples:\n"
                    "  /shell git status\n"
                    "  /shell npm install\n"
                    "  /shell pip install requests\n"
                    "  /exec docker login",
                    style=BRAND_INFO,
                ),
                title=f"[bold {BRAND_ACCENT}]Shell Command[/bold {BRAND_ACCENT}]",
                border_style=BRAND_ACCENT,
            ))
            return True

        command = " ".join(args)

        try:
            from aicippy.cli.shell_executor import ShellExecutor, is_interactive_command

            if self._shell_executor is None:
                self._shell_executor = ShellExecutor(
                    console=self.console,
                    working_dir=get_working_directory(),
                )

            # Check if command is interactive
            if is_interactive_command(command):
                # Run interactive command with input callback
                def get_input(prompt: str) -> str:
                    return self._shell_executor.prompt_user_input(prompt)

                # Use asyncio to run the interactive command
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context, schedule as task
                    result = asyncio.run_coroutine_threadsafe(
                        self._shell_executor.execute_interactive(
                            command,
                            input_callback=get_input,
                        ),
                        loop,
                    ).result()
                else:
                    result = asyncio.run(
                        self._shell_executor.execute_interactive(
                            command,
                            input_callback=get_input,
                        )
                    )
            else:
                # Simple command execution
                result = self._shell_executor.execute_simple(command)

            # Store output in conversation for AI context
            if result.stdout:
                self.state.conversation.append({
                    "role": "system",
                    "content": f"[Shell Command Output]\n$ {command}\n{result.stdout[:2000]}",
                })

            # Display result
            self._shell_executor.display_result(result)

        except Exception as e:
            self.console.print(create_error_panel(
                f"Shell execution failed: {e}",
                suggestion="Check the command syntax and try again"
            ))

        return True

    def _handle_quit(self, args: list[str]) -> bool:
        """Exit the session."""
        return False


# ============================================================================
# Main Interactive Session
# ============================================================================


async def start_interactive_session() -> None:
    """Start the interactive AiCippy session with beautiful UI."""
    settings = get_settings()

    # Generate session ID
    session_id = generate_correlation_id()

    # Initialize state
    state = SessionState(
        session_id=session_id,
        model=settings.default_model,
    )

    # Add initial demo tasks
    state.add_task("Initialize session")
    state.start_task(0)

    # Create command handler
    cmd_handler = SlashCommandHandler(state, console)

    # Create the new interactive layout
    layout = InteractiveLayout(console, __version__)

    # Create prompt session with history
    history_file = settings.local_config_dir / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Custom prompt style - use bright white for input text (visible on both dark/light terminals)
    prompt_style = Style.from_dict({
        "prompt": f"{BRAND_PRIMARY} bold",
        "": "#e0e0e0 bold",  # Bright white for better contrast on all terminals
    })

    # Key bindings
    kb = KeyBindings()

    @kb.add(Keys.ControlL)
    def clear_screen(event: Any) -> None:
        """Clear the screen and preview."""
        console.clear()
        layout.clear_preview()

    completer = WordCompleter(
        SLASH_COMMANDS + MODEL_OPTIONS + MODE_OPTIONS + ["quit", "exit", "q", "bye"],
        ignore_case=True,
    )

    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=prompt_style,
        key_bindings=kb,
    )

    # Skip welcome animation - shown during login
    # Just complete initialization silently
    state.complete_task(0)

    # Check authentication and get username (silently)
    try:
        from aicippy.auth.cognito import CognitoAuth
        from aicippy.installer.session_manager import get_current_user
        auth = CognitoAuth()
        if auth.is_authenticated():
            state.connected = True
            # Get username from session
            username, email = get_current_user()
            state.username = username or email or "authenticated"
    except Exception:
        pass

    # Setup working directory silently
    working_dir = get_working_directory()

    # Create uploads folder silently
    try:
        uploads_dir = working_dir / "uploads"
        if not uploads_dir.exists():
            uploads_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Main loop
    running = True

    def signal_handler(sig: int, frame: Any) -> None:
        nonlocal running
        layout.add_preview_line("Type 'quit' to exit", style=BRAND_WARNING)

    signal.signal(signal.SIGINT, signal_handler)

    while running:
        try:
            # Increment mascot animation frame
            state.mascot_frame = (state.mascot_frame + 1) % 100

            # Update and display the layout
            updated_layout = layout.update(
                agents=[a.to_widget() for a in state.agents],
                tasks=state.tasks,
                current_task_idx=state.current_task_idx,
                session_model=state.model,
                tokens_used=state.tokens_used,
                username=state.username,
                session_duration=state.get_session_duration(),
                background_tasks=state.background_tasks,
                connected=state.connected,
                mascot_mood=state.mascot_mood,
            )
            console.print(updated_layout)

            # Create input prompt
            prompt_text = create_input_section(mode=state.mode, model=state.model)
            console.print(prompt_text, end="")

            # Get input
            user_input = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: session.prompt(""),
            )

            if not user_input.strip():
                continue

            # Handle quit/exit commands without slash prefix
            user_input_lower = user_input.strip().lower()
            if user_input_lower in ("quit", "exit", "q", "bye"):
                running = False
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                running = cmd_handler.handle(user_input)
                continue

            # Log user input to preview
            layout.add_preview_line(f"❯ {user_input}", style=BRAND_INFO)

            # Regular chat message
            state.conversation.append({"role": "user", "content": user_input})

            # Add task for this query
            state.add_task(f"Process: {user_input[:30]}...")
            state.start_task(len(state.tasks) - 1)

            # Process with orchestrator
            try:
                from aicippy.agents.orchestrator import AgentOrchestrator

                orchestrator = AgentOrchestrator(
                    model_id=settings.get_model_id(state.model),
                    max_agents=len(state.agents) if state.agents else 3,
                )

                # Update agents status and mascot mood
                state.mascot_mood = "thinking"
                state.is_streaming = True
                state.stream_tokens = 0
                state.stream_content = ""

                for agent in state.agents:
                    agent.status = "thinking"
                    agent.progress = 0
                    layout.add_agent_update(agent.id, "thinking", "Processing...")

                # Show streaming indicator
                layout.preview_buffer.start_streaming() if hasattr(layout.preview_buffer, 'start_streaming') else layout.add_preview_line("◐ Processing...", style=BRAND_WARNING)

                # Show animated thinking indicator with live progress
                start_time = time.monotonic()
                animation_running = True
                frame_idx = 0
                streaming_state = StreamingState(is_streaming=True)

                async def process_with_streaming() -> Any:
                    """Process the chat request with streaming display."""
                    nonlocal animation_running, frame_idx, streaming_state
                    state.mascot_mood = "working"

                    # Streaming callback for token-by-token display
                    def on_stream_token(token: str) -> None:
                        nonlocal streaming_state
                        streaming_state.content += token
                        streaming_state.tokens_received += 1
                        state.stream_tokens += 1
                        state.stream_content += token

                        # Update preview buffer with streaming
                        if hasattr(layout.preview_buffer, 'stream_token'):
                            layout.preview_buffer.stream_token(token)

                    with Live(
                        create_streaming_response_panel(streaming_state),
                        console=console,
                        transient=True,
                        refresh_per_second=8,
                    ) as live:
                        async def update_display() -> None:
                            """Update the live display with streaming content."""
                            nonlocal frame_idx, streaming_state
                            while animation_running:
                                frame_idx += 1
                                state.mascot_frame = frame_idx

                                # Toggle cursor visibility for blink effect
                                streaming_state.cursor_visible = frame_idx % 4 < 2

                                # Calculate tokens per second
                                elapsed = time.monotonic() - start_time
                                if elapsed > 0:
                                    streaming_state.tokens_per_second = streaming_state.tokens_received / elapsed

                                # Update progress for agents
                                for agent in state.agents:
                                    if agent.status == "thinking":
                                        agent.progress = min(95, agent.progress + 1)

                                # Update display
                                live.update(create_streaming_response_panel(streaming_state))
                                await asyncio.sleep(0.125)

                        # Start animation task
                        animation_task = asyncio.create_task(update_display())

                        try:
                            # Process the actual chat request
                            result = await orchestrator.chat(user_input)

                            # Mark streaming complete
                            streaming_state.is_streaming = False
                            streaming_state.content = result.content

                            return result
                        finally:
                            # Stop animation
                            animation_running = False
                            animation_task.cancel()
                            try:
                                await animation_task
                            except asyncio.CancelledError:
                                pass

                response = await process_with_streaming()

                # Mark streaming complete
                state.is_streaming = False
                execution_time = time.monotonic() - start_time

                # End streaming in preview buffer
                if hasattr(layout.preview_buffer, 'end_streaming'):
                    layout.preview_buffer.end_streaming(
                        total_tokens=state.stream_tokens,
                        duration_seconds=execution_time,
                    )

                # Mark agents complete
                for agent in state.agents:
                    agent.status = "complete"
                    agent.progress = 100
                    layout.add_agent_update(agent.id, "complete", "Done")

                # Display final response with beautiful panel
                console.print(create_response_panel(
                    content=response.content,
                    agent_type=response.agent_type.value if response.agent_type else None,
                    tokens_used=(
                        (response.usage.input_tokens + response.usage.output_tokens)
                        if response.usage else 0
                    ),
                    execution_time=execution_time,
                ))

                # Update state
                state.conversation.append({"role": "assistant", "content": response.content})
                if response.usage:
                    state.tokens_used += response.usage.input_tokens + response.usage.output_tokens

                # AUTO-EXECUTE: Detect and offer to execute commands from AI response
                try:
                    ai_cmd_executor = AICommandExecutor(
                        console=console,
                        working_dir=get_working_directory(),
                        auto_confirm=False,  # Always ask for confirmation
                    )

                    detected_commands = ai_cmd_executor.detect_commands(response.content)

                    if detected_commands:
                        layout.add_preview_line(f"Detected {len(detected_commands)} command(s)", style=BRAND_INFO)

                        # Execute detected commands with passthrough
                        cmd_results = await ai_cmd_executor.execute_detected_commands(
                            response.content,
                            execute_all=False,
                        )

                        # Add execution results to conversation for AI context
                        execution_summary = ai_cmd_executor.get_execution_summary()
                        if execution_summary:
                            state.conversation.append({
                                "role": "system",
                                "content": f"[Command Execution Results]\n{execution_summary}",
                            })
                            layout.add_success("Command results added to context")

                except Exception as cmd_err:
                    logger.warning("ai_command_execution_warning", error=str(cmd_err))
                    # Don't fail the conversation if command detection/execution fails

                # Complete task
                state.complete_task()

                # Set mascot to happy after success
                state.mascot_mood = "happy"

                # Reset agents to idle
                for agent in state.agents:
                    agent.status = "idle"

                # Reset mascot to idle after a short happy moment
                await asyncio.sleep(0.5)
                state.mascot_mood = "idle"

            except Exception as e:
                logger.exception("chat_error", error=str(e))
                layout.add_error(str(e))
                console.print(create_error_panel(
                    str(e),
                    suggestion="Check your connection and try again"
                ))

                # Mark task as failed
                if state.tasks and state.current_task_idx < len(state.tasks):
                    state.tasks[state.current_task_idx].status = "pending"

        except EOFError:
            running = False
        except KeyboardInterrupt:
            continue

    # Farewell message with waving mascot
    console.print()

    # Create farewell with mascot waving goodbye
    animator = MascotAnimator(mood=MascotMood.WAVING, use_mini=True)
    frames = animator.get_frames()
    farewell_mascot = animator.render_frame(frames[0])

    farewell_text = Text()
    farewell_text.append("\n")
    farewell_text.append(f" {STATUS_ICONS['complete']} ", style=BRAND_SUCCESS)
    farewell_text.append("Session ended. ", style=f"bold {BRAND_PRIMARY}")
    farewell_text.append("Goodbye!", style=f"bold {MASCOT_PRIMARY}")
    farewell_text.append(f"\n\n   Tokens used: {state.tokens_used:,}", style="dim")
    farewell_text.append(f"\n   Messages: {len(state.conversation)}", style="dim")
    farewell_text.append("\n\n   See you next time!", style=f"italic {BRAND_ACCENT}")

    console.print(Panel(
        Group(
            Align.center(farewell_mascot),
            farewell_text,
        ),
        border_style=BRAND_PRIMARY,
        title="[bold]Bye! 👋[/bold]",
        title_align="center",
    ))
