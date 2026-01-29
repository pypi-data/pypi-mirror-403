<!-- FILE: docs/contributing/development-setup.md -->

# Development Setup

Thank you for your interest in contributing to TMDBFusion! This guide will help you set up a robust local environment.

TMDBFusion supports all modern Python versions (3.13+) and uses strict tooling to ensure quality.

---

## Prerequisites

Ensure you have the following installed:

1. **Python 3.13+**
2. **Git**
3. **Rust** (Required for compiling `msgspec` from source, if wheels are missing)

We recommend using a virtual environment manager.

---

## Cloning

```bash
git clone https://github.com/xsyncio/tmdbfusion.git
cd tmdbfusion
```

---

## Dependency Management

We use `pip` with `pyproject.toml` standards. You can also use `poetry`, `hatch`, or `uv`.

### Method 1: Standard Pip (Recommended)

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev,docs,cli]"
```

### Method 2: Poetry

```bash
poetry install --all-extras
```

---

## Task Runner: Nox

We use `nox` (similar to Tox) to orchestrate testing and linting across multiple Python versions.

### Running All Checks

```bash
nox
```

### Running Specific Sessions

You often don't want to run everything.

- **Fast Lint**: `nox -s lint`
- **Type Check**: `nox -s mypy`
- **Unit Tests**: `nox -s test`
- **Docs Build**: `nox -s docs`

---

## Running Tests directly

If you want to run `pytest` directly (faster than Nox for TDD):

```bash
pytest
```

**Note**: You must export `TMDB_API_KEY` in your environment if you plan to run integration tests, although the default test suite mocks network calls via `respx`.

### Coverage

We enforce 100% test coverage on new code.

```bash
pytest --cov=tmdbfusion --cov-report=html
open htmlcov/index.html
```

---

## Building Documentation

We use `mkdocs-material`.

```bash
# Serve locally
mkdocs serve
```

Go to `http://localhost:8000` to see your changes live.

---

## Pre-Commit Hooks

We use `pre-commit` to prevent bad code from being committed.

```bash
# Install hooks
pre_commit install
```

Now, every `git commit` will automatically run:

- Ruff (Lint & Format)
- Mypy (Types)
- Numpydoc (Docstring validation)

To run manually:

```bash
pre-commit run --all-files
```
