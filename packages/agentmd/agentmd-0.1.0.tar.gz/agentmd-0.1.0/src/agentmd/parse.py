"""Parse AGENT.md: extract YAML frontmatter and Markdown body."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_DELIM = "---"


def parse(content: str) -> tuple[dict[str, Any] | None, str]:
    """
    Parse AGENT.md content into (frontmatter, body).
    - If no frontmatter: (None, content).
    - If frontmatter: (dict, body). Raises on invalid YAML.
    """
    content = content.strip()
    if not content.startswith(FRONTMATTER_DELIM):
        return None, content

    # First line is ---; find the next ---
    rest = content[len(FRONTMATTER_DELIM) :].lstrip("\n")
    idx = rest.find("\n" + FRONTMATTER_DELIM)
    if idx == -1:
        # Closing --- may be on the first line of rest (empty frontmatter: ---\n---\n)
        if rest.startswith(FRONTMATTER_DELIM + "\n"):
            return {}, rest[len(FRONTMATTER_DELIM) + 1 :].lstrip("\n")
        return None, content

    closing_len = len("\n" + FRONTMATTER_DELIM)
    fm_str = rest[:idx].strip()
    body = rest[idx + closing_len :].lstrip("\n")

    if not fm_str:
        return {}, body

    data = yaml.safe_load(fm_str)
    if data is None:
        return {}, body
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML object")
    return data, body


def parse_file(path: Path | str) -> tuple[dict[str, Any] | None, str]:
    """Read path and parse AGENT.md. Raises FileNotFoundError, OSError, ValueError."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    text = p.read_text(encoding="utf-8")
    return parse(text)


def find_agent_md(cwd: Path | str | None = None) -> Path | None:
    """Return the path to AGENT.md in the given directory or its ancestors, or None."""
    cur = Path(cwd or ".").resolve()
    for _ in range(20):  # limit depth
        p = cur / "AGENT.md"
        if p.is_file():
            return p
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return None
