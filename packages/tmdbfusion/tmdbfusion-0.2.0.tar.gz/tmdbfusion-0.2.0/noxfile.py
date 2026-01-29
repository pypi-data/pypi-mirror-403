import nox


@nox.session
def lint(session) -> None:
    session.install("ruff", "numpydoc", "deptry")
    session.install("-e", ".")
    session.run("ruff", "check", "tmdbfusion")
    session.run("python", "scripts/validate_docs.py")
    session.run("deptry", "tmdbfusion")


@nox.session
def tests(session) -> None:
    session.install("pytest", "pytest-cov", "msgspec", "httpx")
    session.install("-e", ".")
    session.run("pytest", "--cov=tmdb", "--cov-report=term-missing")


@nox.session
def type_check(session) -> None:
    session.install("mypy", "msgspec", "httpx")
    session.run("mypy", "tmdb")


@nox.session
def enforce_max_lines(session) -> None:
    """Enforce strict 500-line limit per file."""
    session.run(
        "bash",
        "-c",
        "files=$(find tmdb tests -name '*.py' -not -path '*/.*'); "
        'if [ -z "$files" ]; then exit 0; fi; '
        'echo "$files" | xargs wc -l | awk \'$1 > 500 && $2 != "total" {print "Error: " $2 " has " $1 " lines (limit: 500)."; exit_code=1} END {exit exit_code}\'',
        external=True,
    )


@nox.session
def security(session) -> None:
    session.install("pip-audit")
    session.run("pip-audit")
