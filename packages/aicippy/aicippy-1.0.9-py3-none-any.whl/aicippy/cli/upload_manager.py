"""
Upload Manager for AiCippy CLI.

Provides smart file upload capability with OS-specific file browser dialogs.
Supports Windows, macOS, and Linux with native file picker integration.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Final, Callable

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskID
from rich.table import Table
from rich.text import Text

# Brand colors
BRAND_PRIMARY: Final[str] = "#667eea"
BRAND_SUCCESS: Final[str] = "#10b981"
BRAND_WARNING: Final[str] = "#f59e0b"
BRAND_ERROR: Final[str] = "#ef4444"
BRAND_INFO: Final[str] = "#3b82f6"
BRAND_ACCENT: Final[str] = "#a78bfa"

# Default uploads folder name
UPLOADS_FOLDER_NAME: Final[str] = "uploads"


@dataclass
class UploadResult:
    """Result of a file upload operation."""

    success: bool
    file_name: str
    file_path: Path | None
    file_size: int
    message: str
    error: str | None = None


@dataclass
class UploadSession:
    """Tracks uploads in the current session."""

    working_dir: Path
    uploads_dir: Path
    uploaded_files: list[UploadResult] = field(default_factory=list)
    total_bytes: int = 0

    def add_upload(self, result: UploadResult) -> None:
        """Add an upload result to the session."""
        self.uploaded_files.append(result)
        if result.success:
            self.total_bytes += result.file_size


def get_working_directory() -> Path:
    """Get the current working directory."""
    return Path.cwd()


def get_uploads_directory(working_dir: Path | None = None) -> Path:
    """
    Get or create the uploads directory.

    Args:
        working_dir: Optional working directory. Defaults to cwd.

    Returns:
        Path to uploads directory.
    """
    if working_dir is None:
        working_dir = get_working_directory()

    uploads_dir = working_dir / UPLOADS_FOLDER_NAME

    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True, exist_ok=True)

    return uploads_dir


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def detect_os() -> str:
    """Detect the operating system."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    return "unknown"


def open_file_dialog_macos(
    title: str = "Select files to upload",
    multiple: bool = True,
    initial_dir: Path | None = None,
) -> list[Path]:
    """
    Open native macOS file dialog using osascript.

    Args:
        title: Dialog title.
        multiple: Allow multiple file selection.
        initial_dir: Initial directory to open.

    Returns:
        List of selected file paths.
    """
    # Build AppleScript command
    multiple_flag = "with multiple selections allowed" if multiple else ""
    initial_folder = ""
    if initial_dir and initial_dir.exists():
        initial_folder = f'default location POSIX file "{initial_dir}"'

    script = f'''
    tell application "System Events"
        activate
    end tell
    set selectedFiles to choose file with prompt "{title}" {multiple_flag} {initial_folder}
    set filePaths to ""
    if class of selectedFiles is list then
        repeat with aFile in selectedFiles
            set filePaths to filePaths & POSIX path of aFile & linefeed
        end repeat
    else
        set filePaths to POSIX path of selectedFiles
    end if
    return filePaths
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for file selection
        )

        if result.returncode == 0 and result.stdout.strip():
            paths = result.stdout.strip().split("\n")
            return [Path(p.strip()) for p in paths if p.strip()]

    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    return []


def open_file_dialog_windows(
    title: str = "Select files to upload",
    multiple: bool = True,
    initial_dir: Path | None = None,
) -> list[Path]:
    """
    Open native Windows file dialog using PowerShell.

    Args:
        title: Dialog title.
        multiple: Allow multiple file selection.
        initial_dir: Initial directory to open.

    Returns:
        List of selected file paths.
    """
    initial_path = str(initial_dir) if initial_dir else ""
    multiselect = "true" if multiple else "false"

    # PowerShell script for file dialog
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "{title}"
$dialog.Multiselect = ${multiselect}
$dialog.Filter = "All files (*.*)|*.*"
if ("{initial_path}") {{
    $dialog.InitialDirectory = "{initial_path}"
}}
$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    $dialog.FileNames -join "`n"
}}
'''

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0 and result.stdout.strip():
            paths = result.stdout.strip().split("\n")
            return [Path(p.strip()) for p in paths if p.strip()]

    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    return []


