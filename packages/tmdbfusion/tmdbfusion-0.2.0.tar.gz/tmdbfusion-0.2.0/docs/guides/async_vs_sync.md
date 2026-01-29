# Deep Dive: Async vs Sync Architecture

Understanding the internal transport layers is crucial for configuring TMDBFusion for high-load environments.

## Architecture

TMDBFusion wraps `httpx` for both synchronous and asynchronous operations.

| Feature | `TMDBClient` (Sync) | `AsyncTMDBClient` (Async) |
| :--- | :--- | :--- |
| **Underlying Driver** | `httpx.Client` | `httpx.AsyncClient` |
| **Concurrency Model** | Blocking I/O | Non-blocking Event Loop (`asyncio`) |
| **Connection Pooling** | Thread-local | Task-safe (Event Loop bound) |
| **Use Case** | Scripts, CLI tools, ETL jobs | Web Servers (FastAPI), Spiders |

## Lifecycle Management

Proper resource management is enforced via the Context Manager protocol.

### Connections & Keep-Alive

The client is configured with aggressive keep-alive settings to minimize TLS handshake overhead.

* **`max_connections`**: Default `100`. The hard limit on open TCP connections.
* **`max_keepalive_connections`**: Default `20`. The number of idle connections kept open in the pool.

> [!TIP]
> **Performance Tuning**: If you are running a high-concurrency scraper, increase `max_connections`.
> If you are making sporadic requests, decrease `max_keepalive_connections` to save system resources.

```python
client = AsyncTMDBClient(
    token, 
    max_connections=200, 
    max_keepalive_connections=50
)
```

### The "Unclosed Client" Warning

If you instantiate the client without a `with` block and forget to call `.close()`, `httpx` will leak connections.

**Correct Pattern**:

```python
async with AsyncTMDBClient(token) as client:
    await client.movies.details(123)
# Connection pool is automatically drained and sockets closed here
```

**Incorrect Pattern**:

```python
client = AsyncTMDBClient(token) # DANGER: Resource leak risk
await client.movies.details(123)
# Garbage collection might close it, but it's non-deterministic
```

## Concurrency Control (Async)

While `AsyncTMDBClient` is non-blocking, you must handle concurrency limits at the application level to avoid overwhelming your local network stack (or getting hard-banned by TMDB).

### Using `asyncio.gather` vs `asyncio.Semaphore`

**Bad (Unbounded Concurrency):**

```python
# Tries to open 10,000 connections simultaneously
# Will likely crash your OS or get flagged by TMDB WAF
results = await asyncio.gather(*[client.movies.details(id) for id in range(10000)])
```

**Good (Bounded Concurrency):**

```python
sem = asyncio.Semaphore(50) # Limit to 50 concurrent requests

async def fetch(id):
    async with sem:
        return await client.movies.details(id)

tasks = [fetch(id) for id in ids]
results = await asyncio.gather(*tasks)
```

## Error Propagation

Both clients normalize `httpx` exceptions into `tmdbfusion.exceptions.TMDBError` subclasses.

* `httpx.TimeoutException` -> `tmdbfusion.exceptions.ServerError` (treated as temporary failure)
* `httpx.ConnectError` -> `tmdbfusion.exceptions.ServerError`

This ensures your error handling logic remains consistent regardless of the underlying network failure mode.
