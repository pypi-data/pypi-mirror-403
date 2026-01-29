"""Form Wizard - Multi-step form with group()."""

import re

from python_clack import (
    cancel,
    confirm,
    group,
    intro,
    is_cancel,
    log,
    outro,
    password,
    text,
)


def validate_email(value: str | None) -> str | None:
    """Validate email format."""
    if not value:
        return "Email is required"
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
        return "Please enter a valid email"
    return None


def validate_username(value: str | None) -> str | None:
    """Validate username."""
    if not value:
        return "Username is required"
    if len(value) < 3:
        return "Username must be at least 3 characters"
    if not value.isalnum():
        return "Username must be alphanumeric"
    return None


def validate_password(value: str | None) -> str | None:
    """Validate password strength."""
    if not value:
        return "Password is required"
    if len(value) < 8:
        return "Password must be at least 8 characters"
    return None


def run() -> None:
    """Run the form wizard demo."""
    intro("User Registration Wizard")

    log.info("This demo shows group() for multi-step forms")

    results = group(
        {
            "username": lambda _: text(
                "Choose a username",
                placeholder="e.g., johndoe",
                validate=validate_username,
            ),
            "email": lambda _: text(
                "Enter your email",
                placeholder="you@example.com",
                validate=validate_email,
            ),
            "password": lambda _: password(
                "Create a password",
                validate=validate_password,
            ),
            "confirm_password": lambda r: password(
                f"Confirm password for {r['username']}",
                validate=lambda v: (
                    "Passwords don't match" if v != r.get("password") else None
                ),
            ),
            "newsletter": lambda r: confirm(
                f"Subscribe {r['email']} to newsletter?",
                initial_value=False,
            ),
            "final_confirm": lambda r: confirm(
                f"Create account for {r['username']}?",
                initial_value=True,
            ),
        },
        on_cancel=lambda _: cancel("Registration cancelled"),
    )

    # Check if completed
    if is_cancel(results.get("final_confirm")):
        return

    if not results.get("final_confirm"):
        cancel("Registration declined")
        return

    # Success summary
    log.success(f"Account created: {results['username']}")
    log.info(f"Email: {results['email']}")
    if results.get("newsletter"):
        log.step("Newsletter: subscribed")

    outro("Registration complete!")
