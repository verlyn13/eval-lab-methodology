#!/usr/bin/env python3
"""Validate the repository-owned Codex and Claude agent contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


agents = ROOT / "AGENTS.md"
require(agents.is_file(), "AGENTS.md is missing")
if agents.is_file():
    require(
        agents.stat().st_size <= 32 * 1024,
        "AGENTS.md exceeds the 32 KiB Codex discovery limit",
    )
    require(
        "uv sync --frozen --no-install-project --extra dev --extra report"
        in agents.read_text(),
        "AGENTS.md must use the locked development/report environment",
    )

require((ROOT / "uv.lock").is_file(), "uv.lock is missing")
require(
    (ROOT / "scripts/audit-dependencies.sh").is_file(),
    "dependency audit script is missing",
)

for workflow_name in ("render-report.yml", "deploy-pages.yml"):
    workflow = ROOT / ".github/workflows" / workflow_name
    require(workflow.is_file(), f"{workflow_name} is missing")
    if workflow.is_file():
        workflow_text = workflow.read_text()
        require(
            "uv sync --frozen --python 3.13 --no-install-project --extra dev --extra report"
            in workflow_text,
            f"{workflow_name} must install the locked gate environment",
        )
        require(
            'version: "${{ steps.quarto-version.outputs.version }}"' in workflow_text,
            f"{workflow_name} must install the repository-pinned Quarto version",
        )
        require(
            "uv run --frozen --no-sync bash scripts/run-merge-gate.sh" in workflow_text,
            f"{workflow_name} must run the canonical merge gate",
        )

claude = ROOT / "CLAUDE.md"
require(claude.is_file(), "CLAUDE.md is missing")
if claude.is_file():
    require(
        claude.read_text() == "@AGENTS.md\n",
        "CLAUDE.md must be the exact @AGENTS.md bridge",
    )

ignore = ROOT / ".gitignore"
require(ignore.is_file(), ".gitignore is missing")
if ignore.is_file():
    require(
        ".claude/settings.local.json" in ignore.read_text().splitlines(),
        ".claude/settings.local.json must be ignored",
    )

settings_path = ROOT / ".claude/settings.json"
require(settings_path.is_file(), ".claude/settings.json is missing")
settings: dict[str, Any] = {}
if settings_path.is_file():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f".claude/settings.json is invalid JSON: {exc}")
    require(
        settings.get("$schema")
        == "https://json.schemastore.org/claude-code-settings.json",
        "Claude settings schema is missing",
    )
    require(
        "enableAllProjectMcpServers" not in settings,
        "enableAllProjectMcpServers is forbidden",
    )
    require(
        "model" not in settings,
        "project Claude settings must inherit the user-selected model",
    )
    status_line = as_dict(settings.get("statusLine"))
    require(
        ".claude/statusline.py" in str(status_line.get("command", "")),
        "statusLine must use .claude/statusline.py",
    )
    hooks = as_dict(settings.get("hooks"))
    require(
        ".claude/hooks/session_context.py" in json.dumps(hooks.get("SessionStart", [])),
        "SessionStart context hook is missing",
    )
    permissions = as_dict(settings.get("permissions"))
    deny = as_list(permissions.get("deny"))
    require(
        any(".env" in str(item) for item in deny),
        "Claude settings must deny reads of populated env files",
    )
    require(
        any("git push origin main" in str(item) for item in deny),
        "Claude settings must deny direct pushes to main",
    )

codex_skill = ROOT / ".agents/skills/project-status/SKILL.md"
claude_skill = ROOT / ".claude/skills/project-status/SKILL.md"
require(codex_skill.is_file(), "Codex project-status skill is missing")
require(claude_skill.is_file(), "Claude project-status skill is missing")
if codex_skill.is_file() and claude_skill.is_file():
    require(
        codex_skill.read_bytes() == claude_skill.read_bytes(),
        "Codex and Claude project-status skills drifted",
    )

codex_agent_path = ROOT / ".codex/agents/status-auditor.toml"
require(codex_agent_path.is_file(), "Codex status-auditor is missing")
if codex_agent_path.is_file():
    try:
        codex_agent = tomllib.loads(codex_agent_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"Codex status-auditor TOML is invalid: {exc}")
        codex_agent = {}
    require(
        codex_agent.get("sandbox_mode") == "read-only",
        "Codex status-auditor must be read-only",
    )
    require(
        "model" not in codex_agent,
        "Codex status-auditor must inherit the selected model",
    )

claude_agent_path = ROOT / ".claude/agents/status-auditor.md"
require(claude_agent_path.is_file(), "Claude status-auditor is missing")
if claude_agent_path.is_file():
    text = claude_agent_path.read_text()
    require(
        "model: inherit" in text,
        "Claude status-auditor must inherit the selected model",
    )
    require(
        "permissionMode: plan" in text,
        "Claude status-auditor must use plan permission mode",
    )

samples = [
    (
        ROOT / ".claude/hooks/session_context.py",
        {"cwd": str(ROOT)},
        lambda output: "hookSpecificOutput" in json.loads(output),
        "SessionStart hook",
    ),
    (
        ROOT / ".claude/statusline.py",
        {
            "workspace": {"current_dir": str(ROOT)},
            "model": {"display_name": "test"},
            "context_window": {"used_percentage": 25},
        },
        lambda output: "test |" in output and "ctx 25%" in output,
        "status line",
    ),
]
for script, payload, validate, label in samples:
    require(script.is_file(), f"{label} script is missing")
    if not script.is_file():
        continue
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    require(
        result.returncode == 0,
        f"{label} exited {result.returncode}: {result.stderr.strip()}",
    )
    if result.returncode == 0:
        try:
            require(
                bool(validate(result.stdout.strip())),
                f"{label} returned an unexpected payload",
            )
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{label} returned invalid output: {exc}")

if errors:
    for error in errors:
        print(f"FAIL: {error}")
    raise SystemExit(1)
print("agent contract: PASS")
