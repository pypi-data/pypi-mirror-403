"""
AiCippy Mascot - Animated ZooZoo-style character.

Provides cute animated ASCII art mascot with various poses and animations:
- Idle animation (breathing/bobbing)
- Thinking animation (head scratch)
- Working animation (typing)
- Happy animation (jumping)
- Waving animation
"""

from __future__ import annotations

import asyncio
import itertools
import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from typing import Final

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Brand colors
MASCOT_PRIMARY: Final[str] = "#667eea"
MASCOT_SECONDARY: Final[str] = "#764ba2"
MASCOT_ACCENT: Final[str] = "#f093fb"
MASCOT_GLOW: Final[str] = "#a78bfa"
MASCOT_WHITE: Final[str] = "#ffffff"
MASCOT_HIGHLIGHT: Final[str] = "#c4b5fd"


class MascotMood(Enum):
    """Mascot mood/animation state."""

    IDLE = auto()
    THINKING = auto()
    WORKING = auto()
    HAPPY = auto()
    WAVING = auto()
    SLEEPING = auto()
    EXCITED = auto()


# ============================================================================
# Mascot Frames - ZooZoo Style Character
# ============================================================================

# Idle animation frames (gentle bobbing)
IDLE_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
         '--'
    ''',
    '''
       .~~~~~.
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
         |  |
         '--'
    ''',
)

# Thinking animation frames (scratching head)
THINKING_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.  ?
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
        \\|  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.  ?
      /   __   \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
     ? .~~~~~.
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |/
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.
      /   ??   \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
)

# Working animation frames (typing)
WORKING_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.
      /       \\
     |  *   *  |
     |    __   |
      \\  \\__/ /
       '-----'
        \\|  |/
       __|  |__
      |  |  |  |
      '  '--'  '
    ''',
    '''
       .~~~~~.
      /       \\
     |  *   *  |
     |    __   |
      \\  \\__/ /
       '-----'
        \\|  |/
      ___|  |___
     |   |  |   |
      '  '--'  '
    ''',
    '''
       .~~~~~.
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
        \\|  |/
       __|  |__
      |  '--'  |
      '        '
    ''',
    '''
       .~~~~~.
      /       \\
     |  *   *  |
     |    __   |
      \\  \\__/ /
       '-----'
        \\|  |/
      ___|  |___
      |  '--'  |
      '        '
    ''',
)

# Happy/jumping animation frames
HAPPY_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.    *
      /       \\
     |  ^   ^  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
    *  .~~~~~.  *
      /       \\
     |  ^   ^  |
     |   \\__/  |
      \\        /
       '-----'
       \\ |  | /
        \\|  |/
         |  |
         '--'
    ''',
    '''
       .~~~~~.
      /   *    \\
     |  ^   ^  |
     |   \\__/  |
      \\        /
       '-----'
         \\  /
          ||
         /  \\
        /    \\
    ''',
    '''
   *   .~~~~~.   *
      /       \\
     |  ^   ^  |
     |   \\__/  |
      \\        /
       '-----'
        \\|  |/
         |  |
        /    \\
       '      '
    ''',
)

# Waving animation frames
WAVING_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.
      /       \\
     |  o   o  | /
     |    __   |/
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.   \\
      /       \\  |
     |  o   o  | |
     |    __   |/
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.  __/
      /       \\
     |  o   o  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.   \\
      /       \\  \\
     |  o   o  |  |
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
)

# Sleeping animation frames
SLEEPING_FRAMES: Final[tuple[str, ...]] = (
    '''
       .~~~~~.   z
      /       \\  z
     |  -   -  |  z
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.    z
      /       \\   z
     |  -   -  |   z
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
    '''
       .~~~~~.     z
      /       \\    z
     |  -   -  |    z
     |    __   |
      \\  \\__/ /
       '-----'
         |  |
        /|  |\\
       / |  | \\
      '  '--'  '
    ''',
)

# Excited animation frames (bouncing with sparkles)
EXCITED_FRAMES: Final[tuple[str, ...]] = (
    '''
    ** .~~~~~. **
      /       \\
     |  *   *  |
     |   \\__/  |
      \\        /
       '-----'
       \\ |  | /
        \\|  |/
        /|  |\\
       ' '--' '
    ''',
    '''
   **  .~~~~~.  **
      /   **   \\
     |  *   *  |
     |   \\__/  |
      \\        /
       '-----'
         |  |
        /|  |\\
         |  |
         '--'
    ''',
    '''
  **   .~~~~~.   **
      /       \\
     |  *   *  |
     |   \\__/  |
      \\        /
       '-----'
      \\ |    | /
       \\|    |/
        '----'
    ''',
    '''
    ** .~~~~~. **
      /       \\
     |  *   *  |
     |   \\__/  |
      \\        /
       '-----'
        \\    /
         \\  /
         /  \\
        /    \\
    ''',
)

