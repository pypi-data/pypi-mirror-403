"""
Visual Progress UI for AiCippy Installer.

Provides beautiful animated progress displays with:
- Animated progress bars
- Mascot animations
- Poetic welcome messages
- Motivating slogans
- Installation hints
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Final

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# Brand colors
PRIMARY: Final[str] = "#667eea"
SECONDARY: Final[str] = "#764ba2"
ACCENT: Final[str] = "#f093fb"
SUCCESS: Final[str] = "#10b981"
WARNING: Final[str] = "#f59e0b"
INFO: Final[str] = "#3b82f6"
GLOW: Final[str] = "#a78bfa"

# Poetic welcome messages
WELCOME_MESSAGES: Final[tuple[str, ...]] = (
    "Where imagination meets intelligence...",
    "Crafting digital dreams into reality...",
    "Your AI companion awaits...",
    "The future of development begins here...",
    "Empowering creators, one command at a time...",
    "Intelligence that inspires, code that captivates...",
    "From vision to version, seamlessly...",
)

# Motivating slogans
SLOGANS: Final[tuple[str, ...]] = (
    "Build Faster. Dream Bigger. Code Smarter.",
    "Your Vision. Our Intelligence. Infinite Possibilities.",
    "Where Every Line of Code Tells a Story.",
    "Transforming Ideas into Impact.",
    "The Art of Intelligent Automation.",
    "Elevate Your Code. Amplify Your Impact.",
    "Innovation at the Speed of Thought.",
)

# Installation phase descriptions
PHASE_DESCRIPTIONS: Final[dict[str, str]] = {
    "init": "Initializing installation...",
    "prereq": "Checking prerequisites...",
    "deps": "Installing dependencies...",
    "perms": "Configuring permissions...",
    "env": "Setting up environment...",
    "install": "Installing AiCippy...",
    "verify": "Verifying installation...",
    "complete": "Installation complete!",
}

# Post-installation hints
INSTALLATION_HINTS: Final[tuple[str, ...]] = (
    "Run 'aicippy login' to authenticate with your account",
    "Use 'aicippy --help' to see all available commands",
    "Try 'aicippy agent' to start an interactive AI session",
    "Configure your settings in ~/.aicippy/config.yaml",
    "Join our community at https://community.aicippy.io",
    "Check for updates with 'aicippy upgrade'",
    "Enable multi-agent mode with 'aicippy agent --parallel 5'",
)

# ASCII art banner
BANNER: Final[str] = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     ####  ###  ####  ###  #####  #####  ##   ##           ║
    ║    ##  ## ##  ##    ##   ##  ## ##  ##  ## ##             ║
    ║    ###### ##  ##    ##   #####  #####    ###              ║
    ║    ##  ## ##  ##    ##   ##     ##       ##               ║
    ║    ##  ## ###  ####  ### ##     ##       ##               ║
    ║                                                           ║
    ║          Enterprise Multi-Agent CLI System                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
"""

# Mini mascot for progress display
MASCOT_FRAMES: Final[tuple[str, ...]] = (
    """
  .---.
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    """,
    """
  .---.
 / * * \\
 \\  ^  /
  '---'
  \\| |/
  /   \\
    """,
    """
  .---.
 / o o \\
 \\  ~  /
  '---'
   | |
   | |
    """,
)


@dataclass
class ProgressPhase:
    """A phase in the installation progress."""

    id: str
    name: str
    weight: int = 1  # Relative weight for progress calculation


# Installation phases with weights
INSTALLATION_PHASES: Final[list[ProgressPhase]] = [
    ProgressPhase("init", "Initialization", 5),
    ProgressPhase("prereq", "Prerequisites", 10),
    ProgressPhase("deps", "Dependencies", 40),
    ProgressPhase("perms", "Permissions", 10),
    ProgressPhase("env", "Environment", 15),
    ProgressPhase("install", "Installation", 15),
    ProgressPhase("verify", "Verification", 5),
]


