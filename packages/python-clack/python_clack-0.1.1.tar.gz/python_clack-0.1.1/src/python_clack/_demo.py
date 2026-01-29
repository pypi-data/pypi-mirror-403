"""Demo script for python-clack.

This module provides example usage of all python-clack prompts.

Run with:
    uv run python-clack-demo
    # or
    uv run python main.py
"""

import time

from python_clack import (
    cancel,
    confirm,
    group,
    intro,
    is_cancel,
    log,
    multiselect,
    outro,
    password,
    select,
    spinner,
    text,
)


def main() -> None:
    """Run the interactive demo."""
    intro("Welcome to python-clack!")

    # Text input
    name = text(
        "What is your name?",
        placeholder="Anonymous",
    )
    if is_cancel(name):
        cancel()
        return

    # Select
    color = select(
        "Pick your favorite color",
        options=[
            {"value": "red", "label": "Red", "hint": "warm"},
            {"value": "green", "label": "Green", "hint": "nature"},
            {"value": "blue", "label": "Blue", "hint": "cool"},
        ],
    )
    if is_cancel(color):
        cancel()
        return

    # Multi-select
    features = multiselect(
        "Select features to enable",
        options=[
            {"value": "typescript", "label": "TypeScript"},
            {"value": "eslint", "label": "ESLint"},
            {"value": "prettier", "label": "Prettier"},
            {"value": "tests", "label": "Unit Tests"},
        ],
        required=True,
    )
    if is_cancel(features):
        cancel()
        return

    # Password
    secret = password(
        "Enter your API key",
        validate=lambda v: "API key is required" if not v else None,
    )
    if is_cancel(secret):
        cancel()
        return

    # Confirm
    proceed = confirm(
        f"Create project for {name}?",
        initial_value=True,
    )
    if is_cancel(proceed):
        cancel()
        return

    if not proceed:
        cancel("User declined")
        return

    # Spinner
    s = spinner()
    s.start("Setting up project...")
    time.sleep(1.5)
    s.stop("Project created!")

    # Log messages
    log.info(f"User: {name}")
    log.success(f"Color: {color}")
    log.step(f"Features: {', '.join(features)}")  # type: ignore

    outro("All done! Thanks for trying python-clack.")


def demo_group() -> None:
    """Demo the group function."""
    intro("Group demo")

    results = group(
        {
            "name": lambda _: text("What is your name?"),
            "age": lambda _: text("What is your age?"),
            "confirm": lambda r: confirm(f"Is your name {r.get('name', '?')}?"),
        },
        on_cancel=lambda _: cancel(),
    )

    if not is_cancel(results.get("confirm")):
        log.success(f"Collected: {results}")

    outro("Group demo complete!")


if __name__ == "__main__":
    main()
