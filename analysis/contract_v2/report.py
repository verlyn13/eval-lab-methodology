"""Deterministic human-facing Markdown for a verified Contract B v2 draft."""

from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any], *, evidence_sha256: str) -> str:
    """Render only the independently recomputed report model."""

    registration = report["registration"]
    design = report["design"]
    attrition = report["attrition"]
    analysis = report["analysis"]
    verification = report["verification"]
    reason_explanations = {
        "METHOD_AUTHORITY_HELD": "No inferential method has been accepted for enforcing use.",
        "R1_R2_R4_HELD": (
            "The inferential basis and test, replication policy, and practical-benefit "
            "threshold remain undecided and unauthorized."
        ),
    }
    reasons = "\n".join(
        f"- `{code}` — {reason_explanations.get(code, 'Unrecognized reason code.')}"
        for code in analysis["reason_codes"]
    )
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# {report["title"]}

> **{report["decision"]}** — {report["claim_boundary"]}

## Registration

- Receipt: `{registration["receipt_sha256"]}`
- Informational verification result: `{registration["verification_result_sha256"]}`
- Provenance: `{registration["provenance"]}`

## Design and data integrity

- Campaign type: `{design["campaign_type"]}`
- Scheduled attempts: `{design["scheduled_attempts"]}`
- Observed attempts: `{attrition["observed_attempts"]}`
- Gateway retry attempts: `{attrition["retry_attempts"]}`
- Method authority: `{design["method_authority"]}`
- Science protocol: `{design["science_protocol_sha256"]}`
- Task-set reveal: `{design["task_set_sha256"]}`
- Assignment schedule: `{design["assignment_schedule_sha256"]}`

## Analysis

- Status: `{analysis["status"]}`
- Statistics emitted: `{analysis["statistics_emitted"]}`
- Reason codes:

{reasons}

No enforcing test, promotion rule, replicate policy, margin, or minimum practical
benefit is installed by this draft.

## Provenance and independent verification

- Gateway invocation-open receipts: `{len(report["provenance"]["gateway_open_receipts"])}`
- Gateway call receipts: `{len(report["provenance"]["gateway_receipts"])}`
- Gateway invocation-closure receipts: `{len(report["provenance"]["gateway_closure_receipts"])}`
- Editing-harness descriptor-validation receipts: `{len(report["provenance"]["editing_harness_validation_receipts"])}`
- Evaluation-harness completion receipts: `{len(report["provenance"]["harness_completion_receipts"])}`
- Provenance upgrades: `{report["provenance"]["provenance_upgrades"]}`
- Verified evidence: `{evidence_sha256}`
- Contract schema: `{verification["contract_schema_version"]}`
- Contract schema bytes: `{verification["contract_schema_sha256"]}`
- Verifier implementation: `{verification["verifier_implementation_version"]}`
- Verifier/report/safety implementation bundle: `{verification["verifier_implementation_bundle_sha256"]}`
- Recomputed analysis result: `{verification["analysis_result_sha256"]}`
- Recomputed decision receipt: `{verification["decision_receipt_sha256"]}`

## Limitations

{limitations}
"""
