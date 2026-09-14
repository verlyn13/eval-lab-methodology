#!/usr/bin/env python3
"""Inject small, current repository context at Claude session start."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    payload = {}

candidate = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
cwd = Path(candidate).expanduser().resolve()
root_text = git(cwd, "rev-parse", "--show-toplevel")
root = Path(root_text) if root_text != "unknown" else cwd
branch = git(root, "branch", "--show-current")
head = git(root, "log", "-1", "--format=%h %s")
porcelain = git(root, "status", "--porcelain")
tree = "unknown" if porcelain == "unknown" else ("dirty" if porcelain else "clean")

context = (
    f"Current repository context: root={root}; branch={branch}; HEAD={head}; working_tree={tree}. "
    "Read AGENTS.md and use the project-status skill before substantive work. Keep source, Git, "
    "runtime, remote/provider, and decision evidence separate."
)
print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
)
