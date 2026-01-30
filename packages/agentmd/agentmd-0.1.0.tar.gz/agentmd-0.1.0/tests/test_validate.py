import pytest

from agentmd.validate import validate


def test_validate_none() -> None:
    assert validate(None) == []


def test_validate_empty_dict_requires_version() -> None:
    errs = validate({})
    assert len(errs) >= 1
    assert "version" in errs[0].lower()


def test_validate_valid_minimal() -> None:
    assert validate({"version": "1.0"}) == []


def test_validate_valid_full() -> None:
    fm = {
        "version": "1.0",
        "name": "x",
        "role": "Engineer",
        "priorities": ["a", "b"],
        "tech": {"stack": ["Python"], "versions": {"python": "3.11"}},
        "rules": ["Rule 1", {"description": "Rule 2", "globs": ["*.py"]}],
        "change-policy": {"branching": "feature/*", "commits": "conventional"},
        "output": {"docs": True},
    }
    assert validate(fm) == []


def test_validate_invalid_version_pattern() -> None:
    # Schema pattern: ^[0-9]+\.[0-9]+(\.[0-9]+)?$
    errs = validate({"version": "v1.0"})
    assert len(errs) >= 1