def open_file_dialog_linux(
    title: str = "Select files to upload",
    multiple: bool = True,
    initial_dir: Path | None = None,
) -> list[Path]:
    """
    Open file dialog on Linux using zenity, kdialog, or yad.

    Args:
        title: Dialog title.
        multiple: Allow multiple file selection.
        initial_dir: Initial directory to open.

    Returns:
        List of selected file paths.
    """
    # Try zenity first (most common on GNOME)
    if shutil.which("zenity"):
        args = ["zenity", "--file-selection", f"--title={title}"]
        if multiple:
            args.append("--multiple")
            args.append("--separator=|")
        if initial_dir:
            args.append(f"--filename={initial_dir}/")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split("|")
                return [Path(p.strip()) for p in paths if p.strip()]
        except Exception:
            pass

    # Try kdialog (KDE)
    if shutil.which("kdialog"):
        args = ["kdialog", "--title", title, "--getopenfilename"]
        if initial_dir:
            args.append(str(initial_dir))

        if multiple:
            args = ["kdialog", "--title", title, "--multiple", "--getopenfilename"]
            if initial_dir:
                args.append(str(initial_dir))

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split("\n")
                return [Path(p.strip()) for p in paths if p.strip()]
        except Exception:
            pass

    # Try yad (Yet Another Dialog)
    if shutil.which("yad"):
        args = ["yad", "--file", f"--title={title}"]
        if multiple:
            args.append("--multiple")
        if initial_dir:
            args.append(f"--filename={initial_dir}/")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split("|")
                return [Path(p.strip()) for p in paths if p.strip()]
        except Exception:
            pass

    return []


def open_file_dialog(
    title: str = "Select files to upload",
    multiple: bool = True,
    initial_dir: Path | None = None,
) -> list[Path]:
    """
    Open OS-specific file dialog.

    Args:
        title: Dialog title.
        multiple: Allow multiple file selection.
        initial_dir: Initial directory to open.

    Returns:
        List of selected file paths.
    """
    os_type = detect_os()

    if os_type == "macos":
        return open_file_dialog_macos(title, multiple, initial_dir)
    elif os_type == "windows":
        return open_file_dialog_windows(title, multiple, initial_dir)
    elif os_type == "linux":
        return open_file_dialog_linux(title, multiple, initial_dir)

    return []


def copy_file_to_uploads(
    source_path: Path,
    uploads_dir: Path,
    progress_callback: Callable[[int, int], None] | None = None,
) -> UploadResult:
    """
    Copy a file to the uploads directory.

    Args:
        source_path: Path to the source file.
        uploads_dir: Destination uploads directory.
        progress_callback: Optional callback for progress updates.

    Returns:
        UploadResult with operation status.
    """
    if not source_path.exists():
        return UploadResult(
            success=False,
            file_name=source_path.name,
            file_path=None,
            file_size=0,
            message=f"File not found: {source_path}",
            error="FileNotFoundError",
        )

    if not source_path.is_file():
        return UploadResult(
            success=False,
            file_name=source_path.name,
            file_path=None,
            file_size=0,
            message=f"Not a file: {source_path}",
            error="NotAFileError",
        )

    try:
        file_size = source_path.stat().st_size
        dest_path = uploads_dir / source_path.name

        # Handle name conflicts
        counter = 1
        while dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = uploads_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # Copy with progress
        if file_size > 1024 * 1024:  # > 1MB, show progress
            bytes_copied = 0
            chunk_size = 1024 * 1024  # 1MB chunks

            with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_copied, file_size)
        else:
            shutil.copy2(source_path, dest_path)

        return UploadResult(
            success=True,
            file_name=dest_path.name,
            file_path=dest_path,
            file_size=file_size,
            message=f"Uploaded: {dest_path.name}",
        )

    except PermissionError as e:
        return UploadResult(
            success=False,
            file_name=source_path.name,
            file_path=None,
            file_size=0,
            message=f"Permission denied: {source_path.name}",
            error=str(e),
        )
    except Exception as e:
        return UploadResult(
            success=False,
            file_name=source_path.name,
            file_path=None,
            file_size=0,
            message=f"Error uploading: {source_path.name}",
            error=str(e),
        )


