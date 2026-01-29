"""Python-Clack: Beautiful CLI prompts for Python.

A Python port of the Node.js clack package for creating beautiful,
interactive command-line interfaces.

Example:
    >>> from python_clack import intro, text, select, confirm, outro, is_cancel
    >>>
    >>> intro("Welcome to my app")
    >>>
    >>> name = text("What is your name?", placeholder="Anonymous")
    >>> if is_cancel(name):
    ...     outro("Cancelled!")
    ...     exit(1)
    >>>
    >>> color = select(
    ...     "Pick a color",
    ...     options=[
    ...         {"value": "red", "label": "Red"},
    ...         {"value": "blue", "label": "Blue"},
    ...     ]
    ... )
    >>>
    >>> outro("All done!")
"""

from ._core.state import CANCEL, is_cancel
from .group import group
from .log import Log, log
from .messages import cancel, intro, outro
from .prompts import confirm, multiselect, password, select, text
from .spinner import Spinner, spinner

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Core utilities
    "CANCEL",
    "is_cancel",
    # Prompts
    "text",
    "select",
    "multiselect",
    "confirm",
    "password",
    # Messages
    "intro",
    "outro",
    "cancel",
    # Utilities
    "log",
    "Log",
    "spinner",
    "Spinner",
    "group",
]
