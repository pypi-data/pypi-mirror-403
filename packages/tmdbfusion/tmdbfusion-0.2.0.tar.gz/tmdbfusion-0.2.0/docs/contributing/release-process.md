<!-- FILE: docs/contributing/release-process.md -->

# Release Process

This document describes how to cut a new release of `tmdbfusion`.

We use **Semantic Versioning** (SemVer).

---

## Changelog Management

We use `towncrier` to manage the changelog.

### Adding a Change

When you submit a PR, add a "news fragment" file in `changes/`.
The filename format is `<issue_number>.<type>`.

Types:

- `.feature`: New feature.
- `.bugfix`: Bug fix.
- `.doc`: Documentation improvement.
- `.removal`: Deprecation or removal.
- `.misc`: Internal details.

**Example**:
`changes/123.feature`:

```
Added support for the V4 List API.
```

---

## Cut a Release

Only maintainers can perform a release.

### 1. Bump Version

We use `bump-my-version` to handle versioning across files (`pyproject.toml`, `__init__.py`).

```bash
# For a patch (0.1.0 -> 0.1.1)
bump-my-version bump patch

# For a minor (0.1.0 -> 0.2.0)
bump-my-version bump minor
```

This command will:

1. Update version strings.
2. Run `towncrier` to compile `changes/*` into `CHANGELOG.md`.
3. Create a git commit and tag.

### 2. Push

```bash
git push origin main --tags
```

### 3. CI/CD

GitHub Actions will detect the tag and:

1. Build the wheel and sdist.
2. Publish to PyPI.
3. Build and deploy documentation to GitHub Pages.

---

## Post-Release Verification

1. Check PyPI: <https://pypi.org/project/tmdbfusion/>
2. Check Docs: <https://xsyncio.github.io/tmdbfusion/>
3. Verify `pip install --upgrade tmdbfusion` works.
