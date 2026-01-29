# python-clack

Beautiful CLI prompts for Python, inspired by [clack](https://github.com/bombshell-dev/clack).

## Installation

```bash
pip install python-clack
```

Or with uv:

```bash
uv add python-clack
```

## Features

- **Text input** - Free-form text with placeholder, validation, and default values
- **Select** - Single selection from a list of options
- **Multi-select** - Multiple selection with checkboxes
- **Confirm** - Yes/No confirmation prompts
- **Password** - Masked password input
- **Spinner** - Animated loading indicator
- **Log utilities** - Styled info/success/warn/error messages
- **Messages** - Intro/outro banners

## Quick Start

```python
from python_clack import intro, text, select, confirm, outro, is_cancel

intro("Welcome to my app")

name = text(
    "What is your name?",
    placeholder="Anonymous",
    validate=lambda v: "Name is required" if not v else None
)

if is_cancel(name):
    outro("Cancelled!")
    exit(1)

color = select(
    "Pick your favorite color",
    options=[
        {"value": "red", "label": "Red", "hint": "warm"},
        {"value": "green", "label": "Green"},
        {"value": "blue", "label": "Blue", "hint": "cool"},
    ]
)

confirmed = confirm("Continue?", initial_value=True)

outro("All done!")
```

## API Reference

### Prompts

#### `text(message, **options) -> str | CANCEL`

Text input prompt.

Options:
- `placeholder` - Placeholder text when empty
- `default_value` - Value if user submits empty
- `initial_value` - Starting value
- `validate` - Validation function `(value) -> error_message | None`

#### `select(message, options, **kwargs) -> T | CANCEL`

Single selection prompt.

Options:
- `options` - List of `{"value": T, "label": str, "hint": str, "disabled": bool}`
- `initial_value` - Initially selected value

#### `multiselect(message, options, **kwargs) -> list[T] | CANCEL`

Multiple selection prompt.

Options:
- `options` - List of option dicts
- `initial_values` - Initially selected values
- `required` - Require at least one selection

#### `confirm(message, **options) -> bool | CANCEL`

Yes/No confirmation prompt.

Options:
- `active` - Label for "yes" (default: "Yes")
- `inactive` - Label for "no" (default: "No")
- `initial_value` - Initial selection (default: False)

#### `password(message, **options) -> str | CANCEL`

Password input with masked characters.

Options:
- `mask` - Character to show (default: "*")
- `validate` - Validation function

### Utilities

#### `is_cancel(value) -> bool`

Check if a prompt was cancelled.

```python
result = text("Name?")
if is_cancel(result):
    print("User cancelled")
```

#### `intro(title)`

Display an intro banner.

#### `outro(message)`

Display an outro message.

#### `cancel(message)`

Display a cancellation message.

#### `log`

Log utilities with styled output.

```python
from python_clack import log

log.info("Processing...")
log.success("Done!")
log.warn("Deprecation warning")
log.error("Something failed")
log.step("Step completed")
```

#### `spinner()`

Animated spinner for loading states.

```python
from python_clack import spinner
import time

s = spinner()
s.start("Loading...")
time.sleep(2)
s.stop("Done!")

# Or with error/warn/cancel
s.error("Failed!")
s.warn("Warning!")
s.cancel("Cancelled!")
```

#### `group(prompts, on_cancel=None)`

Run multiple prompts sequentially.

```python
from python_clack import group, text, confirm

results = group({
    "name": lambda _: text("Name?"),
    "email": lambda _: text("Email?"),
    "confirm": lambda r: confirm(f"Create {r['name']}?"),
})
```

## Unicode Support

python-clack automatically detects terminal Unicode support:
- Uses Unicode symbols on modern terminals (Windows Terminal, VSCode, iTerm, etc.)
- Falls back to ASCII on legacy terminals

Force a specific mode with environment variable:

```bash
# Force Unicode
PYTHON_CLACK_UNICODE=1 python app.py

# Force ASCII
PYTHON_CLACK_UNICODE=0 python app.py
```

## License

MIT