# Mini mascot for header (smaller version)
MINI_IDLE_FRAMES: Final[tuple[str, ...]] = (
    '''
  .---.
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
    '''
  .---.
 / o o \\
 \\  ^  /
  '---'
   | |
   | |
    ''',
    '''
  .---.
 / o o \\
 \\  ^  /
  '---'
   ||
  /  \\
    ''',
)

MINI_THINKING_FRAMES: Final[tuple[str, ...]] = (
    '''
  .---. ?
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
    '''
  .---.  ?
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
    '''
? .---.
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
)

MINI_HAPPY_FRAMES: Final[tuple[str, ...]] = (
    '''
  .---. *
 / ^ ^ \\
 \\ \\_/ /
  '---'
   \\|/
    |
    ''',
    '''
* .---.
 / ^ ^ \\
 \\ \\_/ /
  '---'
   |||
   \\_/
    ''',
    '''
  .---. *
 / ^ ^ \\
 \\ \\_/ /
  '---'
  \\   /
   \\_/
    ''',
)

MINI_WORKING_FRAMES: Final[tuple[str, ...]] = (
    '''
  .---.
 / * * \\
 \\  ^  /
  '---'
  \\| |/
  _| |_
    ''',
    '''
  .---.
 / * * \\
 \\  ^  /
  '---'
  \\| |/
 __| |__
    ''',
    '''
  .---.
 / o o \\
 \\  ^  /
  '---'
  \\| |/
  _| |_
    ''',
)

MINI_WAVING_FRAMES: Final[tuple[str, ...]] = (
    '''
  .---. /
 / o o \\/
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
    '''
  .---.  \\
 / o o \\ |
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
    '''
  .---._/
 / o o \\
 \\  ^  /
  '---'
   | |
  /   \\
    ''',
)


# ============================================================================
# Mascot Animation Controller
# ============================================================================


@dataclass
class MascotAnimator:
    """
    Animated mascot controller.

    Provides frame-by-frame animation with mood transitions.
    """

    mood: MascotMood = MascotMood.IDLE
    frame_delay: float = 0.3
    use_mini: bool = False

    def get_frames(self) -> tuple[str, ...]:
        """Get animation frames for current mood."""
        if self.use_mini:
            frames_map = {
                MascotMood.IDLE: MINI_IDLE_FRAMES,
                MascotMood.THINKING: MINI_THINKING_FRAMES,
                MascotMood.WORKING: MINI_WORKING_FRAMES,
                MascotMood.HAPPY: MINI_HAPPY_FRAMES,
                MascotMood.WAVING: MINI_WAVING_FRAMES,
                MascotMood.SLEEPING: MINI_IDLE_FRAMES,  # Reuse idle for mini
                MascotMood.EXCITED: MINI_HAPPY_FRAMES,
            }
        else:
            frames_map = {
                MascotMood.IDLE: IDLE_FRAMES,
                MascotMood.THINKING: THINKING_FRAMES,
                MascotMood.WORKING: WORKING_FRAMES,
                MascotMood.HAPPY: HAPPY_FRAMES,
                MascotMood.WAVING: WAVING_FRAMES,
                MascotMood.SLEEPING: SLEEPING_FRAMES,
                MascotMood.EXCITED: EXCITED_FRAMES,
            }
        return frames_map.get(self.mood, IDLE_FRAMES if not self.use_mini else MINI_IDLE_FRAMES)

    def get_frame_iterator(self) -> Iterator[str]:
        """Get infinite frame iterator."""
        return itertools.cycle(self.get_frames())

    def render_frame(self, frame: str, with_color: bool = True) -> Text:
        """
        Render a single frame with gradient coloring.

        Args:
            frame: ASCII art frame string.
            with_color: Whether to apply gradient colors.

        Returns:
            Rich Text with colored frame.
        """
        if not with_color:
            return Text(frame)

        lines = frame.strip('\n').split('\n')
        result = Text()

        for i, line in enumerate(lines):
            # Apply gradient based on line position
            if i < len(lines) // 3:
                color = MASCOT_GLOW
            elif i < 2 * len(lines) // 3:
                color = MASCOT_PRIMARY
            else:
                color = MASCOT_SECONDARY

            # Highlight special characters
            colored_line = Text()
            for char in line:
                if char in 'o*^':
                    colored_line.append(char, style=MASCOT_ACCENT)
                elif char in '?z':
                    colored_line.append(char, style=f"bold {MASCOT_HIGHLIGHT}")
                elif char in '/-\\|_':
                    colored_line.append(char, style=color)
                elif char in "'.~":
                    colored_line.append(char, style="dim " + color)
                else:
                    colored_line.append(char, style=color)

            result.append(colored_line)
            if i < len(lines) - 1:
                result.append('\n')

        return result


