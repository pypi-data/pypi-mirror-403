<!-- FILE: docs/getting-started/quickstart.md -->

# Quickstart

Welcome to the fast lane. This guide will get you from zero to fetching live data in under 5 minutes.

We assume you have **[installed the library](installation.md)** and **[configured your API Key](authentication.md)**.

## Sync Example: Top Rated Movies

For scripts, data analysis, or simple applications, the synchronous client is the easiest way to start.

Create a file named `quickstart_sync.py`:

```python
from tmdbfusion import TMDBClient

def main():
    # 1. Initialize the Client
    # It automatically looks for TMDB_API_KEY in environment variables
    client = TMDBClient()

    print("--- Top Rated Movies ---")

    # 2. Fetch Requests
    # .top_rated() returns a paginated response object
    response = client.movies.top_rated(page=1)

    print(f"Total Results: {response.total_results:,}")
    print(f"Total Pages: {response.total_pages:,}\n")

    # 3. Access Data
    # The 'results' attribute contains a list of strongly-typed Movie objects
    for movie in response.results[:5]:
        print(f"Title: {movie.title}")
        print(f"Date:  {movie.release_date}")
        print(f"Rating: {movie.vote_average}")
        print(f"ID:    {movie.id}")
        print("-" * 30)

    # 4. Fetch Specific Details
    # Let's drill down into the first movie found
    first_movie_id = response.results[0].id
    details = client.movies.details(first_movie_id)

    print(f"\n--- Detailed Info for '{details.title}' ---")
    print(f"Tagline: {details.tagline}")
    print(f"Budget:  ${details.budget:,}")
    print(f"Revenue: ${details.revenue:,}")
    
    # Genres are a list of objects, not just strings
    genres = [g.name for g in details.genres]
    print(f"Genres:  {', '.join(genres)}")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python quickstart_sync.py
```

---

## Async Example: Concurrent Fetching

Accessing the API asynchronously allows you to fetch multiple resources at the same time, significantly speeding up your application.

Create a file named `quickstart_async.py`:

```python
import asyncio
from tmdbfusion import AsyncTMDBClient

async def fetch_movie_data():
    # 1. Context Manager
    # Ensures the HTTP session is closed properly when done
    async with AsyncTMDBClient() as client:
        
        print("--- Fetching Matrix Trilogy concurrently ---")
        
        # Matrix Message IDs (known beforehand)
        matrix_ids = [603, 604, 605]

        # 2. Create Tasks
        # We start all 3 requests at the exact same time
        tasks = [client.movies.details(mid) for mid in matrix_ids]

        # 3. Await All
        # asyncio.gather waits for all of them to finish
        movies = await asyncio.gather(*tasks)

        for movie in movies:
            print(f"Title: {movie.title}")
            print(f"Runtime: {movie.runtime} min")
            print("-" * 20)

        # 4. Search Example
        print("\n--- searching for 'Inception' ---")
        search_res = await client.search.multi_search(query="Inception")
        
        if search_res.results:
            top_hit = search_res.results[0]
            # Multi-search can return Movies, TV Shows, or People
            # We can check the media_type
            print(f"Top Result: {top_hit.media_type.upper()} - {getattr(top_hit, 'title', getattr(top_hit, 'name', 'Unknown'))}")

if __name__ == "__main__":
    asyncio.run(fetch_movie_data())
```

Run it:

```bash
python quickstart_async.py
```

---

## Key Concepts to Notice

### 1. Strongly Typed Objects

In the examples above, we accessed `movie.title`, not `movie["title"]`.
If you try to access `movie.tittle` (typo), your IDE or code will raise an `AttributeError` immediately. This saves countless hours of debugging.

### 2. Context Managers (`with` / `async with`)

We recommend using the client as a context manager.

- **Sync**: `client` *can* be used without `with`, but using it ensures connection pooling is managed safely.
- **Async**: `async with` is **highly recommended** to ensure the underlying `httpx.AsyncClient` is properly closed.

### 3. Namespace Organization

Everything is organized logically:

- `client.movies.*`
- `client.tv.*`
- `client.people.*`
- `client.search.*`

You don't need to remember URL paths, just the logical resource you want.

---

## Ready for more?

You have the basics. Now let's go deeper.

**[Understand the Architecture](../concepts/architecture.md)**  
**[Master Error Handling](../concepts/error-handling.md)**  
**[Browse the API Reference](../api/overview.md)**
