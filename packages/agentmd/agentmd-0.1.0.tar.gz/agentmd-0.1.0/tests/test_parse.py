import pytest

from agentmd.parse import parse, parse_file
from pathlib import Path


def test_parse_no_frontmatter() -> None:
    content = "## Setup\n- `npm install`"
    fm, body = parse(content)
    assert fm is None
    assert "## Setup" in body
    assert "npm install" in body


def test_parse_empty_frontmatter() -> None:
    content = "---\n---\n## Body"
    fm, body = parse(content)
    assert fm == {}
    assert "## Body" in body


def test_parse_frontmatter_and_body() -> None:
    content = '---\nversion: "1.0"\nname: test\n---\n## Body here'
    fm, body = parse(content)
    assert fm == {"version": "1.0", "name": "test"}
    assert body.strip() == "## Body here"


def test_parse_invalid_yaml_raises() -> None:
    # Undefined YAML alias causes PyYAML to raise
    content = "---\n*undefined_anchor\n---\nbody"
    with pytest.raises(Exception):
        parse(content)


def test_parse_frontmatter_not_object_raises() -> None:
    content = "---\n- a\n- b\n---\nbody"
    with pytest.raises(ValueError, match="must be a YAML object"):
        parse(content)


def test_parse_file(tmp_path: Path) -> None:
    p = tmp_path / "AGENT.md"
    p.write_text('---\nversion: "1.0"\n---\n## Setup\n- run')
    fm, body = parse_file(p)
    assert fm == {"version": "1.0"}
    assert "## Setup" in body
