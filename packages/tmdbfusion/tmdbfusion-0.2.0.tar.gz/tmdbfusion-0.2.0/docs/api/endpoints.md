<!-- FILE: docs/api/endpoints.md -->

# Endpoints Reference

TMDBFusion organizes endpoints into logical namespaces under the client.

e.g., `client.movies` maps to the `MoviesAPI` class.

---

## Core Resources

### `client.movies` (MoviesAPI)

Interacts with `/movie/*` endpoints.

- **`details(movie_id, append_to_response=None)`**: Get primary info.
- **`credits(movie_id)`**: Get cast and crew.
- **`images(movie_id)`**: Get posters and backdrops.
- **`videos(movie_id)`**: Get trailers and teasers.
- **`recommendations(movie_id, page=1)`**: Get recommended movies.
- **`similar(movie_id, page=1)`**: Get similar movies.
- **`reviews(movie_id, page=1)`**: Get user reviews.
- **`lists(movie_id, page=1)`**: Get lists containing this movie.
- **`popular(page=1)`**: Get current popular movies.
- **`top_rated(page=1)`**: Get all-time top rated.
- **`upcoming(page=1)`**: Get upcoming releases.
- **`now_playing(page=1)`**: Get movies in theaters.
- **`latest()`**: Get the most recently added movie ID.
- **`account_states(movie_id, session_id)`**: Check if user has rated/watchlist.
- **`add_rating(movie_id, rating, session_id)`**: Rate a movie (0.5-10).
- **`delete_rating(movie_id, session_id)`**: Remove rating.

### `client.tv` (TVAPI)

Interacts with `/tv/*`, `/tv/{id}/season/*`, and `/tv/{id}/season/{num}/episode/*`.

#### Series

- **`details(series_id, ...)`**: Get show details.
- **`aggregate_credits(series_id)`**: Get credits for entire run.
- **`reviews(series_id, page=1)`**: Get reviews.
- **`popular(page=1)`**: Get popular shows.
- **`top_rated(page=1)`**: Get top rated shows.
- **`on_the_air(page=1)`**: Get shows currently airing.
- **`airing_today(page=1)`**: Get episodes airing today.

#### Seasons

- **`season_details(series_id, season_number)`**: Get full season info.
- **`season_credits(series_id, season_number)`**: Get season-specific cast.
- **`season_images(series_id, season_number)`**: Get season posters.

#### Episodes

- **`episode_details(series_id, season_number, episode_number)`**: Get single episode.
- **`episode_credits(...)`**: Get guest stars and crew.
- **`episode_images(...)`**: Get stills.
- **`add_episode_rating(...)`**: Rate an episode.

### `client.people` (PeopleAPI)

Interacts with `/person/*`.

- **`details(person_id)`**: Get bio and info.
- **`movie_credits(person_id)`**: Get roles in movies.
- **`tv_credits(person_id)`**: Get roles in TV.
- **`combined_credits(person_id)`**: Get roles in both.
- **`images(person_id)`**: Get profile photos.
- **`popular(page=1)`**: Get currently popular people.

---

## Discovery & Search

### `client.search` (SearchAPI)

- **`multi_search(query, page=1)`**: Search Movies, TV, and People.
- **`movies(query, year=None, page=1)`**: Search movies.
- **`tv(query, first_air_date_year=None, page=1)`**: Search TV.
- **`people(query, page=1)`**: Search people.
- **`collections(query, page=1)`**: Search collections (franchises).
- **`companies(query, page=1)`**: Search production companies.
- **`keywords(query, page=1)`**: Search keywords.

### `client.discover` (DiscoverAPI)

The SQL-of-endpoints.

- **`movie(...)`**: Complex filter for movies.
  - `sort_by`: "popularity.desc", "revenue.desc", etc.
  - `with_genres`: "28,12".
  - `primary_release_year`: 2023.
  - `vote_average_gte`: 7.0.
- **`tv(...)`**: Complex filter for TV.

### `client.trending` (TrendingAPI)

- **`all(time_window="day"|"week")`**: Trending everything.
- **`movie(time_window)`**: Trending movies.
- **`tv(time_window)`**: Trending TV.
- **`person(time_window)`**: Trending people.

### `client.find` (FindAPI)

- **`by_id(external_id, external_source)`**: Find TMDB items by IMDB ID, TVDB ID, etc.

---

## Account & Auth

### `client.authentication` (AuthenticationAPI)

V3 Auth flow.

- **`create_guest_session()`**: Make a temp session.
- **`create_request_token()`**: Step 1 of login.
- **`create_session(request_token)`**: Step 3 of login.

### `client.account` (AccountAPI)

User account details.

- **`details(session_id)`**: Get user info.
- **`favorite_movies(account_id, session_id)`**: Get favorites.
- **`rated_movies(account_id, session_id)`**: Get rated items.
- **`watchlist_movies(account_id, session_id)`**: Get watchlist.
- **`add_to_watchlist(...)`**: Add/Remove items.
- **`mark_as_favorite(...)`**: Add/Remove items.

---

## Metadata Resources

### `client.configuration` (ConfigurationAPI)

- **`details()`**: Get image base URLs and change keys.
- **`countries()`**: Get valid country codes.
- **`languages()`**: Get valid language codes.
- **`jobs()`**: Get valid departments/jobs.

### `client.genres` (GenresAPI)

- **`movie_list()`**: Get movie genre IDs.
- **`tv_list()`**: Get TV genre IDs.

### `client.certifications` (CertificationsAPI)

- **`movie_list()`**: Get ratings (PG-13, R) per country.
- **`tv_list()`**: Get ratings (TV-MA) per country.

### `client.watch_providers` (WatchProvidersAPI)

- **`movie_list()`**: Get available streamers (Netflix, Hulu).
- **`tv_list()`**: Get available streamers.

---

## Components

### `client.collections` (CollectionsAPI)

Movie collections (e.g., Avengers Collection).

- **`details(collection_id)`**: Get parts.
- **`images(collection_id)`**: Get art.

### `client.companies` (CompaniesAPI)

- **`details(company_id)`**: Get info.

### `client.networks` (NetworksAPI)

- **`details(network_id)`**: Get info (e.g., HBO).

### `client.keywords` (KeywordsAPI)

- **`details(keyword_id)`**: Get info.

### `client.reviews` (ReviewsAPI)

- **`details(review_id)`**: Get full text of a specific review.
