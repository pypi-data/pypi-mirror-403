<!-- FILE: docs/api/exceptions.md -->

# Exception Reference

All exceptions raised by TMDBFusion are defined in `tmdbfusion.exceptions`.

They form a hierarchy rooted at `TMDBError`.

## Base Exception

### `TMDBError`

The base class for all library exceptions.

**Attributes:**

- `message` (str): The error message.
- `response` (httpx.Response | None): The raw response object (if available).
- `status_code` (int | None): The HTTP status code (if available).

Usage:

```python
try:
    ...
except TMDBError as e:
    # Catches everything
    pass
```

---

## Network & Server Errors

### `NetworkError(TMDBError)`

Raised when a network connection failure occurs (DNS, SSL, Connection Refused).

- This wraps `httpx.NetworkError`.

### `ServerError(TMDBError)`

Raised when the TMDB server returns a 5xx error (500, 502, 503, 504).

- Retry safe? **Yes**.

---

## Client Errors (4xx)

These errors generally indicate a problem with your request.

### `ClientError(TMDBError)`

Base class for 4xx errors.

### `AuthenticationError(ClientError)`

**Status Code**: 401
Raised when the API Key is missing, invalid, or revoked.

### `AuthorizationError(ClientError)`

**Status Code**: 403
Raised when the API Key is valid, but does not have permission to access the resource.

### `NotFoundError(ClientError)`

**Status Code**: 404
Raised when the requested resource (Movie ID, List ID) does not exist.

### `RateLimitError(ClientError)`

**Status Code**: 429
Raised when the request limit is exceeded.

**Additional Attributes:**

- `retry_after` (int | None): The number of seconds to wait before retrying.

### `ValidationError(ClientError)`

Raised when local validation fails before sending the request.

---

## Usage in Code

### Basic Handling

The most common pattern is to wrap specific calls where you expect failure.

```python
from tmdbfusion.exceptions import (
    TMDBError, 
    NotFoundError, 
    RateLimitError
)

try:
    client.movies.details(550)
except NotFoundError:
    # Handle missing movie
    print("Not found")
except RateLimitError as e:
    # Handle limits
    print(f"Wait {e.retry_after} seconds")
except TMDBError as e:
    # Handle everything else (Network, 500s)
    print(f"Oops: {e}")
```

### Advanced Handling: Status Codes

Sometimes you want to handle specific HTTP status codes that don't map to a convenient exception subclass, or you want to log the specific status for debugging.

```python
try:
    client.movies.details(550)
except TMDBError as e:
    if e.status_code == 418:
        print("I'm a teapot? TMDB doesn't return this.")
    elif e.status_code == 503:
        print("Service Unavailable - Maintenance Mode")
    else:
        print(f"Status: {e.status_code}")
```

### Advanced Handling: Response Inspection

For deep debugging, you can access the raw `httpx.Response` object attached to the exception.

```python
try:
    client.movies.details(550)
except TMDBError as e:
    if e.response:
        print(f"Headers: {e.response.headers}")
        print(f"Body: {e.response.text}")
        print(f"URL: {e.response.url}")
```

---

## Full Hierarchy

For reference, here is the complete class tree.

- `Exception`
  - `TMDBError`
    - `NetworkError` (Wraps `httpx.NetworkError`)
    - `ServerError` (HTTP 500-599)
    - `ClientError` (HTTP 400-499)
      - `AuthenticationError` (401)
      - `AuthorizationError` (403)
      - `NotFoundError` (404)
      - `RateLimitError` (429)
      - `ValidationError` (Pre-flight checks)

---

## When to Raise These Yourself

If you are implementing a custom `Transport` or extending the library, you should raise these exceptions to maintain contract with the application code.

```python
if response.status_code == 404:
    raise NotFoundError("Resource not found", response=response)
```
