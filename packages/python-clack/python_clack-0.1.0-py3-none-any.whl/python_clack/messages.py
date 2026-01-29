"""Message display functions (intro, outro, cancel)."""

from __future__ import annotations

import sys
from typing import TextIO

from rich.console import Console

from .symbols import S_BAR, S_BAR_END, S_BAR_START, S_STEP_CANCEL


def _get_console(output: TextIO | None = None) -> Console:
    """Get a console for output."""
    return Console(file=output or sys.stdout, highlight=False)


def intro(title: str = "", *, _output: TextIO | None = None) -> None:
    """Display an intro message.

    Args:
        title: The intro title to display.
        _output: Output stream (for testing).

    Example:
        >>> intro("Welcome to my app")
    """
    console = _get_console(_output)

    if title:
        console.print(f"[bright_black]{S_BAR_START}[/bright_black]  {title}")
    else:
        console.print(f"[bright_black]{S_BAR_START}[/bright_black]")


def outro(message: str = "", *, _output: TextIO | None = None) -> None:
    """Display an outro message.

    Args:
        message: The outro message to display.
        _output: Output stream (for testing).

    Example:
        >>> outro("All done!")
    """
    console = _get_console(_output)

    console.print()
    if message:
        console.print(f"[bright_black]{S_BAR_END}[/bright_black]  {message}")
    else:
        console.print(f"[bright_black]{S_BAR_END}[/bright_black]")
    console.print()


def cancel(message: str = "Operation cancelled.", *, _output: TextIO | None = None) -> None:
    """Display a cancellation message.

    Args:
        message: The cancellation message to display.
        _output: Output stream (for testing).

    Example:
        >>> cancel("User cancelled the operation")
    """
    console = _get_console(_output)

    console.print()
    console.print(f"[bright_black]{S_BAR}[/bright_black]")
    console.print(f"[red]{S_STEP_CANCEL}[/red]  {message}")
    console.print()
