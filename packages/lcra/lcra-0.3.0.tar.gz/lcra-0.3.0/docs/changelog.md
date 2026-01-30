# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-25

### Changed

- Bumped minimum Python version from 3.10 to 3.12
- Migrated to PEP 735 `[dependency-groups]` for dev and docs dependencies (replacing optional-dependencies)
- CI test matrix: Python 3.12, 3.13, 3.14 on ubuntu-latest, macos-latest, and windows-latest
- Tests workflow uses `uv sync --group dev` and runs `ruff check` plus `ty check`

### Added

- Type checking with ty
- Markdown formatting with rumdl
- Ruff for linting and formatting
- Codecov coverage upload in CI
- Python 3.13 and 3.14 in package classifiers

## [0.2.1] - 2025-12-09

### Changed

- Migrated to `src/` layout for better package isolation and standard Python packaging practices
- Updated minimum Python version requirement from 3.9 to 3.10 (required by latest dependencies)
- CLI module moved from `main.py` to `src/lcra/cli.py`

### Added

- Support for `uv tool install lcra` for standalone CLI installation
- Changelog documentation

### Fixed

- Package now correctly includes all modules (`lcra`, `api`, `scraper`) when installed via `uv tool install`

## [0.2.0] - 2025-07-22

### Added

- Initial public release
- CLI tool with `get` and `serve` commands
- FastAPI-based REST API
- Data scraping from LCRA Hydromet APIs
- Pydantic models for type-safe data structures
- Support for lake levels, river conditions, and floodgate operations
- JSON output with save-to-file options
- Comprehensive test suite
- MkDocs documentation

[0.3.0]: https://github.com/lancereinsmith/lcra/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/lancereinsmith/lcra/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/lancereinsmith/lcra/releases/tag/v0.2.0