class UploadManager:
    """
    Manages file uploads for the AiCippy CLI.

    Provides OS-specific file browser dialogs and handles
    file copying to the uploads directory.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        console: Console | None = None,
    ) -> None:
        """
        Initialize upload manager.

        Args:
            working_dir: Working directory for uploads.
            console: Rich console for output.
        """
        self.working_dir = working_dir or get_working_directory()
        self.uploads_dir = get_uploads_directory(self.working_dir)
        self.console = console or Console()
        self.session = UploadSession(
            working_dir=self.working_dir,
            uploads_dir=self.uploads_dir,
        )
        self._os_type = detect_os()

    def get_os_info(self) -> str:
        """Get OS information string."""
        os_names = {
            "macos": "macOS",
            "windows": "Windows",
            "linux": "Linux",
        }
        return os_names.get(self._os_type, "Unknown OS")

    def show_working_directory(self) -> None:
        """Display the current working directory info."""
        cwd = self.working_dir

        # Count files and folders
        files = [f for f in cwd.iterdir() if f.is_file()]
        dirs = [d for d in cwd.iterdir() if d.is_dir()]

        # Create info panel
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style=BRAND_INFO)
        info_table.add_column(style="white")

        info_table.add_row("📁 Working Directory:", str(cwd))
        info_table.add_row("📊 Contents:", f"{len(files)} files, {len(dirs)} folders")
        info_table.add_row("💾 Uploads Folder:", str(self.uploads_dir))

        # Show recent uploads if any
        if self.session.uploaded_files:
            info_table.add_row(
                "📤 Session Uploads:",
                f"{len(self.session.uploaded_files)} files ({format_file_size(self.session.total_bytes)})"
            )

        self.console.print(Panel(
            info_table,
            title=f"[bold {BRAND_PRIMARY}]Workspace Info[/bold {BRAND_PRIMARY}]",
            border_style=BRAND_PRIMARY,
        ))

    def prompt_upload(
        self,
        target_dir: Path | None = None,
        title: str = "Select files to upload to AiCippy",
    ) -> list[UploadResult]:
        """
        Open file browser and upload selected files.

        Args:
            target_dir: Optional target directory (defaults to uploads).
            title: Dialog title.

        Returns:
            List of upload results.
        """
        dest_dir = target_dir or self.uploads_dir

        # Ensure destination exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Show prompt
        self.console.print(Panel(
            Text(
                f"📂 Opening {self.get_os_info()} file browser...\n\n"
                f"Select files to upload to:\n{dest_dir}",
                style=BRAND_INFO,
            ),
            title=f"[bold {BRAND_ACCENT}]/upload[/bold {BRAND_ACCENT}]",
            border_style=BRAND_ACCENT,
        ))

        # Open OS file dialog
        selected_files = open_file_dialog(
            title=title,
            multiple=True,
            initial_dir=Path.home(),
        )

        if not selected_files:
            self.console.print(Panel(
                Text("No files selected.", style="dim"),
                border_style="dim",
            ))
            return []

        # Upload files with progress
        results: list[UploadResult] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            overall_task = progress.add_task(
                f"[{BRAND_INFO}]Uploading {len(selected_files)} file(s)...",
                total=len(selected_files),
            )

            for file_path in selected_files:
                # Create task for this file
                file_task = progress.add_task(
                    f"[{BRAND_ACCENT}]{file_path.name}",
                    total=100,
                )

                def update_progress(copied: int, total: int) -> None:
                    pct = int(copied / total * 100)
                    progress.update(file_task, completed=pct)

                result = copy_file_to_uploads(
                    file_path,
                    dest_dir,
                    progress_callback=update_progress,
                )

                results.append(result)
                self.session.add_upload(result)

                progress.update(file_task, completed=100)
                progress.advance(overall_task)

        # Show results
        self._show_upload_results(results)

        return results

    def _show_upload_results(self, results: list[UploadResult]) -> None:
        """Display upload results in a nice table."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            success_table = Table(
                title=f"[bold {BRAND_SUCCESS}]Uploaded Files[/bold {BRAND_SUCCESS}]",
                border_style=BRAND_SUCCESS,
            )
            success_table.add_column("File", style=BRAND_INFO)
            success_table.add_column("Size", style="white", justify="right")
            success_table.add_column("Location", style="dim")

            for r in successful:
                success_table.add_row(
                    r.file_name,
                    format_file_size(r.file_size),
                    str(r.file_path.parent.name) if r.file_path else "",
                )

            self.console.print(success_table)

        if failed:
            self.console.print()
            error_table = Table(
                title=f"[bold {BRAND_ERROR}]Failed Uploads[/bold {BRAND_ERROR}]",
                border_style=BRAND_ERROR,
            )
            error_table.add_column("File", style=BRAND_WARNING)
            error_table.add_column("Error", style=BRAND_ERROR)

            for r in failed:
                error_table.add_row(r.file_name, r.error or "Unknown error")

            self.console.print(error_table)

        # Summary
        total_size = sum(r.file_size for r in successful)
        self.console.print(Panel(
            Text(
                f"✓ {len(successful)} uploaded  ✗ {len(failed)} failed  "
                f"📦 {format_file_size(total_size)} total",
                style=BRAND_SUCCESS if not failed else BRAND_WARNING,
            ),
            border_style=BRAND_SUCCESS if not failed else BRAND_WARNING,
        ))

    def list_uploads(self) -> list[Path]:
        """List all files in the uploads directory."""
        if not self.uploads_dir.exists():
            return []

        return list(self.uploads_dir.iterdir())

    def show_uploads_list(self) -> None:
        """Display the uploads directory contents."""
        files = self.list_uploads()

        if not files:
            self.console.print(Panel(
                Text("No uploaded files yet.", style="dim italic"),
                title="Uploads",
                border_style="dim",
            ))
            return

        table = Table(
            title=f"[bold {BRAND_ACCENT}]Uploaded Files[/bold {BRAND_ACCENT}]",
            border_style=BRAND_ACCENT,
        )
        table.add_column("File", style=BRAND_INFO)
        table.add_column("Size", style="white", justify="right")
        table.add_column("Modified", style="dim")
        table.add_column("Type", style=BRAND_ACCENT)

        for file in sorted(files):
            if file.is_file():
                stat = file.stat()
                modified = datetime.fromtimestamp(stat.st_mtime)
                file_type = file.suffix[1:].upper() if file.suffix else "FILE"

                table.add_row(
                    file.name,
                    format_file_size(stat.st_size),
                    modified.strftime("%Y-%m-%d %H:%M"),
                    file_type,
                )

        self.console.print(table)
        self.console.print(f"\n[dim]Location: {self.uploads_dir}[/dim]")

    def get_uploaded_file_path(self, filename: str) -> Path | None:
        """
        Get the full path to an uploaded file.

        Args:
            filename: Name of the uploaded file.

        Returns:
            Full path if file exists, None otherwise.
        """
        file_path = self.uploads_dir / filename
        return file_path if file_path.exists() else None

    def clear_uploads(self) -> bool:
        """
        Clear all files from the uploads directory.

        Returns:
            True if successful.
        """
        try:
            for file in self.uploads_dir.iterdir():
                if file.is_file():
                    file.unlink()
            self.session.uploaded_files.clear()
            self.session.total_bytes = 0
            return True
        except Exception:
            return False
