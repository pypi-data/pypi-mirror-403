# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-24

### Added

- Dependabot configuration for automatic dependency updates (pip and GitHub Actions)
- Auto-merge workflow for Dependabot PRs (minor and patch versions)
- CLI entry point `python-clack-demo` for quick testing after install
- Examples directory with `basic.py` and `group.py` demos

### Changed

- Moved demo from `main.py` to `examples/` directory (follows Python package conventions)
- Updated README with "Try It Out" section

## [0.1.0] - 2025-01-24

### Added

- Initial release of python-clack
- Text input prompt with placeholder, validation, and default values
- Select prompt for single selection with arrow key navigation
- Multiselect prompt with space toggle and select all/invert
- Confirm prompt for yes/no with y/n keyboard shortcuts
- Password prompt with masked input
- Spinner with animated loading indicator
- Log utilities (info, success, warn, error, step)
- Intro/outro/cancel message banners
- Group function for sequential prompt execution
- Automatic Unicode/ASCII fallback based on terminal capabilities
- Cross-platform support via prompt_toolkit and rich
