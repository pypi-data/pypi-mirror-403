<!-- FILE: docs/guides/testing-and-mocking.md -->

# Testing and Mocking

When writing automated tests for your application, you should **not** make real API calls to TMDB.

- It is slow.
- It is flaky (network issues).
- It consumes your rate limit.
- Data changes (a movie title might be updated, breaking your assertion).

Instead, you should **Mock** the client or the network.

---

## 1. Mocking the Client (Easy)

The simplest approach is to replace the `TMDBClient` methods with fake return values. This is great for unit testing *your* logic.

We use Python's standard `unittest.mock`.

```python
from unittest.mock import Mock, patch
from tmdbfusion.models.movie import MovieDetails

def test_my_movie_logic():
    # 1. Create a fake movie object
    # Note: We can instantiate Models manually!
    fake_movie = MovieDetails(id=1, title="Test Movie", overview="...")
    
    # 2. Patch the client
    with patch('tmdbfusion.TMDBClient') as MockClientClass:
        # Configure the mock to return our fake movie
        mock_instance = MockClientClass.return_value
        mock_instance.movies.details.return_value = fake_movie
        
        # 3. Run YOUR code
        result = my_function_that_uses_client(mock_instance)
        
        # 4. Assert
        assert result == "Test Movie"
        mock_instance.movies.details.assert_called_with(1)
```

**Pros**: Fast, no external libs.
**Cons**: You assume `client.movies.details` works locally. You aren't testing serialization.

---

## 2. Mocking the Network (`respx`)

Since specific TMDBFusion clients are built on `httpx`, the best tool for network mocking is [`respx`](https://lundberg.github.io/respx/).

It intercepts the HTTP request at the socket level. This allows you to test:

- Parsing logic (can we handle this JSON?).
- Error handling (what if we get a 404?).

### Setup

```bash
pip install respx
```

### Testing Sync Client

```python
import respx
from httpx import Response
from tmdbfusion import TMDBClient

@respx.mock
def test_sync_fetching():
    # 1. Define the Rule
    # "If anyone GETs /movie/550, return this JSON"
    route = respx.get("https://api.themoviedb.org/3/movie/550").mock(
        return_value=Response(200, json={"id": 550, "title": "Mock Club"})
    )
    
    client = TMDBClient(api_key="test")
    movie = client.movies.details(550)
    
    assert movie.title == "Mock Club"
    assert route.called
```

### Testing Async Client

```python
import pytest
import respx
from httpx import Response
from tmdbfusion import AsyncTMDBClient

@pytest.mark.asyncio
@respx.mock
async def test_async_fetching():
    respx.get("https://api.themoviedb.org/3/movie/550").mock(
        return_value=Response(200, json={"id": 550, "title": "Async Club"})
    )
    
    async with AsyncTMDBClient(api_key="test") as client:
        movie = await client.movies.details(550)
        
        assert movie.title == "Async Club"
```

---

## 3. Testing Error Handling

You want to make sure your app survives a 500 error.

```python
@respx.mock
def test_server_error_handling():
    # Simulate a crash
    respx.get("https://api.themoviedb.org/3/movie/550").mock(
        return_value=Response(500)
    )
    
    client = TMDBClient(api_key="test")
    
    try:
        client.movies.details(550)
        assert False, "Should have raised exception"
    except TMDBError as e:
        assert isinstance(e, ServerError)
```

---

## Using Fixtures

Tests are cleaner if you separate the JSON data.

1. Create a folder `tests/fixtures/`.
2. Save a real TMDB response as `movie_550.json`.

```python
import json

def load_fixture(filename):
    with open(f"tests/fixtures/{filename}") as f:
        return json.load(f)

@respx.mock
def test_with_fixture():
    data = load_fixture("movie_550.json")
    
    respx.get("https://api.themoviedb.org/3/movie/550").mock(
        return_value=Response(200, json=data)
    )
    
    client = TMDBClient(api_key="test")
    movie = client.movies.details(550)
    
    # Now you are testing against a real-world data shape!
    assert movie.production_companies[0].name == "20th Century Fox"
```
