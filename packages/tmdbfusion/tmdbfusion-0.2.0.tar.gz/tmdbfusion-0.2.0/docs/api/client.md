<!-- FILE: docs/api/client.md -->

# Client Reference

The Client class is the central coordinator of the library. It manages configuration, authentication, and the HTTP session lifecycle.

---

## `TMDBClient` (Synchronous)

```python
class TMDBClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.themoviedb.org/3"):
        ...
```

### Parameters

- **`api_key`** (`str | None`): Your TMDB API Key or v4 Read Access Token.
  - If `None`, attempts to load from `os.environ["TMDB_API_KEY"]`.
  - Raises `ValueError` if no key is found.
- **`base_url`** (`str`): The API root. Defaults to V3. Rarely needs changing unless using a proxy.

### Attributes

The client exposes resource namespaces as properties.

| Attribute | Type | Description |
|:----------|:-----|:------------|
| `.movies` | `MoviesAPI` | Access `/movie` endpoints. |
| `.tv` | `TVAPI` | Access `/tv` endpoints. |
| `.people` | `PeopleAPI` | Access `/person` endpoints. |
| `.search` | `SearchAPI` | Access `/search` endpoints. |
| `.images` | `ImagesAPI` | Helper for image URLs. |
| `.discover` | `DiscoverAPI` | Access `/discover` endpoints. |
| `.trending` | `TrendingAPI` | Access `/trending` endpoints. |
| `.lists` | `ListsAPI` | Access `/list` endpoints. |
| `.changes` | `ChangesAPI` | Access `/changes` endpoints. |
| ... | ... | (See full list in Endpoints) |

### Methods

#### `close()`

Closes the underlying `httpx.Client` connection pool.

```python
client.close()
```

### Context Manager

It is recommended to use the client as a context manager to ensure `close()` is called.

```python
with TMDBClient() as client:
    client.movies.details(550)
# Connection closed
```

---

## `AsyncTMDBClient` (Asynchronous)

```python
class AsyncTMDBClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.themoviedb.org/3"):
        ...
```

### Parameters

*(Same as TMDBClient)*

### Attributes

*(Same as TMDBClient)*

### Methods

#### `aclose()` (Async)

Closes the underlying `httpx.AsyncClient` connection pool.

```python
await client.aclose()
```

### Context Manager (Async)

```python
async with AsyncTMDBClient() as client:
    await client.movies.details(550)
# Connection closed
```

---

## Internal Configuration

The clients maintain internal state for optimization.

- **`_transport`**: The `httpx` client instance.
  - You generally should not touch this, but if you need to mutate headers globally, you can access `client._transport.headers`.
- **`_config`**: Stores the cached Configuration (image base URLs, countries, etc).
  - Fetched lazily on first need by helpers like `client.images`.

---

## Thread Safety

- **`TMDBClient`**: Thread-safe. You can share a single instance across threads (e.g., in a generic `ThreadPoolExecutor`). The underlying `httpx` client is thread-safe.
- **`AsyncTMDBClient`**: Not thread-safe. You should not share it across different Event Loops. Stick to one loop (the default behavior of asyncio applications).

---

## Extension Points

### Custom Transport

If you need to usage a custom `httpx` client (e.g., for extensive proxy auth or client-side certificates), you must presently subclass or monkey-patch.

*(Future versions may allow passing a pre-configured transport)*.
