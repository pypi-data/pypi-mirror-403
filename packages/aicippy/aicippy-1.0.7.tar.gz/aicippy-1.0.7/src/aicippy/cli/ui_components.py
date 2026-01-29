"""
Rich UI Components for AiCippy CLI.

Provides beautiful terminal widgets including:
- Animated progress bars with gradients
- Status sidebar with agent visualization
- Task checklist footer
- Keyboard shortcut overlay
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import ProgressColumn, Task
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# ============================================================================
# Constants & Theme
# ============================================================================

# Brand colors
BRAND_PRIMARY: Final[str] = "#667eea"
BRAND_SECONDARY: Final[str] = "#764ba2"
BRAND_ACCENT: Final[str] = "#f093fb"
BRAND_SUCCESS: Final[str] = "#10b981"
BRAND_WARNING: Final[str] = "#f59e0b"
BRAND_ERROR: Final[str] = "#ef4444"
BRAND_INFO: Final[str] = "#3b82f6"

# Gradient colors for progress bars
PROGRESS_GRADIENT: Final[tuple[str, ...]] = (
    "#667eea",
    "#764ba2",
    "#f093fb",
    "#f5576c",
)

# Status icons
STATUS_ICONS: Final[dict[str, str]] = {
    "running": "●",
    "thinking": "◐",
    "complete": "✓",
    "error": "✗",
    "idle": "○",
    "pending": "◌",
    "in_progress": "●",
}

# Keyboard shortcuts
KEYBOARD_SHORTCUTS: Final[list[tuple[str, str]]] = [
    ("Ctrl+C", "Cancel/Interrupt"),
    ("Ctrl+D", "Exit session"),
    ("↑/↓", "History navigation"),
    ("Tab", "Auto-complete"),
    ("/help", "Show commands"),
    ("quit", "Exit AiCippy"),
]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TaskItem:
    """A task item for the checklist."""

    content: str
    status: str = "pending"  # pending, in_progress, completed
    progress: int = 0

    @property
    def icon(self) -> str:
        """Get status icon."""
        return STATUS_ICONS.get(self.status, "○")

    @property
    def style(self) -> str:
        """Get status style."""
        return {
            "pending": "dim",
            "in_progress": f"bold {BRAND_INFO}",
            "completed": f"{BRAND_SUCCESS}",
        }.get(self.status, "white")


@dataclass
class AgentWidget:
    """Agent status widget data."""

    id: str
    name: str
    status: str
    progress: int = 0
    message: str = ""
    tokens: int = 0


# ============================================================================
# Custom Progress Columns
# ============================================================================


class GradientBarColumn(ProgressColumn):
    """A progress bar with gradient effect."""

    def __init__(
        self,
        bar_width: int = 20,
        complete_style: str = BRAND_SUCCESS,
        finished_style: str = BRAND_SUCCESS,
    ) -> None:
        self.bar_width = bar_width
        self.complete_style = complete_style
        self.finished_style = finished_style
        super().__init__()

    def render(self, task: Task) -> Text:
        """Render the gradient progress bar."""
        completed = int(task.percentage / 100 * self.bar_width)
        remaining = self.bar_width - completed

        # Build gradient bar
        bar = Text()

        # Completed portion with gradient
        for i in range(completed):
            color_idx = int(i / self.bar_width * len(PROGRESS_GRADIENT))
            color_idx = min(color_idx, len(PROGRESS_GRADIENT) - 1)
            bar.append("█", style=PROGRESS_GRADIENT[color_idx])

        # Remaining portion
        bar.append("░" * remaining, style="dim")

        return bar


class TaskStatusColumn(ProgressColumn):
    """Column showing task status with icon."""

    def render(self, task: Task) -> Text:
        """Render status with icon."""
        status = task.fields.get("status", "running")
        icon = STATUS_ICONS.get(status, "○")

        color = {
            "running": BRAND_INFO,
            "thinking": BRAND_WARNING,
            "complete": BRAND_SUCCESS,
            "error": BRAND_ERROR,
            "idle": "dim",
        }.get(status, "white")

        return Text(f"{icon} {status}", style=color)


# ============================================================================
# Widget Components
# ============================================================================


def create_header_panel(version: str = "1.0.0") -> Panel:
    """
    Create the main header panel with branding.

    Args:
        version: Application version.

    Returns:
        Rich Panel with header content.
    """
    # ASCII art logo with gradient - clean AiCippy text
    logo_text = Text()
    logo_lines = [
        "     _    _  ____  _                     ",
        "    / \\  (_)/ ___||_|_ __  _ __  _   _   ",
        "   / _ \\ | | |    | | '_ \\| '_ \\| | | |  ",
        "  / ___ \\| | |___ | | |_) | |_) | |_| |  ",
        " /_/   \\_\\_|\\____||_| .__/| .__/ \\__, |  ",
        "                    |_|   |_|    |___/   ",
    ]

    for i, line in enumerate(logo_lines):
        color_idx = int(i / len(logo_lines) * len(PROGRESS_GRADIENT))
        color_idx = min(color_idx, len(PROGRESS_GRADIENT) - 1)
        logo_text.append(line + "\n", style=PROGRESS_GRADIENT[color_idx])

    subtitle = Text()
    subtitle.append("\n  Enterprise Multi-Agent CLI System  ", style=f"italic {BRAND_SECONDARY}")
    subtitle.append(f"v{version}", style="dim")

    return Panel(
        Group(logo_text, subtitle),
        border_style=BRAND_PRIMARY,
        box=ROUNDED,
        padding=(0, 2),
    )


def create_status_sidebar(
    agents: Sequence[AgentWidget],
    session_model: str = "opus",
    tokens_used: int = 0,
    connected: bool = True,
    mascot_mood: str = "idle",
    mascot_frame: int = 0,
) -> Panel:
    """
    Create the status sidebar widget with mini mascot.

    Args:
        agents: List of agent widgets.
        session_model: Current model name.
        tokens_used: Total tokens used.
        connected: Connection status.
        mascot_mood: Current mascot mood.
        mascot_frame: Current animation frame.

    Returns:
        Rich Panel with sidebar content.
    """
    from aicippy.cli.mascot import MascotAnimator, MascotMood

    content_parts: list[RenderableType] = []

    # Mini mascot at the top
    mood_map = {
        "idle": MascotMood.IDLE,
        "thinking": MascotMood.THINKING,
        "working": MascotMood.WORKING,
        "happy": MascotMood.HAPPY,
        "waving": MascotMood.WAVING,
    }
    mood = mood_map.get(mascot_mood, MascotMood.IDLE)
    animator = MascotAnimator(mood=mood, use_mini=True)
    frames = animator.get_frames()
    frame = frames[mascot_frame % len(frames)]
    mascot_text = animator.render_frame(frame)
    content_parts.append(Align.center(mascot_text))
    content_parts.append(Rule(style="dim"))
    content_parts.append(Text())

    # Connection status
    conn_icon = "●" if connected else "○"
    conn_color = BRAND_SUCCESS if connected else BRAND_ERROR
    conn_text = "Connected" if connected else "Offline"
    conn_status = Text()
    conn_status.append(f" {conn_icon} ", style=conn_color)
    conn_status.append(conn_text, style=f"bold {conn_color}")
    content_parts.append(conn_status)
    content_parts.append(Text())

    # Model info
    model_display = Text()
    model_display.append(" ◈ ", style=BRAND_ACCENT)
    model_display.append("Model: ", style="dim")
    model_display.append(session_model.upper(), style=f"bold {BRAND_PRIMARY}")
    content_parts.append(model_display)

    # Tokens
    tokens_display = Text()
    tokens_display.append(" ◇ ", style=BRAND_WARNING)
    tokens_display.append("Tokens: ", style="dim")
    tokens_display.append(f"{tokens_used:,}", style=f"bold {BRAND_WARNING}")
    content_parts.append(tokens_display)

    content_parts.append(Text())
    content_parts.append(Rule(style="dim"))
    content_parts.append(Text())

    # Agents header
    agents_header = Text()
    agents_header.append(" ⚡ AGENTS ", style=f"bold {BRAND_INFO}")
    agents_header.append(f"({len(agents)}/10)", style="dim")
    content_parts.append(agents_header)
    content_parts.append(Text())

    # Agent list
    if agents:
        for agent in agents:
            agent_line = Text()
            icon = STATUS_ICONS.get(agent.status, "○")
            color = {
                "running": BRAND_INFO,
                "thinking": BRAND_WARNING,
                "complete": BRAND_SUCCESS,
                "error": BRAND_ERROR,
                "idle": "dim",
            }.get(agent.status, "white")

            agent_line.append(f"   {icon} ", style=color)
            agent_line.append(f"{agent.name[:12]:<12}", style="white")

            # Mini progress bar
            bar_width = 8
            completed = int(agent.progress / 100 * bar_width)
            bar = "█" * completed + "░" * (bar_width - completed)
            agent_line.append(f" {bar} ", style=color)
            agent_line.append(f"{agent.progress:>3}%", style="dim")

            content_parts.append(agent_line)
    else:
        no_agents = Text("   No active agents", style="dim italic")
        content_parts.append(no_agents)

    return Panel(
        Group(*content_parts),
        title="[bold]◐ Status[/bold]",
        title_align="left",
        border_style=BRAND_PRIMARY,
        box=ROUNDED,
        width=32,
        padding=(1, 1),
    )


def create_task_footer(
    tasks: Sequence[TaskItem],
    current_task_idx: int = 0,
) -> Panel:
    """
    Create the task checklist footer.

    Args:
        tasks: List of task items.
        current_task_idx: Index of current task.

    Returns:
        Rich Panel with task checklist.
    """
    content = Text()

    # Tasks header
    content.append(" 📋 TASKS ", style=f"bold {BRAND_INFO}")

    completed = sum(1 for t in tasks if t.status == "completed")
    content.append(f"({completed}/{len(tasks)}) ", style="dim")

    # Show current and next tasks
    if tasks:
        content.append("\n")

        for i, task in enumerate(tasks):
            if i > current_task_idx + 2:
                break

            # Task line
            icon = task.icon
            style = task.style

            # Highlight current task
            if i == current_task_idx:
                content.append(f"  → {icon} ", style=f"bold {BRAND_INFO}")
                content.append(f"{task.content[:40]}", style=f"bold white")
                if task.progress > 0 and task.status == "in_progress":
                    content.append(f" ({task.progress}%)", style=BRAND_INFO)
            else:
                content.append(f"    {icon} ", style=style)
                content.append(f"{task.content[:40]}", style=style)

            if i < len(tasks) - 1 and i < current_task_idx + 2:
                content.append("\n")
    else:
        content.append("\n    No tasks", style="dim italic")

    return Panel(
        content,
        border_style="dim",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_shortcuts_panel() -> Panel:
    """
    Create the keyboard shortcuts panel.

    Returns:
        Rich Panel with shortcuts.
    """
    content = Text()
    content.append(" ⌨ ", style=BRAND_ACCENT)

    shortcuts_text = []
    for key, desc in KEYBOARD_SHORTCUTS[:4]:  # Show first 4
        shortcuts_text.append(f"[{BRAND_PRIMARY}]{key}[/] {desc}")

    content.append("  ".join(shortcuts_text), style="dim")

    return Panel(
        content,
        border_style="dim",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_input_prompt(
    mode: str = "agent",
    model: str = "opus",
    show_hint: bool = True,
) -> Text:
    """
    Create a beautiful input prompt.

    Args:
        mode: Current mode.
        model: Current model.
        show_hint: Whether to show hint line.

    Returns:
        Rich Text for prompt.
    """
    prompt = Text()

    # Mode indicator
    mode_colors = {
        "agent": BRAND_INFO,
        "edit": BRAND_WARNING,
        "research": BRAND_ACCENT,
        "code": BRAND_SUCCESS,
    }
    mode_color = mode_colors.get(mode, BRAND_PRIMARY)

    prompt.append("┌─", style="dim")
    prompt.append(f"[{mode}]", style=mode_color)
    prompt.append("─", style="dim")
    prompt.append(f"[{model}]", style=BRAND_SECONDARY)
    prompt.append("─────────────────────", style="dim")
    prompt.append("\n")

    # Add hint line
    if show_hint:
        prompt.append("│ ", style="dim")
        prompt.append("Type message, ", style="dim")
        prompt.append("/help", style=BRAND_INFO)
        prompt.append(" for commands, or ", style="dim")
        prompt.append("quit", style=BRAND_WARNING)
        prompt.append(" to exit", style="dim")
        prompt.append("\n")

    prompt.append("└─❯ ", style=BRAND_PRIMARY)

    return prompt


def create_response_panel(
    content: str,
    agent_type: str | None = None,
    tokens_used: int = 0,
    execution_time: float = 0.0,
) -> Panel:
    """
    Create a panel for AI response display.

    Args:
        content: Response content (markdown).
        agent_type: Type of agent that responded.
        tokens_used: Tokens used for response.
        execution_time: Response time in seconds.

    Returns:
        Rich Panel with response.
    """
    # Header with agent info
    header_parts = []
    if agent_type:
        header_parts.append(f"[{BRAND_INFO}]◈ {agent_type.upper()}[/]")
    if tokens_used:
        header_parts.append(f"[dim]{tokens_used:,} tokens[/]")
    if execution_time:
        header_parts.append(f"[dim]{execution_time:.1f}s[/]")

    title = " │ ".join(header_parts) if header_parts else "Response"

    return Panel(
        Markdown(content),
        title=title,
        title_align="left",
        border_style=BRAND_SUCCESS,
        box=ROUNDED,
        padding=(1, 2),
    )


def create_thinking_indicator(frame_idx: int = 0) -> Panel:
    """
    Create a thinking/processing indicator with animated mascot.

    Args:
        frame_idx: Animation frame index for mascot.

    Returns:
        Rich Panel with spinner and mascot.
    """
    from aicippy.cli.mascot import MascotAnimator, MascotMood

    # Mini mascot in thinking pose
    animator = MascotAnimator(mood=MascotMood.WORKING, use_mini=True)
    frames = animator.get_frames()
    frame = frames[frame_idx % len(frames)]
    mascot_text = animator.render_frame(frame)

    content = Text()
    content.append("  ", style="dim")
    content.append("◐ ", style=f"bold {BRAND_INFO}")
    content.append("Thinking", style=BRAND_INFO)
    content.append(" ", style="dim")
    # Use animated dots without blink (better terminal compatibility)
    dot_styles = [BRAND_ACCENT, BRAND_SECONDARY, BRAND_PRIMARY]
    for i, color in enumerate(dot_styles):
        # Alternating brightness based on frame for visual interest
        content.append("●", style=f"bold {color}")

    return Panel(
        Group(Align.center(mascot_text), content),
        border_style=BRAND_INFO,
        box=ROUNDED,
        padding=(0, 1),
    )


def create_error_panel(error: str, suggestion: str | None = None) -> Panel:
    """
    Create an error display panel.

    Args:
        error: Error message.
        suggestion: Optional suggestion for fixing.

    Returns:
        Rich Panel with error.
    """
    content = Text()
    content.append(" ✗ ", style=f"bold {BRAND_ERROR}")
    content.append(error, style=BRAND_ERROR)

    if suggestion:
        content.append("\n")
        content.append(" 💡 ", style=BRAND_WARNING)
        content.append(suggestion, style="italic dim")

    return Panel(
        content,
        title="[bold red]Error[/bold red]",
        border_style=BRAND_ERROR,
        box=ROUNDED,
        padding=(0, 1),
    )


def create_success_panel(message: str, details: str | None = None) -> Panel:
    """
    Create a success display panel.

    Args:
        message: Success message.
        details: Optional additional details.

    Returns:
        Rich Panel with success message.
    """
    content = Text()
    content.append(" ✓ ", style=f"bold {BRAND_SUCCESS}")
    content.append(message, style=BRAND_SUCCESS)

    if details:
        content.append("\n")
        content.append(f"   {details}", style="dim")

    return Panel(
        content,
        border_style=BRAND_SUCCESS,
        box=ROUNDED,
        padding=(0, 1),
    )


# ============================================================================
# Layout Builder
# ============================================================================


class AiCippyLayout:
    """
    Main layout manager for AiCippy CLI.

    Provides a beautiful terminal interface with:
    - Header with branding
    - Main content area
    - Status sidebar
    - Task footer
    - Keyboard shortcuts
    """

    def __init__(self, console: Console) -> None:
        """Initialize layout manager."""
        self.console = console
        self._layout = Layout()
        self._setup_layout()

    def _setup_layout(self) -> None:
        """Setup the layout structure."""
        # Main split: header, body, footer
        self._layout.split(
            Layout(name="header", size=9),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=5),
        )

        # Body split: main content + sidebar
        self._layout["body"].split_row(
            Layout(name="main", ratio=3),
            Layout(name="sidebar", size=34),
        )

        # Footer split: tasks + shortcuts
        self._layout["footer"].split_row(
            Layout(name="tasks", ratio=3),
            Layout(name="shortcuts", ratio=1),
        )

    def update(
        self,
        main_content: RenderableType | None = None,
        agents: Sequence[AgentWidget] | None = None,
        tasks: Sequence[TaskItem] | None = None,
        current_task_idx: int = 0,
        session_model: str = "opus",
        tokens_used: int = 0,
        connected: bool = True,
        version: str = "1.0.0",
    ) -> Layout:
        """
        Update all layout components.

        Args:
            main_content: Content for main area.
            agents: Agent widgets for sidebar.
            tasks: Task items for footer.
            current_task_idx: Current task index.
            session_model: Current model.
            tokens_used: Token count.
            connected: Connection status.
            version: App version.

        Returns:
            Updated Layout.
        """
        # Header
        self._layout["header"].update(create_header_panel(version))

        # Sidebar
        self._layout["sidebar"].update(
            create_status_sidebar(
                agents=agents or [],
                session_model=session_model,
                tokens_used=tokens_used,
                connected=connected,
            )
        )

        # Main content
        if main_content:
            self._layout["main"].update(
                Panel(
                    main_content,
                    border_style="dim",
                    box=ROUNDED,
                    padding=(1, 2),
                )
            )

        # Tasks footer
        self._layout["tasks"].update(
            create_task_footer(
                tasks=tasks or [],
                current_task_idx=current_task_idx,
            )
        )

        # Shortcuts
        self._layout["shortcuts"].update(create_shortcuts_panel())

        return self._layout

    @property
    def layout(self) -> Layout:
        """Get the layout."""
        return self._layout


def create_welcome_screen(version: str = "1.0.0", frame_idx: int = 0) -> Group:
    """
    Create the welcome screen shown at startup with animated mascot.

    Args:
        version: Application version.
        frame_idx: Animation frame index.

    Returns:
        Rich Group with welcome content.
    """
    from aicippy.cli.mascot import (
        MascotAnimator,
        MascotMood,
        MASCOT_ACCENT,
        MASCOT_GLOW,
        MASCOT_HIGHLIGHT,
        MASCOT_PRIMARY,
        MASCOT_SECONDARY,
    )

    # Animated mascot
    animator = MascotAnimator(mood=MascotMood.WAVING, use_mini=False)
    frames = animator.get_frames()
    frame = frames[frame_idx % len(frames)]
    mascot = animator.render_frame(frame)

    # Big ASCII title with gradient - clean readable design
    title = Text()
    title.append("\n")
    title.append("  +================================================================+\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                                ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("       _    _  ____  _                                         ", style=MASCOT_GLOW)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("      / \\  (_)/ ___||_|_ __  _ __  _   _                        ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("     / _ \\ | | |    | | '_ \\| '_ \\| | | |                       ", style=MASCOT_SECONDARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("    / ___ \\| | |___ | | |_) | |_) | |_| |                       ", style=MASCOT_ACCENT)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("   /_/   \\_\\_|\\____||_| .__/| .__/ \\__, |                       ", style=MASCOT_HIGHLIGHT)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                      |_|   |_|    |___/                        ", style=MASCOT_HIGHLIGHT)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                                ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append(f"          Enterprise Multi-Agent CLI System  v{version}           ", style=f"italic {MASCOT_HIGHLIGHT}")
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                                ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  +================================================================+\n", style=MASCOT_PRIMARY)

    # Speech bubble - centered and properly aligned
    speech = Text()
    speech.append("\n", style="dim")
    speech.append("                    +-----------------------------+\n", style=MASCOT_HIGHLIGHT)
    speech.append("                    |", style=MASCOT_HIGHLIGHT)
    speech.append("  Hi! I'm Cippy!           ", style=f"bold {MASCOT_ACCENT}")
    speech.append("|\n", style=MASCOT_HIGHLIGHT)
    speech.append("                    |", style=MASCOT_HIGHLIGHT)
    speech.append("  Ready to help you!       ", style=MASCOT_GLOW)
    speech.append("|\n", style=MASCOT_HIGHLIGHT)
    speech.append("                    +-----------------------------+\n", style=MASCOT_HIGHLIGHT)
    speech.append("                              \\\n", style=MASCOT_HIGHLIGHT)

    # Quick start guide
    guide = Table.grid(padding=(0, 2))
    guide.add_column(style=BRAND_PRIMARY)
    guide.add_column(style="white")

    guide.add_row("", "")
    guide.add_row("  Quick Start:", "")
    guide.add_row("  -------------", "")
    guide.add_row(f"  [bold]{STATUS_ICONS['complete']}[/]", "Type your message and press Enter")
    guide.add_row(f"  [bold]{STATUS_ICONS['complete']}[/]", "Use /help for available commands")
    guide.add_row(f"  [bold]{STATUS_ICONS['complete']}[/]", "Use /model to switch AI models")
    guide.add_row(f"  [bold]{STATUS_ICONS['complete']}[/]", "Use /agents spawn N for parallel agents")
    guide.add_row("", "")

    guide_panel = Panel(
        guide,
        border_style="dim",
        box=ROUNDED,
        title="[bold]Getting Started[/bold]",
        title_align="left",
    )

    # Shortcuts
    shortcuts_table = Table.grid(padding=(0, 3))
    shortcuts_table.add_column(style=BRAND_ACCENT)
    shortcuts_table.add_column(style="dim")

    for key, desc in KEYBOARD_SHORTCUTS:
        shortcuts_table.add_row(f"  {key}", desc)

    shortcuts_panel = Panel(
        shortcuts_table,
        border_style="dim",
        box=ROUNDED,
        title="[bold]Keyboard Shortcuts[/bold]",
        title_align="left",
    )

    return Group(title, speech, Align.center(mascot), guide_panel, shortcuts_panel)


# ============================================================================
# New Layout Components for Live Preview Interface
# ============================================================================

# Preview area configuration
PREVIEW_LINES: Final[int] = 25  # Number of lines in preview area


@dataclass
class PreviewLine:
    """A line in the preview buffer."""

    content: str
    style: str = "white"
    timestamp: str = ""
    line_type: str = "info"  # info, command, output, error, success, agent


class LivePreviewBuffer:
    """
    Buffer for the live preview area with auto-scrolling.

    Maintains a fixed-size buffer of lines that can be displayed
    in the preview panel with auto-scroll to latest content.
    """

    def __init__(self, max_lines: int = PREVIEW_LINES) -> None:
        """Initialize preview buffer."""
        self.max_lines = max_lines
        self._lines: list[PreviewLine] = []
        self._auto_scroll = True

    def add_line(
        self,
        content: str,
        style: str = "white",
        line_type: str = "info",
    ) -> None:
        """Add a line to the buffer."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._lines.append(PreviewLine(
            content=content,
            style=style,
            timestamp=timestamp,
            line_type=line_type,
        ))

        # Keep only max_lines
        if len(self._lines) > self.max_lines * 3:  # Keep some history
            self._lines = self._lines[-self.max_lines * 2:]

    def add_command(self, command: str) -> None:
        """Add a command line."""
        self.add_line(f"$ {command}", style=BRAND_INFO, line_type="command")

    def add_output(self, output: str) -> None:
        """Add command output lines."""
        for line in output.split("\n"):
            if line.strip():
                self.add_line(f"  {line}", style="white", line_type="output")

    def add_error(self, error: str) -> None:
        """Add an error line."""
        self.add_line(f"✗ {error}", style=BRAND_ERROR, line_type="error")

    def add_success(self, message: str) -> None:
        """Add a success line."""
        self.add_line(f"✓ {message}", style=BRAND_SUCCESS, line_type="success")

    def add_agent_update(self, agent_id: str, status: str, message: str = "") -> None:
        """Add an agent status update."""
        icon = STATUS_ICONS.get(status, "○")
        color = {
            "running": BRAND_INFO,
            "thinking": BRAND_WARNING,
            "complete": BRAND_SUCCESS,
            "error": BRAND_ERROR,
        }.get(status, "dim")
        text = f"{icon} [{agent_id}] {status}"
        if message:
            text += f": {message}"
        self.add_line(text, style=color, line_type="agent")

    def add_streaming(self, chunk: str) -> None:
        """Add streaming content (appends to last line if same type)."""
        if self._lines and self._lines[-1].line_type == "streaming":
            self._lines[-1].content += chunk
        else:
            self.add_line(chunk, style=BRAND_ACCENT, line_type="streaming")

    def get_visible_lines(self) -> list[PreviewLine]:
        """Get lines visible in the preview area."""
        return self._lines[-self.max_lines:]

    def clear(self) -> None:
        """Clear the buffer."""
        self._lines.clear()

    def render(self) -> Text:
        """Render the buffer as Rich Text."""
        text = Text()
        visible = self.get_visible_lines()

        # Pad with empty lines if needed
        empty_lines = self.max_lines - len(visible)
        for _ in range(empty_lines):
            text.append("\n")

        for i, line in enumerate(visible):
            # Timestamp
            text.append(f"[{line.timestamp}] ", style="dim")
            # Content
            text.append(line.content, style=line.style)
            if i < len(visible) - 1:
                text.append("\n")

        return text


