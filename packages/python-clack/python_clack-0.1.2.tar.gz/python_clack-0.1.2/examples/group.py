"""Example demonstrating the group function for sequential prompts.

Run with: uv run python examples/group.py
"""

from python_clack import cancel, confirm, group, intro, is_cancel, log, outro, text


def main() -> None:
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
