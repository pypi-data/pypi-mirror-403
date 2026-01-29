<!-- FILE: docs/concepts/sync-vs-async.md -->

# Sync vs Async: Making the Choice

TMDBFusion offers two complete clients: `TMDBClient` (Synchronous) and `AsyncTMDBClient` (Asynchronous). Choosing the right one is the most important architectural decision you will make when using this library.

This guide explains the difference, the trade-offs, and when to use each.

---

## Synchronous (Blocking)

The standard Python way. Simple, linear, easier to debug.

### How it works

When you call a function, your program **stops and waits** until the server responds.

```python
# 1. Send Request ... WAIT ...
movie = client.movies.details(550) 
# 2. Got Response. Continue.
print(movie.title)
```

### Pros

- **Simplicity**: No `await`, no `asyncio.run()`, no weird event loop errors.
- **Predictability**: Code executes exactly line-by-line.
- **Debugger Friendly**: Works perfectly with `pdb`.

### Cons

- **Inefficient for Bulk Data**: If fetching 100 movies takes 0.5s each, your script takes **50 seconds**. The CPU is idle for 49.9s of that time, just waiting for network packets.

### When to use Sync

- CLI scripts running locally.
- Data science notebooks (Jupyter/Colab).
- Cron jobs where execution time doesn't matter much.
- Simple web apps (Flask/Django) that use worker threads.

---

## Asynchronous (Non-Blocking)

The modern, high-performance way. Powered by Python's `asyncio`.

### How it works

When you call a function, you yield control back to the "Event Loop". The loop can do other work (like sending *another* request) while waiting for the first one.

```python
# 1. Send Request, but don't wait. Return a specific "Task" handle.
task = client.movies.details(550)

# 2. Yield control. Pause this function until response comes back.
movie = await task 

# 3. Resume.
print(movie.title)
```

The magic happens when you do multiple things at once:

```python
# Launch 100 requests INSTANTLY.
tasks = [client.movies.details(i) for i in ids]

# Wait for all of them. Total time ≈ time of slowest request (e.g., 0.6s).
movies = await asyncio.gather(*tasks)
```

### Pros

- **Massive Concurrency**: Fetch 100 movies in ~1-2 seconds instead of 50 seconds.
- **Resource Efficiency**: A single thread can handle thousands of connections.

### Cons

- **Complexity**: "Function color" problem. Async code must be called by other Async code.
- **Debugging**: Stack traces can be confusing.
- **Race Conditions**: You must be careful about shared state.

### When to use Async

- **FastAPI / Sanic / Quartz** web applications.
- **Discord Bots** (discord.py is async).
- **Scrapers / Crawlers** processing large datasets.
- **Real-time Dashboards**.

---

## Mixing Worlds

Can I use both? **Yes, but be careful.**

### Calling Async from Sync

If you have a sync codebase but want to speed up *one specific part*, you can wrap it:

```python
import asyncio

def get_movies_fast(ids):
    async def worker():
        async with AsyncTMDBClient() as client:
            tasks = [client.movies.details(i) for i in ids]
            return await asyncio.gather(*tasks)
            
    return asyncio.run(worker())
```

### Calling Sync from Async

**AVOID THIS**. Calling a blocking function (like `time.sleep` or `requests.get`) inside an async function **freezes the entire Event Loop**. No other tasks can run. This defeats the purpose of async.

If you absolutely must run blocking code in an async app, use a thread pool:

```python
await asyncio.to_thread(blocking_function, args)
```

---

## Performance Benchmark

*Scenario: Fetching details for 50 Movies.*

| Client | Code Style | Time (approx) | Explanation |
|:-------|:-----------|:--------------|:------------|
| **Sync** | Sequential Loop | ~25.0s | 50 * 0.5s latency |
| **Async** | Sequential Loop | ~25.0s | `await` inside loop is same as sync! |
| **Async** | `asyncio.gather` | **~0.8s** | Limited only by bandwidth/rate-limit |

> [!TIP]
> **Use Async for Bulk Operations.**
> If your application only makes 1 request at a time, Async offers no speed benefit over Sync. It only shines when you parallelize.

---

## Summary Recommendation

1. **Default to Sync**. If you don't *know* you need Async, stick to Sync. It's easier.
2. **Switch to Async** if performance becomes a bottleneck or you are integrating into an existing Async framework (like FastAPI).
3. **Never block the loop** when writing Async code.
