# Plan: Add Dependabot, examples structure, dev testing

**Status:** Completed
**Date:** 2026-01-24

## Goal

Add CI/CD automation with Dependabot for dependency updates, restructure examples to follow Python package conventions, and add developer testing infrastructure.

## Summary of Changes

- Added Dependabot configuration for Python pip ecosystem and GitHub Actions
- Added auto-merge workflow for Dependabot PRs (minor/patch versions)
- Restructured examples from root `main.py` to `examples/` directory
- Added CLI entry point `python-clack-demo` for quick testing
- Created internal `_demo.py` module for CLI support
- Updated README with "Try It Out" section
- Documented Python package example patterns in dev notes

## Files Modified

- [.github/dependabot.yml](.github/dependabot.yml) - Dependabot config for pip and github-actions
- [.github/workflows/dependabot-auto-merge.yml](.github/workflows/dependabot-auto-merge.yml) - Auto-merge workflow for Dependabot PRs
- [pyproject.toml](pyproject.toml) - Added CLI entry point for demo
- [src/python_clack/_demo.py](src/python_clack/_demo.py) - Demo module for CLI entry point
- [examples/basic.py](examples/basic.py) - Full demo with all prompts
- [examples/group.py](examples/group.py) - Group function example
- [README.md](README.md) - Added "Try It Out" section
- [.dev-notes/2026-01-24.md](.dev-notes/2026-01-24.md) - Documented example patterns

## Files Removed

- `main.py` - Replaced by `examples/basic.py`

## Breaking Changes

None

## Deprecations

None
