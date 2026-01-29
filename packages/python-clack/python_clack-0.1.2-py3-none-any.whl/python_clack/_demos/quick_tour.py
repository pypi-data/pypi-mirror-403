"""Quick Tour - Overview of all python-clack prompts."""

from python_clack import (
    cancel,
    confirm,
    intro,
    is_cancel,
    log,
    multiselect,
    outro,
    password,
    select,
    text,
)


def run() -> None:
    """Run the quick tour demo."""
    intro("Quick Tour - All Prompts Overview")

    # text() - basic input
    name = text("What's your name?", placeholder="Enter your name")
    if is_cancel(name):
        cancel()
        return

    # select() - single choice with hints
    theme = select(
        "Pick a theme",
        options=[
            {"value": "light", "label": "Light", "hint": "bright colors"},
            {"value": "dark", "label": "Dark", "hint": "easy on eyes"},
            {"value": "system", "label": "System", "hint": "match OS"},
        ],
    )
    if is_cancel(theme):
        cancel()
        return

    # multiselect() - multiple choices
    interests: list[str] = multiselect(  # type: ignore[assignment]
        "Select your interests",
        options=[
            {"value": "cli", "label": "CLI tools"},
            {"value": "web", "label": "Web development"},
            {"value": "data", "label": "Data science"},
            {"value": "devops", "label": "DevOps"},
        ],
        required=True,
    )
    if is_cancel(interests):
        cancel()
        return

    # password() - masked input
    token = password("API token (optional)")
    if is_cancel(token):
        cancel()
        return

    # confirm() - yes/no
    proceed = confirm(f"All set, {name}?", initial_value=True)
    if is_cancel(proceed) or not proceed:
        cancel("Tour cancelled")
        return

    # Summary with logging
    log.success(f"Welcome, {name}!")
    log.info(f"Theme: {theme}")
    log.step(f"Interests: {', '.join(interests)}")

    outro("Tour complete!")
