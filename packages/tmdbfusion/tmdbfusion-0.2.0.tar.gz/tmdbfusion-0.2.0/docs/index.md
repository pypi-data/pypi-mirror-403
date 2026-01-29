<!-- FILE: docs/index.md -->

# TMDBFusion Documentation

Welcome to the **TMDBFusion** documentation the definitive guide to the high-performance, type-safe Python wrapper for The Movie Database (TMDB) API.

TMDBFusion is engineered for **enterprise-grade applications**, **data-intensive pipelines**, and **modern async web services**. It is not just a request wrapper; it is a full-featured SDK that handles the complexities of API integration so you can focus on building your application.

---

## Key Capabilities

### High-Performance Architecture

- **Dual-Engine Support**: Seamlessly switch between `SyncTMDBClient` for scripts and `AsyncTMDBClient` for high-concurrency apps (built on `httpx`).
- **Zero-Overhead Serialization**: Powered by `msgspec` for ultra-fast JSON parsing and validation.
- **Smart Caching**: Built-in caching strategies to minimize latency and respect API limits.

### Type-Safety & Correctness

- **100% Type Hints**: Fully typed codebase compatible with `mypy` and modern IDEs.
- **Strict Models**: Data is validated against strict Pydantic-style models (via `msgspec.Struct`) ensuring you never handle malformed data.
- **Comprehensive Error Handling**: Granular exception hierarchy mapping every TMDB error code to a specific Python exception.

### Developer Experience

- **Iterator-Based Pagination**: Forget manual page tracking. Iterate over `client.movies.popular()` as if it were a simple list.
- **Rate Limit Management**: Automatic handling of `429 Too Many Requests` with configurable backoff strategies.
- **Rich Debugging**: Detailed logging hooks and debug modes to trace request lifecycles.

---

## Documentation Structure

### [Getting Started](getting-started/overview.md)

Everything you need to go from zero to your first API call.

- **[Installation](getting-started/installation.md)**: Setup via pip, poetry, or from source.
- **[Authentication](getting-started/authentication.md)**: Managing API Keys and detailed access controls.
- **[Quickstart](getting-started/quickstart.md)**: "Hello World" examples for Sync and Async.

### [Core Concepts](concepts/architecture.md)

Deep dives into how TMDBFusion works under the hood.

- **[Architecture](concepts/architecture.md)**: internal design and data flow.
- **[Sync vs Async](concepts/sync-vs-async.md)**: When to use which client.
- **[Error Handling](concepts/error-handling.md)**: Best practices for robust apps.
- **[Rate Limiting](concepts/rate-limiting.md)**: How we protect your API quota.

### [User Guides](guides/basic-usage.md)

Practical, code-heavy walkthroughs for common implementation patterns.

- **[Basic Usage](guides/basic-usage.md)**: Fetching movies, TV shows, and people.
- **[Async Patterns](guides/async-patterns.md)**: Leveraging `asyncio` for concurrent fetching.
- **[Retries & Backoff](guides/retries-and-backoff.md)**: Configuring resilience policies.
- **[Testing](guides/testing-and-mocking.md)**: How to test your code that uses TMDBFusion.

### [API Reference](api/overview.md)

The authoritative technical reference for every class and function.

- **[Client API](api/client.md)**: `TMDBClient` and `AsyncTMDBClient` references.
- **[Endpoints](api/endpoints.md)**: Detailed docs for Movies, TV, People, and Search endpoints.
- **[Models](api/models.md)**: Data structures and response schemas.
- **[Exceptions](api/exceptions.md)**: Full list of raised errors.

### [Reference & Config](reference/configuration.md)

Configuration variables, environment settings, and constants.

---

## Quick Peek

Here is how simple it is to get started using the synchronous client:

```python
from tmdbfusion import TMDBClient

def main():
    # Initialize the client (API Key from environment or argument)
    client = TMDBClient(api_key="your_api_key_here")

    # Fetch details for "Fight Club"
    movie = client.movies.details(550)
    
    print(f"Title: {movie.title}")
    print(f"Tagline: {movie.tagline}")
    print(f"Release Date: {movie.release_date}")

    # Iterate over popular movies (Auto-pagination!)
    print("\nPopular Movies:")
    for movie in client.movies.popular().results[:5]:
        print(f" - {movie.title} ({movie.vote_average}/10)")

if __name__ == "__main__":
    main()
```

And the equivalent **Async** workflow:

```python
import asyncio
from tmdbfusion import AsyncTMDBClient

async def main():
    async with AsyncTMDBClient(api_key="your_api_key_here") as client:
        # Fetch data concurrently
        movie_task = client.movies.details(550)
        credits_task = client.movies.credits(550)

        movie, credits = await asyncio.gather(movie_task, credits_task)

        print(f"Movie: {movie.title}")
        print(f"Starring: {credits.cast[0].name}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Project Status

| Component | Status | Description |
|-----------|--------|-------------|
| **Core API** | Stable | Full coverage of V3 Movies, TV, People APIs. |
| **Async** | Stable | Fully aligned with Sync API capabilities. |
| **Models** | Stable | Strict typing for response validation. |
| **V4 API** | Beta | Partial support for Lists and Auth. |

---

## License

TMDBFusion is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT).

Copyright (c) 2026 Xsyncio.
