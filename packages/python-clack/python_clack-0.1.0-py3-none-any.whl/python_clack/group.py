"""Group function for running prompts sequentially."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from ._core.state import CANCEL, is_cancel

T = TypeVar("T")


def group(
    prompts: dict[str, Callable[[dict[str, Any]], Any]],
    *,
    on_cancel: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run multiple prompts sequentially with shared context.

    Each prompt function receives the results of previous prompts,
    allowing you to make decisions based on earlier answers.

    Args:
        prompts: Dictionary mapping keys to prompt functions.
                 Each function receives the results dict so far.
        on_cancel: Optional callback when a prompt is cancelled.
                   Receives the results collected so far.

    Returns:
        Dictionary of all prompt results keyed by their names.
        If cancelled, returns partial results up to cancellation.

    Example:
        >>> results = group({
        ...     "name": lambda _: text("What is your name?"),
        ...     "email": lambda _: text("What is your email?"),
        ...     "confirm": lambda r: confirm(f"Create user {r['name']}?"),
        ... })
    """
    results: dict[str, Any] = {}

    for key, prompt_fn in prompts.items():
        try:
            result = prompt_fn(results)
        except KeyboardInterrupt:
            # Handle Ctrl+C outside of prompt
            if on_cancel:
                on_cancel(results)
            results[key] = CANCEL
            break

        if is_cancel(result):
            if on_cancel:
                on_cancel(results)
            results[key] = CANCEL
            break

        results[key] = result

    return results
