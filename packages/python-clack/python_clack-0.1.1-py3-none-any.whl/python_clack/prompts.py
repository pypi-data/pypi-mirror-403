"""High-level styled prompt functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TextIO, TypeVar

from ._core.prompt import Prompt
from ._core.state import State, _CancelType
from ._prompts.confirm import ConfirmPrompt
from ._prompts.multiselect import MultiSelectPrompt
from ._prompts.password import PasswordPrompt
from ._prompts.select import SelectOption, SelectPrompt
from ._prompts.text import TextPrompt
from .style import (
    color_cyan,
    color_dim,
    color_gray,
    color_strikethrough,
    color_yellow,
    symbol,
)
from .symbols import (
    S_BAR,
    S_BAR_END,
    S_CHECKBOX_ACTIVE,
    S_CHECKBOX_INACTIVE,
    S_CHECKBOX_SELECTED,
    S_RADIO_ACTIVE,
    S_RADIO_INACTIVE,
)

T = TypeVar("T")


def text(
    message: str,
    *,
    placeholder: str = "",
    default_value: str = "",
    initial_value: str = "",
    validate: Callable[[str | None], str | None] | None = None,
    _input: TextIO | None = None,
    _output: TextIO | None = None,
) -> str | _CancelType:
    """Prompt for text input.

    Args:
        message: The message to display.
        placeholder: Placeholder text shown when empty.
        default_value: Value used if user submits empty input.
        initial_value: Initial value to start with.
        validate: Optional validation function.
        _input: Input stream (for testing).
        _output: Output stream (for testing).

    Returns:
        The entered text, or CANCEL if cancelled.

    Example:
        >>> name = text("What is your name?", placeholder="Anonymous")
    """

    def render(p: Prompt[str]) -> str:
        prompt = p  # type: TextPrompt
        title = f"{symbol(prompt.state)}  {message}"

        # Placeholder display
        if not prompt.user_input and placeholder:
            placeholder_display = (
                f"[reverse]{placeholder[0]}[/reverse][dim]{placeholder[1:]}[/dim]"
                if len(placeholder) > 1
                else f"[reverse]{placeholder}[/reverse]"
            )
        else:
            placeholder_display = "[reverse] [/reverse]"

        user_display = prompt.user_input_with_cursor if prompt.user_input else placeholder_display

        match prompt.state:
            case State.ERROR:
                error_text = f"  {color_yellow(prompt.error)}" if prompt.error else ""
                return (
                    f"{color_gray(S_BAR)}\n"
                    f"{title}\n"
                    f"{color_yellow(S_BAR)}  {user_display}\n"
                    f"{color_yellow(S_BAR_END)}{error_text}\n"
                )
            case State.SUBMIT:
                value_text = f"  {color_dim(prompt.value or '')}"
                return f"{title}\n{color_gray(S_BAR)}{value_text}"
            case State.CANCEL:
                value = prompt.value or ""
                value_text = f"  {color_strikethrough(color_dim(value))}" if value else ""
                suffix = f"\n{color_gray(S_BAR)}" if value else ""
                return f"{title}\n{color_gray(S_BAR)}{value_text}{suffix}"
            case _:
                return (
                    f"{color_gray(S_BAR)}\n"
                    f"{title}\n"
                    f"{color_cyan(S_BAR)}  {user_display}\n"
                    f"{color_cyan(S_BAR_END)}\n"
                )

    prompt = TextPrompt(
        render=render,  # type: ignore
        validate=validate,
        placeholder=placeholder,
        default_value=default_value,
        initial_value=initial_value,
        input_stream=_input,
        output_stream=_output,
    )
    return prompt.prompt()


def confirm(
    message: str,
    *,
    active: str = "Yes",
    inactive: str = "No",
    initial_value: bool = False,
    _input: TextIO | None = None,
    _output: TextIO | None = None,
) -> bool | _CancelType:
    """Prompt for yes/no confirmation.

    Args:
        message: The message to display.
        active: Label for the "yes" option.
        inactive: Label for the "no" option.
        initial_value: Initial value (True for yes).
        _input: Input stream (for testing).
        _output: Output stream (for testing).

    Returns:
        True for yes, False for no, or CANCEL if cancelled.

    Example:
        >>> proceed = confirm("Continue?", initial_value=True)
    """

    def render(p: Prompt[bool]) -> str:
        prompt = p  # type: ConfirmPrompt
        title = f"{symbol(prompt.state)}  {message}"

        match prompt.state:
            case State.SUBMIT:
                result = active if prompt.value else inactive
                return f"{title}\n{color_gray(S_BAR)}  {color_dim(result)}"
            case State.CANCEL:
                return f"{title}\n{color_gray(S_BAR)}"
            case _:
                # Show toggle options
                if prompt.value:
                    yes_opt = f"{color_cyan('[reverse] ' + active + ' [/reverse]')}"
                    options = f"{yes_opt} / {color_dim(inactive)}"
                else:
                    no_opt = f"{color_cyan('[reverse] ' + inactive + ' [/reverse]')}"
                    options = f"{color_dim(active)} / {no_opt}"
                return (
                    f"{color_gray(S_BAR)}\n"
                    f"{title}\n"
                    f"{color_cyan(S_BAR)}  {options}\n"
                    f"{color_cyan(S_BAR_END)}\n"
                )

    prompt = ConfirmPrompt(
        render=render,  # type: ignore
        active_label=active,
        inactive_label=inactive,
        initial_value=initial_value,
        input_stream=_input,
        output_stream=_output,
    )
    return prompt.prompt()


def password(
    message: str,
    *,
    mask: str = "*",
    validate: Callable[[str | None], str | None] | None = None,
    _input: TextIO | None = None,
    _output: TextIO | None = None,
) -> str | _CancelType:
    """Prompt for password input.

    Args:
        message: The message to display.
        mask: Character to show instead of actual input.
        validate: Optional validation function.
        _input: Input stream (for testing).
        _output: Output stream (for testing).

    Returns:
        The entered password, or CANCEL if cancelled.

    Example:
        >>> secret = password("Enter API key")
    """

    def render(p: Prompt[str]) -> str:
        prompt = p  # type: PasswordPrompt
        title = f"{symbol(prompt.state)}  {message}"

        match prompt.state:
            case State.ERROR:
                error_text = f"  {color_yellow(prompt.error)}" if prompt.error else ""
                return (
                    f"{color_gray(S_BAR)}\n"
                    f"{title}\n"
                    f"{color_yellow(S_BAR)}  {prompt.masked_value_with_cursor}\n"
                    f"{color_yellow(S_BAR_END)}{error_text}\n"
                )
            case State.SUBMIT:
                return f"{title}\n{color_gray(S_BAR)}  {color_dim(prompt.masked_value)}"
            case State.CANCEL:
                masked = prompt.masked_value
                value_text = f"  {color_strikethrough(color_dim(masked))}" if masked else ""
                suffix = f"\n{color_gray(S_BAR)}" if masked else ""
                return f"{title}\n{color_gray(S_BAR)}{value_text}{suffix}"
            case _:
                if prompt.user_input:
                    display = prompt.masked_value_with_cursor
                else:
                    display = "[reverse] [/reverse]"
                return (
                    f"{color_gray(S_BAR)}\n"
                    f"{title}\n"
                    f"{color_cyan(S_BAR)}  {display}\n"
                    f"{color_cyan(S_BAR_END)}\n"
                )

    prompt = PasswordPrompt(
        render=render,  # type: ignore
        validate=validate,
        mask=mask,
        input_stream=_input,
        output_stream=_output,
    )
    return prompt.prompt()


def select(
    message: str,
    *,
    options: list[SelectOption],
    initial_value: T | None = None,
    _input: TextIO | None = None,
    _output: TextIO | None = None,
) -> T | _CancelType:
    """Prompt for single selection.

    Args:
        message: The message to display.
        options: List of options to select from.
        initial_value: Initially selected value.
        _input: Input stream (for testing).
        _output: Output stream (for testing).

    Returns:
        The selected value, or CANCEL if cancelled.

    Example:
        >>> color = select(
        ...     "Pick a color",
        ...     options=[
        ...         {"value": "red", "label": "Red"},
        ...         {"value": "blue", "label": "Blue"},
        ...     ]
        ... )
    """

    def render(p: Prompt[T]) -> str:
        prompt = p  # type: SelectPrompt[T]
        title = f"{symbol(prompt.state)}  {message}"

        match prompt.state:
            case State.SUBMIT:
                # Find selected option label
                selected_opt = options[prompt.cursor_index]
                label = selected_opt.get("label", str(selected_opt.get("value", "")))
                return f"{title}\n{color_gray(S_BAR)}  {color_dim(label)}"
            case State.CANCEL:
                return f"{title}\n{color_gray(S_BAR)}"
            case _:
                lines = [f"{color_gray(S_BAR)}", title]

                for i, opt in enumerate(options):
                    label = opt.get("label", str(opt.get("value", "")))
                    hint = opt.get("hint", "")
                    disabled = opt.get("disabled", False)
                    is_active = i == prompt.cursor_index

                    if disabled:
                        radio = color_dim(S_RADIO_INACTIVE)
                        text = color_dim(f"{label} (disabled)")
                    elif is_active:
                        radio = color_cyan(S_RADIO_ACTIVE)
                        text = label
                        if hint:
                            text += f" {color_dim(hint)}"
                    else:
                        radio = color_dim(S_RADIO_INACTIVE)
                        text = color_dim(label)

                    bar = color_cyan(S_BAR) if not disabled else color_gray(S_BAR)
                    lines.append(f"{bar}  {radio} {text}")

                lines.append(color_cyan(S_BAR_END))
                lines.append("")
                return "\n".join(lines)

    prompt: SelectPrompt[T] = SelectPrompt(
        render=render,  # type: ignore
        options=options,
        initial_value=initial_value,
        input_stream=_input,
        output_stream=_output,
    )
    return prompt.prompt()


def multiselect(
    message: str,
    *,
    options: list[SelectOption],
    initial_values: list[T] | None = None,
    required: bool = False,
    _input: TextIO | None = None,
    _output: TextIO | None = None,
) -> list[T] | _CancelType:
    """Prompt for multiple selection.

    Args:
        message: The message to display.
        options: List of options to select from.
        initial_values: Initially selected values.
        required: If True, at least one option must be selected.
        _input: Input stream (for testing).
        _output: Output stream (for testing).

    Returns:
        List of selected values, or CANCEL if cancelled.

    Example:
        >>> features = multiselect(
        ...     "Select features",
        ...     options=[
        ...         {"value": "ts", "label": "TypeScript"},
        ...         {"value": "eslint", "label": "ESLint"},
        ...     ],
        ...     required=True
        ... )
    """

    def render(p: Prompt[list[T]]) -> str:
        prompt = p  # type: MultiSelectPrompt[T]
        title = f"{symbol(prompt.state)}  {message}"

        match prompt.state:
            case State.ERROR:
                lines = [f"{color_gray(S_BAR)}", title]

                for i, opt in enumerate(options):
                    label = opt.get("label", str(opt.get("value", "")))
                    disabled = opt.get("disabled", False)
                    is_active = i == prompt.cursor_index
                    is_selected = prompt.is_selected(i)

                    if disabled:
                        checkbox = color_dim(S_CHECKBOX_INACTIVE)
                        text = color_dim(f"{label} (disabled)")
                    elif is_selected:
                        checkbox = color_yellow(S_CHECKBOX_SELECTED)
                        text = label if is_active else color_dim(label)
                    elif is_active:
                        checkbox = color_yellow(S_CHECKBOX_ACTIVE)
                        text = label
                    else:
                        checkbox = color_dim(S_CHECKBOX_INACTIVE)
                        text = color_dim(label)

                    lines.append(f"{color_yellow(S_BAR)}  {checkbox} {text}")

                error_text = f"  {color_yellow(prompt.error)}" if prompt.error else ""
                lines.append(f"{color_yellow(S_BAR_END)}{error_text}")
                lines.append("")
                return "\n".join(lines)

            case State.SUBMIT:
                # Show selected labels
                selected_labels = []
                for i in sorted(prompt.selected_indices):
                    opt = options[i]
                    selected_labels.append(opt.get("label", str(opt.get("value", ""))))
                labels_text = ", ".join(selected_labels) if selected_labels else "(none)"
                return f"{title}\n{color_gray(S_BAR)}  {color_dim(labels_text)}"

            case State.CANCEL:
                return f"{title}\n{color_gray(S_BAR)}"

            case _:
                lines = [f"{color_gray(S_BAR)}", title]

                for i, opt in enumerate(options):
                    label = opt.get("label", str(opt.get("value", "")))
                    hint = opt.get("hint", "")
                    disabled = opt.get("disabled", False)
                    is_active = i == prompt.cursor_index
                    is_selected = prompt.is_selected(i)

                    if disabled:
                        checkbox = color_dim(S_CHECKBOX_INACTIVE)
                        text = color_dim(f"{label} (disabled)")
                    elif is_selected:
                        checkbox = color_cyan(S_CHECKBOX_SELECTED)
                        text = label if is_active else color_dim(label)
                        if hint and is_active:
                            text += f" {color_dim(hint)}"
                    elif is_active:
                        checkbox = color_cyan(S_CHECKBOX_ACTIVE)
                        text = label
                        if hint:
                            text += f" {color_dim(hint)}"
                    else:
                        checkbox = color_dim(S_CHECKBOX_INACTIVE)
                        text = color_dim(label)

                    lines.append(f"{color_cyan(S_BAR)}  {checkbox} {text}")

                lines.append(color_cyan(S_BAR_END))
                lines.append("")
                return "\n".join(lines)

    prompt: MultiSelectPrompt[T] = MultiSelectPrompt(
        render=render,  # type: ignore
        options=options,
        initial_values=initial_values,
        required=required,
        input_stream=_input,
        output_stream=_output,
    )
    return prompt.prompt()