def create_mascot_panel(
    mood: MascotMood = MascotMood.IDLE,
    frame_idx: int = 0,
    mini: bool = False,
    title: str | None = None,
) -> Panel:
    """
    Create a panel with the mascot in specified mood.

    Args:
        mood: Mascot mood/animation state.
        frame_idx: Which frame to show.
        mini: Use mini version.
        title: Optional panel title.

    Returns:
        Rich Panel with mascot.
    """
    animator = MascotAnimator(mood=mood, use_mini=mini)
    frames = animator.get_frames()
    frame = frames[frame_idx % len(frames)]
    colored = animator.render_frame(frame)

    return Panel(
        Align.center(colored),
        border_style=MASCOT_PRIMARY,
        title=title,
        title_align="center",
        padding=(0, 1),
    )


def create_animated_header(
    version: str = "1.0.0",
    mood: MascotMood = MascotMood.IDLE,
    frame_idx: int = 0,
) -> Group:
    """
    Create animated header with mini mascot.

    Args:
        version: App version string.
        mood: Mascot mood.
        frame_idx: Animation frame index.

    Returns:
        Rich Group with header and mascot.
    """
    animator = MascotAnimator(mood=mood, use_mini=True)
    frames = animator.get_frames()
    frame = frames[frame_idx % len(frames)]
    mascot_text = animator.render_frame(frame)

    # Logo text
    logo = Text()
    logo.append("+=======================================================+\n", style=MASCOT_PRIMARY)
    logo.append("|", style=MASCOT_PRIMARY)
    logo.append("          ", style=MASCOT_PRIMARY)
    logo.append("A", style=f"bold {MASCOT_GLOW}")
    logo.append("i", style=f"bold {MASCOT_PRIMARY}")
    logo.append("C", style=f"bold {MASCOT_SECONDARY}")
    logo.append("i", style=f"bold {MASCOT_ACCENT}")
    logo.append("p", style=f"bold {MASCOT_PRIMARY}")
    logo.append("p", style=f"bold {MASCOT_GLOW}")
    logo.append("y", style=f"bold {MASCOT_SECONDARY}")
    logo.append(f"  v{version}", style="dim")
    logo.append("                            ", style=MASCOT_PRIMARY)
    logo.append("|\n", style=MASCOT_PRIMARY)
    logo.append("|", style=MASCOT_PRIMARY)
    logo.append("    Enterprise Multi-Agent CLI System    ", style=f"italic {MASCOT_HIGHLIGHT}")
    logo.append("              |\n", style=MASCOT_PRIMARY)
    logo.append("+=======================================================+", style=MASCOT_PRIMARY)

    return Group(mascot_text, logo)


async def run_mascot_animation(
    console: Console,
    mood: MascotMood = MascotMood.IDLE,
    duration: float = 3.0,
    mini: bool = False,
) -> None:
    """
    Run mascot animation for specified duration.

    Args:
        console: Rich console.
        mood: Mascot mood.
        duration: Animation duration in seconds.
        mini: Use mini version.
    """
    animator = MascotAnimator(mood=mood, use_mini=mini)
    frames = animator.get_frames()

    start_time = time.monotonic()
    frame_idx = 0

    with Live(console=console, refresh_per_second=4) as live:
        while time.monotonic() - start_time < duration:
            frame = frames[frame_idx % len(frames)]
            colored = animator.render_frame(frame)
            live.update(Align.center(colored))
            frame_idx += 1
            await asyncio.sleep(animator.frame_delay)


