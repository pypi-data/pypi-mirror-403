<!-- FILE: docs/getting-started/authentication.md -->

# Authentication

To use the TMDB API, you must authenticate your requests. TMDBFusion handles the low-level details of header injection, but you are responsible for providing a valid credential.

## Obtaining Credentials

If you do not have an API Key yet:

1. **Create an Account**: Go to the [The Movie Database (TMDB)](https://www.themoviedb.org/) and sign up.
2. **Register an App**: Navigate to your [Account Settings > API](https://www.themoviedb.org/settings/api).
3. **Generate Key**: Click "Create" and follow the form. You will be given two types of credentials:
    - **API Key (v3 auth)**: A short alphanumeric string.
    - **API Read Access Token (v4 auth)**: A long JWT-like string starting with `eyJ...`.

**TMDBFusion supports both.** However, the **API Read Access Token (v4)** is recommended for new applications as it is more secure and granular.

---

## Best Practices: Environment Variables

**NEVER commit your API Key to version control (git).**

The most secure and industry-standard way to manage secrets is via environment variables. TMDBFusion is designed to look for the `TMDB_API_KEY` environment variable automatically if you do not provide one explicitly.

### Setting the Environment Variable

**Linux / macOS:**

```bash
export TMDB_API_KEY="your_api_read_access_token_here"
```

**Windows (PowerShell):**

```powershell
$env:TMDB_API_KEY="your_api_read_access_token_here"
```

**Using `.env` files:**
If you use `python-dotenv` or similar tools, add this to your `.env` file:

```ini
TMDB_API_KEY=your_api_read_access_token_here
```

---

## Programmatic Usage

You can also pass the key directly to the client constructor. This is useful for scripts traversing multiple keys or testing.

### Synchronous Client

```python
from tmdbfusion import TMDBClient

# Method 1: Explicit Key (NOT RECOMMENDED for production code)
client = TMDBClient(api_key="your_long_api_token")

# Method 2: Automatic Discovery (RECOMMENDED)
# Checks os.environ["TMDB_API_KEY"]
client = TMDBClient()
```

### Asynchronous Client

```python
from tmdbfusion import AsyncTMDBClient

async def main():
    # Method 1: Explicit Key
    async with AsyncTMDBClient(api_key="your_token") as client:
        pass

    # Method 2: Automatic Discovery
    async with AsyncTMDBClient() as client:
        pass
```

---

## Troubleshooting Authentication

### `AuthenticationError: Invalid API Key`

This specific exception is raised when TMDB returns a `401 Unauthorized`.

**Common Causes:**

1. **Copy-Paste Error**: You missed a character.
2. **Whitespace**: Start or end of the string has a space.
3. **Wrong Type**: You used the "API Key" string where a "Read Access Token" was expected, or vice versa. TMDBFusion accepts both, but ensure it's copied exactly.
4. **Environment**: You set the env var in one terminal but ran the script in another.

**Debugging Snippet:**

```python
import os
from tmdbfusion import TMDBClient, AuthenticationError

key = os.getenv("TMDB_API_KEY")
print(f"Key loaded: {key[:5]}...{key[-5:] if key else 'None'}")  # Don't print the whole key!

try:
    client = TMDBClient(api_key=key)
    # Simple call to verify auth
    client.movies.details(550)
    print("Authentication successful!")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

---

## User Session Authentication

Some advanced actions (like rating a movie or modifying a list) require a user to log in to your application via TMDB. This involves "Session IDs".

This process is distinct from the read-only API Key authentication described above.

1. **Request Token**: App requests a temp token.
2. **User Approval**: User is redirected to TMDB website to approve token.
3. **Session Creation**: App exchanges approved token for a `session_id`.

Once you have a `session_id`, you pass it to specific methods, not the client constructor.

```python
# Rating a movie requires an active user session
client.movies.add_rating(
    movie_id=550,
    rating=8.5,
    session_id="user_session_id_xyz"
)
```

See the **[Advanced Usage Guide](../guides/advanced-usage.md)** for a full OAuth flow walkthrough.
