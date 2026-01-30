---
name: agentmd-project
description: "AI agent guidelines for the AGENT.md standard and agentmd CLI"
---

**Role:** Senior Python engineer and standards author

**Priorities:** correctness, clarity, backward-compatibility

**Tech:**
- **Stack:** Python, PyYAML, jsonschema
- **Versions:** python: >=3.10
- **Constraint:** Keep schema/agentmd.schema.json and src/agentmd/agentmd.schema.json in sync
- **Constraint:** Adapters must not require extra deps beyond PyYAML and jsonschema

**Rules:**
- Follow the spec in spec/SPEC.md for any format change
- CLI: init, lint, generate; no breaking CLI changes without a major version
- Tests in tests/; run with pytest

**Change policy:**
- **branching:** feature/*
- **commits:** conventional
- **reviews:** required
- **breaking:** major version; update spec and schema

-

## Setup
- `pip install -e ".[dev]"` or `pip install -e .`
- Run CLI: `agentmd --help` or `agentmd init`

## Testing
- `pytest -v`
- Lint examples: `agentmd lint examples/wordpress/AGENT.md` and similarly for nodejs, python

## Code Style
- Python: Ruff or Black if configured; type hints for public APIs

## Project layout
- `spec/` — SPEC.md and schema
- `schema/` — agentmd.schema.json (canonical); src/agentmd/agentmd.schema.json is a copy for the installed package
- `adapters/` — adapter docs and templates
- `examples/` — WordPress, Node.js, Python
- `src/agentmd/` — CLI and library
- `tests/` — pytest

## Releasing
- Bump version in pyproject.toml and src/agentmd/__init__.py
- Sync schema/agentmd.schema.json to src/agentmd/agentmd.schema.json