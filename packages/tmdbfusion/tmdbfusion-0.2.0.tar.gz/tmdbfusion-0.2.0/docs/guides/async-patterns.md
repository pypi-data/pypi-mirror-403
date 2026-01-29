<!-- FILE: docs/guides/async-patterns.md -->

# Async Patterns

The `AsyncTMDBClient` unlocks the full potential of high-performance applications. However, "Async" is more than just adding `await` keywords.

This guide explores common patterns for managing concurrency effectively.

---

## Pattern 1: The Batch Gather

**Use Case**: You have a list of items and want them all NOW.

This is the Bread-and-Butter of async.

```python
import asyncio
from tmdbfusion import AsyncTMDBClient

async def get_movies(movie_ids):
    async with AsyncTMDBClient() as client:
        # 1. Create Coroutines (Tasks)
        tasks = [client.movies.details(mid) for mid in movie_ids]
        
        # 2. Fire them all at once
        # returns results in same order as inputs
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for mid, result in zip(movie_ids, results):
            if isinstance(result, Exception):
                print(f"Failed to get {mid}: {result}")
            else:
                print(f"Got {result.title}")
```

**Warning**: With `gather`, one failure *can* crash the whole batch unless you set `return_exceptions=True`.

---

## Pattern 2: The Stream (as_completed)

**Use Case**: You want to process results *as soon as they arrive*, without waiting for the slowest one.

```python
async def process_stream(movie_ids):
    async with AsyncTMDBClient() as client:
        tasks = [client.movies.details(mid) for mid in movie_ids]
        
        # Returns an internal iterator that yields tasks as they finish
        for future in asyncio.as_completed(tasks):
            try:
                movie = await future
                print(f"just finished: {movie.title}")
                # Save to DB immediately...
            except Exception as e:
                print(f"One failed: {e}")
```

This makes your application feel much more responsive.

---

## Pattern 3: The Bounded Worker (Semaphore)

**Use Case**: You have 10,000 items. `gather` would kill the API. You need a "Worker Pool".

```python
async def fetch_bounded(ids, limit=20):
    sem = asyncio.Semaphore(limit)
    
    async with AsyncTMDBClient() as client:
        
        async def worker(mid):
            async with sem:  # Wait here if 20 requests are active
                print(f"Fetching {mid}...")
                return await client.movies.details(mid)
        
        tasks = [worker(mid) for mid in ids]
        return await asyncio.gather(*tasks)
```

---

## Pattern 4: The Producer-Consumer Queue

**Use Case**: A complex crawler. You find movies, then for each movie, you find 5 actors, then for each actor...

Using a `Queue` allows you to dynamically add work while running.

```python
async def crawler_worker(name, queue, client):
    while True:
        # Get a "unit of work"
        movie_id = await queue.get()
        
        try:
            print(f"Worker {name} processing {movie_id}")
            # Fetch details
            movie = await client.movies.details(movie_id)
            
            # Logic: If it's a Marvel movie, add related movies to queue
            if "Marvel" in movie.title:
                similar = await client.movies.similar(movie_id)
                for sim in similar.results[:3]:
                    await queue.put(sim.id)
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Mark work as done
            queue.task_done()

async def run_crawler():
    queue = asyncio.Queue()
    
    # Seed the queue
    await queue.put(550) # Fight Club
    
    async with AsyncTMDBClient() as client:
        # Create 3 workers
        workers = [
            asyncio.create_task(crawler_worker(f"W-{i}", queue, client))
            for i in range(3)
        ]
        
        # Wait until queue is empty (processed)
        await queue.join()
        
        # Cancel workers (they are stuck in while True)
        for w in workers:
            w.cancel()
```

---

## Anti-Patterns to Avoid

### 1. Sequential Await in Loop

```python
# SLOW: This is effectively Synchronous code
for mid in ids:
    await client.movies.details(mid)
```

### 2. Blocking the Loop

```python
import time
async def bad_worker():
    # KILLS PERFORMANCE
    time.sleep(1) 
    await client.movies.details(550)
```

Always use `await asyncio.sleep(1)`.

### 3. Fire and Forget

```python
# DANGEROUS: You have no way to catch errors
asyncio.create_task(client.movies.details(550))
```

Always keep a reference to your tasks so you can await them or check for exceptions.
