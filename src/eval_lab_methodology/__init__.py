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
from .identity_domain import (
    BASE_IMAGE_DIGEST_KEYS,
    CONFORMANCE_IDENTITY_DOMAIN,
    CONFORMANCE_IDENTITY_DOMAIN_SHA256,
    FORBIDDEN_KEYS,
    IDENTITY_DOMAIN_SCHEMA_VERSION,
    IDENTITY_DOMAIN_SECTIONS,
    IDENTITY_DOMAIN_TOP_LEVEL_KEYS,
    SHA256_PATTERN,
    canonical_json,
    identity_domain_sha256,
    validate_identity_domain,
)
from .primitives import bootstrap_ci, sign_test, wilson_interval
from .schema_contract import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceValidationError,
    validate_evidence_report,
)

__all__ = [
    "BASE_IMAGE_DIGEST_KEYS",
    "BootstrapResult",
    "CONFORMANCE_IDENTITY_DOMAIN",
    "CONFORMANCE_IDENTITY_DOMAIN_SHA256",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceValidationError",
    "FORBIDDEN_KEYS",
    "GLMMResult",
    "IDENTITY_DOMAIN_SCHEMA_VERSION",
    "IDENTITY_DOMAIN_SECTIONS",
    "IDENTITY_DOMAIN_TOP_LEVEL_KEYS",
    "OptionalDependencyError",
    "PowerPoint",
    "PowerSimulationResult",
    "SHA256_PATTERN",
    "SuperiorityDecision",
    "WilcoxonResult",
    "__core_content_hash__",
    "__core_version__",
    "bootstrap_ci",
    "canonical_json",
    "core_content_hash",
    "fit_glmm_logistic",
    "identity_domain_sha256",
    "power_simulation",
    "sign_test",
    "superiority_by_margin",
    "two_stage_bootstrap",
    "validate_evidence_report",
    "validate_identity_domain",
    "wilson_interval",
    "wilcoxon_signed_rank",
]
