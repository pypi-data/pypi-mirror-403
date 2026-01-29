"""Log utilities for displaying messages."""

from __future__ import annotations

import sys
from typing import TextIO

from rich.console import Console

from .symbols import S_BAR, S_ERROR, S_INFO, S_STEP_ACTIVE, S_SUCCESS, S_WARN


class Log:
    """Log utilities for displaying formatted messages.

    Provides methods for different log levels with appropriate
    colors and symbols.

    Example:
        >>> from python_clack import log
        >>> log.info("Processing...")
        >>> log.success("Done!")
        >>> log.warn("Deprecation warning")
        >>> log.error("Something failed")
    """

    def __init__(self, output: TextIO | None = None) -> None:
        """Initialize the logger.

        Args:
            output: Output stream (defaults to stdout).
        """
        self._output = output or sys.stdout
        self._console = Console(file=self._output, highlight=False)

    def _log(self, symbol: str, color: str, message: str) -> None:
        """Internal log method."""
        self._console.print(f"[bright_black]{S_BAR}[/bright_black]")
        self._console.print(f"[{color}]{symbol}[/{color}]  {message}")

    def message(self, message: str) -> None:
        """Display a plain message.

        Args:
            message: The message to display.
        """
        self._console.print(f"[bright_black]{S_BAR}[/bright_black]  {message}")

    def info(self, message: str) -> None:
        """Display an info message.

        Args:
            message: The message to display.
        """
        self._log(S_INFO, "blue", message)

    def success(self, message: str) -> None:
        """Display a success message.

        Args:
            message: The message to display.
        """
        self._log(S_SUCCESS, "green", message)

    def warn(self, message: str) -> None:
        """Display a warning message.

        Args:
            message: The message to display.
        """
        self._log(S_WARN, "yellow", message)

    def warning(self, message: str) -> None:
        """Display a warning message (alias for warn).

        Args:
            message: The message to display.
        """
        self.warn(message)

    def error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: The message to display.
        """
        self._log(S_ERROR, "red", message)

    def step(self, message: str) -> None:
        """Display a step message.

        Args:
            message: The message to display.
        """
        self._log(S_STEP_ACTIVE, "cyan", message)


# Default log instance
log = Log()
