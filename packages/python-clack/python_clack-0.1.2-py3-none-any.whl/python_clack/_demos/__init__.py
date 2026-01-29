"""Demo registry for python-clack demos."""

from collections.abc import Callable
from typing import TypedDict

from .config_builder import run as config_builder
from .form_wizard import run as form_wizard
from .progress_demo import run as progress_demo
from .quick_tour import run as quick_tour
from .validation import run as validation_demo


class DemoEntry(TypedDict):
    """Registry entry for a demo."""

    label: str
    hint: str
    run: Callable[[], None]


DEMOS: dict[str, DemoEntry] = {
    "quick_tour": {
        "label": "Quick Tour",
        "hint": "overview of all prompts",
        "run": quick_tour,
    },
    "form_wizard": {
        "label": "Form Wizard",
        "hint": "multi-step form with data passing",
        "run": form_wizard,
    },
    "config_builder": {
        "label": "Configuration Builder",
        "hint": "settings with disabled options",
        "run": config_builder,
    },
    "progress": {
        "label": "Progress & Logging",
        "hint": "spinner states and log levels",
        "run": progress_demo,
    },
    "validation": {
        "label": "Validation Showcase",
        "hint": "input validation patterns",
        "run": validation_demo,
    },
}
