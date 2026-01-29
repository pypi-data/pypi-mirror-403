"""Spinner for showing loading state."""

from __future__ import annotations

import sys
import threading
import time
from typing import TextIO

from rich.console import Console

from .symbols import S_BAR, S_ERROR, S_STEP_CANCEL, S_STEP_SUBMIT, S_WARN, UNICODE


class Spinner:
    """An animated spinner for showing loading state.

    Example:
        >>> s = spinner()
        >>> s.start("Loading...")
        >>> # do work
        >>> s.stop("Done!")
    """

    # Spinner frames
    FRAMES = ["◒", "◐", "◓", "◑"]
    FRAMES_ASCII = ["|", "/", "-", "\\"]

    def __init__(self, output: TextIO | None = None) -> None:
        """Initialize the spinner.

        Args:
            output: Output stream (defaults to stdout).
        """
        self._output = output or sys.stdout
        self._console = Console(file=self._output, highlight=False)
        self._message = ""
        self._running = False
        self._thread: threading.Thread | None = None
        self._frame_index = 0

        # Use ASCII frames if Unicode not supported
        self._frames = self.FRAMES if UNICODE else self.FRAMES_ASCII

    def _animate(self) -> None:
        """Animation loop running in background thread."""
        while self._running:
            frame = self._frames[self._frame_index % len(self._frames)]
            self._frame_index += 1

            # Write directly to output (no Rich markup in animation)
            # Use carriage return to overwrite the line
            line = f"\r{S_BAR}  {frame}  {self._message}"
            self._output.write(line)
            self._output.flush()

            time.sleep(0.08)

    def start(self, message: str = "") -> Spinner:
        """Start the spinner.

        Args:
            message: Message to display next to spinner.

        Returns:
            Self for chaining.
        """
        if self._running:
            return self

        self._message = message
        self._running = True
        self._frame_index = 0

        # Start animation thread
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

        return self

    def _stop_animation(self) -> None:
        """Stop the animation thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
            self._thread = None

    def stop(self, message: str = "", code: int = 0) -> None:
        """Stop the spinner with a final message.

        Args:
            message: Final message to display.
            code: Exit code (0=success, 1=error, 2=warning, 3=cancel).
        """
        self._stop_animation()

        # Clear line with carriage return and spaces
        self._output.write("\r" + " " * 80 + "\r")
        self._output.flush()

        # Choose symbol based on code
        if code == 0:
            symbol = f"[green]{S_STEP_SUBMIT}[/green]"
        elif code == 1:
            symbol = f"[red]{S_ERROR}[/red]"
        elif code == 2:
            symbol = f"[yellow]{S_WARN}[/yellow]"
        else:
            symbol = f"[red]{S_STEP_CANCEL}[/red]"

        msg = message or self._message
        self._console.print(f"[bright_black]{S_BAR}[/bright_black]")
        self._console.print(f"{symbol}  {msg}")

    def error(self, message: str = "") -> None:
        """Stop with an error.

        Args:
            message: Error message to display.
        """
        self.stop(message, code=1)

    def warn(self, message: str = "") -> None:
        """Stop with a warning.

        Args:
            message: Warning message to display.
        """
        self.stop(message, code=2)

    def cancel(self, message: str = "") -> None:
        """Stop with cancellation.

        Args:
            message: Cancellation message to display.
        """
        self.stop(message, code=3)

    def message(self, message: str) -> None:
        """Update the spinner message.

        Args:
            message: New message to display.
        """
        self._message = message


def spinner(output: TextIO | None = None) -> Spinner:
    """Create a new spinner instance.

    Args:
        output: Output stream (defaults to stdout).

    Returns:
        A new Spinner instance.

    Example:
        >>> s = spinner()
        >>> s.start("Loading data...")
        >>> # do work
        >>> s.stop("Data loaded!")
    """
    return Spinner(output)