def get_mood_message(mood: MascotMood) -> str:
    """Get a message for the mascot's mood."""
    messages = {
        MascotMood.IDLE: "Ready to help!",
        MascotMood.THINKING: "Hmm, let me think...",
        MascotMood.WORKING: "Working on it...",
        MascotMood.HAPPY: "Yay! All done!",
        MascotMood.WAVING: "Hello there!",
        MascotMood.SLEEPING: "Zzz...",
        MascotMood.EXCITED: "This is exciting!",
    }
    return messages.get(mood, "")


# ============================================================================
# Welcome Screen with Animated Mascot
# ============================================================================


def create_welcome_with_mascot(
    version: str = "1.0.0",
    frame_idx: int = 0,
) -> Group:
    """
    Create welcome screen with animated mascot.

    Args:
        version: App version.
        frame_idx: Animation frame.

    Returns:
        Rich Group with welcome content.
    """
    animator = MascotAnimator(mood=MascotMood.WAVING, use_mini=False)
    frames = animator.get_frames()
    frame = frames[frame_idx % len(frames)]
    mascot = animator.render_frame(frame)

    # Title with gradient
    title = Text()
    title.append("\n")
    title.append("  +===============================================================+\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                               ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("      _    _  ____  _                           ", style=MASCOT_GLOW)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("     / \\  (_)/ ___||_|_ __  _ __  _   _          ", style=MASCOT_PRIMARY)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("    / _ \\ | | |    | | '_ \\| '_ \\| | | |         ", style=MASCOT_SECONDARY)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("   / ___ \\| | |___ | | |_) | |_) | |_| |         ", style=MASCOT_ACCENT)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("  /_/   \\_\\_|\\____||_| .__/| .__/ \\__, |         ", style=MASCOT_HIGHLIGHT)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                     |_|   |_|    |___/          ", style=MASCOT_HIGHLIGHT)
    title.append("              |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                               ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append(f"         Enterprise Multi-Agent CLI System  v{version}         ", style=f"italic {MASCOT_HIGHLIGHT}")
    title.append("    |\n", style=MASCOT_PRIMARY)
    title.append("  |", style=MASCOT_PRIMARY)
    title.append("                                                               ", style=MASCOT_PRIMARY)
    title.append("|\n", style=MASCOT_PRIMARY)
    title.append("  +===============================================================+\n", style=MASCOT_PRIMARY)

    # Mascot says hi - properly aligned speech bubble
    speech_bubble = Text()
    speech_bubble.append("\n")
    speech_bubble.append("                    +---------------------------+\n", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("                    |", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("  Hi! I'm Cippy!         ", style=f"bold {MASCOT_ACCENT}")
    speech_bubble.append("|\n", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("                    |", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("  Let's build magic!     ", style=MASCOT_GLOW)
    speech_bubble.append("|\n", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("                    +---------------------------+\n", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("                              \\\n", style=MASCOT_HIGHLIGHT)
    speech_bubble.append("                               \\\n", style=MASCOT_HIGHLIGHT)

    return Group(title, speech_bubble, Align.center(mascot))


async def animate_welcome(
    console: Console,
    version: str = "1.0.0",
    duration: float = 2.5,
) -> None:
    """
    Show animated welcome screen.

    Args:
        console: Rich console.
        version: App version.
        duration: Animation duration.
    """
    animator = MascotAnimator(mood=MascotMood.WAVING, use_mini=False)
    frames = animator.get_frames()

    start_time = time.monotonic()
    frame_idx = 0

    with Live(console=console, refresh_per_second=4, transient=False) as live:
        while time.monotonic() - start_time < duration:
            content = create_welcome_with_mascot(version, frame_idx)
            live.update(content)
            frame_idx += 1
            await asyncio.sleep(0.25)

    # End with happy pose
    console.print(create_welcome_with_mascot(version, 0))


# ============================================================================
# Compact Colored Zozoo Welcome Animation (for login success)
# ============================================================================

# Compact oval-bodied Zozoo frames (filled with color)
COMPACT_ZOZOO_WELCOME_FRAMES: Final[tuple[str, ...]] = (
    '''
      ╭─────╮
     ╱  ◕ ◕  ╲
    │    ▽    │
    │  ╲___╱  │
     ╲       ╱
      ╰─────╯
       │ │ ╱
      ╱│ │╱
     ╱ │ │
    ''',
    '''
      ╭─────╮
     ╱  ◕ ◕  ╲
    │    ▽    │
    │  ╲___╱  │
     ╲       ╱
      ╰─────╯
       │ │  \\
      ╱│ │  │
     ╱ │ │
    ''',
    '''
      ╭─────╮
     ╱  ◕ ◕  ╲
    │    ▽    │
    │  ╲___╱  │
     ╲       ╱
      ╰─────╯
       │ │__╱
      ╱│ │
     ╱ │ │
    ''',
    '''
      ╭─────╮
     ╱  ◕ ◕  ╲
    │    ▽    │
    │  ╲___╱  │
     ╲       ╱
      ╰─────╯
       │ │ \\
      ╱│ │ \\
     ╱ │ │  │
    ''',
)


def render_compact_zozoo(frame: str, fill_color: str = MASCOT_PRIMARY) -> Text:
    """
    Render compact Zozoo with colored fill.

    Args:
        frame: ASCII art frame string.
        fill_color: Main fill color for the body.

    Returns:
        Rich Text with colored frame.
    """
    lines = frame.strip('\n').split('\n')
    result = Text()

    for i, line in enumerate(lines):
        colored_line = Text()
        for char in line:
            if char in '◕':
                # Eyes - bright accent
                colored_line.append(char, style=f"bold {MASCOT_ACCENT}")
            elif char in '▽':
                # Nose - highlight
                colored_line.append(char, style=MASCOT_HIGHLIGHT)
            elif char in '╭╮╰╯─│':
                # Body outline - gradient based on position
                if i < 3:
                    colored_line.append(char, style=f"bold {MASCOT_GLOW}")
                elif i < 6:
                    colored_line.append(char, style=f"bold {fill_color}")
                else:
                    colored_line.append(char, style=f"bold {MASCOT_SECONDARY}")
            elif char in '╱╲\\/_':
                # Body curves and limbs
                if i < 4:
                    colored_line.append(char, style=fill_color)
                else:
                    colored_line.append(char, style=MASCOT_SECONDARY)
            elif char == ' ':
                colored_line.append(char)
            else:
                colored_line.append(char, style=fill_color)

        result.append(colored_line)
        if i < len(lines) - 1:
            result.append('\n')

    return result


def create_compact_welcome_panel(username: str, frame_idx: int = 0) -> Panel:
    """
    Create compact welcome panel with Zozoo animation.

    Args:
        username: User's name to greet.
        frame_idx: Animation frame index.

    Returns:
        Rich Panel with welcome content.
    """
    frames = COMPACT_ZOZOO_WELCOME_FRAMES
    frame = frames[frame_idx % len(frames)]
    zozoo = render_compact_zozoo(frame)

    # Welcome message
    welcome = Text()
    welcome.append("\n")
    welcome.append("  ✨ ", style=MASCOT_ACCENT)
    welcome.append("Welcome, ", style=f"bold {MASCOT_HIGHLIGHT}")
    welcome.append(username, style=f"bold {MASCOT_GLOW}")
    welcome.append("!", style=f"bold {MASCOT_HIGHLIGHT}")
    welcome.append(" ✨\n\n", style=MASCOT_ACCENT)
    welcome.append("     Hi! I'm ", style=MASCOT_WHITE)
    welcome.append("Cippy", style=f"bold {MASCOT_PRIMARY}")
    welcome.append("!\n", style=MASCOT_WHITE)
    welcome.append("     Let's build something amazing!\n", style=f"italic {MASCOT_HIGHLIGHT}")

    return Panel(
        Group(
            Align.center(zozoo),
            welcome,
        ),
        border_style=MASCOT_PRIMARY,
        title=f"[bold {MASCOT_GLOW}]AiCippy[/bold {MASCOT_GLOW}]",
        title_align="center",
        padding=(0, 2),
    )


async def animate_welcome_compact(
    console: Console,
    username: str,
    duration: float = 1.5,
) -> None:
    """
    Show compact colored Zozoo welcome animation after login.

    Args:
        console: Rich console.
        username: User's name to greet.
        duration: Animation duration.
    """
    console.clear()

    start_time = time.monotonic()
    frame_idx = 0

    with Live(console=console, refresh_per_second=6, transient=False) as live:
        while time.monotonic() - start_time < duration:
            panel = create_compact_welcome_panel(username, frame_idx)
            live.update(panel)
            frame_idx += 1
            await asyncio.sleep(0.15)

    # End with final frame
    console.print(create_compact_welcome_panel(username, 0))
    console.print()  # Add spacing before prompt area
