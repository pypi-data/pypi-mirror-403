"""CLI for agentmd: init, lint, generate."""

from __future__ import annotations

import sys
from pathlib import Path

from .adapters import write_claude, write_copilot, write_cursor
from .parse import find_agent_md, parse_file
from .validate import validate


def main() -> None:
    """Entry point. Dispatches to init, lint, or generate."""
    args = sys.argv[1:]
    if not args:
        _usage()
        sys.exit(0)
    cmd = args[0].lower()
    rest = args[1:]

    if cmd == "init":
        _cmd_init(rest)
    elif cmd == "lint":
        _cmd_lint(rest)
    elif cmd == "generate":
        _cmd_generate(rest)
    else:
        _usage()
        sys.exit(2)


def _usage() -> None:
    print("Usage: agentmd <command> [options]")
    print("  agentmd init [directory]  Scaffold AGENT.md (default: current directory)")
    print("  agentmd lint [path]       Validate AGENT.md against the schema")
    print("  agentmd generate [path]   Generate Cursor, Claude, Copilot files from AGENT.md")
    print("")
    print("  generate options:")
    print("    --target cursor,claude,copilot   Comma-separated targets (default: all)")


def _cmd_init(rest: list[str]) -> None:
    out_dir = Path(rest[0]).resolve() if rest and not rest[0].startswith("-") else Path.cwd()
    out = out_dir / "AGENT.md"
    if out.exists():
        print(f"AGENT.md already exists at {out}")
        sys.exit(1)
    scaffold = _scaffold()
    out.write_text(scaffold, encoding="utf-8")
    print(f"Created {out}")


def _scaffold() -> str:
    return '''---
version: "1.0"
---

## Setup
- `npm install` or `pnpm install`
- `npm run dev` or `pnpm dev`

## Testing
- `npm test` or `pnpm test`

## Code Style
- Run the project linter before committing
'''


def _cmd_lint(rest: list[str]) -> None:
    path: Path | None = None
    if rest and not rest[0].startswith("-"):
        path = Path(rest[0]).resolve()
    else:
        path = find_agent_md()
    if not path or not path.exists():
        print("AGENT.md not found. Run from a project with AGENT.md or pass a path.")
        sys.exit(1)
    try:
        fm, body = parse_file(path)
    except Exception as e:
        print(f"Parse error: {e}")
        sys.exit(1)
    errs = validate(fm)
    if errs:
        for e in errs:
            print(f"Error: {e}")
        sys.exit(1)
    print("AGENT.md is valid.")


def _cmd_generate(rest: list[str]) -> None:
    targets = {"cursor", "claude", "copilot"}
    path: Path | None = None
    i = 0
    while i < len(rest):
        if rest[i] == "--target" and i + 1 < len(rest):
            targets = {t.strip().lower() for t in rest[i + 1].split(",") if t.strip()}
            i += 2
            continue
        if not rest[i].startswith("-"):
            path = Path(rest[i]).resolve()
            i += 1
            continue
        i += 1
    if not path:
        agent_path = find_agent_md()
        if agent_path:
            path = agent_path.parent
        else:
            path = Path.cwd()
    # Resolve AGENT.md: path may be a dir or the AGENT.md file itself
    if path.is_file() and path.name == "AGENT.md":
        agent_file = path
    elif (path / "AGENT.md").is_file():
        agent_file = path / "AGENT.md"
    else:
        agent_file = find_agent_md(path)
    if not agent_file or not agent_file.exists():
        print("AGENT.md not found. Run agentmd init first or pass a directory that contains AGENT.md.")
        sys.exit(1)
    out_dir = agent_file.parent
    try:
        fm, body = parse_file(agent_file)
    except Exception as e:
        print(f"Parse error: {e}")
        sys.exit(1)
    errs = validate(fm)
    if errs:
        for e in errs:
            print(f"Validation error: {e}")
        sys.exit(1)
    # If no frontmatter, use empty dict so adapters still produce reasonable output from body
    if fm is None:
        fm = {"version": "1.0"}
    written: list[Path] = []
    if "cursor" in targets:
        written.append(write_cursor(fm, body, out_dir))
    if "claude" in targets:
        written.append(write_claude(fm, body, out_dir))
    if "copilot" in targets:
        written.append(write_copilot(fm, body, out_dir))
    for p in written:
        print(f"Wrote {p}")


if __name__ == "__main__":
    main()
