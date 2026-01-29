# Plan: Add interactive demo menu system

**Status:** Completed
**Date:** 2026-01-25

## Goal

Transform `python-clack-demo` from a single fixed demo into an interactive menu where users can choose different demos to explore. Each demo showcases different features and use cases of the library.

## Summary of Changes

- Added interactive demo menu using `select()` to choose demos
- Created 5 focused demo modules covering different use cases:
  - Quick Tour: Overview of all prompt types
  - Form Wizard: Multi-step form using `group()` with validation
  - Configuration Builder: Settings with disabled options
  - Progress & Logging: Spinner states and all log levels
  - Validation Showcase: Input validation patterns
- Switched from mypy to pyright for type checking
- Fixed type errors in prompts.py using `cast()`
- Updated CI workflow to use pyright
- Added tool cache documentation to dev notes

## Files Modified

- [_demo.py](src/python_clack/_demo.py) - Replaced fixed demo with menu launcher
- [_demos/__init__.py](src/python_clack/_demos/__init__.py) - Created demo registry
- [_demos/quick_tour.py](src/python_clack/_demos/quick_tour.py) - Created
- [_demos/form_wizard.py](src/python_clack/_demos/form_wizard.py) - Created
- [_demos/config_builder.py](src/python_clack/_demos/config_builder.py) - Created
- [_demos/progress_demo.py](src/python_clack/_demos/progress_demo.py) - Created
- [_demos/validation.py](src/python_clack/_demos/validation.py) - Created
- [prompts.py](src/python_clack/prompts.py) - Fixed type errors with cast()
- [pyproject.toml](pyproject.toml) - Switched mypy to pyright
- [publish.yml](.github/workflows/publish.yml) - Added pyright step
- [2026-01-25.md](.dev-notes/2026-01-25.md) - Added tool cache documentation

## Breaking Changes

None

## Deprecations

- mypy configuration removed in favor of pyright
