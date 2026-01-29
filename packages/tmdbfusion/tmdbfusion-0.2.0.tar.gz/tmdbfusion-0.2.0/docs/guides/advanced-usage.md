<!-- FILE: docs/guides/advanced-usage.md -->

# Advanced Usage

Once you have mastered the basics, you can start using TMDBFusion's power features to optimize your application.

---

## Optimization: Append To Response

The single most impactful optimization you can make is using `append_to_response`. This TMDB feature allows you to attach sub-requests to a main request, saving network round-trips.

### The Problem

You want to show a movie page with:

1. Details
2. Credits (Cast)
3. Images
4. Similar Movies

**Naive Approach (4 Requests):**

```python
movie = client.movies.details(550)
credits = client.movies.credits(550)
images = client.movies.images(550)
similar = client.movies.similar(550)
```

*Latency: 4x (e.g., 2000ms)*

### The Solution (1 Request)

```python
movie = client.movies.details(
    550, 
    append_to_response="credits,images,similar"
)

# Now the data is attached to the movie object!
print(f"Cast Count: {len(movie.credits.cast)}")
print(f"Poster Count: {len(movie.images.posters)}")
print(f"First Similar: {movie.similar.results[0].title}")
```

*Latency: 1x (e.g., 500ms)*

Note: The attributes `credits`, `images`, etc. are optional on the `MovieDetails` model. They will be populated only if you request them.

---

## Image URL Builders

TMDB returns partial paths for images (e.g., `/pB8BM7r0p3dD8...jpg`). You need to combine this with a base URL and a size.

The client includes a helper namespace `client.images` to do this safely.

### Basic Generation

```python
path = movie.poster_path  # "/abc.jpg"

# Get default URL (Original size)
url = client.images.poster_url(path)
# https://image.tmdb.org/t/p/original/abc.jpg
```

### Custom Sizes

We provide strict constants so you don't guess invalid sizes (which result in broken images).

```python
from tmdbfusion.utils.images import ImageSize

# "w500" - Good for listing pages
url = client.images.poster_url(path, size=ImageSize.POSTER_LARGE)

# "w92" - Good for tiny thumbnails
tiny = client.images.poster_url(path, size=ImageSize.POSTER_SMALL)
```

### Supported Method

- `poster_url()`
- `backdrop_url()`
- `profile_url()` (for people)
- `still_url()` (for episodes)
- `logo_url()` (for networks/companies)

---

## Discover Presets

The `/discover/movie` and `/discover/tv` endpoints are powerful SQL-like query engines, but the parameters can be complex.

TMDBFusion includes a `DiscoverPresets` wrapper that implements common "recipes" for you.

### Initialization

```python
from tmdbfusion.utils.presets import DiscoverPresets

presets = DiscoverPresets(client)
```

### Recipes

#### 1. Hidden Gems

Highly rated movies with low vote counts (often overlooked).

```python
# Movies with > 7.0 rating but < 500 votes
gems = presets.hidden_gems(min_rating=7.0, max_votes=500)

for m in gems.results:
    print(f"{m.title} ({m.vote_average})")
```

#### 2. Theatrical Releases (Not digital)

Find movies currently in theatres or released recently.

```python
# Released in last 30 days
new_movies = presets.new_releases(days=30, region="US")
```

#### 3. Anime Series

Find Japanese animation.

```python
anime = presets.anime_series(sort="popularity")
```

#### 4. Streaming Search

What's on Netflix right now?

```python
# Provider ID 8 = Netflix
# Region US
netflix_hits = presets.streaming_on(8, region="US")
```

---

## Language & Region

Almost every method in TMDBFusion accepts `language` and `region` arguments, or respects a global default if configured.

### Per-Request

```python
# Get details in French
movie = client.movies.details(550, language="fr-FR")
print(movie.overview)  # "Le narrateur..."
```

### Fallbacks

If a translation is missing, TMDB usually falls back to English or an empty string. If you get empty strings, check the `translations` endpoint to see what languages are available for that specific item.

```python
trans = client.movies.translations(550)
available_codes = [t.iso_639_1 for t in trans.translations]
```
