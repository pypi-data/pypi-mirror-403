<!-- FILE: docs/api/overview.md -->

# API Reference Overview

This section contains the technical specification for every class, method, function, and variable exported by TMDBFusion.

It is auto-generated from the codebase and reflects version **0.1.0**.

---

## Navigation Map

### [Client Classes](client.md)

The entry points. Start here.

- `TMDBClient`: The synchronous client.
- `AsyncTMDBClient`: The asynchronous client.
- `BaseAPI`: The parent class for all resources.

### [Endpoints](endpoints.md)

The meat of the library. Organized by namespace:

- `client.movies` (MoviesAPI)
- `client.tv` (TVAPI)
- `client.people` (PeopleAPI)
- `client.search` (SearchAPI)
- ...and 26 others.

### [Models](models.md)

The data structures returned by the endpoints.

- `Movie`: Title, runtime, budget.
- `Person`: Name, birthday, credits.
- `TVShow`: Name, seasons, networks.
- `PaginatedResponse`: The wrapper for lists.

### [Exceptions](exceptions.md)

What goes wrong.

- `TMDBError`
- `RateLimitError`
- `NotFoundError`

---

## Conventions used in this Ref

### Type Annotations

All parameters include their python types.

- `int | None`: This argument is optional. Pass `None` or an integer.
- `msgspec.Struct`: A high-performance struct (behaves like a frozen class).

### Keyword-Only Arguments

Most methods force keyword arguments (`*`) for clarity.

```python
# Definition
def details(self, movie_id: int, *, language: str = "en")

# Usage
client.movies.details(550, language="fr")  # OK
client.movies.details(550, "fr")           # TypeError!
```

We do this to prevent bugs when arguments are reordered in future versions.

### Sync vs Async Parity

Unless noted otherwise, `TMDBClient` and `AsyncTMDBClient` expose the **exact same names**.

- Sync: `client.movies.details(...)`
- Async: `await client.movies.details(...)`

The arguments and return types are identical. Only the `await` keyword differs.
