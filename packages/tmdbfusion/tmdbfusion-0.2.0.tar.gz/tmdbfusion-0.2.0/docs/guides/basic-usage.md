<!-- FILE: docs/guides/basic-usage.md -->

# Basic Usage

This guide covers the 80% use case: fetching movies, TV shows, and people.

We will use `TMDBClient` (Sync) for these examples, but every method exists on `AsyncTMDBClient` as well (just `await` them).

---

## Movies

The `client.movies` namespace maps to `/movie/*` endpoints.

### Get Movie Details

The most common operation.

```python
movie = client.movies.details(550)  # Fight Club

print(f"Title: {movie.title}")
print(f"Overview: {movie.overview}")
print(f"Budget: ${movie.budget:,}")
```

### Browse Lists

TMDB maintains standard lists like "Popular", "Top Rated", "Upcoming".

```python
# Get the first page of popular movies
popular = client.movies.popular(page=1)

for m in popular.results:
    print(f"#{m.id} {m.title}")
```

### Get Credits (Cast & Crew)

```python
credits = client.movies.credits(550)

# Cast: The actors
for actor in credits.cast[:3]:
    print(f"Character: {actor.character} | Actor: {actor.name}")

# Crew: The production team
director = next((c for c in credits.crew if c.job == "Director"), None)
if director:
    print(f"Directed by: {director.name}")
```

---

## TV Shows

The `client.tv` namespace handles metadata for Series, Seasons, and Episodes.

### Get Series Details

```python
show = client.tv.details(1399)  # Game of Thrones

print(f"Name: {show.name}")
print(f"Total Seasons: {show.number_of_seasons}")
```

### Get Season Details

To get specific episodes, you must fetch the season.

```python
# Game of Thrones, Season 1
season = client.tv.season_details(series_id=1399, season_number=1)

for episode in season.episodes:
    print(f"E{episode.episode_number}: {episode.name} ({episode.air_date})")
```

### Get Episode Details

Drill down to a specific episode.

```python
episode = client.tv.episode_details(
    series_id=1399, 
    season_number=1, 
    episode_number=1
)
print(f"Director: {episode.crew[0].name}")
```

---

## People

The `client.people` namespace handles Actors, Directors, and other crew.

### Get Person Details

```python
person = client.people.details(287)  # Brad Pitt

print(f"Name: {person.name}")
print(f"Birthday: {person.birthday}")
print(f"Place of Birth: {person.place_of_birth}")
```

### Get Combined Credits

What else have they worked on?

```python
credits = client.people.combined_credits(287)

# Sort by release date (descending)
works = sorted(
    credits.cast, 
    key=lambda x: x.release_date or "0000-00-00", 
    reverse=True
)

for work in works[:5]:
    # 'title' for movies, 'name' for TV
    title = getattr(work, 'title', getattr(work, 'name', 'Unknown'))
    print(f"{work.media_type.upper()}: {title}")
```

---

## Search

The `client.search` namespace is robust.

### Multi-Search (Recommended)

Searches Movies, TV, and People simultaneously. Best for "Global Search" bars.

```python
results = client.search.multi_search(query="The Matrix")

for res in results.results:
    if res.media_type == "movie":
        print(f"Movie: {res.title}")
    elif res.media_type == "tv":
        print(f"Show: {res.name}")
    elif res.media_type == "person":
        print(f"Person: {res.name}")
```

### Specific Search

```python
# Only movies
movies = client.search.movies(query="The Matrix", year=1999)

# Only people
people = client.search.people(query="Keanu")
```

---

## Common Patterns

### Handling Missing Data

TMDB data is community-edited. Fields can be `None`.

```python
# BAD
print("Budget: " + str(movie.budget))

# GOOD
budget = movie.budget if movie.budget else 0
print(f"Budget: ${budget:,}")

# BETTER
# The Type Checker knows 'release_date' can be None
if movie.release_date:
    year = movie.release_date.split("-")[0]
else:
    year = "Unknown"
```

### Iterating All Pages

Use a loop to fetch multiple pages of results.

```python
all_results = []
for page in range(1, 4):  # Fetch pages 1, 2, 3
    res = client.search.movies(query="Batman", page=page)
    all_results.extend(res.results)
    
    if page >= res.total_pages:
        break
```
