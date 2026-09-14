#!/usr/bin/env python3
"""Render model, repository, Git, and context use without remote calls."""

from __future__ import annotations

import json
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
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    payload = {}

workspace = payload.get("workspace") or {}
cwd = (
    Path(workspace.get("current_dir") or payload.get("cwd") or ".")
    .expanduser()
    .resolve()
)
root_text = git(cwd, "rev-parse", "--show-toplevel")
root = Path(root_text) if root_text else cwd
branch = git(root, "branch", "--show-current") or "detached"
dirty = bool(git(root, "status", "--porcelain"))
model_data = payload.get("model") or {}
model = model_data.get("display_name") or model_data.get("id") or "model"
used = (payload.get("context_window") or {}).get("used_percentage")
context = f"ctx {used:.0f}%" if isinstance(used, (int, float)) else "ctx ?"
print(f"{model} | {root.name}:{branch}{'*' if dirty else ''} | {context}")
