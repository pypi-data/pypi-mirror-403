"""Integration tests for client flows."""

import pytest
import respx
import httpx
from tmdbfusion import TMDBClient, AsyncTMDBClient

MOVIE_ID = 550
MOVIE_URL = f"https://api.themoviedb.org/3/movie/{MOVIE_ID}"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"


def test_movie_details_flow(tmdb_client: TMDBClient, respx_mock: respx.MockRouter):
    """Test fetching movie details."""
    respx_mock.get(MOVIE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": MOVIE_ID,
                "title": "Fight Club",
                "overview": "An insomniac office worker...",
                "release_date": "1999-10-15",
                "vote_average": 8.4,
                "vote_count": 20000,
            },
        )
    )

    movie = tmdb_client.movies.details(MOVIE_ID)

    assert movie.id == MOVIE_ID
    assert movie.title == "Fight Club"
    assert movie.vote_average == 8.4


@pytest.mark.asyncio
async def test_search_and_pagination_flow(
    async_tmdb_client: AsyncTMDBClient, respx_mock: respx.MockRouter
):
    """Test searching and iterating through results."""
    # Page 1
    respx_mock.get(SEARCH_URL, params={"query": "Matrix", "page": "1"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "page": 1,
                "total_pages": 2,
                "total_results": 2,
                "results": [{"id": 1, "title": "The Matrix"}],
            },
        )
    )
    # Page 2
    respx_mock.get(SEARCH_URL, params={"query": "Matrix", "page": "2"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "page": 2,
                "total_pages": 2,
                "total_results": 2,
                "results": [{"id": 2, "title": "The Matrix Reloaded"}],
            },
        )
    )

    results = []
    iterator = async_tmdb_client.paginate(
        async_tmdb_client.search.movie, query="Matrix"
    )
    async for movie in iterator:
        results.append(movie)

    assert len(results) == 2
    assert results[0].title == "The Matrix"
    assert results[1].title == "The Matrix Reloaded"
