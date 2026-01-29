"""Password prompt implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import TextIO

from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from .._core.prompt import Prompt
from .._core.state import State
from ..symbols import S_PASSWORD_MASK


class PasswordPrompt(Prompt[str]):
    """A password input prompt.

    Like text input but masks the characters.
    """

    def __init__(
        self,
        *,
        render: Callable[[Prompt[str]], str],
        validate: Callable[[str | None], str | None] | None = None,
        mask: str = S_PASSWORD_MASK,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the password prompt.

        Args:
            render: Function that returns the prompt display string.
            validate: Optional validation function.
            mask: Character to show instead of actual input.
            input_stream: Input stream.
            output_stream: Output stream.
        """
        super().__init__(
            render=render,
            validate=validate,
            initial_value="",
            input_stream=input_stream,
            output_stream=output_stream,
        )
        self.mask = mask
        self.user_input = ""

        # Sync value with user input
        self.on("finalize", self._on_finalize)

    @property
    def masked_value(self) -> str:
        """Get the masked representation of the input."""
        return self.mask * len(self.user_input)

    @property
    def masked_value_with_cursor(self) -> str:
        """Get masked value with cursor indicator."""
        if self.state == State.SUBMIT:
            return self.masked_value

        masked = self.masked_value
        if self._cursor >= len(masked):
            return f"{masked}[reverse] [/reverse]"

        before = masked[: self._cursor]
        at_cursor = masked[self._cursor]
        after = masked[self._cursor + 1 :]
        return f"{before}[reverse]{at_cursor}[/reverse]{after}"

    def _on_finalize(self) -> None:
        """Handle finalize event."""
        if self.state == State.SUBMIT:
            self.value = self.user_input

    def _on_key(self, key_press: KeyPress) -> None:
        """Handle key press."""
        key = key_press.key

        # Character input
        if len(key_press.data) == 1 and key_press.data.isprintable():
            # Insert character at cursor
            before = self.user_input[: self._cursor]
            after = self.user_input[self._cursor :]
            self.user_input = before + key_press.data + after
            self._cursor += 1
            self._set_value(self.user_input)
            return

        # Backspace
        if key in (Keys.Backspace, Keys.ControlH):
            if self._cursor > 0:
                before = self.user_input[: self._cursor - 1]
                after = self.user_input[self._cursor :]
                self.user_input = before + after
                self._cursor -= 1
                self._set_value(self.user_input)
            return

        # Delete
        if key == Keys.Delete:
            if self._cursor < len(self.user_input):
                before = self.user_input[: self._cursor]
                after = self.user_input[self._cursor + 1 :]
                self.user_input = before + after
                self._set_value(self.user_input)
            return

        # Cursor movement
        if key == Keys.Left:
            if self._cursor > 0:
                self._cursor -= 1
            return

        if key == Keys.Right:
            if self._cursor < len(self.user_input):
                self._cursor += 1
            return

        if key == Keys.Home or key == Keys.ControlA:
            self._cursor = 0
            return

        if key == Keys.End or key == Keys.ControlE:
            self._cursor = len(self.user_input)
            return

        # Clear line (Ctrl+U)
        if key == Keys.ControlU:
            self.user_input = ""
            self._cursor = 0
            self._set_value(self.user_input)
            return
