"""Unicode symbols with ASCII fallbacks."""

import os
import sys


def _is_unicode_supported() -> bool:
    """Check if the terminal supports Unicode.

    Returns True only if we're confident Unicode will work.
    """
    # Allow forcing via environment variable
    force = os.environ.get("PYTHON_CLACK_UNICODE")
    if force is not None:
        return force.lower() in ("1", "true", "yes")

    # Check stdout encoding - this is the most reliable indicator
    encoding = getattr(sys.stdout, "encoding", None) or ""
    encoding_lower = encoding.lower()

    # If encoding explicitly supports UTF-8, we're good
    if encoding_lower in ("utf-8", "utf8"):
        return True

    # On Windows, be conservative - only trust UTF-8 encoding
    # The terminal might have LANG set but not actually support Unicode output
    if sys.platform == "win32":
        # Windows Terminal (new) supports Unicode via WT_SESSION
        if os.environ.get("WT_SESSION"):
            return True

        # VSCode integrated terminal supports Unicode
        if os.environ.get("TERM_PROGRAM") == "vscode":
            return True

        # Code page 65001 is UTF-8 on Windows
        if "65001" in encoding:
            return True

        # Default to ASCII on Windows for compatibility
        return False

    # Non-Windows platforms: check common indicators
    if os.environ.get("TERM_PROGRAM") in ("iTerm.app", "Apple_Terminal", "Hyper"):
        return True

    # Check LANG for UTF-8 (reliable on non-Windows)
    if "UTF-8" in os.environ.get("LANG", "").upper():
        return True

    # Default to Unicode on non-Windows (most modern terminals support it)
    return True


UNICODE = _is_unicode_supported()


def _u(unicode_char: str, fallback: str) -> str:
    """Return Unicode character or ASCII fallback."""
    return unicode_char if UNICODE else fallback


# Step indicators (used with prompt states)
S_STEP_ACTIVE = _u("◆", "*")
S_STEP_CANCEL = _u("■", "x")
S_STEP_ERROR = _u("▲", "x")
S_STEP_SUBMIT = _u("◇", "o")

# Bar characters (for visual structure)
S_BAR_START = _u("┌", "T")
S_BAR = _u("│", "|")
S_BAR_END = _u("└", "-")
S_BAR_H = _u("─", "-")

# Radio buttons (for select prompts)
S_RADIO_ACTIVE = _u("●", ">")
S_RADIO_INACTIVE = _u("○", " ")

# Checkboxes (for multiselect prompts)
S_CHECKBOX_ACTIVE = _u("◻", "[*]")
S_CHECKBOX_SELECTED = _u("◼", "[+]")
S_CHECKBOX_INACTIVE = _u("◻", "[ ]")

# Password mask
S_PASSWORD_MASK = _u("▪", "*")

# Log symbols
S_INFO = _u("●", "*")
S_SUCCESS = _u("◆", "*")
S_WARN = _u("▲", "!")
S_ERROR = _u("■", "x")

# Box corners (for note/box display)
S_CORNER_TOP_LEFT = _u("╭", "+")
S_CORNER_TOP_RIGHT = _u("╮", "+")
S_CORNER_BOTTOM_LEFT = _u("╰", "+")
S_CORNER_BOTTOM_RIGHT = _u("╯", "+")
S_CONNECT_LEFT = _u("├", "+")
