# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called `ai-sidekick` managed with [uv](https://github.com/astral-sh/uv) as the package manager. Python 3.13 is required (see `.python-version` and `pyproject.toml`).

## Development Commands

### Installation
```bash
uv sync --locked --all-extras --dev
```

### Running the Application
```bash
uv run python src/main.py
# Or simply:
uv run python -m ai-sidekick
```

### Testing
```bash
# Run all tests
uv run pytest tests

# Run a single test file
uv run pytest tests/smoke_test.py

# Run a specific test
uv run pytest tests/smoke_test.py::test_function_name
```

### Building
```bash
# Build distribution packages
uv build
```

### Publishing
The project uses OIDC for PyPI publishing. Build artifacts are tested before publishing:
```bash
# Smoke test a wheel
uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py

# Smoke test a source distribution
uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py

# Publish to PyPI
uv publish
```

## Release Process

This project uses [release-please](https://github.com/googleapis/release-please-action) for automated releases:

1. **Conventional Commits**: All commits must follow conventional commit format (feat:, fix:, docs:, etc.)
2. **PR Validation**: The `convetional-commit.yml` workflow validates PR titles
3. **Auto-release**: When commits are pushed to `main`, release-please creates/releases versions and updates CHANGELOG.md
4. **Publishing**: Tags matching `ai-sidekick-v*` trigger PyPI publishing via `publish-on-tag.yml`

### Conventional Commit Types
- `feat`: New features (appears in CHANGELOG under "🎉 Features")
- `fix`: Bug fixes (appears in CHANGELOG under "🛠️ Fixes")
- `docs`: Documentation changes (appears in CHANGELOG under "📄 Documentation")
- `perf`, `refactor`: Code improvements (hidden in CHANGELOG)
- `chore`, `test`, `build`, `ci`: Hidden from CHANGELOG

The version is managed in both `.release-please-manifest.json` and `pyproject.toml` (kept in sync by release-please).

## CI/CD Matrix

Tests run on all combinations of:
- OS: ubuntu-latest, windows-latest, macos-latest
- Python: 3.11, 3.12, 3.13

All test jobs must pass before merging (gated by `test-success` job).