class InstallationProgress:
    """
    Manages the visual progress display during installation.

    Provides animated progress bars, mascot animations, and
    motivational messages throughout the installation process.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize progress display."""
        self.console = console or Console()
        self.current_phase = 0
        self.current_progress = 0
        self.total_weight = sum(p.weight for p in INSTALLATION_PHASES)
        self.frame_idx = 0
        self.start_time = time.monotonic()

        # Select random messages
        self.welcome_message = random.choice(WELCOME_MESSAGES)
        self.slogan = random.choice(SLOGANS)

    def _get_banner_text(self) -> Text:
        """Get the colored banner text."""
        text = Text()
        lines = BANNER.strip().split("\n")

        for i, line in enumerate(lines):
            # Apply gradient colors
            if i < len(lines) // 3:
                color = GLOW
            elif i < 2 * len(lines) // 3:
                color = PRIMARY
            else:
                color = SECONDARY

            text.append(line + "\n", style=color)

        return text

    def _get_mascot_frame(self) -> Text:
        """Get the current mascot animation frame."""
        frame = MASCOT_FRAMES[self.frame_idx % len(MASCOT_FRAMES)]
        text = Text()

        for line in frame.strip().split("\n"):
            text.append(line + "\n", style=ACCENT)

        return text

    def _create_progress_display(
        self,
        phase_name: str,
        phase_progress: int,
        overall_progress: int,
        status_message: str,
    ) -> Group:
        """Create the progress display group."""
        # Banner
        banner = self._get_banner_text()

        # Welcome message
        welcome = Text()
        welcome.append("\n")
        welcome.append("    ", style="dim")
        welcome.append(self.welcome_message, style=f"italic {GLOW}")
        welcome.append("\n\n")

        # Slogan
        slogan = Text()
        slogan.append("    ", style="dim")
        slogan.append(f'"{self.slogan}"', style=f"bold {ACCENT}")
        slogan.append("\n\n")

        # Mascot
        mascot = self._get_mascot_frame()

        # Progress info
        progress_text = Text()
        progress_text.append("\n")
        progress_text.append("    Phase: ", style="dim")
        progress_text.append(phase_name, style=f"bold {INFO}")
        progress_text.append("\n")
        progress_text.append("    Status: ", style="dim")
        progress_text.append(status_message, style=PRIMARY)
        progress_text.append("\n\n")

        # Progress bar
        bar_width = 50
        filled = int(overall_progress / 100 * bar_width)
        empty = bar_width - filled

        progress_bar = Text()
        progress_bar.append("    [", style="dim")

        # Gradient progress bar
        for i in range(filled):
            if i < bar_width // 3:
                progress_bar.append("█", style=GLOW)
            elif i < 2 * bar_width // 3:
                progress_bar.append("█", style=PRIMARY)
            else:
                progress_bar.append("█", style=SECONDARY)

        progress_bar.append("░" * empty, style="dim")
        progress_bar.append("] ", style="dim")
        progress_bar.append(f"{overall_progress}%", style=f"bold {SUCCESS}")
        progress_bar.append("\n")

        # Time elapsed
        elapsed = time.monotonic() - self.start_time
        time_text = Text()
        time_text.append(f"\n    Elapsed: {elapsed:.1f}s", style="dim")
        time_text.append("\n")

        return Group(
            Align.center(banner),
            Align.center(welcome),
            Align.center(slogan),
            Align.center(mascot),
            Align.center(progress_text),
            Align.center(progress_bar),
            Align.center(time_text),
        )

    def show_welcome(self) -> None:
        """Display the welcome screen."""
        self.console.clear()
        banner = self._get_banner_text()

        welcome = Text()
        welcome.append("\n\n")
        welcome.append("    ", style="dim")
        welcome.append(self.welcome_message, style=f"italic {GLOW}")
        welcome.append("\n\n")
        welcome.append("    ", style="dim")
        welcome.append(f'"{self.slogan}"', style=f"bold {ACCENT}")
        welcome.append("\n\n")

        mascot = self._get_mascot_frame()

        self.console.print(Align.center(banner))
        self.console.print(Align.center(welcome))
        self.console.print(Align.center(mascot))
        self.console.print()

    def update_progress(
        self,
        phase: str,
        phase_progress: int,
        status: str,
    ) -> tuple[str, int, int, str]:
        """
        Calculate overall progress based on phase.

        Args:
            phase: Current phase ID.
            phase_progress: Progress within current phase (0-100).
            status: Status message.

        Returns:
            Tuple of (phase_name, phase_progress, overall_progress, status).
        """
        # Find phase index
        phase_idx = 0
        for i, p in enumerate(INSTALLATION_PHASES):
            if p.id == phase:
                phase_idx = i
                break

        # Calculate overall progress
        completed_weight = sum(p.weight for p in INSTALLATION_PHASES[:phase_idx])
        current_phase_weight = INSTALLATION_PHASES[phase_idx].weight
        current_contribution = current_phase_weight * (phase_progress / 100)

        overall = int((completed_weight + current_contribution) / self.total_weight * 100)
        phase_name = INSTALLATION_PHASES[phase_idx].name

        return phase_name, phase_progress, overall, status

    async def run_with_progress(
        self,
        phases_generator,
    ) -> None:
        """
        Run installation with animated progress display.

        Args:
            phases_generator: Async generator yielding (phase, progress, status).
        """
        self.console.clear()

        with Live(console=self.console, refresh_per_second=4, transient=False) as live:
            async for phase, progress, status in phases_generator:
                phase_name, phase_pct, overall_pct, status_msg = self.update_progress(
                    phase, progress, status
                )

                self.frame_idx += 1
                display = self._create_progress_display(
                    phase_name, phase_pct, overall_pct, status_msg
                )
                live.update(display)

                await asyncio.sleep(0.1)

    def show_completion(self, success: bool = True, errors: list[str] | None = None) -> None:
        """
        Display completion screen with hints.

        Args:
            success: Whether installation was successful.
            errors: Optional list of errors.
        """
        self.console.print()
        self.console.print(Rule(style=SUCCESS if success else WARNING))
        self.console.print()

        if success:
            # Success header
            header = Text()
            header.append("\n")
            header.append("    ✓ ", style=f"bold {SUCCESS}")
            header.append("Installation Complete!", style=f"bold {SUCCESS}")
            header.append("\n\n")
            self.console.print(Align.center(header))

            # Hints
            hints_table = Table.grid(padding=(0, 2))
            hints_table.add_column(style=ACCENT)
            hints_table.add_column()

            self.console.print(
                Align.center(Text("    Quick Start Guide:", style=f"bold {INFO}"))
            )
            self.console.print()

            # Select random hints
            selected_hints = random.sample(INSTALLATION_HINTS, min(5, len(INSTALLATION_HINTS)))
            for i, hint in enumerate(selected_hints, 1):
                hints_table.add_row(f"    {i}.", hint)

            self.console.print(Align.center(hints_table))
            self.console.print()

            # Final message
            final = Text()
            final.append("\n    ")
            final.append("Ready to begin? ", style="dim")
            final.append("Run ", style="dim")
            final.append("aicippy", style=f"bold {ACCENT}")
            final.append(" to start your journey!", style="dim")
            final.append("\n\n")
            self.console.print(Align.center(final))

        else:
            # Error header
            header = Text()
            header.append("\n")
            header.append("    ✗ ", style=f"bold {WARNING}")
            header.append("Installation encountered issues", style=f"bold {WARNING}")
            header.append("\n\n")
            self.console.print(Align.center(header))

            if errors:
                for error in errors[:5]:  # Show max 5 errors
                    error_text = Text()
                    error_text.append("    • ", style=WARNING)
                    error_text.append(error, style="white")
                    self.console.print(Align.center(error_text))

            self.console.print()

            # Troubleshooting hint
            trouble = Text()
            trouble.append("\n    Try: ", style="dim")
            trouble.append("pip install --upgrade aicippy", style=f"{INFO}")
            trouble.append("\n    Or visit: ", style="dim")
            trouble.append("https://docs.aicippy.io/troubleshooting", style=f"{ACCENT}")
            trouble.append("\n\n")
            self.console.print(Align.center(trouble))

        self.console.print(Rule(style=SUCCESS if success else WARNING))
        self.console.print()


def create_simple_progress() -> Progress:
    """Create a simple progress bar for quick operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=Console(),
    )


async def demo_progress() -> None:
    """Demo the progress display."""
    console = Console()
    progress = InstallationProgress(console)

    async def phase_generator():
        phases = [
            ("init", "Initializing..."),
            ("prereq", "Checking Python version..."),
            ("deps", "Installing pydantic..."),
            ("deps", "Installing rich..."),
            ("deps", "Installing boto3..."),
            ("perms", "Setting up directories..."),
            ("env", "Configuring PATH..."),
            ("install", "Finalizing..."),
            ("verify", "Verifying installation..."),
        ]

        for i, (phase, status) in enumerate(phases):
            for pct in range(0, 101, 20):
                yield phase, pct, status
                await asyncio.sleep(0.1)

    await progress.run_with_progress(phase_generator())
    progress.show_completion(success=True)


if __name__ == "__main__":
    asyncio.run(demo_progress())
