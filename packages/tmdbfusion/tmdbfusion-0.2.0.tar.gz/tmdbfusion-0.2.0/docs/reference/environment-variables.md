<!-- FILE: docs/reference/environment-variables.md -->

# Environment Variables

TMDBFusion respects standard environment variables to control its behavior. This allows 12-factor app configuration, making it easy to deploy to Docker, Kubernetes, or Serverless platforms without changing code.

---

## Library Specific

### `TMDB_API_KEY`

- **Required**: Yes (if not passed to constructor).
- **Value**: Your V3 API Key or V4 Read Access Token.
- **Usage**: Automatically read by `TMDBClient()` if no key argument is provided. This is the safest way to handle credentials.

```bash
export TMDB_API_KEY="eyJhbGciOiJIUz..."
```

---

## Networking (via HTTPX)

Since the library is built on `httpx`, it respects standard proxy variables. This is critical for corporate environments.

### `HTTP_PROXY`

- **Value**: URL of the proxy for HTTP requests.
- **Example**: `http://10.10.1.10:3128`

### `HTTPS_PROXY`

- **Value**: URL of the proxy for HTTPS requests (TMDB is HTTPS only, so this is the important one).
- **Example**: `http://user:pass@10.10.1.10:3128`

### `ALL_PROXY`

- **Value**: Catch-all proxy for all protocols (SOCKS, HTTP, HTTPS).

### `NO_PROXY`

- **Value**: Comma-separated list of hostnames to exclude from proxying.
- **Example**: `localhost,127.0.0.1,.internal`

---

## SSL / Certificates

### `SSL_CERT_FILE`

- **Value**: Path to a `.pem` file containing CAs.
- **Usage**: Useful in corporate environments with custom Root CAs that man-in-the-middle SSL traffic for inspection.

### `SSL_CERT_DIR`

- **Value**: Path to a directory of CA certificates.

---

## CI/CD Variables

If you are running tests in a CI environment (GitHub Actions, GitLab CI), you might see different behavior regarding timeouts or logging.

### `CI`

- **Value**: `true` or `1`.
- **Effect**: Some test runners use this to disable interactive features (like progress bars) or increase timeout tolerances.

### `GITHUB_ACTIONS`

- **Value**: `true`.
- **Effect**: Specific GitHub Actions logging formats.

---

## Python Standard

These affect the Python interpreter itself, which impacts TMDBFusion.

### `PYTHONASYNCIODEBUG`

- **Value**: `1`
- **Usage**: Enables debug mode for the `asyncio` event loop.
- **Why**: Useful if you suspect TMDBFusion is hanging or blocking the loop incorrectly. It will print warnings if a callback takes too long (>100ms).

### `PYTHONTRACEMALLOC`

- **Value**: `1`
- **Usage**: Tracks memory allocations.
- **Why**: Useful if you are debugging a memory leak in a long-running crawler.

### `PYTHONPATH`

- **Value**: Path to source code.
- **Usage**: If you are developing locally and want to run scripts without installing the package.

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## Nox / Testing

Variables used when running the `nox` task runner.

### `NOX_SESSION`

- **Value**: The name of the session to run (e.g., `lint`, `tests-3.11`).
- **Usage**: `export NOX_SESSION=lint` makes `nox` run only linting by default.

### `PYTEST_ADDOPTS`

- **Value**: Extra arguments for pytest.
- **Usage**: `export PYTEST_ADDOPTS="-vv --durations=10"` to make tests more verbose and show slow tests.
