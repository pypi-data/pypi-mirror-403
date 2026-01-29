"""
CLI module for AiCippy.

Provides the command-line interface using Typer with Rich UI.
Features:
- Interactive session with beautiful UI
- File upload with OS-native file browser dialogs
- Shell command execution with user input passthrough
- Workspace management
- AI command detection and automatic execution
- Human verification to prevent automated access
"""

from __future__ import annotations

from aicippy.cli.main import app
from aicippy.cli.upload_manager import (
    UploadManager,
    UploadResult,
    get_uploads_directory,
    get_working_directory,
    open_file_dialog,
)
from aicippy.cli.shell_executor import (
    ShellExecutor,
    CommandResult,
    execute_command_with_passthrough,
)
from aicippy.cli.ai_command_executor import (
    AICommandExecutor,
    DetectedCommand,
    CommandExecutionResult,
    process_ai_response_with_commands,
)
from aicippy.cli.human_verify import (
    HumanVerifier,
    VerificationResult,
    is_likely_automated,
    require_human_verification,
)

__all__ = [
    "app",
    # Upload management
    "UploadManager",
    "UploadResult",
    "get_uploads_directory",
    "get_working_directory",
    "open_file_dialog",
    # Shell execution
    "ShellExecutor",
    "CommandResult",
    "execute_command_with_passthrough",
    # AI command execution
    "AICommandExecutor",
    "DetectedCommand",
    "CommandExecutionResult",
    "process_ai_response_with_commands",
    # Human verification
    "HumanVerifier",
    "VerificationResult",
    "is_likely_automated",
    "require_human_verification",
]
