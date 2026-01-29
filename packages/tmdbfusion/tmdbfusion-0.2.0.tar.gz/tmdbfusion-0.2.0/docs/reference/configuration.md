<!-- FILE: docs/reference/configuration.md -->

# Configuration

Beyond authentication, TMDBFusion can be configured to suit different runtime environments.

---

## Client Arguments

The `TMDBClient` and `AsyncTMDBClient` accept several arguments at initialization.

### `api_key`

- **Type**: `str | None`
- **Default**: `None` (Loads from env)
- **Description**: The V3 API Key or V4 Read Access Token.

### `base_url`

- **Type**: `str`
- **Default**: `"https://api.themoviedb.org/3"`
- **Description**: The API root. Useful if you need to route requests through a transparent proxy or a mock server.

---

## Global Timeouts

By default, TMDBFusion relies on `httpx` default timeouts (usually 5 seconds for connect, 30 for read).

To change this, you must access the underlying transport **before** making requests.

```python
import httpx
from tmdbfusion import TMDBClient

client = TMDBClient()

# Set a 10-second timeout for everything
client._transport.timeout = httpx.Timeout(10.0)
```

*Note: In v0.1.0, direct timeout configuration in the constructor is planned for v0.2.0.*

---

## Proxy Settings

Proxies are configured via standard Environment Variables (see [Environment Variables](environment-variables.md)) or by monkey-patching the transport.

---

## Logging Configuration

TMDBFusion emits logs under the `tmdbfusion` namespace.

```python
import logging

# Get the logger
logger = logging.getLogger("tmdbfusion")

# Set level
logger.setLevel(logging.DEBUG)

# Add handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
```

### Log Levels

- **DEBUG**: Logs every URL requested, method, and HTTP status code. Payload bodies are typically NOT logged to protect PII/Keys.
- **INFO**: General lifecycle events (client init).
- **WARNING**: Retries, Deprecation warnings.
- **ERROR**: Network failures, 5xx responses.
