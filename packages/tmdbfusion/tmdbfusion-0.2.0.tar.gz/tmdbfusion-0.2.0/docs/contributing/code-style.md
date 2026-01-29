<!-- FILE: docs/contributing/code-style.md -->

# Code Style

TMDBFusion enforces **extremely strict** code quality standards. This ensures the codebase remains maintainable, readable, and bug-free as it scales to thousands of lines.

---

## Linter & Formatter: Ruff

We use `ruff` for both linting and formatting. It replaces Black, Isort, Flake8, and Pylint.

### Configuration

- **Line Length**: 120 characters.
- **Quote Style**: Double quotes (`"`).
- **Indent**: 4 spaces.

### Strict Rules (`ALL`)

We enable almost ALL Ruff rules, including:

- `ANN`: Missing type annotations (even for `self` return types).
- `D`: Docstring style (NumPy).
- `SIM`: Code simplification suggestions.
- `PL`: Pylint refactoring rules.

You do not need to memorize them. Just run:

```bash
ruff check --fix .
ruff format .
```

---

## Type Checking: MyPy

We use `mypy` in **Strict Mode**.

- **No `Any`**: You cannot use `Any` unless absolutely necessary (and it requires a `# type: ignore[misc]` comment with justification).
- **No Untyped Defs**: Every function, including tests, must have types.
- **No Implicit Optional**: `x: str = None` is banned. Use `x: str | None = None`.

### Msgspec Structs

When defining new models, always use `msgspec.Struct` instead of `dataclass` or `pydantic.BaseModel`.

```python
import msgspec

# GOOD
class Movie(msgspec.Struct):
    id: int
    title: str

# BAD
@dataclass
class Movie: ...
```

---

## Docstrings

We use the **NumPy** docstring standard.

Every public module, class, method, and function **MUST** have a docstring.

### Format

```python
def fetch_data(id: int) -> dict:
    """Short summary (one line).
    
    Extended description if needed.
    
    Parameters
    ----------
    id : int
        The resource identifier.
        
    Returns
    -------
    dict
        The data blob.
        
    Raises
    ------
    NotFoundError
        If ID is missing.
    """
```

---

## Architecture Rules

1. **No Logic in Models**: Models should be dumb data containers.
2. **No I/O in Resources**: Resource classes (e.g., `MoviesAPI`) should not import `httpx`. They delegate to `self._client`.
3. **Async Parity**: If you add a feature to `TMDBClient`, you **MUST** add it to `AsyncTMDBClient`.

---

## forbidden Patterns

- **`print()`**: Use `logging`.
- **`import json`**: Use `msgspec.json`.
- **`requests`**: Use `httpx` (even for sync).
- **`from module import *`**: Explicit imports only.

---

## Good Code Examples

### Early Returns

Don't nest deep `if` statements.

```python
# BAD
if movie:
    if movie.release_date:
        return movie.release_date
    else:
        return None
else:
    raise Exception()

# GOOD
if not movie:
    raise Exception()
    
if not movie.release_date:
    return None
    
return movie.release_date
```

### Context Managers

Always use context managers for resources.

```python
# FATAL
f = open("file.txt")
f.write("data")
# if crash here, file handles leak

# CORRECT
with open("file.txt", "w") as f:
    f.write("data")
```

### Explicit Types

Never leave the reader guessing.

```python
# LAZY
def process(items):
    for x in items:
        x.do()

# STRICT
def process(items: list[Task]) -> None:
    for task in items:
        task.run()
```
