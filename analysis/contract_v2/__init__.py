"""Repository-only Contract B v2 draft and independent verifier.

This package is deliberately outside ``src/eval_lab_methodology``.  It is a
normative *draft* for review, not part of the released 0.2.0 wheel and not an
accepted statistical method.
"""

from .verification import (
    CONTRACT_V2_SCHEMA_VERSION,
    VerificationRefusal,
    VerifiedContractV2,
    canonical_json_bytes,
    recompute_or_refuse,
    sha256_bytes,
    verify_exact_bytes,
)

__all__ = [
    "CONTRACT_V2_SCHEMA_VERSION",
    "VerificationRefusal",
    "VerifiedContractV2",
    "canonical_json_bytes",
    "recompute_or_refuse",
    "sha256_bytes",
    "verify_exact_bytes",
]
