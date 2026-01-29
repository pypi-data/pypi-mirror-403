"""Validation Showcase - Input validation patterns."""

import re

from python_clack import (
    cancel,
    intro,
    is_cancel,
    log,
    multiselect,
    outro,
    password,
    text,
)


def run() -> None:
    """Run the validation showcase demo."""
    intro("Validation Showcase")

    log.info("Try submitting invalid input to see validation")

    # Required field - simple presence check
    name = text(
        "Enter your name (required)",
        validate=lambda v: "Name is required" if not v else None,
    )
    if is_cancel(name):
        cancel()
        return

    # Length validation
    username = text(
        "Username (3-20 characters)",
        validate=lambda v: (
            "Username is required"
            if not v
            else "Too short (min 3)"
            if len(v) < 3
            else "Too long (max 20)"
            if len(v) > 20
            else None
        ),
    )
    if is_cancel(username):
        cancel()
        return

    # Format validation - alphanumeric only
    slug = text(
        "Project slug (letters, numbers, hyphens)",
        placeholder="my-project-123",
        validate=lambda v: (
            "Slug is required"
            if not v
            else "Only letters, numbers, and hyphens allowed"
            if not re.match(r"^[a-zA-Z0-9-]+$", v)
            else "Cannot start with hyphen"
            if v.startswith("-")
            else "Cannot end with hyphen"
            if v.endswith("-")
            else None
        ),
    )
    if is_cancel(slug):
        cancel()
        return

    # Email validation
    email = text(
        "Email address",
        placeholder="you@example.com",
        validate=lambda v: (
            "Email is required"
            if not v
            else "Invalid email format"
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v)
            else None
        ),
    )
    if is_cancel(email):
        cancel()
        return

    # Numeric validation
    age = text(
        "Age (18-120)",
        validate=lambda v: (
            "Age is required"
            if not v
            else "Must be a number"
            if not v.isdigit()
            else "Must be 18 or older"
            if int(v) < 18
            else "Please enter a valid age"
            if int(v) > 120
            else None
        ),
    )
    if is_cancel(age):
        cancel()
        return

    # Password with strength requirements
    pwd = password(
        "Password (8+ chars, letter + number)",
        validate=lambda v: (
            "Password is required"
            if not v
            else "At least 8 characters"
            if len(v) < 8
            else "Must contain a letter"
            if not re.search(r"[a-zA-Z]", v)
            else "Must contain a number"
            if not re.search(r"[0-9]", v)
            else None
        ),
    )
    if is_cancel(pwd):
        cancel()
        return

    # multiselect with required
    skills: list[str] = multiselect(  # type: ignore[assignment]
        "Select at least one skill",
        options=[
            {"value": "python", "label": "Python"},
            {"value": "javascript", "label": "JavaScript"},
            {"value": "rust", "label": "Rust"},
            {"value": "go", "label": "Go"},
        ],
        required=True,  # Built-in "at least one" validation
    )
    if is_cancel(skills):
        cancel()
        return

    # Success!
    log.success("All validation passed!")
    log.info(f"Name: {name}")
    log.info(f"Username: {username}")
    log.info(f"Slug: {slug}")
    log.info(f"Email: {email}")
    log.info(f"Age: {age}")
    log.step(f"Skills: {', '.join(skills)}")

    outro("Validation demo complete!")
