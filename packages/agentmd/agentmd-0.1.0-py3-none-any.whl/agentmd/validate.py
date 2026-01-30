"""Validate AGENT.md frontmatter against the JSON schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

# Bundled schema (kept in sync with schema/agentmd.schema.json in the repo)
_SCHEMA_PATH = Path(__file__).resolve().parent / "agentmd.schema.json"


def _load_schema() -> dict[str, Any]:
    p = _SCHEMA_PATH
    if not p.exists():
        # Fallback: minimal schema requiring only version
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"version": {"type": "string"}},
            "required": ["version"],
            "additionalProperties": True,
        }
    return json.loads(p.read_text(encoding="utf-8"))


def validate(frontmatter: dict[str, Any] | None) -> list[str]:
    """
    Validate frontmatter against the AGENT.md schema.
    Returns a list of error messages (empty if valid).
    - If frontmatter is None, returns [] (no frontmatter is valid). An empty dict {} is validated and will error if "version" is missing.
    - If 'version' is missing, returns ["'version' is required when frontmatter is present"].
    """
    if frontmatter is None:
        return []

    schema = _load_schema()
    try:
        jsonschema.validate(instance=frontmatter, schema=schema)
        return []
    except jsonschema.ValidationError as e:
        # Prefer a readable message
        msg = e.message or str(e)
        if e.path:
            msg = f"{'.'.join(str(p) for p in e.path)}: {msg}"
        return [msg]
    except jsonschema.SchemaError as e:
        return [f"Schema error: {e}"]
