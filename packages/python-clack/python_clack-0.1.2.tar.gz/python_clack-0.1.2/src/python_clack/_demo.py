"""Demo script for python-clack.

This module provides an interactive demo launcher for python-clack.

Run with:
    uv run python-clack-demo
"""

from python_clack import intro, is_cancel, outro, select

from ._demos import DEMOS


def main() -> None:
    """Run the interactive demo launcher."""
    intro("python-clack Demo Gallery")

    # Build options from demo registry
    options = [
        {"value": key, "label": f"{i}. {demo['label']}", "hint": demo["hint"]}
        for i, (key, demo) in enumerate(DEMOS.items(), 1)
    ]
    options.append({"value": "exit", "label": "Exit", "hint": "quit demo"})

    while True:
        choice_result = select(
            "Choose a demo to run",
            options=options,  # type: ignore[arg-type]
        )

        if is_cancel(choice_result):
            break
        choice = str(choice_result)

        if choice == "exit":
            break

        # Run selected demo
        demo_fn = DEMOS[choice]["run"]
        demo_fn()

        # Spacing before returning to menu
        print()

    outro("Thanks for exploring python-clack!")


if __name__ == "__main__":
    main()
