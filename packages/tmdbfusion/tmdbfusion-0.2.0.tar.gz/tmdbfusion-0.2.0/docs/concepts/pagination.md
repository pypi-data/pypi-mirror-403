<!-- FILE: docs/concepts/pagination.md -->

# Pagination

The TMDB API often limits results to 20 items per page. When a resource like "Popular Movies" has 10,000 pages, efficient retrieval is key.

TMDBFusion offers two ways to handle this: **Manual Paging** (Raw Control) and **Iterators** (The Easy Way).

---

## The Underlying Concept

Most "List" endpoints return a `PaginatedResponse` generic structure:

```python
class PaginatedResponse(Struct):
    page: int
    total_pages: int
    total_results: int
    results: list[T]  # T is Movie, Person, TVShow, etc.
```

When you call `client.movies.popular()`, you are implicitly asking for `page=1`.

---

## Approach 1: Manual Paging

Use this when you need precise control, like building a UI with "Next >" buttons.

```python
# 1. Fetch Page 1
response = client.movies.popular(page=1)
process_results(response.results)

# 2. Check if there is a Page 2
if response.page < response.total_pages:
    # 3. Fetch Page 2
    next_response = client.movies.popular(page=2)
    process_results(next_response.results)
```

### Pros

- Exact control over when network requests happen.
- Suitable for stateless web handlers (e.g., user is on `?page=5`).

### Cons

- Boilerplate code.
- Annoying `while` loops for bulk fetching.

---

## Approach 2: Smart Iterators (Recommended)

When you just want "All Popular Movies" or "The Top 100", use the built-in iterator support.

**Wait, what iterator?**
The client doesn't return an iterator directly (to keep the API simple). But the Python ecosystem allows us to iterate easily.

*Correction*: TMDBFusion v1 (current) returns the `PaginatedResponse` directly. To iterate automatically, you would write a helper or use the upcoming v2 Iterator feature.

**Current Best Practice Implementation:**

Since the library returns a raw Response object (to remain unopinionated), standard Python loops are your friend.

```python
def get_all_movies(max_pages=5):
    all_movies = []
    current_page = 1
    
    while current_page <= max_pages:
        response = client.movies.popular(page=current_page)
        all_movies.extend(response.results)
        
        if current_page >= response.total_pages:
            break
            
        current_page += 1
        
    return all_movies
```

> [!NOTE]
> Future versions of TMDBFusion may include a `client.paginate(client.movies.popular)` helper. For now, we prefer explicit loops so you don't accidentally fetch 10,000 pages (API Limit risk).

---

## Async Pagination

In Async, you can fetch pages **in parallel**. This is much faster than sequential iteration.

**The "Batch Fetch" Pattern:**

If you know you want pages 1 through 10, don't wait for page 1 to finish before asking for page 2.

```python
async def fetch_top_10_pages():
    async with AsyncTMDBClient() as client:
        # Create 10 tasks instantly
        tasks = [client.movies.popular(page=i) for i in range(1, 11)]
        
        # Wait for all
        responses = await asyncio.gather(*tasks)
        
        # Flatten results
        all_movies = []
        for res in responses:
            all_movies.extend(res.results)
            
        print(f"Fetched {len(all_movies)} movies!")
```

**Warning**: Do not try this with `range(1, 1000)`. You will hit the rate limit immediately. Use a semaphore or batching logic (see [Rate Limiting](rate-limiting.md)).

---

## Limits

TMDB strictly limits most lists to **500 Pages máximo**. Even if `total_pages` says 35,000, asking for `page=501` will often return an error or valid-but-clamped data.

- **Check `total_pages`**: Always respect the API's reported limit.
- **Max Page 500**: Generally, don't try to go beyond page 500 (~10,000 items).

---

## Search Results

The same logic applies to search.

```python
# Find "Star Wars"
res = client.search.movies(query="Star Wars", page=1)

print(f"Found {res.total_results} matches.")

# Get page 2
if res.total_pages > 1:
    res2 = client.search.movies(query="Star Wars", page=2)
```