def create_compact_header(version: str = "1.0.0") -> Panel:
    """
    Create a compact header bar.

    Args:
        version: Application version.

    Returns:
        Compact header panel.
    """
    header = Text()
    header.append(" ◈ ", style=f"bold {BRAND_PRIMARY}")
    header.append("AiCippy", style=f"bold {BRAND_PRIMARY}")
    header.append(f" v{version} ", style="dim")
    header.append("│", style="dim")
    header.append(" Enterprise Multi-Agent CLI ", style=f"italic {BRAND_SECONDARY}")

    return Panel(
        header,
        border_style=BRAND_PRIMARY,
        box=ROUNDED,
        padding=(0, 1),
    )


def create_compact_status_widget(
    agents: Sequence[AgentWidget],
    session_model: str = "opus",
    tokens_used: int = 0,
    connected: bool = True,
    mascot_mood: str = "idle",
) -> Panel:
    """
    Create a compact status widget for top-right corner.

    Args:
        agents: List of agent widgets.
        session_model: Current model name.
        tokens_used: Total tokens used.
        connected: Connection status.
        mascot_mood: Current mascot mood.

    Returns:
        Compact status panel.
    """
    content = Text()

    # Connection indicator
    conn_icon = "●" if connected else "○"
    conn_color = BRAND_SUCCESS if connected else BRAND_ERROR
    content.append(f"{conn_icon}", style=conn_color)
    content.append(" ", style="dim")

    # Model
    content.append(f"{session_model.upper()}", style=f"bold {BRAND_PRIMARY}")
    content.append(" │ ", style="dim")

    # Tokens
    content.append(f"{tokens_used:,}", style=BRAND_WARNING)
    content.append(" tok", style="dim")
    content.append(" │ ", style="dim")

    # Agents count
    active_agents = sum(1 for a in agents if a.status in ("running", "thinking"))
    content.append(f"⚡{active_agents}/{len(agents)}", style=BRAND_INFO)

    # Mood indicator
    mood_icons = {"idle": "○", "thinking": "◐", "working": "●", "happy": "★"}
    mood_icon = mood_icons.get(mascot_mood, "○")
    content.append(f" {mood_icon}", style=BRAND_ACCENT)

    return Panel(
        content,
        border_style=BRAND_SECONDARY,
        box=ROUNDED,
        padding=(0, 1),
        title="[dim]Status[/dim]",
        title_align="left",
    )


