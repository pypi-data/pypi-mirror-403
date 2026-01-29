<!-- FILE: docs/getting-started/installation.md -->

# Installation

Getting TMDBFusion up and running is straightforward. We support all major Python package managers and offer optional extras for specific use cases.

## Prerequisites

Before installing, ensure your environment meets the following requirements:

- **Python**: Version **3.13** or higher.
- **OS**: Linux, macOS, or Windows.
- **Network**: Access to `api.themoviedb.org` (HTTPS).

> [!NOTE]
> TMDBFusion requires Python 3.13+ because it leverages the latest typing features and performance improvements in the language. If you are on an older version, you will need to upgrade.

---

## Standard Installation

For most users, installing the core package is sufficient. The core package includes:

- The `SyncTMDBClient` and `AsyncTMDBClient`.
- All data models and API definitions.
- `httpx` for networking.
- `msgspec` for serialization.

### Using pip

The standard Python package installer.

```bash
pip install tmdbfusion
```

### Using uv

If you are using the ultra-fast `uv` package manager:

```bash
uv pip install tmdbfusion
```

### Using Poetry

For modern project dependency management:

```bash
poetry add tmdbfusion
```

### Using Hatch

If you are managing your project with Hatch:

```bash
hatch add tmdbfusion
```

---

## Optional Dependencies

TMDBFusion is modular. You can install additional features based on your needs to keep your environment lean.

### `cli` - Command Line Interface

Includes the `tmdbf` command-line tool for quick querying and debugging from the terminal. Adds `click` and `rich`.

```bash
pip install "tmdbfusion[cli]"
```

### `rich` - Pretty Printing

If you want colorized tracebacks and formatted logging output but don't need the full CLI.

```bash
pip install "tmdbfusion[rich]"
```

### `dev` - Development Tools

Install everything needed to contribute to TMDBFusion (tests, linters, docs).

```bash
pip install "tmdbfusion[dev]"
```

### `docs` - Documentation Building

Dependencies required to build this documentation site locally (`mkdocs`, `material`, etc.).

```bash
pip install "tmdbfusion[docs]"
```

---

## Verifying Installation

Once installed, it is good practice to verify that the package is correctly recognized by Python and that the version is what you expect.

### Check Version via CLI

If you installed the standard package, you can check the version using `python -c`:

```bash
python -c "import tmdbfusion; print(tmdbfusion.__version__)"
# Output: 0.1.0
```

### Check Version via `tmdbf`

If you installed the `[cli]` extra:

```bash
tmdbf --version
# Output: tmdbfusion, version 0.1.0
```

### Simple Import Test

Create a file named `check_tmdb.py`:

```python
import tmdbfusion
import sys

print(f"TMDBFusion Version: {tmdbfusion.__version__}")
print(f"Python Location: {sys.executable}")
```

Run it:

```bash
python check_tmdb.py
```

If this prints the version without errors, you are ready to proceed.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'tmdbfusion'`

- **Cause**: You installed the package in a different Python environment than the one you are running.
- **Fix**: Ensure your virtual environment is active.

    ```bash
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows
    ```

### `ImportError: cannot import name 'AsyncTMDBClient'`

- **Cause**: You might have an old version cached or a namespace collision.
- **Fix**: Force a clean reinstall.

    ```bash
    pip uninstall tmdbfusion
    pip install --no-cache-dir tmdbfusion
    ```

### `SSL: CERTIFICATE_VERIFY_FAILED`

- **Cause**: Your local Python environment has outdated root certificates.
- **Fix**: Update the `certifi` package or your system certificates.

    ```bash
    pip install --upgrade certifi
    ```

---

## Proxy Configuration

If you are behind a corporate proxy, `httpx` (our underlying transport) will automatically respect the standard environment variables:

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `ALL_PROXY`

Example:

```bash
export HTTPS_PROXY="http://user:pass@proxy.company.com:8080"
python my_script.py
```

TMDBFusion requires no code changes to work with proxies configured this way.

---

## Next Steps

Now that you have the library installed, you need an API Key to talk to the servers.

**[Go to Authentication Guide](authentication.md)**
