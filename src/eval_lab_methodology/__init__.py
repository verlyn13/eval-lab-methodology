"""Public statistical core for the Agentic-Coding Evaluation Lab methodology."""

from __future__ import annotations

from ._version import __core_content_hash__, __core_version__, core_content_hash
from .decision import SuperiorityDecision, superiority_by_margin
from .estimators import (
    BootstrapResult,
    GLMMResult,
    OptionalDependencyError,
    PowerPoint,
    PowerSimulationResult,
    WilcoxonResult,
    fit_glmm_logistic,
    power_simulation,
    two_stage_bootstrap,
    wilcoxon_signed_rank,
)
from .primitives import bootstrap_ci, sign_test, wilson_interval
from .schema_contract import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceValidationError,
    validate_evidence_report,
)

__all__ = [
    "BootstrapResult",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceValidationError",
    "GLMMResult",
    "OptionalDependencyError",
    "PowerPoint",
    "PowerSimulationResult",
    "SuperiorityDecision",
    "WilcoxonResult",
    "__core_content_hash__",
    "__core_version__",
    "bootstrap_ci",
    "core_content_hash",
    "fit_glmm_logistic",
    "power_simulation",
    "sign_test",
    "superiority_by_margin",
    "two_stage_bootstrap",
    "validate_evidence_report",
    "wilson_interval",
    "wilcoxon_signed_rank",
]
