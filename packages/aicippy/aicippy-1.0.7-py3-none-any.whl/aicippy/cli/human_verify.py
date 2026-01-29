"""
Human Verification Module for AiCippy CLI.

Prevents automated/robot access by:
- Detecting automation environments (CI/CD, scripts, non-TTY)
- Presenting random puzzle questions requiring human judgment
- Timing-based detection of automated responses
"""

from __future__ import annotations

import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Final

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm

# Brand colors
BRAND_PRIMARY: Final[str] = "#667eea"
BRAND_SUCCESS: Final[str] = "#10b981"
BRAND_WARNING: Final[str] = "#f59e0b"
BRAND_ERROR: Final[str] = "#ef4444"
BRAND_INFO: Final[str] = "#3b82f6"
BRAND_ACCENT: Final[str] = "#a78bfa"

# Minimum response time in seconds (humans need time to read and respond)
MIN_HUMAN_RESPONSE_TIME: Final[float] = 1.5

# Maximum response time (to prevent timeout-based bypasses)
MAX_RESPONSE_TIME: Final[float] = 60.0


@dataclass
class VerificationResult:
    """Result of human verification."""

    is_human: bool
    reason: str
    response_time: float = 0.0
    automation_detected: bool = False


# Puzzle questions with correct answers (True = Yes, False = No)
# These require human judgment and common sense
PUZZLE_QUESTIONS: Final[list[tuple[str, bool]]] = [
    # Simple logic puzzles
    ("Is the sky typically blue during a clear day?", True),
    ("Can fish naturally fly through the air?", False),
    ("Is water wet?", True),
    ("Do birds have four legs?", False),
    ("Is ice cold to touch?", True),
    ("Can humans breathe underwater without equipment?", False),
    ("Does the sun rise in the east?", True),
    ("Is a circle a type of square?", False),
    ("Do trees have leaves or needles?", True),
    ("Can you see in complete darkness?", False),

    # Math-based (simple)
    ("Is 2 + 2 equal to 4?", True),
    ("Is 10 greater than 100?", False),
    ("Is half of 20 equal to 10?", True),
    ("Is 7 an even number?", False),
    ("Is zero a positive number?", False),

    # Common knowledge
    ("Is coffee typically served hot?", True),
    ("Do penguins live in the Sahara Desert?", False),
    ("Is English a language?", True),
    ("Can you hear sounds in outer space?", False),
    ("Is pizza a type of food?", True),
    ("Do cars run on water?", False),
    ("Is the Earth round?", True),
    ("Can plants grow without any light?", False),

    # Reverse psychology / tricky
    ("Is this question asking for a 'Yes' or 'No' answer?", True),
    ("Would a robot have difficulty answering creative questions?", True),
    ("Is it possible to clap with one hand?", False),
    ("Do humans need oxygen to survive?", True),
    ("Is silence a type of sound?", False),

    # Time/context aware
    ("Are you currently using a computer or device?", True),
    ("Is this a CLI (command-line interface) tool?", True),
    ("Are you a human being?", True),
]

# Environment variables that indicate automation
AUTOMATION_ENV_VARS: Final[list[str]] = [
    "CI",
    "CONTINUOUS_INTEGRATION",
    "BUILD_NUMBER",
    "BUILD_ID",
    "JENKINS_URL",
    "TRAVIS",
    "CIRCLECI",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "BITBUCKET_BUILD_NUMBER",
    "AUTOMATED",
    "AUTOMATION",
    "BOT",
    "ROBOT",
    "HEADLESS",
    "PUPPETEER",
    "SELENIUM",
    "PLAYWRIGHT",
    "CYPRESS",
    "TF_BUILD",  # Azure DevOps
    "TEAMCITY_VERSION",
    "BUILDKITE",
    "DRONE",
    "CODEBUILD_BUILD_ID",  # AWS CodeBuild
]


