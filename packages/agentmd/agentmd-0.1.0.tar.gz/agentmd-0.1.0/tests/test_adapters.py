import pytest

from agentmd.adapters import adapter_claude, adapter_copilot, adapter_cursor


def _minimal_fm() -> dict:
    return {"version": "1.0"}


def _rich_fm() -> dict:
    return {
        "version": "1.0",
        "name": "test-agent",
        "description": "Test agent",
        "role": "Senior engineer",
        "priorities": ["correctness", "security"],
        "context": {"project": "API", "domain": "web"},
        "tech": {"stack": ["Node.js"], "versions": {"node": ">=20"}},
        "rules": ["Use TypeScript", {"description": "Validate with Zod", "globs": ["src/*.ts"]}],
        "change-policy": {"branching": "feature/*", "commits": "conventional"},
        "output": {"docs": True, "conventions": ["JSDoc for public APIs"]},
    }


def test_adapter_cursor_minimal() -> None:
    out = adapter_cursor(_minimal_fm(), "## Setup\n- run")
    assert "---" in out
    assert "description:" in out
    assert "alwaysApply:" in out
    assert "## Setup" in out or "run" in out


def test_adapter_cursor_rich() -> None:
    out = adapter_cursor(_rich_fm(), "## Extra\ncontent")
    assert "Senior engineer" in out
    assert "correctness" in out
    assert "TypeScript" in out
    assert "Validate with Zod" in out
    assert "feature/*" in out
    assert "JSDoc" in out
    assert "## Extra" in out or "content" in out


def test_adapter_claude_minimal() -> None:
    out = adapter_claude(_minimal_fm(), "## Setup\n- run")
    assert "## Setup" in out or "run" in out


def test_adapter_claude_rich() -> None:
    out = adapter_claude(_rich_fm(), "## Body")
    assert "test-agent" in out or "Test agent" in out
    assert "Senior engineer" in out
    assert "correctness" in out
    assert "Node.js" in out
    assert "TypeScript" in out
    assert "feature/*" in out


def test_adapter_copilot_minimal() -> None:
    out = adapter_copilot(_minimal_fm(), "## Setup\n- run")
    assert "---" in out
    assert "description:" in out
    assert "## Setup" in out or "run" in out


def test_adapter_copilot_rich() -> None:
    out = adapter_copilot(_rich_fm(), "## Body")
    assert "name:" in out
    assert "description:" in out
    assert "Senior engineer" in out
    assert "TypeScript" in out
