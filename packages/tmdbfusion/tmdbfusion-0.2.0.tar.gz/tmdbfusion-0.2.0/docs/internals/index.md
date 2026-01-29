# Contributing

We welcome contributors!

## Development Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/xsyncio/tmdbfusion.git
    cd tmdbfusion
    ```

2. **Install dependencies**

    ```bash
    pip install -e .[dev,docs]
    ```

3. **Run tests**

    ```bash
    pytest
    ```

## Documentation Standards

We use `mkdocs-material` and `mkdocstrings`.

* **Docstrings**: All code must have **NumPy-style** docstrings.
* **Type Hints**: All code must be fully typed.
* **Linting**: Run `ruff check .` before committing.

## Project Structure

* `tmdbfusion/`: Source code
  * `api/`: API endpoints (one file per resource)
  * `models/`: Data models (msgspec structs)
* `tests/`: Test suite
* `docs/`: Documentation sources
