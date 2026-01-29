<!-- FILE: docs/concepts/performance.md -->

# Performance

TMDBFusion is engineered to be the fastest Python wrapper for TMDB. This document explains where that speed comes from and how you can preserve it in your application.

---

## The Engine: msgspec vs json

Standard Python `json` library is convenient but slow. It parses JSON text into Python dictionaries, lists, strings, and integers.

For a large response (like `popular` movies), creating thousands of dictionary objects and string instances is expensive in CPU time and memory.

### Structs

TMDBFusion uses `msgspec.Struct` for all models.

- **Memory**: Structs are defined with `__slots__` logic (at the C level), using significantly less RAM than `dict`.
- **Parsing**: `msgspec` decodes JSON directly into these structs, bypassing intermediate containers.

### Benchmark

*Parsing a 1MB generic JSON response:*

| Library | Requests/Sec | Relative Speed |
|:--------|:------------:|:--------------:|
| Standard `json` | ~80 | 1x |
| `pydantic` v2 | ~350 | 4.3x |
| **`msgspec` (Fusion)** | **~900+** | **11x** |

*Note: Synthetic benchmarks, actual network conditions vary.*

---

## Connection Pooling

Opening a new TCP/SSL connection requires a handshake. This takes time (often more time than the request itself for small payloads).

### The Wrong Way

Creating a new client for every request forces a new handshake every time.

```python
# BAD: 3 Handshakes
for mid in [550, 551, 552]:
    client = TMDBClient()  # New session created
    client.movies.details(mid)
```

### The Right Way

Reuse the client instance. The underlying `httpx.Client` maintains a pool of open connections ("Keep-Alive").

```python
# GOOD: 1 Handshake, 3 Requests
client = TMDBClient()  # Session created once
for mid in [550, 551, 552]:
    client.movies.details(mid)
```

When using `async with AsyncTMDBClient()`, the pool is automatically managed and closed when you exit the block.

---

## Memory Management

If you are building a crawler or analyzing millions of items, memory is your bottleneck.

### Lazy Iterators

When fetching lists, do not accumulate everything in a massive list unless necessary.

```python
# BAD: Loading 1GB of movie objects into RAM
all_movies = []
for page in range(1, 5000):
   res = client.movies.popular(page=page)
   all_movies.extend(res.results)

# GOOD: Processing stream
for page in range(1, 5000):
   res = client.movies.popular(page=page)
   # Write to DB immediately and discard the python objects
   database.insert_many(res.results) 
   # 'res' is garbage collected after this iteration
```

### Slots

Because our models use `msgspec.Struct`, they are naturally memory-efficient. However, adding dynamic attributes to them at runtime is disabled by default to save space.

---

## Network Latency

Ultimately, your speed is limited by the speed of light to TMDB servers.

- **Use `append_to_response`**: Fetching details + credits + images in 1 request is always faster than 3 requests, regardless of Python performance.
- **Server Location**: Using a server closer to TMDB (AWS US-East) will reduce ping times.

---

## Profiling

If your application feels slow:

1. **Check Networking**: Is it DNS? Is it the API response time?
2. **Check App Logic**: Are you parsing the data inefficiently after receiving it?
3. **Use the Async Client**: Blocking I/O is the #1 cause of slow Python web apps.

### Micro-Benchmarking

You can use `timeit` to test your integration efficiency.

```python
import timeit
import asyncio

setup = """
from tmdbfusion import TMDBClient
client = TMDBClient()
"""

# Test Sync Latency
t = timeit.timeit("client.movies.details(550)", setup=setup, number=10)
print(f"Avg Sync Call: {t/10:.3f}s")
```

### Profiling with Scalene

For CPU/Memory profiles, we recommend `scalene`.

```bash
pip install scalene
scalene my_script.py
```

It will show you exactly which line of Python is allocating memory or holding the GIL.
