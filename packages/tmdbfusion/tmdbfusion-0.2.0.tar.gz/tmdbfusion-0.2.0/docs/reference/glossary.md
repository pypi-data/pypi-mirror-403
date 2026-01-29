<!-- FILE: docs/reference/glossary.md -->

# Glossary

A definition of terms used in this documentation and the TMDB API.

### API Key (v3)

A 32-character alphanumeric string used for authentication. It is the legacy authentication method but still fully supported and widely used. It grants full access to public data but cannot access user-specific data without a session.

### Append To Response

A powerful TMDB API feature that allows you to request extra data (like credits, images, videos, similar movies) in the same HTTP call as the primary details. Crucial for performance as it reduces network round-trips (latency).

### Backdrop

A horizontal image associated with a movie or show, typically used as a background header in UI designs. The standard aspect ratio is 16:9.

### Blocking

Code that stops the execution of the entire program until a task (like a network request) is complete. In Python, standard functions are blocking.

### Context Manager

A Python object that defines runtime context (the `with` statement). In TMDBFusion, `with TMDBClient() as client:` ensures that the network connection pool is properly closed when the block exits.

### Discover

The search engine of TMDB. Unlike simple text search, Discover allows filtering by 30+ criteria (year, genre, cast, crew, certification, runtime, etc.) to build complex queries like "Action movies from the 90s with Brad Pitt".

### Guest Session

A temporary session ID that allows a user to rate movies without having a full TMDB account. Valid for 24 hours. Useful for kiosk applications or quick polls.

### Idempotency

A property of an operation where applying it multiple times has the same effect as applying it once. GET requests are idempotent. POST requests (like Rating) are generally not, though rating the same value twice is safe.

### ISO-3166-1

The international standard for 2-letter Country Codes (e.g., "US", "FR", "GB", "JP"). Used for the `region` parameter (release dates) and `watch_region` (streaming availability).

### ISO-639-1

The international standard for 2-letter Language Codes (e.g., "en", "fr", "ja", "de"). Used for the `language` parameter (metadata translation) and `include_image_language` (poster text localization).

### JWT (JSON Web Token)

The format used for the v4 "Read Access Token". It is a long, encoded string usually starting with `ey...`. It contains signed claims about the user's permissions.

### Non-Blocking

Code that allows other operations to run while it waits for a task to complete. This is the basis of Asynchronous programming (`asyncio`).

### Pagination

The practice of splitting a large list of results into pages (usually 20 items per page). To get all results, you must iterate through the pages.

### Person

An entity in the database usually representing a Cast or Crew member. Can be an Actor, Director, Writer, Producer, etc.

### Poster

A vertical image associated with a movie or show. The standard aspect ratio is 1:1.5. Used for grid views and lists.

### Rate Limit

A restriction on the number of API requests you can make in a given timeframe. TMDB typically allows ~40 requests per 10 seconds. Exceeding this triggers a 429 error.

### Read Access Token (v4)

The modern authentication credential. It allows for more granular scopes (though for this wrapper, it functions identically to the V3 Key). It is generally considered more secure.

### Semaphore

A concurrency primitive that limits the number of tasks that can run at the same time. If you have a list of 1000 items to fetch, a Semaphore(10) ensures only 10 requests happen at once, preventing Rate Limit errors.

### Session ID

An alphanumeric string representing an authenticated user. Required for "Write" actions like Rating or Editing Lists. Obtained via the 3-legged Auth Flow (Request Token -> User Approval -> Session ID).

### Slot (Python)

A memory optimization mechanism (`__slots__`) that prevents the creation of `__dict__` for each object instance. Used by `msgspec.Struct` to reduce RAM usage by up to 30% for small objects, which allows holding more results in memory.

### Struct (msgspec)

A high-performance C-struct-like object used for data models. Faster than `dataclass` and `pydantic`. Immutable by default, enforcing a "Read-Only" view of the API data.

### Sync / Async

- **Sync (Synchronous)**: Sequential execution. One line follows another. If a network call takes 5 seconds, the entire program freezes for 5 seconds. Easiest to reasoning about.
- **Async (Asynchronous)**: Concurrent execution. Tasks can yield control. If a network call takes 5 seconds, the CPU can do other work (like handling another request) while waiting.

### Thundering Herd

A problem where many retrying clients all hit the server at the exact same moment it recovers (e.g., after a rate limit window resets), causing it to crash again or trigger new limits. Solved by "Jitter" (randomizing wait times).

### TMDB (The Movie Database)

The community-built database that provides the API. It is the source of truth for the data TMDBFusion fetches. Not affiliated with IMDb (Amazon) or Xsyncio.

### Transport Layer

The low-level code responsible for byte-level I/O. In TMDBFusion, this is wrapped around `httpx`. It handles connection pooling, SSL/TLS negotiation, and raw HTTP parsing.

### User Agent

A string sent with every HTTP request identifying the client software. TMDBFusion sends `tmdbfusion/0.1.0/python`. This helps TMDB stats tracking and debugging.

### Watch Provider

A streaming service (Netflix, Hulu, Disney+) or rental store (iTunes, Amazon) where a movie/show can be watched legally. Data is provided to TMDB by JustWatch.

### Window (Time Window)

Used in Trending APIs to define the scope of popularity. Either "day" (last 24 hours) or "week" (last 7 days). "Week" is more stable, "Day" is more reactive.

### V3 vs V4

- **V3**: The primary REST API. 99% of endpoints (Movies, TV, People, Discover) are here. Uses `api_key` param.
- **V4**: A newer, experimental API mostly used for Lists and Auth. It uses a different ID format (ObjectId) for lists and `Authorization: Bearer` header (though Fusion uses Bearer for V3 too).
