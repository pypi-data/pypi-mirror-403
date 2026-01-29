<!--
 Copyright (c) 2026 xsyncio
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

<!--
 Copyright 2026 xsyncio.
 SPDX-License-Identifier: MIT
-->

# THE IRON LAW OF CODE STYLE

> **"Code is read much more often than it is written."** - Guido van Rossum
> **"We do not suggest. We ENFORCE."** - This Project

This document is the **ABSOLUTE LAW**. Violations are not "style preferences"; they are **BUGS**. CI will mercilessly reject any code that deviates by even a single whitespace.

---

## 1. THE FOUNDATION (FORMATTING)

Usage of `ruff format` is MANDATORY. Do not waste human cycles debating indentation.

- **Line Length**: **79 characters**. rigid. No exceptions.
  - *Why?* Readable on split screens, standard terminal width, forces modularity.
  - *Enforcement*: Ruff `line-length = 79`.
- **Indentation**: **4 Spaces**. No tabs.
- **Quotes**: **Double quotes** (`"`) for strings.
  - *Exception*: Single quotes allowed only within strict strings manually if needed, but the formatter will standardize this.
- **Structure**:
  - **Imports**: **ONE IMPORT PER LINE**.
    - *Allowed*: `from os import path`, `from os import sep` (on separate lines).
    - *FORBIDDEN*: `from os import path, sep`.
    - *Enforcement*: `force-single-line = true`.
    - *Organization*: 2 blank lines after imports.

---

## 2. THE LINTING REGIME (STATIC ANALYSIS)

We use **Ruff** with the **ALL** selector enabled.

- **Zero Tolerance**: No warnings. NO "info" level messages. If it's reported, it must be fixed.
- **Ignores**: Only those strictly conflicting with the formatter (e.g., `D203` vs `D211`).
- **Complexity Limits**:
  - **Max Complexity**: 5 (McCabe). *If it's deeper than 5 nested blocks, REFACTOR IT.*
  - **Max Arguments**: 5 (Pylint). *Too many args? Use a data class.*
  - **Max Branches**: 10.
  - **Max Returns**: 5.
  - **Max Statements**: 25.
- **No Dead Code**: Unused variables, imports, or unreachable code are strictly prohibited.

---

## 3. THE TYPING DOCTRINE (STRICT MYPY)

Python is a strongly typed language in this repository. `Any` is the enemy.

- **Strict Mode**: **ON**.
- **Explicit `Any`**: **FORBIDDEN**.
  - `disallow_any_generics = true`
  - `disallow_any_unimported = true`
  - `disallow_any_expr = true`
  - `disallow_any_decorated = true`
  - `disallow_any_explicit = true`
- **Untyped Defs**: **ILLEGAL**. Every function argument and return value MUST have a type annotation.
- **Casting**: `cast()` usage is suspicious. `warn_redundant_casts = true`.

**Example of COMPLIANT code:**

```python
def calculate_total(items: list[float]) -> float:
    """Calculate the sum of items."""
    return sum(items)
```

**Example of VIOLATION (Rejection imminent):**

```python
def calculate_total(items): # Missing type hints
    return sum(items)
```

---

## 4. THE DOCUMENTATION MANDATE

Code without documentation is a black box. We do not ship black boxes.

- **Style**: **NumPy**. (`convention = "numpy"`)
- **Coverage**: Every public module, class, method, and function MUST have a docstring.
- **Content**:
  - **Summary**: Single line summary.
  - **Parameters**: Detailed description of args.
  - **Returns**: Description of return value.
  - **Raises**: Explicit list of all exceptions raised.

- **Validation**: Enforced by `pydoclint`.
  - Docstring types MUST match type hints.
  - Return types and Yield types in docstrings are verified against function signatures.
  - Argument names in docstrings MUST match function arguments.

**Template:**

```python
def complex_algorithm(data: str) -> bool:
    """
    Perform the complex algorithm on the input data.

    Parameters
    ----------
    data : str
        The input string to process.

    Returns
    -------
    bool
        True if successful, False otherwise.

    Raises
    ------
    ValueError
        If data is empty.
    """
    if not data:
        raise ValueError("Data cannot be empty")
    return True
```

---

## 5. THE TESTING CONTRACT

- **Coverage**: **100%**. (`fail_under = 100`).
  - If a line of code exists, it must be executed by a test.
  - Exclusions (`pragma: no cover`) are monitored and must be justified.
- **Warnings**: Treatment as **ERRORS**. (`filterwarnings = ["error"]`).
  - Deprecation warnings will fail the build. Fix the debt immediately.
- **Test Quality**:
  - Tests must be typed.
  - Assertions must be specific (no `assert result`).

---

## 6. THE DEPENDENCY & SECURITY SHIELD

- **Dependencies**: `deptry` is used to detect:
  - Unused dependencies.
  - Missing dependencies.
  - Transitive dependency abuse.
- **Security**: `pip-audit` scans for known vulnerabilities in dependencies.

---

## 7. WORKFLOW & COMMITMENT

1. **Pre-Commit**: Run `pre-commit run --all-files` (or `nox`).
   - Checks: `ruff`, `mypy`, `pydoclint`, `deptry`, `pip-audit`.
2. **Commit**: Code that violates valid valid rules implies you did not check.
3. **Review**: Reviewers are instructed to reject PRs that do not strictly adhere to this document.

**THERE ARE NO EXCUSES. THERE ARE ONLY PASSING BUILDS AND BROKEN ONES.**
