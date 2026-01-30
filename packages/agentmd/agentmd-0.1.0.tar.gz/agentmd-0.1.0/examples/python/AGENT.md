---
version: "1.0"
name: python-agent
description: AI agent guidelines for Python applications and libraries
role: Senior Python engineer
context:
  project: Python application or library
  domain: web, data, CLI, automation
  audience: Developers and data engineers
priorities:
  - correctness
  - readability
  - security
tech:
  stack: [Python, pip, uv/poetry]
  versions: { python: ">=3.11" }
  constraints:
    - "Type hints for all public functions and modules"
    - "Prefer pathlib over os.path"
    - "Use `ruff` or `black` + `isort`; config in pyproject.toml"
rules:
  - "Follow PEP 8; enforce with ruff"
  - "Use `typing` and `from __future__ import annotations` for forward refs"
  - "Structured logging; avoid print in library code"
  - description: "Use dataclasses or Pydantic for config and DTOs"
    globs: ["src/**/*.py", "**/models.py"]
change-policy:
  branching: "feature/*"
  commits: "conventional"
  reviews: "required"
  breaking: "bump major; document in CHANGELOG and migration guide"
output:
  docs: true
  conventions: ["Docstrings (Google or NumPy style)", "README", "ADR for architecture decisions"]
---

## Setup
- `uv sync` or `poetry install` or `pip install -e ".[dev]"`
- Create `.env` from `.env.example` if present
- `alembic upgrade head` or equivalent for DB projects

## Testing
- `pytest`; `pytest -v` or `pytest --cov`
- Fixtures and markers in `conftest.py`
- Async: `pytest-asyncio` when using async tests

## Code Style
- Ruff: `ruff check .` and `ruff format .`
- Type check: `mypy` or `pyright` if configured
- Naming: `snake_case`; `PascalCase` for classes; `UPPER` for constants

## Architecture
- Prefer explicit layers: `src/`, `app/`, or `package/`; avoid deep nesting
- Use virtual envs; pin deps in `pyproject.toml` or `requirements*.txt`

## Security
- No secrets in code; use env vars and secret managers
- Validate input (Pydantic, etc.); avoid `eval` and `exec` on user data
- `pip audit` or `safety`; keep deps updated

## Deployment
- Build: `pip wheel` or `poetry build` for packages
- Run: `uv run python -m app` or `gunicorn` / `uvicorn` for web apps
