"""Runtime checks for the public evidence contract.

This is deliberately small and dependency-free. The normative machine-readable
contract remains ``evidence/schema.json``; these checks cover the public sample
and give offline callers a fail-closed validator for the required core shape.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

EVIDENCE_SCHEMA_VERSION = "1.1.0"

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
        errors.append("$.schema_version must be 1.1.0")

    core = _object(document.get("core"), "$.core", errors)
    if core is not None:
        _require_keys(core, ("core_version", "core_content_hash"), "$.core", errors)
        if not isinstance(core.get("core_version"), str) or not core.get("core_version"):
            errors.append("$.core.core_version must be a non-empty string")
        if not _is_sha256(core.get("core_content_hash")):
            errors.append("$.core.core_content_hash must be sha256:<64 lowercase hex>")

    report = _object(document.get("report"), "$.report", errors)
    if report is not None:
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
        if decision is not None:
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
            if sign_test is not None and sign_test.get("reported_only") is not True:
                errors.append("$.report.decision.sign_test.reported_only must be true")

    raw_outcomes = _array(document.get("raw_outcomes"), "$.raw_outcomes", errors)
    if raw_outcomes is not None:
        if not raw_outcomes:
            errors.append("$.raw_outcomes must contain at least one task")
        for task_index, task in enumerate(raw_outcomes):
            _validate_task(task, f"$.raw_outcomes[{task_index}]", errors)

    manifest = _object(document.get("manifest"), "$.manifest", errors)
    if manifest is not None:
        _require_keys(
            manifest,
            ("identity_domain", "seeds", "task_set", "models", "cost", "preflight", "sanitization"),
            "$.manifest",
            errors,
        )
        identity_domain = _object(
            manifest.get("identity_domain"), "$.manifest.identity_domain", errors
        )
        if identity_domain is not None:
            _require_keys(
                identity_domain,
                (
                    "status",
                    "identity_domain_sha256",
                    "candidate_identity_domain_sha256",
                    "incumbent_identity_domain_sha256",
                    "observed_identity_domain_sha256s",
                    "bridge_authorization",
                    "reason",
                ),
                "$.manifest.identity_domain",
                errors,
            )
            status = identity_domain.get("status")
            if status not in {"matched", "bridge-authorized"}:
                errors.append("$.manifest.identity_domain.status must be matched or bridge-authorized")
            value = identity_domain.get("identity_domain_sha256")
            if value is not None and not _is_sha256(value):
                errors.append(
                    "$.manifest.identity_domain.identity_domain_sha256 must be null or "
                    "sha256:<64 lowercase hex>"
                )
            if status == "matched" and not _is_sha256(value):
                errors.append(
                    "$.manifest.identity_domain.identity_domain_sha256 is required when status is matched"
                )
            for key in ("candidate_identity_domain_sha256", "incumbent_identity_domain_sha256"):
                if not _is_sha256(identity_domain.get(key)):
                    errors.append(f"$.manifest.identity_domain.{key} must be sha256:<64 lowercase hex>")
            observed = _array(
                identity_domain.get("observed_identity_domain_sha256s"),
                "$.manifest.identity_domain.observed_identity_domain_sha256s",
                errors,
            )
            if observed is not None:
                if not observed:
                    errors.append(
                        "$.manifest.identity_domain.observed_identity_domain_sha256s must not be empty"
                    )
                for index, item in enumerate(observed):
                    if not _is_sha256(item):
                        errors.append(
                            "$.manifest.identity_domain.observed_identity_domain_sha256s"
                            f"[{index}] must be sha256:<64 lowercase hex>"
                        )
            if status == "matched" and _is_sha256(value):
                for key in ("candidate_identity_domain_sha256", "incumbent_identity_domain_sha256"):
                    other = identity_domain.get(key)
                    if _is_sha256(other) and other != value:
                        errors.append(
                            f"$.manifest.identity_domain.{key} must equal "
                            "identity_domain_sha256 when status is matched"
                        )
                if observed is not None and value not in observed:
                    errors.append(
                        "$.manifest.identity_domain.identity_domain_sha256 must appear in "
                        "observed_identity_domain_sha256s when status is matched"
                    )
            bridge = identity_domain.get("bridge_authorization")
            if status == "bridge-authorized":
                bridge_object = _object(bridge, "$.manifest.identity_domain.bridge_authorization", errors)
                if bridge_object is not None:
                    _require_keys(
                        bridge_object,
                        ("bridge_id", "reason"),
                        "$.manifest.identity_domain.bridge_authorization",
                        errors,
                    )
                    for key in ("bridge_id", "reason", "authorized_by"):
                        if key not in bridge_object:
                            continue
                        item = bridge_object.get(key)
                        if not isinstance(item, str) or not item:
                            errors.append(
                                f"$.manifest.identity_domain.bridge_authorization.{key} "
                                "must be a non-empty string"
                            )
            elif bridge is not None:
                errors.append("$.manifest.identity_domain.bridge_authorization must be null when matched")
            if not isinstance(identity_domain.get("reason"), str) or not identity_domain.get("reason"):
                errors.append("$.manifest.identity_domain.reason must be a non-empty string")
        seeds = _object(manifest.get("seeds"), "$.manifest.seeds", errors)
        if seeds is not None and not seeds:
            errors.append("$.manifest.seeds must not be empty")
        task_set = _object(manifest.get("task_set"), "$.manifest.task_set", errors)
        if task_set is not None and not _is_sha256(task_set.get("task_set_hash")):
            errors.append("$.manifest.task_set.task_set_hash must be sha256:<64 lowercase hex>")
        models = _array(manifest.get("models"), "$.manifest.models", errors)
        if models is not None and not models:
            errors.append("$.manifest.models must not be empty")
        cost = _object(manifest.get("cost"), "$.manifest.cost", errors)
        if cost is not None and not isinstance(cost.get("total"), int | float):
            errors.append("$.manifest.cost.total must be numeric")
        preflight = _object(manifest.get("preflight"), "$.manifest.preflight", errors)
        if preflight is not None and preflight.get("status") not in {"passed", "failed", "not-run"}:
            errors.append("$.manifest.preflight.status must be passed, failed, or not-run")

    if errors:
        raise EvidenceValidationError("; ".join(errors))


def _validate_task(value: Any, path: str, errors: list[str]) -> None:
    task = _object(value, path, errors)
    if task is None:
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
    if replicate is None:
        return
    _require_keys(replicate, ("replicate", "incumbent", "candidate"), path, errors)
    if not isinstance(replicate.get("replicate"), int):
        errors.append(f"{path}.replicate must be integer")
    for model_role in ("incumbent", "candidate"):
        outcome = _object(replicate.get(model_role), f"{path}.{model_role}", errors)
        if outcome is not None:
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
