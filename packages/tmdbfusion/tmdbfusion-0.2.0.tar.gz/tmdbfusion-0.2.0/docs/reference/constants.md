<!-- FILE: docs/reference/constants.md -->

# Constants

TMDBFusion exposes several classes of constants to help you avoid "magic strings" and "magic numbers".

These are available in `tmdbfusion.utils`.

---

## `tmdbfusion.utils.images`

### `ImageSize`

Standard sizes for image URL generation. Using these constants prevents 404s caused by guessing invalid sizes.

#### Posters

- `POSTER_SMALL` ("w185"): Best for mobile list views.
- `POSTER_MEDIUM` ("w342"): Best for tablet/desktop list views.
- `POSTER_LARGE` ("w500"): Best for details pages.
- `POSTER_XLARGE` ("w780"): Best for high-DPI displays.
- `POSTER_ORIGINAL` ("original"): The raw upload (often 2000px+). Warning: Large payload size.

#### Backdrops

- `BACKDROP_SMALL` ("w300"): Very small, rarely used.
- `BACKDROP_MEDIUM` ("w780"): Standard hero image.
- `BACKDROP_LARGE` ("w1280"): Full HD hero image.
- `BACKDROP_ORIGINAL` ("original"): 4K+ potentially.

#### Profiles (People)

- `PROFILE_SMALL` ("w45"): Tiny avatar.
- `PROFILE_MEDIUM` ("w185"): Standard card size.
- `PROFILE_LARGE` ("h632"): High-res portrait.
- `PROFILE_ORIGINAL` ("original"): Raw upload.

---

## `tmdbfusion.utils.presets`

### `GenreIds`

Mapping of standard Genre Names to their Integer IDs (V3).

#### Movie Genres

| Name | ID | Description |
|:-----|:---|:------------|
| `ACTION` | 28 | Action movies (fights, chases). |
| `ADVENTURE` | 12 | Adventure movies (travel, quests). |
| `ANIMATION` | 16 | Animated feature films. |
| `COMEDY` | 35 | Humorous movies. |
| `CRIME` | 80 | Gangster, detective, noir. |
| `DOCUMENTARY` | 99 | Non-fiction films. |
| `DRAMA` | 18 | Serious narrative films. |
| `FAMILY` | 10751 | Child-friendly. |
| `FANTASY` | 14 | Magic, supernatural. |
| `HISTORY` | 36 | Historical events. |
| `HORROR` | 27 | Scary movies. |
| `MUSIC` | 10402 | Musicals. |
| `MYSTERY` | 9648 | Whodunit. |
| `ROMANCE` | 10749 | Love stories. |
| `SCIFI` | 878 | Science Fiction. |
| `TV_MOVIE` | 10770 | Made for TV. |
| `THRILLER` | 53 | Suspense. |
| `WAR` | 10752 | Military conflict. |
| `WESTERN` | 37 | American West. |

#### TV Genres

| Name | ID | Description |
|:-----|:---|:------------|
| `TV_ACTION` | 10759 | Action & Adventure. |
| `TV_ANIMATION` | 16 | Animation (Same as Movie). |
| `TV_COMEDY` | 35 | Comedy (Same as Movie). |
| `TV_CRIME` | 80 | Crime (Same as Movie). |
| `TV_DOCUMENTARY` | 99 | Documentary (Same as Movie). |
| `TV_DRAMA` | 18 | Drama (Same as Movie). |
| `TV_FAMILY` | 10751 | Family. |
| `TV_KIDS` | 10762 | Content strictly for kids. |
| `TV_MYSTERY` | 9648 | Mystery. |
| `TV_NEWS` | 10763 | News programs. |
| `TV_REALITY` | 10764 | Reality TV. |
| `TV_SCIFI` | 10765 | Sci-Fi & Fantasy. |
| `TV_SOAP` | 10766 | Soap Operas. |
| `TV_TALK` | 10767 | Talk Shows. |
| `TV_WAR` | 10768 | War & Politics. |
| `TV_WESTERN` | 37 | Western. |

### Usage Example

```python
from tmdbfusion.utils.presets import GenreIds

# Get all action movies
client.discover.movie(with_genres=str(GenreIds.ACTION))

# Get Action OR Comedy (Comma)
client.discover.movie(with_genres=f"{GenreIds.ACTION},{GenreIds.COMEDY}")

# Get Action AND Comedy (Pipe - verify API support for AND logic, usually implicit)
# TMDB API semantics: Comma = OR (Union), Pipe = AND (Intersection) usually, check API docs
```

---

## `tmdbfusion.core.client`

### Default Settings

The client comes with sane defaults that you can override if necessary.

- `DEFAULT_API_VERSION`: "3"
- `DEFAULT_BASE_URL`: "<https://api.themoviedb.org/3>"
- `DEFAULT_TIMEOUT`: 5.0 (Connect), 30.0 (Read). This is generous enough for most endpoints but strict enough to fail fast on hangs.
- `MAX_RETRIES`: 0. By default, the library does not retry. It raises exceptions so you can decide the retry policy (using Tenacity).

### Headers

Every request includes these headers:

- `Authorization`: `Bearer <token>`
- `User-Agent`: `tmdbfusion/0.1.0 (Python)`
- `Accept`: `application/json`
- `Content-Type`: `application/json` (for POST/PUT)
