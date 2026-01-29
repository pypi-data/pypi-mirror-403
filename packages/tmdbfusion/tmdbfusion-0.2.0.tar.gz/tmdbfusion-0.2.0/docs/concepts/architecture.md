<!-- FILE: docs/concepts/architecture.md -->

# Architecture

TMDBFusion's design is not accidental. It is built on a "layered onion" architecture, designed to balance ease of use with extreme performance and maintainability.

Understanding this architecture helps when debugging complex issues or deciding how to structure your own application's integration.

---

## The Three Layers

The library is strictly separated into three distinct layers:

### 1. The Facade Layer (Client)

Files: `tmdbfusion.core.client` (`TMDBClient`, `AsyncTMDBClient`)

This is the only layer your application code should typically touch.

- **Responsibilities**:
  - Holds the `api_key` and base configuration.
  - Manages the lifecycle of the underlying HTTP session (connection pooling).
  - Acts as a "Registry" for all API resources (`.movies`, `.tv`).
- **Design Pattern**: Facade + Registry.
- **Why?**: Centralizes configuration. You don't pass your API key to every function; you give it to the client once.

### 2. The Resource Layer (Services)

Files: `tmdbfusion.api.*` (e.g., `MoviesAPI`, `PeopleAPI`)

Each TMDB "namespace" has a matching service class.

- **Responsibilities**:
  - Defines the exact method signatures (e.g., `details(id)`).
  - Maps pythonic arguments to URL parameters.
  - Selects the correct Response Model (`msgspec.Struct`).
  - **Does NOT** perform I/O directly. It delegates to the client's internal transport.
- **Design Pattern**: Service / Repository.
- **Why?**: Separation of concerns. The `MoviesAPI` class knows about *Parameters*, not about *HTTP Headers*.

### 3. The Transport Layer (Core)

Files: `tmdbfusion.core.http`, `tmdbfusion.core.sync_client`

The engine room. This is where the bytes actually move.

- **Responsibilities**:
  - URL Construction (`BASE_URL` + path).
  - Authentication (Header injection).
  - Rate Limit handling (Sleep/Retry).
  - Error Status mapping (404 -> `NotFoundError`, 429 -> `RateLimitError`).
  - **Serialization**: using `msgspec` to decode JSON bytes into Structs.
- **Design Pattern**: Adapter.
- **Why?**: We can swap `httpx` for another library (hypothetically) without breaking the top two layers.

---

## Serialization Engine: `msgspec`

One of TMDBFusion's "secret weapons" is its use of `msgspec` instead of `pydantic` or `json`.

### Why msgspec?

1. **Speed**: It is order-of-magnitude faster than standard `json`.
2. **Validation**: It validates types strictly during parsing.
3. **Zero-Overhead**: It parses directly into optimized C-struct-like objects, not heavy Python dictionaries.

### The Parsing Flow

1. **network**: `b'{"id": 550, "title": "Fight Club"}'` (Raw Bytes)
2. **msgspec**: Direct decode -> `MovieDetails(id=550, title="Fight Club")`
3. **app**: `movie.title`

There is no intermediate `dict` creation step. This saves significant memory, especially when fetching thousands of items.

---

## Sync vs Async Architecture

TMDBFusion maintains two parallel implementations of the Transport Layer:

1. `SyncTMDBClient` maps to `httpx.Client`.
2. `AsyncTMDBClient` maps to `httpx.AsyncClient`.

However, the **Models** and **Resource Definitions** are shared.

- `tmdbfusion.models.*`: **SHARED** (Pure Data)
- `tmdbfusion.api.*`: **HYBRID**. We generate parallel methods or use inheritance to share logic where possible, ensuring feature parity.

This "Code Duplication" in the transport layer is intentional. It allows us to optimize the Async path for event loops without compromising the simplicity of the Sync path with "async-to-sync" bridges that often cause deadlocks.

---

## Dependency Graph

We rely on a minimal but powerful set of dependencies:

| Package | Purpose | Justification |
|:--------|:--------|:--------------|
| **httpx** | HTTP Client | The standard for modern python HTTP. Supports Sync/Async consistently. Supports HTTP/2. |
| **msgspec** | Serialization | fastest JSON parser available. Strict typing support. |
| **typing_extensions** | Typing | Backwards compatibility for older python versions (if supported). |

We explicitly **AVOID**:

- `requests`: No native async support.
- `pydantic`: While excellent, it is heavier than `msgspec` for pure read-only API wrappers.

---

## Mental Model

Think of `TMDBClient` as a web browser.

- You open the browser (**Initialize Client**).
- You type a URL (**Call Resource Method**).
- The browser handles DNS, TCP, SSL (**Transport Layer**).
- The browser parses HTML/JSON and shows you the page (**Parser Layer**).
- You read the page (**Your Code**).

Start with this mental model, and the rest of the documentation will click into place.
