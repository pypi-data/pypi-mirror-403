<!-- FILE: docs/guides/retries-and-backoff.md -->

# Retries and Backoff

Distributed systems are unreliable. Packets get dropped, load balancers hiccup, and rate limits get hit.

A robust production application treats these failures as temporary ("transient") rather than fatal.

---

## The Need for Retries

You should retry when:

1. **Rate Limited (429)**: The server told you to wait.
2. **Server Error (5xx)**: TMDB had a momentary glitch.
3. **Timeout**: The request took too long (often due to congestion).

You should **NOT** retry when:

1. **Not Found (404)**: It won't magically appear.
2. **Unauthorized (401)**: Your key is still wrong.
3. **Bad Request (400)**: Your logic is flawed.

---

## Recommended Tool: `tenacity`

While you can write `while` loops, we strongly recommend using the battle-tested [Tenacity](https://tenacity.readthedocs.io/) library.

It allows you to add retry logic decoratively.

```bash
pip install tenacity
```

### Basic Setup

```python
from tenacity import retry, stop_after_attempt, wait_fixed
from tmdbfusion import TMDBClient, ServerError

client = TMDBClient()

# Retry 3 times, waiting 2 seconds between attempts
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_robustly(movie_id):
    # This will raise ServerError if TMDB is down
    return client.movies.details(movie_id)
```

### Handling Rate Limits (Advanced)

`RateLimitError` usually comes with a specific wait time. We can teach Tenacity to respect that.

```python
from tenacity import retry, retry_if_exception_type, wait_exponential
from tmdbfusion.exceptions import RateLimitError, ServerError

# Retry on 5xx OR 429
@retry(
    retry=retry_if_exception_type((ServerError, RateLimitError)),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5)
)
def get_data_safe(mid):
    return client.movies.details(mid)
```

In this example, `wait_exponential` will wait 2s, 4s, 8s, 10s... giving the server breathing room.

---

## Manual Implementation

If you don't want extra dependencies, use a "Retry Loop".

```python
import time
from tmdbfusion.exceptions import RateLimitError, ServerError

def get_movie_with_retry(client, mid, max_retries=3):
    attempt = 0
    while attempt < max_retries:
        try:
            return client.movies.details(mid)
            
        except RateLimitError as e:
            wait = e.retry_after or (2 ** attempt)
            print(f"Rate limited. Sleeping {wait}s...")
            time.sleep(wait)
            attempt += 1
            
        except ServerError:
            print("Server error. Retrying...")
            time.sleep(1)
            attempt += 1
            
    raise Exception(f"Failed to fetch {mid} after {max_retries} attempts.")
```

---

## Async Retries

Tenacity also works natively with `async`/`await`!

```python
from tenacity import retry

class MyService:
    def __init__(self):
        self.client = AsyncTMDBClient()
        
    @retry(stop=stop_after_attempt(3))
    async def get_poster(self, mid):
        # Note: tenacity detects this is an async func
        movie = await self.client.movies.details(mid)
        return movie.poster_path
```

---

## Circuit Breakers

If you are running a high-traffic web service, retries can cause a "Thundering Herd" (DDOSing the server when it recovers).

Consider implementing a **Circuit Breaker** (using plugins like `pybreaker`).

- If 5 requests fail in a row, "Trip" the breaker.
- For the next 60 seconds, fail ALL requests instantly (don't even send them).
- After 60s, allow 1 test request through.

This protects both your app (from hanging threads) and TMDB (from overload).
