"""Path utilities for locating Claude Code trace files."""

import re
from pathlib import Path


def encode_project_path(project_path: str | Path) -> str:
    """
    Encode a project path for Claude's directory naming.

    /Users/foo/bar -> -Users-foo-bar
    /Users/foo/ct_test -> -Users-foo-ct-test
    """
    resolved = Path(project_path).resolve()
    return re.sub(r"[^a-zA-Z0-9]", "-", str(resolved))


def get_claude_projects_dir() -> Path:
    """Get the ~/.claude/projects/ directory."""
    return Path.home() / ".claude" / "projects"


def get_project_traces_dir(project_path: str | Path | None = None) -> Path:
    """
    Get the trace directory for a project.

    Returns ~/.claude/projects/<encoded-path>/
    """
    if project_path is None:
        project_path = Path.cwd()

    encoded = encode_project_path(project_path)
    return get_claude_projects_dir() / encoded


def get_trace_file_path(
    session_id: str,
    project_path: str | Path | None = None,
) -> Path:
    """
    Get the full path to a session's trace file.

    Returns ~/.claude/projects/<encoded-path>/<session_id>.jsonl
    """
    project_dir = get_project_traces_dir(project_path)
    return project_dir / f"{session_id}.jsonl"
