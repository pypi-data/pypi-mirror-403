"""State machine and cancel sentinel for prompts."""

from enum import Enum, auto
from typing import Any


class State(Enum):
    """Prompt states."""

    INITIAL = auto()
    ACTIVE = auto()
    SUBMIT = auto()
    CANCEL = auto()
    ERROR = auto()


class _CancelType:
    """Sentinel for cancelled prompts."""

    _instance: "_CancelType | None" = None

    def __new__(cls) -> "_CancelType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "CANCEL"

    def __bool__(self) -> bool:
        return False


CANCEL = _CancelType()


def is_cancel(value: Any) -> bool:
    """Check if a value represents a cancelled prompt.

    Args:
        value: The value to check.

    Returns:
        True if the value is the CANCEL sentinel.

    Example:
        >>> result = text(message="Name?")
        >>> if is_cancel(result):
        ...     print("User cancelled")
    """
    return value is CANCEL
