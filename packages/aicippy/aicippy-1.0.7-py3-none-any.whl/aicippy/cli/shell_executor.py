"""
Shell Executor with User Input Passthrough for AiCippy CLI.

Provides intelligent command execution with:
- Real-time output streaming
- User input passthrough for interactive commands
- Cross-platform support (Windows/macOS/Linux)
- Command output capture for AI processing
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
from typing import Callable, Final, IO

# Unix-only imports - handle gracefully on Windows
if os.name != "nt":
    import pty
    import select
    import fcntl
else:
    pty = None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    fcntl = None  # type: ignore[assignment]

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

# Brand colors
BRAND_PRIMARY: Final[str] = "#667eea"
BRAND_SUCCESS: Final[str] = "#10b981"
BRAND_WARNING: Final[str] = "#f59e0b"
BRAND_ERROR: Final[str] = "#ef4444"
BRAND_INFO: Final[str] = "#3b82f6"
BRAND_ACCENT: Final[str] = "#a78bfa"


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: str
    duration: float = 0.0
    was_interrupted: bool = False
    user_inputs: list[str] = field(default_factory=list)


@dataclass
class InputRequest:
    """Request for user input from a command."""

    prompt: str
    is_password: bool = False
    default: str | None = None


def detect_shell() -> str:
    """Detect the user's shell."""
    if os.name == "nt":
        # Windows - check for PowerShell or cmd
        if os.environ.get("PSModulePath"):
            return "powershell"
        return "cmd"

    # Unix - use SHELL environment variable
    return os.environ.get("SHELL", "/bin/sh")


def is_interactive_command(command: str) -> bool:
    """
    Check if a command is likely to request user input.

    Args:
        command: The command to check.

    Returns:
        True if the command might be interactive.
    """
    interactive_patterns = [
        "sudo ",
        "ssh ",
        "scp ",
        "git push",
        "git pull",
        "git clone",
        "npm login",
        "npm publish",
        "docker login",
        "aws configure",
        "gcloud auth",
        "az login",
        "read ",
        "passwd",
        "mysql ",
        "psql ",
        "mongo ",
        "redis-cli",
        " -i",
        "--interactive",
        "rm -i",
        "cp -i",
        "mv -i",
        "pip install",  # Can prompt for confirmation
        "brew install",
        "apt install",
        "apt-get install",
        "yum install",
        "dnf install",
    ]

    command_lower = command.lower()
    return any(pattern in command_lower for pattern in interactive_patterns)


