"""Color and styling utilities using Rich."""

from rich.console import Console
from rich.style import Style

from ._core.state import State
from .symbols import (
    S_BAR,
    S_STEP_ACTIVE,
    S_STEP_CANCEL,
    S_STEP_ERROR,
    S_STEP_SUBMIT,
)

# Shared console instance
_console: Console | None = None


def get_console() -> Console:
    """Get or create the shared console instance."""
    global _console
    if _console is None:
        _console = Console(highlight=False)
    return _console


# Style definitions matching clack's color scheme
STYLE_CYAN = Style(color="cyan")
STYLE_GREEN = Style(color="green")
STYLE_RED = Style(color="red")
STYLE_YELLOW = Style(color="yellow")
STYLE_GRAY = Style(color="bright_black")
STYLE_DIM = Style(dim=True)
STYLE_INVERSE = Style(reverse=True)
STYLE_STRIKETHROUGH = Style(strike=True)


def color_cyan(text: str) -> str:
    """Apply cyan color to text."""
    return f"[cyan]{text}[/cyan]"


def color_green(text: str) -> str:
    """Apply green color to text."""
    return f"[green]{text}[/green]"


def color_red(text: str) -> str:
    """Apply red color to text."""
    return f"[red]{text}[/red]"


def color_yellow(text: str) -> str:
    """Apply yellow color to text."""
    return f"[yellow]{text}[/yellow]"


def color_gray(text: str) -> str:
    """Apply gray color to text."""
    return f"[bright_black]{text}[/bright_black]"


def color_dim(text: str) -> str:
    """Apply dim style to text."""
    return f"[dim]{text}[/dim]"


def color_inverse(text: str) -> str:
    """Apply inverse style to text."""
    return f"[reverse]{text}[/reverse]"


def color_strikethrough(text: str) -> str:
    """Apply strikethrough style to text."""
    return f"[strike]{text}[/strike]"


def symbol(state: State) -> str:
    """Get the colored symbol for a prompt state.

    Args:
        state: The current prompt state.

    Returns:
        A colored symbol string representing the state.
    """
    match state:
        case State.INITIAL | State.ACTIVE:
            return color_cyan(S_STEP_ACTIVE)
        case State.CANCEL:
            return color_red(S_STEP_CANCEL)
        case State.ERROR:
            return color_yellow(S_STEP_ERROR)
        case State.SUBMIT:
            return color_green(S_STEP_SUBMIT)


def symbol_bar(state: State) -> str:
    """Get the colored bar symbol for a prompt state.

    Args:
        state: The current prompt state.

    Returns:
        A colored bar string representing the state.
    """
    match state:
        case State.INITIAL | State.ACTIVE:
            return color_cyan(S_BAR)
        case State.CANCEL:
            return color_red(S_BAR)
        case State.ERROR:
            return color_yellow(S_BAR)
        case State.SUBMIT:
            return color_green(S_BAR)
