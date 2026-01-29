"""Terminal rendering utilities."""

import sys
from typing import TextIO

from rich.console import Console


class Renderer:
    """Handles terminal rendering with cursor control."""

    def __init__(self, output: TextIO | None = None) -> None:
        """Initialize the renderer.

        Args:
            output: Output stream (defaults to stdout).
        """
        self._output = output or sys.stdout
        self._console = Console(file=self._output, highlight=False, force_terminal=True)
        self._prev_frame_lines = 0

    @property
    def columns(self) -> int:
        """Get terminal width."""
        return self._console.width

    @property
    def rows(self) -> int:
        """Get terminal height."""
        return self._console.height

    def write(self, text: str) -> None:
        """Write text to output using Rich markup.

        Args:
            text: Text with optional Rich markup.
        """
        self._console.print(text, end="")
        # Track lines for clearing
        self._prev_frame_lines = text.count("\n")

    def write_raw(self, text: str) -> None:
        """Write raw text without Rich processing.

        Args:
            text: Raw text to write.
        """
        self._output.write(text)
        self._output.flush()

    def newline(self) -> None:
        """Write a newline."""
        self.write_raw("\n")

    def hide_cursor(self) -> None:
        """Hide the cursor."""
        self.write_raw("\x1b[?25l")

    def show_cursor(self) -> None:
        """Show the cursor."""
        self.write_raw("\x1b[?25h")

    def move_up(self, n: int = 1) -> None:
        """Move cursor up n lines."""
        if n > 0:
            self.write_raw(f"\x1b[{n}A")

    def move_down(self, n: int = 1) -> None:
        """Move cursor down n lines."""
        if n > 0:
            self.write_raw(f"\x1b[{n}B")

    def move_to_column(self, col: int = 0) -> None:
        """Move cursor to column (0-indexed)."""
        self.write_raw(f"\x1b[{col + 1}G")

    def carriage_return(self) -> None:
        """Move cursor to start of line."""
        self.write_raw("\r")

    def clear_line(self) -> None:
        """Clear the current line."""
        self.write_raw("\x1b[2K")

    def clear_down(self) -> None:
        """Clear from cursor to end of screen."""
        self.write_raw("\x1b[J")

    def clear_screen(self) -> None:
        """Clear the entire screen."""
        self.write_raw("\x1b[2J\x1b[H")

    def restore_cursor(self, lines: int) -> None:
        """Move cursor back to start of previous frame.

        Args:
            lines: Number of lines to move up.
        """
        if lines > 0:
            self.move_up(lines)
        self.carriage_return()

    def clear_previous_frame(self, lines: int) -> None:
        """Clear previous frame and position cursor.

        Args:
            lines: Number of lines in previous frame.
        """
        self.restore_cursor(lines)
        self.clear_down()