def create_live_preview_panel(
    buffer: LivePreviewBuffer,
    title: str = "Live Preview",
) -> Panel:
    """
    Create the live preview panel with scrolling content.

    Args:
        buffer: The preview buffer.
        title: Panel title.

    Returns:
        Preview panel.
    """
    return Panel(
        buffer.render(),
        title=f"[bold {BRAND_INFO}]{title}[/bold {BRAND_INFO}]",
        title_align="left",
        border_style=BRAND_INFO,
        box=ROUNDED,
        padding=(0, 1),
        height=PREVIEW_LINES + 2,  # +2 for border
    )


def create_todos_section(
    tasks: Sequence[TaskItem],
    current_task_idx: int = 0,
) -> Panel:
    """
    Create the todos/next task section.

    Args:
        tasks: List of task items.
        current_task_idx: Current task index.

    Returns:
        Todos panel.
    """
    content = Text()

    # Current task highlight
    if tasks and current_task_idx < len(tasks):
        current = tasks[current_task_idx]
        content.append("→ ", style=f"bold {BRAND_INFO}")
        content.append("CURRENT: ", style=f"bold {BRAND_INFO}")
        content.append(current.content, style="bold white")
        if current.progress > 0:
            content.append(f" ({current.progress}%)", style=BRAND_WARNING)
    else:
        content.append("→ ", style="dim")
        content.append("No active task", style="dim italic")

    # Completion stats
    completed = sum(1 for t in tasks if t.status == "completed")
    pending = sum(1 for t in tasks if t.status == "pending")
    content.append("  │  ", style="dim")
    content.append(f"✓{completed}", style=BRAND_SUCCESS)
    content.append(f" ◌{pending}", style="dim")

    return Panel(
        content,
        border_style="dim",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_input_section(mode: str = "agent", model: str = "opus") -> Text:
    """
    Create the input prompt section.

    Args:
        mode: Current mode.
        model: Current model.

    Returns:
        Input prompt text.
    """
    prompt = Text()

    mode_colors = {
        "agent": BRAND_INFO,
        "edit": BRAND_WARNING,
        "research": BRAND_ACCENT,
        "code": BRAND_SUCCESS,
    }
    mode_color = mode_colors.get(mode, BRAND_PRIMARY)

    prompt.append("╭─", style="dim")
    prompt.append(f"[{mode}]", style=mode_color)
    prompt.append("─", style="dim")
    prompt.append(f"[{model}]", style=BRAND_SECONDARY)
    prompt.append("─", style="dim")
    prompt.append(" Type message, ", style="dim")
    prompt.append("/help", style=BRAND_INFO)
    prompt.append(" or ", style="dim")
    prompt.append("quit", style=BRAND_WARNING)
    prompt.append("\n")
    prompt.append("╰─❯ ", style=BRAND_PRIMARY)

    return prompt


def create_footer_bar() -> Panel:
    """
    Create the footer bar with shortcuts.

    Returns:
        Footer panel.
    """
    shortcuts = Text()

    shortcut_items = [
        ("Ctrl+C", "Cancel"),
        ("Ctrl+L", "Clear"),
        ("↑↓", "History"),
        ("Tab", "Complete"),
        ("/help", "Commands"),
        ("quit", "Exit"),
    ]

    for i, (key, desc) in enumerate(shortcut_items):
        if i > 0:
            shortcuts.append(" │ ", style="dim")
        shortcuts.append(key, style=BRAND_ACCENT)
        shortcuts.append(f" {desc}", style="dim")

    return Panel(
        shortcuts,
        border_style="dim",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_bottom_status_bar(
    tokens_used: int = 0,
    username: str | None = None,
    session_duration: str = "00:00:00",
    background_tasks: int = 0,
    model: str = "opus",
    connected: bool = True,
) -> Panel:
    """
    Create the bottom status bar with session info.

    Args:
        tokens_used: Total tokens used in session.
        username: Logged in username.
        session_duration: Session duration string (HH:MM:SS).
        background_tasks: Number of background tasks running.
        model: Current model name.
        connected: Connection status.

    Returns:
        Bottom status bar panel.
    """
    content = Text()

    # Connection status
    conn_icon = "●" if connected else "○"
    conn_color = BRAND_SUCCESS if connected else BRAND_ERROR
    content.append(f" {conn_icon} ", style=conn_color)

    # Token count
    content.append("Tokens: ", style="dim")
    content.append(f"{tokens_used:,}", style=f"bold {BRAND_WARNING}")
    content.append(" │ ", style="dim")

    # Username
    content.append("User: ", style="dim")
    if username:
        content.append(username, style=f"bold {BRAND_INFO}")
    else:
        content.append("Not logged in", style="dim italic")
    content.append(" │ ", style="dim")

    # Session timer
    content.append("Session: ", style="dim")
    content.append(session_duration, style=f"bold {BRAND_ACCENT}")
    content.append(" │ ", style="dim")

    # Background tasks
    content.append("Background: ", style="dim")
    if background_tasks > 0:
        content.append(f"{background_tasks} task(s)", style=f"bold {BRAND_INFO}")
    else:
        content.append("None", style="dim")
    content.append(" │ ", style="dim")

    # Model
    content.append("Model: ", style="dim")
    content.append(model.upper(), style=f"bold {BRAND_PRIMARY}")

    return Panel(
        content,
        border_style=BRAND_PRIMARY,
        box=ROUNDED,
        padding=(0, 0),
    )


class InteractiveLayout:
    """
    New interactive layout manager with live preview area.

    Layout structure:
    ┌─────────────────────────────────────────────────────────────┐
    │  HEADER (compact)                                            │
    ├─────────────────────────────────────────┬───────────────────┤
    │                                         │  STATUS WIDGET    │
    │  LIVE PREVIEW AREA (25 lines)           │  (compact, fixed) │
    │  - Agent streaming                      │                   │
    │  - Command output                       │                   │
    │  - Progress updates                     │                   │
    │  (auto-scrolling)                       │                   │
    ├─────────────────────────────────────────┴───────────────────┤
    │  TODOS / CURRENT TASK                                        │
    ├─────────────────────────────────────────────────────────────┤
    │  INPUT PROMPT                                                │
    ├─────────────────────────────────────────────────────────────┤
    │  FOOTER (shortcuts)                                          │
    ├─────────────────────────────────────────────────────────────┤
    │  STATUS BAR (tokens, user, timer, background tasks)          │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self, console: Console, version: str = "1.0.0") -> None:
        """Initialize interactive layout."""
        self.console = console
        self.version = version
        self.preview_buffer = LivePreviewBuffer(max_lines=PREVIEW_LINES)
        self._layout = Layout()
        self._setup_layout()
        # Track background tasks
        self.background_tasks: int = 0

    def _setup_layout(self) -> None:
        """Setup the layout structure."""
        self._layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main_area", ratio=1),
            Layout(name="todos", size=3),
            Layout(name="footer", size=3),
            Layout(name="status_bar", size=3),
        )

        # Main area: preview + status widget
        self._layout["main_area"].split_row(
            Layout(name="preview", ratio=3),
            Layout(name="status_widget", size=35),
        )

    def update(
        self,
        agents: Sequence[AgentWidget] | None = None,
        tasks: Sequence[TaskItem] | None = None,
        current_task_idx: int = 0,
        session_model: str = "opus",
        tokens_used: int = 0,
        connected: bool = True,
        mascot_mood: str = "idle",
        username: str | None = None,
        session_duration: str = "00:00:00",
        background_tasks: int = 0,
    ) -> Layout:
        """Update the layout with current state."""
        # Header
        self._layout["header"].update(create_compact_header(self.version))

        # Preview area
        self._layout["preview"].update(
            create_live_preview_panel(self.preview_buffer)
        )

        # Status widget (top-right, compact)
        self._layout["status_widget"].update(
            create_compact_status_widget(
                agents=agents or [],
                session_model=session_model,
                tokens_used=tokens_used,
                connected=connected,
                mascot_mood=mascot_mood,
            )
        )

        # Todos section
        self._layout["todos"].update(
            create_todos_section(tasks=tasks or [], current_task_idx=current_task_idx)
        )

        # Footer (shortcuts)
        self._layout["footer"].update(create_footer_bar())

        # Bottom status bar
        self._layout["status_bar"].update(
            create_bottom_status_bar(
                tokens_used=tokens_used,
                username=username,
                session_duration=session_duration,
                background_tasks=background_tasks,
                model=session_model,
                connected=connected,
            )
        )

        return self._layout

    def add_preview_line(self, content: str, style: str = "white", line_type: str = "info") -> None:
        """Add a line to the preview buffer."""
        self.preview_buffer.add_line(content, style, line_type)

    def add_command(self, command: str) -> None:
        """Add a command to preview."""
        self.preview_buffer.add_command(command)

    def add_output(self, output: str) -> None:
        """Add output to preview."""
        self.preview_buffer.add_output(output)

    def add_error(self, error: str) -> None:
        """Add error to preview."""
        self.preview_buffer.add_error(error)

    def add_success(self, message: str) -> None:
        """Add success message to preview."""
        self.preview_buffer.add_success(message)

    def add_agent_update(self, agent_id: str, status: str, message: str = "") -> None:
        """Add agent update to preview."""
        self.preview_buffer.add_agent_update(agent_id, status, message)

    def add_streaming(self, chunk: str) -> None:
        """Add streaming content to preview."""
        self.preview_buffer.add_streaming(chunk)

    def clear_preview(self) -> None:
        """Clear the preview buffer."""
        self.preview_buffer.clear()

    @property
    def layout(self) -> Layout:
        """Get the layout."""
        return self._layout


# ============================================================================
# Real-time Streaming UI Components
# ============================================================================


@dataclass
class StreamingState:
    """State for streaming response display."""

    content: str = ""
    tokens_received: int = 0
    tokens_per_second: float = 0.0
    is_streaming: bool = False
    cursor_visible: bool = True


def create_streaming_response_panel(
    state: StreamingState,
    agent_type: str | None = None,
) -> Panel:
    """
    Create a panel for streaming AI response with typewriter effect.

    Args:
        state: Current streaming state.
        agent_type: Type of agent responding.

    Returns:
        Rich Panel with streaming content.
    """
    # Header with live indicator
    header_parts = []
    if state.is_streaming:
        header_parts.append(f"[bold {BRAND_INFO}]Streaming[/bold {BRAND_INFO}]")
        header_parts.append(f"[{BRAND_ACCENT}]...[/{BRAND_ACCENT}]")
    else:
        header_parts.append(f"[{BRAND_SUCCESS}]Complete[/{BRAND_SUCCESS}]")

    if agent_type:
        header_parts.append(f"[dim]|[/dim] [{BRAND_INFO}]{agent_type.upper()}[/{BRAND_INFO}]")

    header_parts.append(f"[dim]|[/dim] [{BRAND_WARNING}]{state.tokens_received:,} tokens[/{BRAND_WARNING}]")

    if state.tokens_per_second > 0:
        header_parts.append(f"[dim]({state.tokens_per_second:.1f} tok/s)[/dim]")

    title = " ".join(header_parts)

    # Content with optional cursor
    content = Text()
    content.append(state.content)

    if state.is_streaming and state.cursor_visible:
        # Use bold underline instead of blink for better terminal compatibility
        content.append("_", style=f"bold {BRAND_ACCENT}")

    border_style = BRAND_INFO if state.is_streaming else BRAND_SUCCESS

    return Panel(
        Markdown(str(content)) if not state.is_streaming else content,
        title=title,
        title_align="left",
        border_style=border_style,
        box=ROUNDED,
        padding=(1, 2),
    )


def create_connection_indicator(
    connected: bool,
    latency_ms: float = 0.0,
    reconnecting: bool = False,
    reconnect_attempts: int = 0,
) -> Text:
    """
    Create a connection status indicator.

    Args:
        connected: Whether connected.
        latency_ms: Current latency in milliseconds.
        reconnecting: Whether currently reconnecting.
        reconnect_attempts: Number of reconnection attempts.

    Returns:
        Rich Text with connection indicator.
    """
    text = Text()

    if reconnecting:
        # Removed blink style for better terminal compatibility
        text.append("◐ ", style=f"bold {BRAND_WARNING}")
        text.append("Reconnecting", style=BRAND_WARNING)
        if reconnect_attempts > 0:
            text.append(f" ({reconnect_attempts})", style="dim")
    elif connected:
        # Determine latency color
        if latency_ms <= 100:
            latency_color = BRAND_SUCCESS
        elif latency_ms <= 300:
            latency_color = BRAND_WARNING
        else:
            latency_color = BRAND_ERROR

        text.append("● ", style=f"bold {BRAND_SUCCESS}")
        text.append("Connected", style=BRAND_SUCCESS)
        if latency_ms > 0:
            text.append(f" ({latency_ms:.0f}ms)", style=latency_color)
    else:
        text.append("○ ", style=f"bold {BRAND_ERROR}")
        text.append("Disconnected", style=BRAND_ERROR)

    return text


def create_agent_activity_panel(
    agents: Sequence[AgentWidget],
    show_mini_progress: bool = True,
) -> Panel:
    """
    Create a panel showing agent activity with smooth transitions.

    Args:
        agents: List of agent widgets.
        show_mini_progress: Whether to show mini progress bars.

    Returns:
        Rich Panel with agent activity.
    """
    content_parts: list[RenderableType] = []

    # Header
    active_count = sum(1 for a in agents if a.status in ("running", "thinking"))
    header = Text()
    header.append("  AGENTS ", style=f"bold {BRAND_INFO}")
    header.append(f"({active_count}/{len(agents)} active)", style="dim")
    content_parts.append(header)
    content_parts.append(Text())

    if not agents:
        content_parts.append(Text("    No agents spawned", style="dim italic"))
    else:
        for agent in agents:
            line = Text()

            # Status icon with animation hint
            icon = STATUS_ICONS.get(agent.status, "○")
            color = {
                "running": BRAND_INFO,
                "thinking": BRAND_WARNING,
                "complete": BRAND_SUCCESS,
                "error": BRAND_ERROR,
                "idle": "dim",
            }.get(agent.status, "white")

            # Add activity animation for running/thinking (no blink for compatibility)
            if agent.status in ("running", "thinking"):
                line.append(f"  {icon} ", style=f"bold {color}")
            else:
                line.append(f"  {icon} ", style=color)

            # Agent name
            line.append(f"{agent.name[:15]:<15}", style="white")

            # Progress bar if enabled
            if show_mini_progress:
                bar_width = 10
                completed = int(agent.progress / 100 * bar_width)
                bar_filled = "█" * completed
                bar_empty = "░" * (bar_width - completed)
                line.append(f" {bar_filled}", style=color)
                line.append(bar_empty, style="dim")
                line.append(f" {agent.progress:>3}%", style="dim")

            # Message if present
            if agent.message:
                line.append(f" {agent.message[:20]}", style="dim italic")

            content_parts.append(line)

    return Panel(
        Group(*content_parts),
        border_style=BRAND_INFO,
        box=ROUNDED,
        padding=(0, 1),
        title="[dim]Activity[/dim]",
        title_align="left",
    )


def create_progress_indicator(
    message: str,
    progress: int = 0,
    show_percentage: bool = True,
    style: str = BRAND_INFO,
) -> Text:
    """
    Create a progress indicator with animated spinner.

    Args:
        message: Progress message.
        progress: Progress percentage (0-100).
        show_percentage: Whether to show percentage.
        style: Color style.

    Returns:
        Rich Text with progress indicator.
    """
    text = Text()

    # Spinner frames
    spinners = ("◐", "◓", "◑", "◒")
    import time
    frame_idx = int(time.time() * 4) % len(spinners)
    spinner = spinners[frame_idx]

    text.append(f"{spinner} ", style=f"bold {style}")
    text.append(message, style=style)

    if show_percentage and progress > 0:
        text.append(f" ({progress}%)", style="dim")

    return text


def create_tool_output_panel(
    tool_name: str,
    output: str,
    success: bool,
    execution_time_ms: int = 0,
) -> Panel:
    """
    Create a panel for tool execution output.

    Args:
        tool_name: Name of the tool.
        output: Tool output.
        success: Whether execution was successful.
        execution_time_ms: Execution time in milliseconds.

    Returns:
        Rich Panel with tool output.
    """
    # Header
    status_icon = "✓" if success else "✗"
    status_color = BRAND_SUCCESS if success else BRAND_ERROR

    title_parts = [
        f"[{status_color}]{status_icon}[/{status_color}]",
        f"[bold {BRAND_ACCENT}]{tool_name}[/bold {BRAND_ACCENT}]",
    ]
    if execution_time_ms > 0:
        title_parts.append(f"[dim]({execution_time_ms}ms)[/dim]")

    title = " ".join(title_parts)

    # Content
    content = Text()
    for line in output.split("\n")[:20]:  # Limit to 20 lines
        content.append(f"  {line}\n", style="white")

    if output.count("\n") > 20:
        content.append(f"  ... ({output.count(chr(10)) - 20} more lines)", style="dim")

    return Panel(
        content,
        title=title,
        title_align="left",
        border_style=status_color,
        box=ROUNDED,
        padding=(0, 1),
    )


class EnhancedLivePreviewBuffer(LivePreviewBuffer):
    """
    Enhanced live preview buffer with streaming support.

    Adds:
    - Token-by-token streaming display
    - Agent activity integration
    - Connection status display
    - Smooth scrolling
    """

    def __init__(self, max_lines: int = PREVIEW_LINES) -> None:
        """Initialize enhanced preview buffer."""
        super().__init__(max_lines)
        self._streaming_content: str = ""
        self._is_streaming: bool = False

    def start_streaming(self) -> None:
        """Start streaming mode."""
        self._is_streaming = True
        self._streaming_content = ""
        self.add_line("◐ Receiving response...", style=BRAND_INFO, line_type="streaming_start")

    def stream_token(self, token: str) -> None:
        """Add streaming token."""
        self._streaming_content += token

        # Update the last streaming line or add new one
        if self._lines and self._lines[-1].line_type == "streaming":
            self._lines[-1].content = f"  {self._streaming_content[-100:]}"  # Last 100 chars
        else:
            self.add_line(f"  {token}", style=BRAND_ACCENT, line_type="streaming")

    def end_streaming(self, total_tokens: int = 0, duration_seconds: float = 0.0) -> None:
        """End streaming mode."""
        self._is_streaming = False

        # Replace streaming indicator with completion
        if self._lines and self._lines[-1].line_type in ("streaming", "streaming_start"):
            stats = []
            if total_tokens > 0:
                stats.append(f"{total_tokens:,} tokens")
            if duration_seconds > 0:
                tps = total_tokens / duration_seconds if duration_seconds > 0 else 0
                stats.append(f"{tps:.1f} tok/s")
                stats.append(f"{duration_seconds:.1f}s")

            stats_str = " | ".join(stats) if stats else ""
            self._lines[-1] = PreviewLine(
                content=f"✓ Response complete{' (' + stats_str + ')' if stats_str else ''}",
                style=BRAND_SUCCESS,
                timestamp=self._lines[-1].timestamp,
                line_type="success",
            )

        self._streaming_content = ""

    def add_agent_activity(
        self,
        agent_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
    ) -> None:
        """Add agent activity update."""
        icon = STATUS_ICONS.get(status, "○")
        color = {
            "running": BRAND_INFO,
            "thinking": BRAND_WARNING,
            "complete": BRAND_SUCCESS,
            "error": BRAND_ERROR,
        }.get(status, "dim")

        progress_bar = ""
        if progress > 0:
            bar_width = 10
            filled = int(progress / 100 * bar_width)
            progress_bar = f" [{'█' * filled}{'░' * (bar_width - filled)}] {progress}%"

        text = f"{icon} {agent_id}: {status}{progress_bar}"
        if message:
            text += f" - {message}"

        self.add_line(text, style=color, line_type="agent")

    def add_connection_status(
        self,
        connected: bool,
        latency_ms: float = 0.0,
        reconnecting: bool = False,
    ) -> None:
        """Add connection status update."""
        if reconnecting:
            self.add_line("◐ Reconnecting...", style=BRAND_WARNING, line_type="connection")
        elif connected:
            latency_str = f" ({latency_ms:.0f}ms)" if latency_ms > 0 else ""
            self.add_line(f"● Connected{latency_str}", style=BRAND_SUCCESS, line_type="connection")
        else:
            self.add_line("○ Disconnected", style=BRAND_ERROR, line_type="connection")

    def render_enhanced(self, show_timestamps: bool = True) -> Text:
        """Render enhanced buffer with formatting."""
        text = Text()
        visible = self.get_visible_lines()

        # Pad with empty lines if needed
        empty_lines = self.max_lines - len(visible)
        for _ in range(empty_lines):
            text.append("\n")

        for i, line in enumerate(visible):
            # Type-specific prefix
            type_prefix = {
                "command": "$ ",
                "output": "  ",
                "error": "✗ ",
                "success": "✓ ",
                "agent": "⚡ ",
                "streaming": "◐ ",
                "streaming_start": "◐ ",
                "connection": "● ",
                "info": "  ",
            }.get(line.line_type, "  ")

            # Timestamp
            if show_timestamps and line.timestamp:
                text.append(f"[{line.timestamp}] ", style="dim")

            # Type prefix
            type_color = {
                "command": BRAND_INFO,
                "error": BRAND_ERROR,
                "success": BRAND_SUCCESS,
                "agent": BRAND_ACCENT,
                "streaming": BRAND_WARNING,
                "streaming_start": BRAND_WARNING,
                "connection": BRAND_INFO,
            }.get(line.line_type, "dim")

            if line.line_type != "output":
                text.append(type_prefix, style=type_color)

            # Content
            text.append(line.content, style=line.style)

            if i < len(visible) - 1:
                text.append("\n")

        # Add streaming cursor if active (no blink for compatibility)
        if self._is_streaming:
            text.append("_", style=f"bold {BRAND_ACCENT}")

        return text
