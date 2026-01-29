"""
AI Command Executor for AiCippy CLI.

Provides automatic shell command detection and execution with user input
passthrough when AI agents generate commands that need to be run.

Features:
- Parses AI responses for shell command blocks
- Detects suggested commands in various formats
- Executes commands with user confirmation
- Passes user input through for interactive commands
- Returns output to AI for context
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Final

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.text import Text

from aicippy.cli.shell_executor import (
    CommandResult,
    ShellExecutor,
    is_interactive_command,
)
from aicippy.cli.upload_manager import get_working_directory

# Brand colors
BRAND_PRIMARY: Final[str] = "#667eea"
BRAND_SUCCESS: Final[str] = "#10b981"
BRAND_WARNING: Final[str] = "#f59e0b"
BRAND_ERROR: Final[str] = "#ef4444"
BRAND_INFO: Final[str] = "#3b82f6"
BRAND_ACCENT: Final[str] = "#a78bfa"

# Regex patterns for detecting command blocks
CODE_BLOCK_PATTERNS: Final[list[tuple[str, str]]] = [
    # Standard markdown code blocks with language
    (r"```(?:bash|sh|shell|zsh|fish)\n(.*?)```", "bash"),
    (r"```(?:cmd|powershell|ps1)\n(.*?)```", "shell"),
    # Generic code blocks that look like shell commands
    (r"```\n(\$.*?)```", "bash"),
    (r"```\n(>.*?)```", "shell"),
    # Inline code that looks like commands
    (r"`(\$ [^`]+)`", "bash"),
]

# Patterns that indicate a command suggestion
COMMAND_SUGGESTION_PATTERNS: Final[list[str]] = [
    r"(?:run|execute|try|use)(?: the)?(?: command)?:?\s*`([^`]+)`",
    r"you (?:can|should) run:?\s*`([^`]+)`",
    r"(?:run|execute) this:?\s*\n*```(?:bash|sh|shell)?\n(.*?)```",
    r"to (?:install|run|execute|start|deploy|build|test):?\s*\n*```(?:bash|sh|shell)?\n(.*?)```",
]


@dataclass
class DetectedCommand:
    """A command detected from AI response."""

    command: str
    language: str
    context: str  # Surrounding text that suggested this command
    is_suggestion: bool  # True if AI explicitly suggested running this
    line_number: int = 0


@dataclass
class CommandExecutionResult:
    """Result of AI command execution."""

    command: str
    result: CommandResult
    was_executed: bool
    user_declined: bool = False
    error: str = ""


@dataclass
class AICommandExecutionContext:
    """Context for AI command execution session."""

    commands_executed: list[CommandExecutionResult] = field(default_factory=list)
    total_commands_detected: int = 0
    total_commands_run: int = 0
    auto_execute: bool = False  # If True, execute without confirmation


class AICommandExecutor:
    """
    Detects and executes shell commands from AI responses.

    Parses AI output for command blocks and suggestions, prompts user
    for confirmation, and executes commands with input passthrough.
    """

    def __init__(
        self,
        console: Console | None = None,
        working_dir: Path | None = None,
        auto_confirm: bool = False,
    ) -> None:
        """
        Initialize AI command executor.

        Args:
            console: Rich console for output.
            working_dir: Working directory for commands.
            auto_confirm: Auto-confirm safe commands (read-only).
        """
        self.console = console or Console()
        self.working_dir = working_dir or get_working_directory()
        self.auto_confirm = auto_confirm
        self._shell_executor = ShellExecutor(
            console=self.console,
            working_dir=self.working_dir,
        )
        self._context = AICommandExecutionContext()

    def detect_commands(self, ai_response: str) -> list[DetectedCommand]:
        """
        Detect shell commands in AI response.

        Args:
            ai_response: The AI's response text.

        Returns:
            List of detected commands with context.
        """
        commands: list[DetectedCommand] = []
        seen_commands: set[str] = set()

        # First, find explicit code blocks
        for pattern, lang in CODE_BLOCK_PATTERNS:
            for match in re.finditer(pattern, ai_response, re.DOTALL | re.IGNORECASE):
                cmd_text = match.group(1).strip()
                # Clean up the command
                for line in cmd_text.split("\n"):
                    line = line.strip()
                    # Remove common prefixes
                    if line.startswith("$ "):
                        line = line[2:]
                    elif line.startswith("> "):
                        line = line[2:]

                    if line and line not in seen_commands and self._is_valid_command(line):
                        seen_commands.add(line)
                        # Get surrounding context
                        start = max(0, match.start() - 100)
                        end = min(len(ai_response), match.end() + 50)
                        context = ai_response[start:end]

                        commands.append(DetectedCommand(
                            command=line,
                            language=lang,
                            context=context,
                            is_suggestion=self._is_suggestion_context(context),
                            line_number=ai_response[:match.start()].count("\n") + 1,
                        ))

        # Then, find suggested commands
        for pattern in COMMAND_SUGGESTION_PATTERNS:
            for match in re.finditer(pattern, ai_response, re.DOTALL | re.IGNORECASE):
                cmd_text = match.group(1).strip()
                for line in cmd_text.split("\n"):
                    line = line.strip()
                    if line.startswith("$ "):
                        line = line[2:]
                    elif line.startswith("> "):
                        line = line[2:]

                    if line and line not in seen_commands and self._is_valid_command(line):
                        seen_commands.add(line)
                        commands.append(DetectedCommand(
                            command=line,
                            language="bash",
                            context=match.group(0),
                            is_suggestion=True,
                            line_number=ai_response[:match.start()].count("\n") + 1,
                        ))

        self._context.total_commands_detected += len(commands)
        return commands

    def _is_valid_command(self, cmd: str) -> bool:
        """Check if text looks like a valid shell command."""
        if not cmd or len(cmd) < 2:
            return False

        # Skip if it's just a comment
        if cmd.startswith("#"):
            return False

        # Skip if it's a variable assignment without a command
        if "=" in cmd and not any(c in cmd for c in [" ", "|", ";"]):
            return False

        # Must start with a word character (command name)
        if not re.match(r"^[a-zA-Z_/.]", cmd):
            return False

        return True

    def _is_suggestion_context(self, context: str) -> bool:
        """Check if context suggests the AI wants user to run this command."""
        suggestion_keywords = [
            "run", "execute", "try", "use", "install", "should",
            "can run", "following command", "this command",
            "to do this", "you can", "you should",
        ]
        context_lower = context.lower()
        return any(keyword in context_lower for keyword in suggestion_keywords)

    def _is_safe_command(self, cmd: str) -> bool:
        """Check if command is read-only/safe to auto-execute."""
        safe_prefixes = [
            "ls", "pwd", "echo", "cat", "head", "tail",
            "which", "where", "type", "file", "stat",
            "git status", "git log", "git diff", "git branch",
            "npm list", "pip list", "pip show",
            "node --version", "npm --version", "python --version",
            "aws sts get-caller-identity",
        ]
        cmd_lower = cmd.lower().strip()
        return any(cmd_lower.startswith(prefix) for prefix in safe_prefixes)

    def _is_dangerous_command(self, cmd: str) -> bool:
        """Check if command could be dangerous."""
        dangerous_patterns = [
            r"\brm\s+-rf",
            r"\brmdir\s+/",
            r"\bdel\s+/",
            r"\bformat\s+",
            r"\bmkfs\b",
            r"\bdd\s+",
            r">\s*/dev/",
            r"\bsudo\s+rm",
            r"\bchmod\s+777",
            r"\bcurl.*\|\s*(?:bash|sh)",
            r"\bwget.*\|\s*(?:bash|sh)",
            r":\(\)\{.*:\|:.*\}",  # Fork bomb
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return True
        return False

    async def execute_detected_commands(
        self,
        ai_response: str,
        execute_all: bool = False,
        input_callback: Callable[[str], str] | None = None,
    ) -> list[CommandExecutionResult]:
        """
        Detect and execute commands from AI response.

        Args:
            ai_response: The AI's response text.
            execute_all: Execute all commands without individual prompts.
            input_callback: Callback for getting user input during execution.

        Returns:
            List of execution results.
        """
        commands = self.detect_commands(ai_response)

        if not commands:
            return []

        results: list[CommandExecutionResult] = []

        # Show summary of detected commands
        self.console.print(Panel(
            Text(
                f"Detected {len(commands)} command(s) in AI response.\n"
                f"Commands marked as suggestions will be highlighted.",
                style=BRAND_INFO,
            ),
            title=f"[bold {BRAND_ACCENT}]Commands Detected[/bold {BRAND_ACCENT}]",
            border_style=BRAND_ACCENT,
        ))

        for i, detected in enumerate(commands, 1):
            result = await self._execute_single_command(
                detected,
                index=i,
                total=len(commands),
                execute_all=execute_all,
                input_callback=input_callback,
            )
            results.append(result)
            self._context.commands_executed.append(result)

            if result.was_executed:
                self._context.total_commands_run += 1

        return results

    async def _execute_single_command(
        self,
        detected: DetectedCommand,
        index: int,
        total: int,
        execute_all: bool = False,
        input_callback: Callable[[str], str] | None = None,
    ) -> CommandExecutionResult:
        """Execute a single detected command with confirmation."""
        # Display command
        cmd_display = Syntax(
            detected.command,
            detected.language,
            theme="monokai",
            line_numbers=False,
        )

        # Build info text
        info_parts = []
        if detected.is_suggestion:
            info_parts.append("[bold green]AI suggested running this[/bold green]")
        if self._is_safe_command(detected.command):
            info_parts.append("[dim]Read-only/safe command[/dim]")
        if self._is_dangerous_command(detected.command):
            info_parts.append(f"[bold {BRAND_ERROR}]Potentially dangerous[/bold {BRAND_ERROR}]")

        info_text = " | ".join(info_parts) if info_parts else ""

        self.console.print(Panel(
            cmd_display,
            title=f"[bold]Command {index}/{total}[/bold] {info_text}",
            border_style=BRAND_WARNING if self._is_dangerous_command(detected.command) else BRAND_ACCENT,
        ))

        # Determine if we should auto-execute
        should_auto = (
            execute_all
            or self._context.auto_execute
            or (self.auto_confirm and self._is_safe_command(detected.command))
        )

        # Block dangerous commands from auto-execution
        if self._is_dangerous_command(detected.command):
            should_auto = False
            self.console.print(Text(
                "This command requires explicit confirmation due to potential risk.",
                style=BRAND_WARNING,
            ))

        # Ask for confirmation
        if not should_auto:
            try:
                should_execute = Confirm.ask(
                    "Execute this command?",
                    default=detected.is_suggestion,
                )
            except (EOFError, KeyboardInterrupt):
                return CommandExecutionResult(
                    command=detected.command,
                    result=CommandResult(
                        success=False,
                        exit_code=-1,
                        stdout="",
                        stderr="Cancelled by user",
                        command=detected.command,
                    ),
                    was_executed=False,
                    user_declined=True,
                )
        else:
            should_execute = True
            self.console.print(Text(
                "Auto-executing...",
                style="dim italic",
            ))

        if not should_execute:
            return CommandExecutionResult(
                command=detected.command,
                result=CommandResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="User declined",
                    command=detected.command,
                ),
                was_executed=False,
                user_declined=True,
            )

        # Execute the command
        try:
            if is_interactive_command(detected.command):
                # Use interactive execution with passthrough
                def get_input(prompt: str) -> str:
                    if input_callback:
                        return input_callback(prompt)
                    return self._shell_executor.prompt_user_input(prompt)

                result = await self._shell_executor.execute_interactive(
                    detected.command,
                    input_callback=get_input,
                )
            else:
                # Use simple execution
                result = self._shell_executor.execute_simple(detected.command)

            # Display result
            self._shell_executor.display_result(result)

            return CommandExecutionResult(
                command=detected.command,
                result=result,
                was_executed=True,
            )

        except Exception as e:
            error_result = CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                command=detected.command,
            )
            return CommandExecutionResult(
                command=detected.command,
                result=error_result,
                was_executed=True,
                error=str(e),
            )

    def get_execution_summary(self) -> str:
        """Get summary of all command executions for AI context."""
        if not self._context.commands_executed:
            return ""

        parts = ["## Command Execution Summary\n"]
        for result in self._context.commands_executed:
            status = "executed" if result.was_executed else "skipped"
            if result.user_declined:
                status = "declined by user"

            parts.append(f"\n### `{result.command}`")
            parts.append(f"Status: {status}")

            if result.was_executed:
                parts.append(f"Exit code: {result.result.exit_code}")
                if result.result.stdout:
                    # Truncate long output
                    output = result.result.stdout[:1000]
                    if len(result.result.stdout) > 1000:
                        output += "\n... [truncated]"
                    parts.append(f"Output:\n```\n{output}\n```")
                if result.result.stderr:
                    parts.append(f"Errors:\n```\n{result.result.stderr[:500]}\n```")

        return "\n".join(parts)

    def clear_context(self) -> None:
        """Clear execution context for new session."""
        self._context = AICommandExecutionContext()


async def process_ai_response_with_commands(
    ai_response: str,
    console: Console | None = None,
    working_dir: Path | None = None,
    auto_execute_safe: bool = True,
) -> tuple[str, list[CommandExecutionResult]]:
    """
    Process an AI response, detect and execute any commands.

    Args:
        ai_response: The AI's response text.
        console: Rich console for output.
        working_dir: Working directory for commands.
        auto_execute_safe: Auto-execute safe/read-only commands.

    Returns:
        Tuple of (execution_summary, list of results).
    """
    executor = AICommandExecutor(
        console=console,
        working_dir=working_dir,
        auto_confirm=auto_execute_safe,
    )

    results = await executor.execute_detected_commands(ai_response)
    summary = executor.get_execution_summary()

    return summary, results
