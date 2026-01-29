<!-- FILE: docs/api/models.md -->

# Models Reference

TMDBFusion assumes a schema-first approach. All API responses are parsed into `msgspec.Struct` objects.

These models are stricter than dictionaries and use less memory.

## Core Properties

All models:

- Are **immutable** (frozen).
- Are **type-checked** at runtime during parsing.
- Support standard `__repr__` for clear debugging.
- Do NOT allow dynamic attribute assignment (slots).

---

## Key Models

### `MovieDetails`

Represents the full detail of a movie.

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | `int` | Unique Movie ID. |
| `title` | `str` | Title in requested language. |
| `overview` | `str` | Plot summary. |
| `release_date` | `str | None` | ISO-8601 date. |
| `vote_average` | `float` | Rating (0-10). |
| `genres` | `list[Genre]` | List of genres. |
| `credits` | `Credits | None` | (Optional) If appended. |
| `images` | `ImagesResponse | None` | (Optional) If appended. |

### `TVShowDetails`

Represents the full detail of a TV Show.

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | `int` | Unique Show ID. |
| `name` | `str` | Show name. |
| `number_of_seasons` | `int` | Season count. |
| `seasons` | `list[Season]` | Summary of seasons. |

### `PersonDetails`

Represents a Person (Actor/Crew).

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | `int` | Unique Person ID. |
| `name` | `str` | Full name. |
| `biography` | `str` | Text bio. |
| `known_for_department` | `str` | e.g. "Acting". |

---

## Sub-Models

### `Genre`

```python
class Genre(Struct):
    id: int
    name: str  # "Action", "Comedy"
```

### `ProductionCompany`

```python
class ProductionCompany(Struct):
    id: int
    name: str
    logo_path: str | None
    origin_country: str
```

### `credits.Cast`

A cast member in a movie or show.

```python
class Cast(Struct):
    id: int
    name: str
    character: str
    order: int  # Billing order
    profile_path: str | None
```

### `credits.Crew`

A crew member.

```python
class Crew(Struct):
    id: int
    name: str
    job: str  # "Director", "Writer"
    department: str
```

---

## Response Wrappers

Most "List" endpoints return a paginated wrapper.

### `PaginatedResponse[T]`

Where `T` is the item type (e.g., `Movie`).

| Field | Type | Description |
|:------|:-----|:------------|
| `page` | `int` | Current page number. |
| `total_pages` | `int` | Global total pages. |
| `total_results` | `int` | Global total items. |
| `results` | `list[T]` | The list of items. |

---

## Validation & Null Safety

TMDB data is notoriously "gappy". The models handle this by marking fields as `Optional` (`| None`).

**Example:**
A movie might not have a `poster_path`.

```python
# poster_path is str | None
if movie.poster_path:
    # safe to use
    url = client.images.poster_url(movie.poster_path)
```

However, fields that are guaranteed by the API (like `id`) are strictly typed as `int` and will never be None.
