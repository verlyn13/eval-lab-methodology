#!/usr/bin/env python3
"""Validate public evidence and render the Quarto methodology report."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "src").exists():
            return candidate
    raise SystemExit("Could not locate repository root")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from eval_lab_methodology import validate_evidence_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence",
        default="evidence/sample-lab-report.json",
        help="Contract B evidence JSON to render.",
    )
    parser.add_argument(
        "--report",
        default="reports/methodology-report.qmd",
        help="Parameterized Quarto report to render.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/rendered",
        help="Directory for rendered HTML output.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate evidence and public-safe status without invoking Quarto.",
    )
    return parser.parse_args()


def resolve_repo_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_and_validate(evidence_path: Path) -> dict[str, Any]:
    try:
        document = json.loads(evidence_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Evidence JSON not found: {evidence_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Evidence JSON is not valid JSON: {exc}") from exc

    validate_evidence_report(document)
    sanitization = document["manifest"].get("sanitization", {})
    if sanitization.get("status") != "public-safe":
        raise SystemExit("Refusing to render: manifest.sanitization.status must be public-safe")
    if sanitization.get("checked") is not True:
        raise SystemExit("Refusing to render: manifest.sanitization.checked must be true")
    if sanitization.get("redactions_required") is True:
        raise SystemExit("Refusing to render: manifest.sanitization.redactions_required must be false")

    decision = document["report"]["decision"]
    enhanced = document["report"]["statistics"]["enhanced_estimators"]
    sign = decision["sign_test"]
    required = {
        "decision.label": (decision.get("label"), "enforcing:superiority-by-margin"),
        "decision.rule": (decision.get("rule"), "bootstrap_ci_low_gt_margin"),
        "enhanced.two_stage_bootstrap.label": (
            enhanced["two_stage_bootstrap"].get("label"),
            "enhanced:two-stage-bootstrap",
        ),
        "enhanced.wilcoxon_signed_rank.label": (
            enhanced["wilcoxon_signed_rank"].get("label"),
            "enhanced:wilcoxon-signed-rank",
        ),
        "enhanced.glmm.label": (enhanced["glmm"].get("label"), "enhanced:glmm-logistic"),
        "sign_test.alternative": (sign.get("alternative"), "two-sided"),
        "sign_test.reported_only": (sign.get("reported_only"), True),
    }
    failures = [
        f"{field} expected {expected!r}, got {actual!r}"
        for field, (actual, expected) in required.items()
        if actual != expected
    ]
    if failures:
        raise SystemExit("Refusing to render: " + "; ".join(failures))
    return document


def main() -> int:
    args = parse_args()
    evidence_path = resolve_repo_path(args.evidence)
    report_path = resolve_repo_path(args.report)
    output_dir = resolve_repo_path(args.output_dir)

    document = load_and_validate(evidence_path)
    print(
        "validated public-safe evidence: "
        f"{document['report']['campaign_id']} ({display_path(evidence_path)})"
    )
    if args.validate_only:
        return 0

    quarto = os.environ.get("QUARTO", "quarto")
    if shutil.which(quarto) is None:
        raise SystemExit("quarto executable not found; install Quarto or set QUARTO=/path/to/quarto")

    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_PATH}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(SRC_PATH)
    # Render as a single document (no --output-dir: with the website project's
    # _quarto.yml at the repo root, Quarto rejects --output-dir for documents
    # that are not project render targets). The output lands next to the .qmd
    # and is then moved into the requested output directory.
    command = [
        quarto,
        "render",
        str(report_path),
        "-P",
        f"evidence:{evidence_path}",
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False)
    if completed.returncode != 0:
        return completed.returncode

    rendered_html = report_path.with_suffix(".html")
    if not rendered_html.exists():
        raise SystemExit(f"Quarto succeeded but no output found at {display_path(rendered_html)}")
    resources = report_path.parent / f"{report_path.stem}_files"
    for source in (rendered_html, resources):
        if not source.exists():
            continue
        target = output_dir / source.name
        if target == source:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        shutil.move(str(source), str(target))
    print(f"rendered report: {display_path(output_dir / rendered_html.name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
