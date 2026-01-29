"""Base Prompt class for all interactive prompts."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TextIO, TypeVar

from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from .render import Renderer
from .state import CANCEL, State, _CancelType

T = TypeVar("T")


class Prompt(ABC, Generic[T]):
    """Base class for all prompts.

    This implements the core state machine and rendering loop that all
    prompts inherit from.
    """

    def __init__(
        self,
        *,
        render: Callable[[Prompt[T]], str],
        validate: Callable[[T | None], str | None] | None = None,
        initial_value: T | None = None,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the prompt.

        Args:
            render: Function that returns the prompt display string.
            validate: Optional validation function.
            initial_value: Initial value for the prompt.
            input_stream: Input stream (defaults to stdin).
            output_stream: Output stream (defaults to stdout).
        """
        self._render_fn = render
        self._validate = validate
        self._input_stream = input_stream or sys.stdin
        self._output_stream = output_stream or sys.stdout
        self._renderer = Renderer(self._output_stream)
        self._input = create_input(self._input_stream)

        # State
        self.state = State.INITIAL
        self.value: T | None = initial_value
        self.error: str = ""
        self._cursor: int = 0
        self._prev_frame: str = ""
        self._prev_frame_lines: int = 0

        # Event subscribers
        self._subscribers: dict[str, list[tuple[Callable[..., Any], bool]]] = {}

    @property
    def cursor(self) -> int:
        """Current cursor position."""
        return self._cursor

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Subscribe to an event.

        Args:
            event: Event name (e.g., 'submit', 'cancel', 'key').
            callback: Function to call when event is emitted.
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append((callback, False))

    def once(self, event: str, callback: Callable[..., Any]) -> None:
        """Subscribe to an event once.

        Args:
            event: Event name.
            callback: Function to call when event is emitted.
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append((callback, True))

    def emit(self, event: str, *args: Any) -> None:
        """Emit an event.

        Args:
            event: Event name.
            *args: Arguments to pass to callbacks.
        """
        if event not in self._subscribers:
            return
        to_remove: list[tuple[Callable[..., Any], bool]] = []
        for callback, once in self._subscribers[event]:
            callback(*args)
            if once:
                to_remove.append((callback, once))
        for item in to_remove:
            self._subscribers[event].remove(item)

    def _clear_subscribers(self) -> None:
        """Clear all event subscribers."""
        self._subscribers.clear()

    def _set_value(self, value: T | None) -> None:
        """Set the value and emit event."""
        self.value = value
        self.emit("value", value)

    def render(self) -> None:
        """Render the current frame."""
        frame = self._render_fn(self)

        # Skip if frame hasn't changed
        if frame == self._prev_frame:
            return

        if self.state == State.INITIAL:
            # First render - hide cursor
            self._renderer.hide_cursor()
        else:
            # Subsequent renders - clear previous frame
            self._renderer.clear_previous_frame(self._prev_frame_lines)

        # Write new frame
        self._renderer.write(frame)
        self._prev_frame = frame
        self._prev_frame_lines = frame.count("\n")

        # Transition from initial to active
        if self.state == State.INITIAL:
            self.state = State.ACTIVE

    def _handle_submit(self) -> None:
        """Handle submit (Enter key)."""
        if self._validate:
            error = self._validate(self.value)
            if error:
                self.error = error
                self.state = State.ERROR
                return

        self.state = State.SUBMIT

    def _handle_cancel(self) -> None:
        """Handle cancel (Ctrl+C or Escape)."""
        self.state = State.CANCEL

    def _finalize(self) -> None:
        """Finalize the prompt (on submit or cancel)."""
        self.emit("finalize")
        self.render()
        self._close()

    def _close(self) -> None:
        """Clean up and close the prompt."""
        self._renderer.show_cursor()
        self._renderer.newline()
        self.emit(self.state.name.lower(), self.value)
        self._clear_subscribers()

    @abstractmethod
    def _on_key(self, key_press: KeyPress) -> None:
        """Handle a key press.

        Subclasses must implement this to handle key presses specific
        to their prompt type.

        Args:
            key_press: The key press event from prompt_toolkit.
        """
        pass

    def _is_submit_key(self, key_press: KeyPress) -> bool:
        """Check if key is the submit key (Enter)."""
        return key_press.key == Keys.Enter or key_press.key == Keys.ControlM

    def _is_cancel_key(self, key_press: KeyPress) -> bool:
        """Check if key is a cancel key (Ctrl+C or Escape)."""
        return key_press.key in (Keys.ControlC, Keys.Escape)

    def prompt(self) -> T | _CancelType:
        """Run the prompt and return the result.

        Returns:
            The prompt value if submitted, or CANCEL if cancelled.
        """
        result: T | _CancelType = CANCEL

        def on_submit(value: T | None) -> None:
            nonlocal result
            if value is not None:
                result = value

        def on_cancel(_: Any) -> None:
            pass  # result stays as CANCEL

        self.once("submit", on_submit)
        self.once("cancel", on_cancel)

        self._run_input_loop()

        return result

    def _run_input_loop(self) -> None:
        """Run the input loop."""
        # Initial render
        self.render()

        try:
            with self._input.raw_mode():
                while self.state not in (State.SUBMIT, State.CANCEL):
                    for key_press in self._input.read_keys():
                        # Clear error state on any key
                        if self.state == State.ERROR:
                            self.state = State.ACTIVE

                        # Emit key event
                        self.emit("key", key_press)

                        # Handle submit
                        if self._is_submit_key(key_press):
                            self._handle_submit()
                            if self.state in (State.SUBMIT, State.CANCEL):
                                break
                            self.render()
                            continue

                        # Handle cancel
                        if self._is_cancel_key(key_press):
                            self._handle_cancel()
                            break

                        # Let subclass handle the key
                        self._on_key(key_press)

                        # Re-render
                        self.render()

        finally:
            # Always finalize
            self._finalize()