def is_tty() -> bool:
    """Check if running in an interactive terminal."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def detect_automation_environment() -> tuple[bool, str]:
    """
    Detect if running in an automated/CI environment.

    Returns:
        Tuple of (is_automated, reason).
    """
    # Check for CI/automation environment variables
    for env_var in AUTOMATION_ENV_VARS:
        if os.environ.get(env_var):
            return True, f"Automation environment detected: {env_var}={os.environ.get(env_var)}"

    # Check for non-interactive terminal
    if not is_tty():
        return True, "Non-interactive terminal detected (not a TTY)"

    # Check for common automation indicators in environment
    shell = os.environ.get("SHELL", "").lower()
    term = os.environ.get("TERM", "").lower()

    if term == "dumb":
        return True, "Dumb terminal detected (TERM=dumb)"

    # Check if stdin is a pipe
    try:
        import stat
        mode = os.fstat(sys.stdin.fileno()).st_mode
        if stat.S_ISFIFO(mode):
            return True, "Input is from a pipe (automated input detected)"
    except Exception:
        pass

    return False, "No automation detected"


def get_random_puzzle() -> tuple[str, bool]:
    """Get a random puzzle question and its correct answer."""
    return random.choice(PUZZLE_QUESTIONS)


def verify_human_response(
    question: str,
    correct_answer: bool,
    user_answer: bool,
    response_time: float,
) -> VerificationResult:
    """
    Verify if the response appears to be from a human.

    Args:
        question: The puzzle question asked.
        correct_answer: The correct answer.
        user_answer: The user's answer.
        response_time: Time taken to respond in seconds.

    Returns:
        VerificationResult with verification status.
    """
    # Check if answer is correct
    if user_answer != correct_answer:
        return VerificationResult(
            is_human=False,
            reason="Incorrect answer to verification question",
            response_time=response_time,
        )

    # Check response time - too fast indicates automation
    if response_time < MIN_HUMAN_RESPONSE_TIME:
        return VerificationResult(
            is_human=False,
            reason=f"Response too fast ({response_time:.2f}s) - possible automation",
            response_time=response_time,
            automation_detected=True,
        )

    # Check response time - too slow might indicate script with delays
    if response_time > MAX_RESPONSE_TIME:
        return VerificationResult(
            is_human=False,
            reason=f"Response timed out ({response_time:.2f}s)",
            response_time=response_time,
        )

    return VerificationResult(
        is_human=True,
        reason="Human verification passed",
        response_time=response_time,
    )


class HumanVerifier:
    """
    Verifies human users and blocks automated access.

    Features:
    - Environment-based automation detection
    - Random puzzle questions
    - Response timing analysis
    - Configurable retry limits
    """

    def __init__(
        self,
        console: Console | None = None,
        max_attempts: int = 3,
        skip_env_check: bool = False,
    ) -> None:
        """
        Initialize human verifier.

        Args:
            console: Rich console for output.
            max_attempts: Maximum verification attempts.
            skip_env_check: Skip environment automation check.
        """
        self.console = console or Console()
        self.max_attempts = max_attempts
        self.skip_env_check = skip_env_check
        self._verified = False
        self._verification_result: VerificationResult | None = None

    @property
    def is_verified(self) -> bool:
        """Check if user has been verified as human."""
        return self._verified

    def check_automation(self) -> VerificationResult | None:
        """
        Check for automation environment.

        Returns:
            VerificationResult if automation detected, None otherwise.
        """
        if self.skip_env_check:
            return None

        is_automated, reason = detect_automation_environment()

        if is_automated:
            return VerificationResult(
                is_human=False,
                reason=reason,
                automation_detected=True,
            )

        return None

    def verify(self, force: bool = False) -> VerificationResult:
        """
        Perform human verification.

        Args:
            force: Force verification even if already verified.

        Returns:
            VerificationResult with verification status.
        """
        # Return cached result if already verified
        if self._verified and not force:
            return VerificationResult(
                is_human=True,
                reason="Previously verified",
            )

        # Check for automation environment first
        auto_result = self.check_automation()
        if auto_result:
            self._show_automation_blocked(auto_result)
            return auto_result

        # Show verification prompt
        self.console.print(Panel(
            Text(
                "🔐 Human Verification Required\n\n"
                "AiCippy requires human verification to prevent automated access.\n"
                "Please answer the following question correctly.",
                style=BRAND_INFO,
            ),
            title=f"[bold {BRAND_WARNING}]Security Check[/bold {BRAND_WARNING}]",
            border_style=BRAND_WARNING,
        ))

        # Try verification up to max_attempts
        for attempt in range(1, self.max_attempts + 1):
            result = self._perform_verification_attempt(attempt)

            if result.is_human:
                self._verified = True
                self._verification_result = result
                self._show_verification_success()
                return result

            # Show failure and retry if attempts remaining
            if attempt < self.max_attempts:
                self._show_verification_failure(result, attempts_remaining=self.max_attempts - attempt)
            else:
                self._show_final_failure(result)

        return VerificationResult(
            is_human=False,
            reason=f"Failed verification after {self.max_attempts} attempts",
        )

    def _perform_verification_attempt(self, attempt: int) -> VerificationResult:
        """Perform a single verification attempt."""
        question, correct_answer = get_random_puzzle()

        self.console.print()
        self.console.print(Panel(
            Text(question, style=f"bold {BRAND_ACCENT}"),
            title=f"[bold]Question {attempt}/{self.max_attempts}[/bold]",
            border_style=BRAND_ACCENT,
        ))

        # Record start time
        start_time = time.monotonic()

        try:
            # Get user's answer using Rich Confirm
            user_answer = Confirm.ask(
                "Your answer",
                default=None,  # No default - force explicit answer
            )

            # Calculate response time
            response_time = time.monotonic() - start_time

            # Verify the response
            return verify_human_response(
                question=question,
                correct_answer=correct_answer,
                user_answer=user_answer,
                response_time=response_time,
            )

        except (KeyboardInterrupt, EOFError):
            return VerificationResult(
                is_human=False,
                reason="Verification cancelled by user",
                response_time=time.monotonic() - start_time,
            )

    def _show_automation_blocked(self, result: VerificationResult) -> None:
        """Show message when automation is detected."""
        self.console.print(Panel(
            Text(
                f"🤖 Automated Access Blocked\n\n"
                f"Reason: {result.reason}\n\n"
                f"AiCippy is designed for interactive human use only.\n"
                f"Automated scripts, bots, and CI/CD pipelines are not permitted.\n\n"
                f"If you believe this is an error, please run AiCippy\n"
                f"from an interactive terminal session.",
                style=BRAND_ERROR,
            ),
            title=f"[bold {BRAND_ERROR}]Access Denied[/bold {BRAND_ERROR}]",
            border_style=BRAND_ERROR,
        ))

    def _show_verification_success(self) -> None:
        """Show success message after verification."""
        self.console.print(Panel(
            Text(
                "✓ Human verification successful!\n"
                "Welcome to AiCippy.",
                style=BRAND_SUCCESS,
            ),
            border_style=BRAND_SUCCESS,
        ))

    def _show_verification_failure(
        self,
        result: VerificationResult,
        attempts_remaining: int,
    ) -> None:
        """Show failure message with retry option."""
        self.console.print(Panel(
            Text(
                f"✗ Verification failed: {result.reason}\n\n"
                f"Attempts remaining: {attempts_remaining}\n"
                f"Please try again.",
                style=BRAND_WARNING,
            ),
            border_style=BRAND_WARNING,
        ))

    def _show_final_failure(self, result: VerificationResult) -> None:
        """Show final failure message."""
        self.console.print(Panel(
            Text(
                f"🚫 Verification Failed\n\n"
                f"Reason: {result.reason}\n\n"
                f"Maximum verification attempts exceeded.\n"
                f"Access to AiCippy has been denied.\n\n"
                f"Please try again later.",
                style=BRAND_ERROR,
            ),
            title=f"[bold {BRAND_ERROR}]Access Denied[/bold {BRAND_ERROR}]",
            border_style=BRAND_ERROR,
        ))


def require_human_verification(
    console: Console | None = None,
    max_attempts: int = 3,
) -> bool:
    """
    Convenience function to require human verification.

    Args:
        console: Rich console for output.
        max_attempts: Maximum verification attempts.

    Returns:
        True if human verified, False otherwise.
    """
    verifier = HumanVerifier(console=console, max_attempts=max_attempts)
    result = verifier.verify()
    return result.is_human


def is_likely_automated() -> bool:
    """
    Quick check if running in an automated environment.

    Returns:
        True if automation is likely.
    """
    is_automated, _ = detect_automation_environment()
    return is_automated
