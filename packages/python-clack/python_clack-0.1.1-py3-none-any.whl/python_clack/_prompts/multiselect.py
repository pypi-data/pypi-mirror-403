"""Multi-select prompt implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TextIO, TypeVar

from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from .._core.prompt import Prompt
from .select import SelectOption

T = TypeVar("T")


class MultiSelectPrompt(Prompt[list[T]], Generic[T]):
    """A multi-selection prompt.

    Allows the user to select multiple options from a list.
    """

    def __init__(
        self,
        *,
        render: Callable[[Prompt[list[T]]], str],
        options: list[SelectOption],
        initial_values: list[T] | None = None,
        required: bool = False,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the multi-select prompt.

        Args:
            render: Function that returns the prompt display string.
            options: List of options to select from.
            initial_values: Initially selected values.
            required: If True, at least one option must be selected.
            input_stream: Input stream.
            output_stream: Output stream.
        """
        self.options = options
        self.required = required
        self._cursor_index = 0
        self._selected: set[int] = set()

        # Initialize selected values
        if initial_values:
            for i, opt in enumerate(options):
                if opt.get("value") in initial_values:
                    self._selected.add(i)

        # Skip disabled options for initial position
        self._cursor_index = self._find_next_enabled(0, 1)

        # Get initial value
        init_val = [self.options[i].get("value") for i in self._selected]

        super().__init__(
            render=render,
            validate=self._validate_required if required else None,
            initial_value=init_val,  # type: ignore
            input_stream=input_stream,
            output_stream=output_stream,
        )

    def _validate_required(self, value: list[T] | None) -> str | None:
        """Validate that at least one option is selected."""
        if self.required and not self._selected:
            return "Please select at least one option"
        return None

    @property
    def cursor_index(self) -> int:
        """Current cursor index in options list."""
        return self._cursor_index

    @property
    def selected_indices(self) -> set[int]:
        """Set of selected option indices."""
        return self._selected

    def is_selected(self, index: int) -> bool:
        """Check if an option is selected.

        Args:
            index: Option index.

        Returns:
            True if the option is selected.
        """
        return index in self._selected

    def _find_next_enabled(self, start: int, direction: int) -> int:
        """Find the next enabled option in the given direction."""
        if not self.options:
            return start

        index = start
        for _ in range(len(self.options)):
            if not self.options[index].get("disabled", False):
                return index
            index = (index + direction) % len(self.options)

        return start

    def _move_cursor(self, direction: int) -> None:
        """Move cursor in the given direction."""
        if not self.options:
            return

        new_index = (self._cursor_index + direction) % len(self.options)
        new_index = self._find_next_enabled(new_index, direction)
        self._cursor_index = new_index

    def _toggle_current(self) -> None:
        """Toggle selection of current option."""
        if not self.options:
            return

        opt = self.options[self._cursor_index]
        if opt.get("disabled", False):
            return

        if self._cursor_index in self._selected:
            self._selected.remove(self._cursor_index)
        else:
            self._selected.add(self._cursor_index)

        self._update_value()

    def _toggle_all(self) -> None:
        """Toggle all options."""
        # Get all enabled indices
        enabled = {
            i for i, opt in enumerate(self.options) if not opt.get("disabled", False)
        }

        if self._selected == enabled:
            # All selected, deselect all
            self._selected.clear()
        else:
            # Select all enabled
            self._selected = enabled

        self._update_value()

    def _invert_selection(self) -> None:
        """Invert the current selection."""
        enabled = {
            i for i, opt in enumerate(self.options) if not opt.get("disabled", False)
        }
        self._selected = enabled - self._selected
        self._update_value()

    def _update_value(self) -> None:
        """Update the value based on current selection."""
        values = [self.options[i].get("value") for i in sorted(self._selected)]
        self._set_value(values)  # type: ignore

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

        # Toggle with space
        if char == " ":
            self._toggle_current()
            return

        # Toggle all with 'a'
        if char == "a":
            self._toggle_all()
            return

        # Invert with 'i'
        if char == "i":
            self._invert_selection()
            return

        # Home/End
        if key == Keys.Home:
            self._cursor_index = self._find_next_enabled(0, 1)
            return

        if key == Keys.End:
            self._cursor_index = self._find_next_enabled(len(self.options) - 1, -1)
            return
