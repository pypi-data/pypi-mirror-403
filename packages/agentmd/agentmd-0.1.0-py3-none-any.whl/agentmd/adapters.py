"""Adapters: convert AGENT.md (frontmatter + body) into tool-specific formats."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _rules_text(fm: dict[str, Any]) -> str:
    """Render rules as a bullet list."""
    rules = fm.get("rules") or []
    lines: list[str] = []
    for r in rules:
        if isinstance(r, str):
            lines.append(f"- {r}")
        elif isinstance(r, dict) and "description" in r:
            lines.append(f"- {r['description']}")
    return "\n".join(lines) if lines else ""


def _tech_text(fm: dict[str, Any]) -> str:
    t = fm.get("tech") or {}
    parts: list[str] = []
    if t.get("stack"):
        parts.append(f"- **Stack:** {', '.join(t['stack'])}")
    if t.get("versions"):
        v = ", ".join(f"{k}: {v}" for k, v in t["versions"].items())
        parts.append(f"- **Versions:** {v}")
    if t.get("constraints"):
        for c in t["constraints"]:
            parts.append(f"- **Constraint:** {c}")
    return "\n".join(parts) if parts else ""


def _change_policy_text(fm: dict[str, Any]) -> str:
    cp = fm.get("change-policy") or {}
    parts: list[str] = []
    for k, v in cp.items():
        if v is not None and v != "":
            parts.append(f"- **{k}:** {v}")
    return "\n".join(parts) if parts else ""


def _output_text(fm: dict[str, Any]) -> str:
    o = fm.get("output") or {}
    parts: list[str] = []
    if o.get("formats"):
        parts.append(f"- **Formats:** {', '.join(o['formats'])}")
    if o.get("conventions"):
        for c in o["conventions"]:
            parts.append(f"- {c}")
    if "docs" in o and o["docs"]:
        parts.append("- Maintain or create documentation as needed.")
    return "\n".join(parts) if parts else ""


def _context_text(fm: dict[str, Any]) -> str:
    ctx = fm.get("context")
    if not ctx:
        return ""
    if isinstance(ctx, str):
        return f"- **Context:** {ctx}"
    parts = [f"- **{k}:** {v}" for k, v in ctx.items() if v]
    return "\n".join(parts) if parts else ""


def adapter_cursor(fm: dict[str, Any], body: str) -> str:
    """
    Produce Cursor .mdc rule content.
    Cursor: description, globs, alwaysApply in frontmatter; body is the rule.
    """
    desc = fm.get("description") or fm.get("role") or "Project guidelines from AGENT.md"
    globs = fm.get("globs")
    if isinstance(globs, str):
        globs = [globs] if globs else []
    elif not isinstance(globs, list):
        globs = []
    always = fm.get("alwaysApply", False)

    out: list[str] = ["---"]
    out.append(f'description: "{_escape(desc)}"')
    if globs:
        out.append(f"globs: {globs}")
    out.append(f"alwaysApply: {str(always).lower()}")
    out.append("---")
    out.append("")

    # Build Cursor rule body from AGENT.md
    sections: list[str] = []

    if fm.get("role"):
        sections.append(f"## Role\n\n{fm['role']}")
    if fm.get("priorities"):
        sections.append("## Priorities\n\n" + "\n".join(f"- {p}" for p in fm["priorities"]))
    ctx = _context_text(fm)
    if ctx:
        sections.append("## Context\n\n" + ctx)
    tech = _tech_text(fm)
    if tech:
        sections.append("## Tech\n\n" + tech)
    rules = _rules_text(fm)
    if rules:
        sections.append("## Rules\n\n" + rules)
    cp = _change_policy_text(fm)
    if cp:
        sections.append("## Change policy\n\n" + cp)
    out_text = _output_text(fm)
    if out_text:
        sections.append("## Output\n\n" + out_text)
    if body.strip():
        sections.append(body.strip())

    out.append("\n\n".join(sections))
    return "\n".join(out)


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def adapter_claude(fm: dict[str, Any], body: str) -> str:
    """
    Produce claude.md: structured Markdown for Claude project instructions.
    """
    sections: list[str] = []

    if fm.get("name"):
        sections.append(f"# {fm['name']}\n")
    if fm.get("description"):
        sections.append(f"{fm['description']}\n")
    if fm.get("role"):
        sections.append("## Role\n\n" + fm["role"] + "\n")
    if fm.get("priorities"):
        sections.append("## Priorities\n\n" + "\n".join(f"- {p}" for p in fm["priorities"]) + "\n")
    ctx = _context_text(fm)
    if ctx:
        sections.append("## Context\n\n" + ctx + "\n")
    tech = _tech_text(fm)
    if tech:
        sections.append("## Tech\n\n" + tech + "\n")
    rules = _rules_text(fm)
    if rules:
        sections.append("## Rules\n\n" + rules + "\n")
    cp = _change_policy_text(fm)
    if cp:
        sections.append("## Change policy\n\n" + cp + "\n")
    out_text = _output_text(fm)
    if out_text:
        sections.append("## Output\n\n" + out_text + "\n")

    if body.strip():
        sections.append(body.strip())

    return "\n".join(sections).strip()


def adapter_copilot(fm: dict[str, Any], body: str) -> str:
    """
    Produce GitHub Copilot .agent.md: YAML frontmatter (name, description) + Markdown.
    """
    name = fm.get("name") or "agent"
    desc = fm.get("description") or fm.get("role") or "Project guidelines from AGENT.md"

    out: list[str] = ["---"]
    out.append(f"name: {name}")
    out.append(f'description: "{_escape(desc)}"')
    out.append("---")
    out.append("")

    # Body: combine structured bits + body
    parts: list[str] = []
    if fm.get("role"):
        parts.append(f"**Role:** {fm['role']}\n")
    if fm.get("priorities"):
        parts.append("**Priorities:** " + ", ".join(fm["priorities"]) + "\n")
    tech = _tech_text(fm)
    if tech:
        parts.append("**Tech:**\n" + tech + "\n")
    rules = _rules_text(fm)
    if rules:
        parts.append("**Rules:**\n" + rules + "\n")
    cp = _change_policy_text(fm)
    if cp:
        parts.append("**Change policy:**\n" + cp + "\n")
    if body.strip():
        parts.append(body.strip())

    out.append("\n".join(parts))
    return "\n".join(out)


def write_cursor(fm: dict[str, Any], body: str, out_dir: Path) -> Path:
    """Write .cursor/rules/agent-from-agentmd.mdc. Creates parent dirs."""
    p = out_dir / ".cursor" / "rules"
    p.mkdir(parents=True, exist_ok=True)
    f = p / "agent-from-agentmd.mdc"
    f.write_text(adapter_cursor(fm, body), encoding="utf-8")
    return f


def write_claude(fm: dict[str, Any], body: str, out_dir: Path) -> Path:
    """Write claude.md in out_dir."""
    f = out_dir / "claude.md"
    f.write_text(adapter_claude(fm, body), encoding="utf-8")
    return f


def write_copilot(fm: dict[str, Any], body: str, out_dir: Path) -> Path:
    """Write .github/agents/agent.agent.md. Creates parent dirs."""
    p = out_dir / ".github" / "agents"
    p.mkdir(parents=True, exist_ok=True)
    f = p / "agent.agent.md"
    f.write_text(adapter_copilot(fm, body), encoding="utf-8")
    return f
