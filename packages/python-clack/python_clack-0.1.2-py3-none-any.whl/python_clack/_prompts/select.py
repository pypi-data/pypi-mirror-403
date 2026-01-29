"""Select prompt implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TextIO, TypedDict, TypeVar

from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from .._core.prompt import Prompt

T = TypeVar("T")


class SelectOption(TypedDict, total=False):
    """Option for select prompts."""

    value: Any
    label: str
    hint: str
    disabled: bool


class SelectPrompt(Prompt[T], Generic[T]):
    """A single-selection prompt.

    Allows the user to select one option from a list.
    """

    def __init__(
        self,
        *,
        render: Callable[[Prompt[T]], str],
        options: list[SelectOption],
        initial_value: T | None = None,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the select prompt.

        Args:
            render: Function that returns the prompt display string.
            options: List of options to select from.
            initial_value: Initial selected value.
            input_stream: Input stream.
            output_stream: Output stream.
        """
        self.options = options
        self._cursor_index = 0

        # Find initial cursor position
        if initial_value is not None:
            for i, opt in enumerate(options):
                if opt.get("value") == initial_value:
                    self._cursor_index = i
                    break

        # Skip disabled options for initial position
        self._cursor_index = self._find_next_enabled(self._cursor_index, 1)

        # Set initial value
        if options and self._cursor_index < len(options):
            init_val = options[self._cursor_index].get("value")
        else:
            init_val = None

        super().__init__(
            render=render,
            validate=None,
            initial_value=init_val,  # type: ignore
            input_stream=input_stream,
            output_stream=output_stream,
        )

    @property
    def cursor_index(self) -> int:
        """Current cursor index in options list."""
        return self._cursor_index

    def _find_next_enabled(self, start: int, direction: int) -> int:
        """Find the next enabled option in the given direction.

        Args:
            start: Starting index.
            direction: Direction to search (1 or -1).

        Returns:
            Index of next enabled option, or start if none found.
        """
        if not self.options:
            return start

        index = start
        for _ in range(len(self.options)):
            if not self.options[index].get("disabled", False):
                return index
            index = (index + direction) % len(self.options)

        return start

    def _move_cursor(self, direction: int) -> None:
        """Move cursor in the given direction.

        Args:
            direction: Direction to move (1 for down, -1 for up).
        """
        if not self.options:
            return

        # Start from next/prev position
        new_index = (self._cursor_index + direction) % len(self.options)
        new_index = self._find_next_enabled(new_index, direction)

        self._cursor_index = new_index
        self._set_value(self.options[self._cursor_index].get("value"))  # type: ignore

    def _on_key(self, key_press: KeyPress) -> None:
        """Handle key press."""
        key = key_press.key
        char = key_press.data.lower() if key_press.data else ""

        # Move up
        if key == Keys.Up or char in ("k", "w"):
            self._move_cursor(-1)
            return

        # Move down
        if key == Keys.Down or char in ("j", "s"):
            self._move_cursor(1)
            return

        # Home/End
        if key == Keys.Home:
            self._cursor_index = self._find_next_enabled(0, 1)
            if self.options:
                self._set_value(self.options[self._cursor_index].get("value"))  # type: ignore
            return

        if key == Keys.End:
            self._cursor_index = self._find_next_enabled(len(self.options) - 1, -1)
            if self.options:
                self._set_value(self.options[self._cursor_index].get("value"))  # type: ignore
            return
