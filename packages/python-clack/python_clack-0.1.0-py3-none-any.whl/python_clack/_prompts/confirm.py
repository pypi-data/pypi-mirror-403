"""Confirm prompt implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import TextIO

from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from .._core.prompt import Prompt


class ConfirmPrompt(Prompt[bool]):
    """A yes/no confirmation prompt.

    Allows the user to select between yes and no options.
    """

    def __init__(
        self,
        *,
        render: Callable[[Prompt[bool]], str],
        active_label: str = "Yes",
        inactive_label: str = "No",
        initial_value: bool = False,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the confirm prompt.

        Args:
            render: Function that returns the prompt display string.
            active_label: Label for the "yes" option.
            inactive_label: Label for the "no" option.
            initial_value: Initial value (True for yes, False for no).
            input_stream: Input stream.
            output_stream: Output stream.
        """
        super().__init__(
            render=render,
            validate=None,
            initial_value=initial_value,
            input_stream=input_stream,
            output_stream=output_stream,
        )
        self.active_label = active_label
        self.inactive_label = inactive_label

    def _on_key(self, key_press: KeyPress) -> None:
        """Handle key press."""
        key = key_press.key
        char = key_press.data.lower() if key_press.data else ""

        # Toggle with left/right arrows or h/l (vim keys)
        if key in (Keys.Left, Keys.Right) or char in ("h", "l"):
            self._set_value(not self.value)
            return

        # Direct yes/no with y/n keys
        if char == "y":
            self._set_value(True)
            return

        if char == "n":
            self._set_value(False)
            return

        # Tab to toggle
        if key == Keys.Tab:
            self._set_value(not self.value)
            return
