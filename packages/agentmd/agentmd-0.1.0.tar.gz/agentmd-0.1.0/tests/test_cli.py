import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentmd.cli"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _out(r: subprocess.CompletedProcess) -> str:
    return (r.stdout or "") + (r.stderr or "")


def test_cli_usage() -> None:
    r = _run([], Path.cwd())
    assert r.returncode == 0
    assert "init" in _out(r)
    assert "lint" in _out(r)
    assert "generate" in _out(r)


def test_cli_init(tmp_path: Path) -> None:
    r = _run(["init", str(tmp_path)], tmp_path)
    assert r.returncode == 0
    p = tmp_path / "AGENT.md"
    assert p.exists()
    assert "version" in p.read_text()


def test_cli_init_exists(tmp_path: Path) -> None:
    (tmp_path / "AGENT.md").write_text("existing")
    r = _run(["init", str(tmp_path)], tmp_path)
    assert r.returncode != 0
    assert "already exists" in _out(r)


def test_cli_lint_valid(tmp_path: Path) -> None:
    (tmp_path / "AGENT.md").write_text('---\nversion: "1.0"\n---\n## Setup')
    r = _run(["lint", str(tmp_path / "AGENT.md")], tmp_path)
    assert r.returncode == 0
    assert "valid" in _out(r).lower()


def test_cli_lint_invalid(tmp_path: Path) -> None:
    (tmp_path / "AGENT.md").write_text("---\n{}\n---\n## Setup")
    r = _run(["lint", str(tmp_path / "AGENT.md")], tmp_path)
    assert r.returncode != 0
    out = _out(r).lower()
    assert "version" in out or "error" in out


def test_cli_generate(tmp_path: Path) -> None:
    (tmp_path / "AGENT.md").write_text('---\nversion: "1.0"\n---\n## Setup\n- run')
    (tmp_path / ".cursor" / "rules").mkdir(parents=True)
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    r = _run(["generate", "--target", "cursor,claude,copilot"], tmp_path)
    assert r.returncode == 0
    assert (tmp_path / ".cursor" / "rules" / "agent-from-agentmd.mdc").exists()
    assert (tmp_path / "claude.md").exists()
    assert (tmp_path / ".github" / "agents" / "agent.agent.md").exists()
