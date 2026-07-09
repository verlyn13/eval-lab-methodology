"""Runtime checks for the public evidence contract.

This is deliberately small and dependency-free. The normative machine-readable
contract remains ``evidence/schema.json``; these checks cover the public sample
and give offline callers a fail-closed validator for the required core shape.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

EVIDENCE_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class EvidenceValidationError(ValueError):
    """Raised when a report does not satisfy the required evidence shape."""


def validate_evidence_report(document: Mapping[str, Any]) -> None:
    """Validate the required public evidence-report shape.

    The function raises ``EvidenceValidationError`` with a combined diagnostic
    when the document is not acceptable.
    """

    errors: list[str] = []
    _require_keys(document, ("schema_version", "core", "report", "raw_outcomes", "manifest"), "$", errors)
    if document.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        errors.append("$.schema_version must be 1.0.0")

    core = _object(document.get("core"), "$.core", errors)
    if core:
        _require_keys(core, ("core_version", "core_content_hash"), "$.core", errors)
        if not isinstance(core.get("core_version"), str) or not core.get("core_version"):
            errors.append("$.core.core_version must be a non-empty string")
        if not _is_sha256(core.get("core_content_hash")):
            errors.append("$.core.core_content_hash must be sha256:<64 lowercase hex>")

    report = _object(document.get("report"), "$.report", errors)
    if report:
        _require_keys(
            report,
            ("campaign_id", "created_at", "provenance", "statistics", "decision"),
            "$.report",
            errors,
        )
        if report.get("provenance") not in {"synthetic", "sanitized-real"}:
            errors.append("$.report.provenance must be synthetic or sanitized-real")
        _object(report.get("statistics"), "$.report.statistics", errors)
        decision = _object(report.get("decision"), "$.report.decision", errors)
        if decision:
            _require_keys(
                decision,
                ("rule", "margin", "promote", "sign_test"),
                "$.report.decision",
                errors,
            )
            if decision.get("rule") != "bootstrap_ci_low_gt_margin":
                errors.append("$.report.decision.rule must be bootstrap_ci_low_gt_margin")
            if not isinstance(decision.get("promote"), bool):
                errors.append("$.report.decision.promote must be boolean")
            sign_test = _object(decision.get("sign_test"), "$.report.decision.sign_test", errors)
            if sign_test and sign_test.get("reported_only") is not True:
                errors.append("$.report.decision.sign_test.reported_only must be true")

    raw_outcomes = _array(document.get("raw_outcomes"), "$.raw_outcomes", errors)
    if raw_outcomes is not None:
        if not raw_outcomes:
            errors.append("$.raw_outcomes must contain at least one task")
        for task_index, task in enumerate(raw_outcomes):
            _validate_task(task, f"$.raw_outcomes[{task_index}]", errors)

    manifest = _object(document.get("manifest"), "$.manifest", errors)
    if manifest:
        _require_keys(manifest, ("seeds", "task_set", "models", "cost", "preflight"), "$.manifest", errors)
        seeds = _object(manifest.get("seeds"), "$.manifest.seeds", errors)
        if seeds is not None and not seeds:
            errors.append("$.manifest.seeds must not be empty")
        task_set = _object(manifest.get("task_set"), "$.manifest.task_set", errors)
        if task_set and not _is_sha256(task_set.get("task_set_hash")):
            errors.append("$.manifest.task_set.task_set_hash must be sha256:<64 lowercase hex>")
        models = _array(manifest.get("models"), "$.manifest.models", errors)
        if models is not None and not models:
            errors.append("$.manifest.models must not be empty")
        cost = _object(manifest.get("cost"), "$.manifest.cost", errors)
        if cost and not isinstance(cost.get("total"), int | float):
            errors.append("$.manifest.cost.total must be numeric")
        preflight = _object(manifest.get("preflight"), "$.manifest.preflight", errors)
        if preflight and preflight.get("status") not in {"passed", "failed", "not-run"}:
            errors.append("$.manifest.preflight.status must be passed, failed, or not-run")

    if errors:
        raise EvidenceValidationError("; ".join(errors))


def _validate_task(value: Any, path: str, errors: list[str]) -> None:
    task = _object(value, path, errors)
    if not task:
        return
    _require_keys(task, ("task_id", "task_class", "replicates"), path, errors)
    replicates = _array(task.get("replicates"), f"{path}.replicates", errors)
    if replicates is not None:
        if not replicates:
            errors.append(f"{path}.replicates must not be empty")
        for replicate_index, replicate in enumerate(replicates):
            _validate_replicate(replicate, f"{path}.replicates[{replicate_index}]", errors)


def _validate_replicate(value: Any, path: str, errors: list[str]) -> None:
    replicate = _object(value, path, errors)
    if not replicate:
        return
    _require_keys(replicate, ("replicate", "incumbent", "candidate"), path, errors)
    if not isinstance(replicate.get("replicate"), int):
        errors.append(f"{path}.replicate must be integer")
    for model_role in ("incumbent", "candidate"):
        outcome = _object(replicate.get(model_role), f"{path}.{model_role}", errors)
        if outcome:
            _require_keys(outcome, ("success",), f"{path}.{model_role}", errors)
            success = outcome.get("success")
            if success not in {0, 1, False, True}:
                errors.append(f"{path}.{model_role}.success must be 0/1 or boolean")


def _object(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _array(value: Any, path: str, errors: list[str]) -> Sequence[Any] | None:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        errors.append(f"{path} must be an array")
        return None
    return value


def _require_keys(
    value: Mapping[str, Any],
    keys: Sequence[str],
    path: str,
    errors: list[str],
) -> None:
    for key in keys:
        if key not in value:
            errors.append(f"{path}.{key} is required")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None
