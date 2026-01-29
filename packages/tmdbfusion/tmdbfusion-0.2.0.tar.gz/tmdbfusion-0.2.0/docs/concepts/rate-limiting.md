<!-- FILE: docs/concepts/rate-limiting.md -->

# Rate Limiting

The Movie Database (TMDB) is a free, community-built resource. To ensure availability for everyone, they enforce strict API rate limits.

If you are building a high-performance application, you **will** hit these limits. Here is how TMDBFusion helps you handle them.

---

## The Limits

While TMDB does not publish exact hard numbers for every key tier, the general rule of thumb for a standard API key is:

> **~40 to 50 requests every 10 seconds** per IP address.

This translates to roughly 4-5 requests per second (RPS).

### HTTP Headers

TMDB provides real-time feedback in the response headers of every request:

- `X-RateLimit-Limit`: The total limit (e.g., 40).
- `X-RateLimit-Remaining`: How many you have left in this window (e.g., 38).
- `X-RateLimit-Reset`: Unix timestamp when the window resets.

---

## Built-in Protection

TMDBFusion's transport layer is aware of these headers.

### 429 Handling strategy

If you exceed the limit, TMDB returns `HTTP 429 Too Many Requests`.

By default, the library raises a `tmdbfusion.exceptions.RateLimitError`.

```python
from tmdbfusion import RateLimitError
import time

try:
    make_lots_of_requests()
except RateLimitError as e:
    # The 'retry_after' attribute acts as a hint
    wait_time = e.retry_after or 10
    print(f"Cooling down for {wait_time} seconds...")
    time.sleep(wait_time)
```

### Automatic Backoff (Configurable)

*Note: In the current version, automatic sleep-and-retry is opt-in to avoid initializing unexpected pauses in your application.*

To implement robust retries, we recommend using the industry-standard `tenacity` library or similar decorators on your implementation logic, as wrapping the low-level client often hides performance issues.

---

## Strategies for High Volume

If you need to fetch 10,000 movies, 4 requests per second means it will take **~40 minutes**. You cannot cheat physics, but you can optimize throughput.

### 1. The Semaphore Pattern (Async)

When using `asyncio`, it is tempting to spawn 10,000 tasks. **Don't.** You will just trigger 9,960 429 errors instantly.

Use an `asyncio.Semaphore` to limit concurrent connections.

```python
import asyncio
from tmdbfusion import AsyncTMDBClient

async def fetch_all(ids):
    # Limit to 40 concurrent requests
    sem = asyncio.Semaphore(40)
    
    async with AsyncTMDBClient() as client:
        
        async def worker(mid):
            async with sem:
                 # The semaphore ensures only 40 lines below run at once
                return await client.movies.details(mid)
        
        tasks = [worker(mid) for mid in ids]
        return await asyncio.gather(*tasks)
```

### 2. Leaky Bucket Implementation

For strict compliance, implementing a client-side rate limiter (e.g., [`aiolimiter`](https://pypi.org/project/aiolimiter/)) is superior to reacting to 429s.

```python
from aiolimiter import AsyncLimiter

# Max 40 requests per 10 seconds
limiter = AsyncLimiter(40, 10)

async def worker(client, mid):
    async with limiter:
        return await client.movies.details(mid)
```

### 3. Check `Append-to-Response`

The best request is the one you don't make.
If you need movie details, credits, and images, do **not** make 3 requests.

Use `append_to_response` to get them all in one go. This counts as **1 request** against your quota.

```python
# 1 Request, 3 datasets
details = client.movies.details(
    550, 
    append_to_response="credits,images"
)
print(details.credits.cast[0].name)
print(details.images.posters[0].file_path)
```

This effectively triples your throughput limit.

---

## Blacklisting

If you aggressively ignore 429s and keep hammering the API, TMDB may temporarily ban your API key or IP address (`HTTP 403 Forbidden` or `HTTP 401 Unauthorized`).

**Respect the 429.** It is a stoplight, not a suggestion.