class ShellExecutor:
    """
    Executes shell commands with user input passthrough.

    Provides real-time output streaming and handles interactive
    commands that require user input.
    """

    def __init__(
        self,
        console: Console | None = None,
        working_dir: Path | None = None,
    ) -> None:
        """
        Initialize shell executor.

        Args:
            console: Rich console for output.
            working_dir: Working directory for commands.
        """
        self.console = console or Console()
        self.working_dir = working_dir or Path.cwd()
        self._shell = detect_shell()
        self._output_queue: Queue[str] = Queue()
        self._current_process: subprocess.Popen | None = None

    def _read_output_thread(
        self,
        stream: IO[str],
        queue: Queue[str],
        prefix: str = "",
    ) -> None:
        """Thread function to read output from a stream."""
        try:
            for line in iter(stream.readline, ""):
                if line:
                    queue.put(f"{prefix}{line}")
        except Exception:
            pass
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def execute_simple(
        self,
        command: str,
        timeout: int = 300,
        capture_output: bool = True,
    ) -> CommandResult:
        """
        Execute a simple non-interactive command.

        Args:
            command: Command to execute.
            timeout: Timeout in seconds.
            capture_output: Whether to capture output.

        Returns:
            CommandResult with execution details.
        """
        import time
        start_time = time.monotonic()

        try:
            # Determine shell command format
            if os.name == "nt":
                if self._shell == "powershell":
                    shell_cmd = ["powershell", "-NoProfile", "-Command", command]
                else:
                    shell_cmd = ["cmd", "/c", command]
                use_shell = False
            else:
                shell_cmd = command
                use_shell = True

            result = subprocess.run(
                shell_cmd,
                shell=use_shell,
                cwd=str(self.working_dir),
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )

            duration = time.monotonic() - start_time

            return CommandResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                command=command,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Command timed out",
                command=command,
                duration=timeout,
            )
        except Exception as e:
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                command=command,
                duration=time.monotonic() - start_time,
            )

    async def execute_interactive(
        self,
        command: str,
        timeout: int = 300,
        input_callback: Callable[[str], str] | None = None,
    ) -> CommandResult:
        """
        Execute an interactive command with user input passthrough.

        Args:
            command: Command to execute.
            timeout: Timeout in seconds.
            input_callback: Callback for getting user input.

        Returns:
            CommandResult with execution details.
        """
        import time
        start_time = time.monotonic()
        collected_output = []
        collected_stderr = []
        user_inputs = []

        # Show command being executed
        self.console.print(Panel(
            Text(f"$ {command}", style=BRAND_INFO),
            title=f"[bold {BRAND_ACCENT}]Executing Command[/bold {BRAND_ACCENT}]",
            border_style=BRAND_ACCENT,
        ))

        try:
            if os.name == "nt":
                # Windows: Use subprocess with pipes
                return await self._execute_windows_interactive(
                    command, timeout, input_callback
                )

            # Unix: Use pseudo-terminal for better interactivity
            return await self._execute_unix_interactive(
                command, timeout, input_callback
            )

        except Exception as e:
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="".join(collected_output),
                stderr=str(e),
                command=command,
                duration=time.monotonic() - start_time,
                user_inputs=user_inputs,
            )

    async def _execute_windows_interactive(
        self,
        command: str,
        timeout: int,
        input_callback: Callable[[str], str] | None,
    ) -> CommandResult:
        """Execute interactive command on Windows."""
        import time
        start_time = time.monotonic()
        collected_output = []
        collected_stderr = []
        user_inputs = []

        if self._shell == "powershell":
            shell_cmd = ["powershell", "-NoProfile", "-Command", command]
        else:
            shell_cmd = ["cmd", "/c", command]

        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.working_dir),
        )

        self._current_process = process

        async def read_stream(stream, collection, prefix=""):
            """Read from stream and display output."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                collection.append(decoded)
                self.console.print(Text(decoded.rstrip(), style="white"))

                # Check for input prompts
                if input_callback and self._looks_like_prompt(decoded):
                    user_input = input_callback(decoded)
                    if user_input is not None:
                        user_inputs.append(user_input)
                        process.stdin.write((user_input + "\n").encode())
                        await process.stdin.drain()

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, collected_output),
                    read_stream(process.stderr, collected_stderr, "[stderr] "),
                ),
                timeout=timeout,
            )

            await process.wait()
            exit_code = process.returncode

        except asyncio.TimeoutError:
            process.kill()
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="".join(collected_output),
                stderr="Command timed out",
                command=command,
                duration=timeout,
                user_inputs=user_inputs,
            )

        return CommandResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout="".join(collected_output),
            stderr="".join(collected_stderr),
            command=command,
            duration=time.monotonic() - start_time,
            user_inputs=user_inputs,
        )

    async def _execute_unix_interactive(
        self,
        command: str,
        timeout: int,
        input_callback: Callable[[str], str] | None,
    ) -> CommandResult:
        """Execute interactive command on Unix using PTY."""
        import time
        start_time = time.monotonic()
        collected_output = []
        user_inputs = []

        # Check if PTY is available
        if pty is None or select is None:
            # Fallback to Windows-style execution
            return await self._execute_windows_interactive(
                command, timeout, input_callback
            )

        # Create pseudo-terminal
        master_fd, slave_fd = pty.openpty()

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=str(self.working_dir),
                preexec_fn=os.setsid,
            )

            os.close(slave_fd)
            self._current_process = process

            # Set non-blocking mode
            if fcntl is not None:
                flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
                fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            end_time = time.monotonic() + timeout
            output_buffer = ""

            while process.poll() is None:
                if time.monotonic() > end_time:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    return CommandResult(
                        success=False,
                        exit_code=-1,
                        stdout="".join(collected_output),
                        stderr="Command timed out",
                        command=command,
                        duration=timeout,
                        user_inputs=user_inputs,
                    )

                # Read available output
                try:
                    readable, _, _ = select.select([master_fd], [], [], 0.1)
                    if readable:
                        data = os.read(master_fd, 1024)
                        if data:
                            decoded = data.decode("utf-8", errors="replace")
                            collected_output.append(decoded)
                            output_buffer += decoded

                            # Display output
                            self.console.print(Text(decoded, style="white"), end="")

                            # Check for input prompts
                            if input_callback and self._looks_like_prompt(output_buffer):
                                user_input = input_callback(output_buffer)
                                if user_input is not None:
                                    user_inputs.append(user_input)
                                    os.write(master_fd, (user_input + "\n").encode())
                                    output_buffer = ""
                except (OSError, IOError):
                    await asyncio.sleep(0.05)

            # Read any remaining output
            try:
                while True:
                    readable, _, _ = select.select([master_fd], [], [], 0.1)
                    if not readable:
                        break
                    data = os.read(master_fd, 1024)
                    if not data:
                        break
                    decoded = data.decode("utf-8", errors="replace")
                    collected_output.append(decoded)
                    self.console.print(Text(decoded, style="white"), end="")
            except (OSError, IOError):
                pass

            exit_code = process.returncode

        finally:
            os.close(master_fd)

        return CommandResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout="".join(collected_output),
            stderr="",
            command=command,
            duration=time.monotonic() - start_time,
            user_inputs=user_inputs,
        )

    def _looks_like_prompt(self, text: str) -> bool:
        """
        Check if text looks like an input prompt.

        Args:
            text: Text to check.

        Returns:
            True if it looks like a prompt.
        """
        prompt_indicators = [
            "password:",
            "Password:",
            "PASSWORD:",
            "passphrase:",
            "Enter ",
            "enter ",
            "Type ",
            "type ",
            "(y/n)",
            "(Y/N)",
            "[y/N]",
            "[Y/n]",
            "[yes/no]",
            "? ",
            ": $",
            ">> ",
            "> ",
            "Username:",
            "username:",
            "Email:",
            "email:",
            "Token:",
            "token:",
            "API key:",
            "api key:",
        ]

        return any(indicator in text for indicator in prompt_indicators)

    def prompt_user_input(
        self,
        prompt_text: str,
        is_password: bool = False,
    ) -> str:
        """
        Prompt user for input in the CLI.

        Args:
            prompt_text: The prompt text to display.
            is_password: Whether to hide input (for passwords).

        Returns:
            User's input string.
        """
        from prompt_toolkit import prompt
        from prompt_toolkit.styles import Style

        style = Style.from_dict({
            "prompt": f"{BRAND_ACCENT} bold",
        })

        self.console.print(Panel(
            Text(prompt_text.strip(), style=BRAND_INFO),
            title=f"[bold {BRAND_WARNING}]Input Required[/bold {BRAND_WARNING}]",
            border_style=BRAND_WARNING,
        ))

        try:
            user_input = prompt(
                "➤ ",
                style=style,
                is_password=is_password,
            )
            return user_input
        except (EOFError, KeyboardInterrupt):
            return ""

    def interrupt_current(self) -> bool:
        """
        Interrupt the currently running command.

        Returns:
            True if a command was interrupted.
        """
        if self._current_process and self._current_process.poll() is None:
            try:
                if os.name == "nt":
                    self._current_process.terminate()
                else:
                    os.killpg(os.getpgid(self._current_process.pid), signal.SIGINT)
                return True
            except Exception:
                pass
        return False

    def display_result(self, result: CommandResult) -> None:
        """
        Display command result in a nice format.

        Args:
            result: CommandResult to display.
        """
        if result.success:
            status_text = Text()
            status_text.append("✓ ", style=BRAND_SUCCESS)
            status_text.append(f"Command completed ", style=BRAND_SUCCESS)
            status_text.append(f"(exit code: {result.exit_code}, ", style="dim")
            status_text.append(f"duration: {result.duration:.2f}s)", style="dim")

            self.console.print(Panel(
                status_text,
                border_style=BRAND_SUCCESS,
            ))
        else:
            status_text = Text()
            status_text.append("✗ ", style=BRAND_ERROR)
            status_text.append(f"Command failed ", style=BRAND_ERROR)
            status_text.append(f"(exit code: {result.exit_code})", style="dim")

            error_content = [status_text]

            if result.stderr:
                error_content.append(Text("\n\nError output:", style=BRAND_WARNING))
                error_content.append(Text(result.stderr[:500], style="white"))

            from rich.console import Group
            self.console.print(Panel(
                Group(*error_content),
                border_style=BRAND_ERROR,
            ))


async def execute_command_with_passthrough(
    command: str,
    console: Console | None = None,
    working_dir: Path | None = None,
    timeout: int = 300,
) -> CommandResult:
    """
    Convenience function to execute a command with input passthrough.

    Args:
        command: Command to execute.
        console: Rich console for output.
        working_dir: Working directory.
        timeout: Timeout in seconds.

    Returns:
        CommandResult with execution details.
    """
    executor = ShellExecutor(console=console, working_dir=working_dir)

    # Check if command is likely to be interactive
    if is_interactive_command(command):
        # Use interactive execution with input callback
        def get_input(prompt: str) -> str:
            return executor.prompt_user_input(prompt)

        result = await executor.execute_interactive(
            command,
            timeout=timeout,
            input_callback=get_input,
        )
    else:
        # Use simple execution
        result = executor.execute_simple(command, timeout=timeout)

    executor.display_result(result)
    return result
