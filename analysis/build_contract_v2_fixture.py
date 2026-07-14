"""Build the deterministic synthetic Contract B v2 NOT_EVALUABLE fixture."""

from __future__ import annotations

import copy
import hashlib
import hmac
from pathlib import Path
from typing import Any

from analysis.contract_v2.verification import (
    ANALYSIS_RESULT_VERSION,
    CONTRACT_V2_SCHEMA_VERSION,
    DECISION_RECEIPT_VERSION,
    EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
    EVAL_REGISTRY_PLAN_DOMAIN,
    EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256,
    EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
    EVAL_REGISTRY_TASK_SET_DOMAIN,
    EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256,
    EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
    HUMAN_REPORT_VERSION,
    SYNTHETIC_HELD_METHOD_SHA256,
    SYNTHETIC_HELD_METHOD_VERSION,
    VERIFIER_IMPLEMENTATION_VERSION,
    canonical_json_bytes,
    contract_schema_sha256,
    gateway_ordered_call_bindings_sha256,
    recompute_or_refuse,
    sha256_bytes,
    verifier_implementation_bundle_sha256,
    verifier_implementation_manifest,
)
from analysis.contract_v2.report import render_markdown

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evidence" / "contract-v2" / "synthetic-not-evaluable.json"
REPORT = ROOT / "evidence" / "contract-v2" / "synthetic-not-evaluable-report.md"

SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64


def digest(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def commitment(nonce_hex: str, domain: str, exact_bytes: bytes) -> str:
    return (
        "hmac-sha256:"
        + hmac.new(
            bytes.fromhex(nonce_hex),
            domain.encode("utf-8") + exact_bytes,
            hashlib.sha256,
        ).hexdigest()
    )


def receipt_for(label: str) -> str:
    return sha256_bytes(f"synthetic:{label}\n".encode())


def fact(
    field: str, value: Any, *, observer: str, receipt: str, provenance: str
) -> dict[str, Any]:
    return {
        "schema_version": "agentic-coding-evaluation-lab.provenance-fact.v2.0.0-draft.1",
        "field": field,
        "value": value,
        "provenance": provenance,
        "custody": "copied",
        "originating_observer": observer,
        "originating_receipt_sha256": receipt,
        "source": {
            "schema_version": "agentic-coding-evaluation-lab.source-provenance.v2.0.0-draft.1",
            "observer": observer,
            "provenance": provenance,
            "receipt_sha256": receipt,
        },
    }


def build() -> dict[str, Any]:
    family_commitment = commitment(
        "33" * 32,
        EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
        b"synthetic-family-001\n",
    )
    campaign = {
        "schema_version": "agentic-coding-evaluation-lab.campaign.v2.0.0-draft.1",
        "campaign_id": "urn:uuid:00000000-0000-4000-8000-000000000001",
        "campaign_type": "synthetic_contract_check",
        "campaign_family_commitment": family_commitment,
        "attempt_ordinal": 1,
    }
    task_set = {
        "schema_version": "agentic-coding-evaluation-lab.task-set-reveal.v2.0.0-draft.1",
        "tasks": [
            {
                "schema_version": "agentic-coding-evaluation-lab.task-descriptor.v2.0.0-draft.1",
                "task_id": "synthetic-task-01",
                "task_class": "synthetic-edit",
            },
            {
                "schema_version": "agentic-coding-evaluation-lab.task-descriptor.v2.0.0-draft.1",
                "task_id": "synthetic-task-02",
                "task_class": "synthetic-reasoning",
            },
        ],
    }
    schedule = {
        "schema_version": "agentic-coding-evaluation-lab.assignment-schedule.v2.0.0-draft.1",
        "assignment_mechanism": "synthetic-balanced-order",
        "units": [
            {
                "schema_version": "agentic-coding-evaluation-lab.assignment-unit.v2.0.0-draft.1",
                "task_pair_id": "pair-01",
                "task_id": "synthetic-task-01",
                "session_id": "session-01",
                "arm_order": ["incumbent", "candidate"],
                "attempt_ids": {
                    "schema_version": "agentic-coding-evaluation-lab.assignment-attempt-ids.v2.0.0-draft.1",
                    "incumbent": "attempt-01-incumbent",
                    "candidate": "attempt-01-candidate",
                },
            },
            {
                "schema_version": "agentic-coding-evaluation-lab.assignment-unit.v2.0.0-draft.1",
                "task_pair_id": "pair-02",
                "task_id": "synthetic-task-02",
                "session_id": "session-02",
                "arm_order": ["candidate", "incumbent"],
                "attempt_ids": {
                    "schema_version": "agentic-coding-evaluation-lab.assignment-attempt-ids.v2.0.0-draft.1",
                    "incumbent": "attempt-02-incumbent",
                    "candidate": "attempt-02-candidate",
                },
            },
        ],
    }
    held = {
        "schema_version": "agentic-coding-evaluation-lab.held-decision-input.v2.0.0-draft.1",
        "status": "held",
        "specification": None,
    }
    protocol = {
        "schema_version": "agentic-coding-evaluation-lab.science-protocol.v2.0.0-draft.1",
        "campaign_id": campaign["campaign_id"],
        "campaign_type": campaign["campaign_type"],
        "target_task_universe": "two public synthetic structure-check tasks; no inferential population",
        "outcome_definition": "terminal attempt status only; no capability score",
        "estimand": copy.deepcopy(held),
        "method": copy.deepcopy(held),
        "replicate_policy": copy.deepcopy(held),
        "margin": copy.deepcopy(held),
        "mpib": copy.deepcopy(held),
        "missingness_policy": "every scheduled attempt must have one terminal record; no silent drop",
        "assignment_schedule_sha256": digest(schedule),
        "task_set_sha256": digest(task_set),
    }
    protocol_bytes = canonical_json_bytes(protocol)
    task_set_bytes = canonical_json_bytes(task_set)
    plan_nonce = "11" * 32
    task_nonce = "22" * 32
    receipt_payload = {
        "schema_version": EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        "campaign_id": campaign["campaign_id"],
        "plan_commitment": {
            "algorithm": "hmac-sha256",
            "domain": EVAL_REGISTRY_PLAN_DOMAIN,
            "value": commitment(plan_nonce, EVAL_REGISTRY_PLAN_DOMAIN, protocol_bytes),
        },
        "task_set_commitment": {
            "algorithm": "hmac-sha256",
            "domain": EVAL_REGISTRY_TASK_SET_DOMAIN,
            "value": commitment(
                task_nonce, EVAL_REGISTRY_TASK_SET_DOMAIN, task_set_bytes
            ),
        },
        "methodology": {
            "version": SYNTHETIC_HELD_METHOD_VERSION,
            "method_sha256": SYNTHETIC_HELD_METHOD_SHA256,
        },
        "campaign_family_commitment": {
            "algorithm": "hmac-sha256",
            "domain": EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
            "value": family_commitment,
        },
        "attempt_ordinal": campaign["attempt_ordinal"],
        "signer_policy": {
            "certificate_identity": "urn:synthetic:unconfigured-certificate-identity",
            "oidc_issuer": "urn:synthetic:unconfigured-oidc-issuer",
            "trust_policy_version": "synthetic-d2-unconfigured",
            "trust_policy_sha256": SHA_C,
        },
        "signature_bundle": {
            "kind": "sigstore-bundle",
            "path": "signature.bundle.json",
        },
        "verification_result": {
            "path": "verification.json",
            "authoritative": False,
        },
    }
    exact_receipt_json = canonical_json_bytes(receipt_payload).decode("utf-8")
    registration_receipt_sha256 = sha256_bytes(exact_receipt_json.encode("utf-8"))
    verification_result = {
        "schema_version": EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
        "authoritative": False,
        "record_schema_version": EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        "signed_record_sha256": registration_receipt_sha256,
        "signature_bundle_sha256": SHA_B,
        "trust_policy_sha256": SHA_C,
        "verdict": "refused",
        "verified_tsa_time": None,
        "checks": {
            "exact_schema": "not_checked",
            "signature": "not_checked",
            "certificate_identity": "not_checked",
            "oidc_issuer": "not_checked",
            "certificate_chain": "not_checked",
            "tsa_signature": "not_checked",
            "tsa_imprint_is_signature_bytes": "not_checked",
            "certificate_valid_at_tsa_time": "not_checked",
            "transparency_inclusion": "not_checked",
            "transparency_checkpoint": "not_checked",
        },
        "reasons": ["synthetic D2 structure; no operational trust policy"],
    }
    exact_verification_json = canonical_json_bytes(verification_result).decode("utf-8")
    registration = {
        "schema_version": "agentic-coding-evaluation-lab.registration-binding.v2.0.0-draft.1",
        "owner_contract": {
            "schema_version": "agentic-coding-evaluation-lab.registry-contract-binding.v2.0.0-draft.1",
            "registration_schema_version": EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
            "registration_schema_sha256": EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256,
            "verification_schema_version": EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
            "verification_schema_sha256": EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256,
            "operational_adapter_status": "synthetic-non-authoritative",
        },
        "receipt_copy": {
            "schema_version": "agentic-coding-evaluation-lab.exact-registration-receipt-copy.v2.0.0-draft.1",
            "exact_receipt_json_utf8": exact_receipt_json,
            "registration_receipt_sha256": registration_receipt_sha256,
            "custody": "copied",
            "provenance": "attested",
        },
        "originating_verification_copy": {
            "schema_version": "agentic-coding-evaluation-lab.exact-verification-result-copy.v2.0.0-draft.1",
            "exact_verification_json_utf8": exact_verification_json,
            "verification_result_sha256": sha256_bytes(
                exact_verification_json.encode("utf-8")
            ),
            "custody": "copied",
            "provenance": "attested",
        },
        "reveal": {
            "schema_version": "agentic-coding-evaluation-lab.registration-reveal.v2.0.0-draft.1",
            "status": "synthetic_commitments_verified",
            "plan_nonce_hex": plan_nonce,
            "task_set_nonce_hex": task_nonce,
            "science_protocol_exact_json_utf8": protocol_bytes.decode("utf-8"),
            "task_set_exact_json_utf8": task_set_bytes.decode("utf-8"),
            "science_protocol_sha256": sha256_bytes(protocol_bytes),
            "task_set_sha256": sha256_bytes(task_set_bytes),
        },
    }

    attempts: list[dict[str, Any]] = []
    gateway_opens: list[dict[str, Any]] = []
    gateway: list[dict[str, Any]] = []
    gateway_closures: list[dict[str, Any]] = []
    descriptor_validations: list[dict[str, Any]] = []
    completions: list[dict[str, Any]] = []
    for unit in schedule["units"]:
        for position, arm in enumerate(unit["arm_order"], start=1):
            attempt_id = unit["attempt_ids"][arm]
            invocation_id = f"invocation-{attempt_id}"
            request_id = f"request-{attempt_id}-01"
            open_receipt = receipt_for(f"gateway-open:{invocation_id}")
            attempts.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.attempt.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "task_pair_id": unit["task_pair_id"],
                    "task_id": unit["task_id"],
                    "session_id": unit["session_id"],
                    "arm": arm,
                    "attempt_index": 1,
                    "attempt_position_in_pair": position,
                    "status": "succeeded",
                    "error_class": None,
                }
            )
            gateway_opens.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.gateway-invocation-open.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "invocation_id": invocation_id,
                    "observer": "openai-compatible-gateway",
                    "owner_receipt_schema_version": "synthetic.gateway.invocation-open.v1",
                    "owner_schema_status": "synthetic-fixture-unratified",
                    "open_receipt_sha256": open_receipt,
                    "facts": [
                        fact(
                            "invocation_id",
                            invocation_id,
                            observer="openai-compatible-gateway",
                            receipt=open_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "invocation_opened",
                            True,
                            observer="openai-compatible-gateway",
                            receipt=open_receipt,
                            provenance="measured",
                        ),
                    ],
                }
            )
            gateway_receipt = receipt_for(f"gateway:{request_id}")
            gateway.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.gateway-observation.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "invocation_id": invocation_id,
                    "request_id": request_id,
                    "call_ordinal": 1,
                    "observer": "openai-compatible-gateway",
                    "owner_receipt_schema_version": "synthetic.gateway.call-observation.v1",
                    "owner_schema_status": "synthetic-fixture-unratified",
                    "observation_receipt_sha256": gateway_receipt,
                    "facts": [
                        fact(
                            "invocation_id",
                            invocation_id,
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "request_id",
                            request_id,
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "call_ordinal",
                            1,
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "request_attempt_count",
                            1,
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "request_attempt_vector",
                            [
                                {
                                    "attempt_ordinal": 1,
                                    "outcome": "succeeded",
                                    "error_class": None,
                                }
                            ],
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "fallback_used",
                            False,
                            observer="openai-compatible-gateway",
                            receipt=gateway_receipt,
                            provenance="measured",
                        ),
                    ],
                }
            )
            descriptor_receipt = receipt_for(f"descriptor-validation:{attempt_id}")
            descriptor_validations.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.editing-harness-descriptor-validation.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "invocation_id": invocation_id,
                    "observer": "editing-harness-owner-validator",
                    "owner_receipt_schema_version": "synthetic.editing-harness.descriptor-validation.v1",
                    "owner_schema_status": "synthetic-fixture-unratified",
                    "validation_receipt_sha256": descriptor_receipt,
                    "facts": [
                        fact(
                            "invocation_id",
                            invocation_id,
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "invocation_descriptor_sha256",
                            receipt_for(f"descriptor:{attempt_id}"),
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "descriptor_schema_sha256",
                            receipt_for("descriptor-schema:synthetic-v1"),
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "validator_sha256",
                            receipt_for("descriptor-validator:synthetic-v1"),
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "runtime_version_sha256",
                            receipt_for("editing-runtime:synthetic-0"),
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "retry_policy",
                            "exposed",
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "descriptor_valid",
                            True,
                            observer="editing-harness-owner-validator",
                            receipt=descriptor_receipt,
                            provenance="measured",
                        ),
                    ],
                }
            )
            completion_receipt = receipt_for(f"completion:{attempt_id}")
            completions.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.harness-completion-observation.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "invocation_id": invocation_id,
                    "observer": "evaluation-harness",
                    "owner_receipt_schema_version": "synthetic.evaluation-harness.completion.v1",
                    "owner_schema_status": "synthetic-fixture-unratified",
                    "completion_receipt_sha256": completion_receipt,
                    "facts": [
                        fact(
                            "invocation_id",
                            invocation_id,
                            observer="evaluation-harness",
                            receipt=completion_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "process_completed",
                            True,
                            observer="evaluation-harness",
                            receipt=completion_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "completion_status",
                            "succeeded",
                            observer="evaluation-harness",
                            receipt=completion_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "exit_code",
                            0,
                            observer="evaluation-harness",
                            receipt=completion_receipt,
                            provenance="measured",
                        ),
                    ],
                }
            )
            closure_receipt = receipt_for(f"gateway-closure:{invocation_id}")
            gateway_closures.append(
                {
                    "schema_version": "agentic-coding-evaluation-lab.gateway-invocation-closure.v2.0.0-draft.1",
                    "attempt_id": attempt_id,
                    "invocation_id": invocation_id,
                    "observer": "openai-compatible-gateway",
                    "owner_receipt_schema_version": "synthetic.gateway.invocation-closure.v1",
                    "owner_schema_status": "synthetic-fixture-unratified",
                    "closure_receipt_sha256": closure_receipt,
                    "facts": [
                        fact(
                            "invocation_id",
                            invocation_id,
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "open_receipt_sha256",
                            open_receipt,
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "invocation_closed",
                            True,
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="measured",
                        ),
                        fact(
                            "gateway_call_count",
                            1,
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "ordered_request_ids_sha256",
                            digest([request_id]),
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="derived",
                        ),
                        fact(
                            "ordered_call_bindings_sha256",
                            gateway_ordered_call_bindings_sha256(
                                [(request_id, gateway_receipt)]
                            ),
                            observer="openai-compatible-gateway",
                            receipt=closure_receipt,
                            provenance="derived",
                        ),
                    ],
                }
            )

    attrition = {
        "schema_version": "agentic-coding-evaluation-lab.attrition.v2.0.0-draft.1",
        "scheduled_attempts": 4,
        "observed_attempts": 4,
        "terminal_status_counts": {"succeeded": 4},
        "failures": [],
        "excluded_attempt_ids": [],
        "retry_attempts": 0,
    }
    verifier = {
        "implementation_version": VERIFIER_IMPLEMENTATION_VERSION,
        "implementation_files": verifier_implementation_manifest(),
        "implementation_bundle_sha256": verifier_implementation_bundle_sha256(),
        "custody": "repository-only",
        "release_status": "unreleased-draft",
    }
    analysis_input = {
        "campaign": campaign,
        "verifier": verifier,
        "science_protocol": protocol,
        "registration": registration,
        "assignment_schedule": schedule,
        "attempts": attempts,
        "attrition": attrition,
        "gateway_invocation_opens": gateway_opens,
        "gateway_observations": gateway,
        "gateway_invocation_closures": gateway_closures,
        "editing_harness_descriptor_validations": descriptor_validations,
        "harness_completion_observations": completions,
    }
    reasons = ["METHOD_AUTHORITY_HELD", "R1_R2_R4_HELD"]
    analysis = {
        "schema_version": ANALYSIS_RESULT_VERSION,
        "analysis_input_sha256": digest(analysis_input),
        "status": "not_evaluable",
        "method_authority": "held",
        "method_id": None,
        "statistics": {},
        "reason_codes": reasons,
    }
    decision = {
        "schema_version": DECISION_RECEIPT_VERSION,
        "analysis_result_sha256": digest(analysis),
        "outcome": "NOT_EVALUABLE",
        "enforcing_rule": None,
        "promotion_recommendation": None,
        "reason_codes": reasons,
    }
    report = {
        "schema_version": HUMAN_REPORT_VERSION,
        "title": "Synthetic Contract B v2 refusal example",
        "decision": "NOT_EVALUABLE",
        "claim_boundary": "Contract structure and independent refusal behavior only; no model or population claim.",
        "registration": {
            "receipt_sha256": registration["receipt_copy"][
                "registration_receipt_sha256"
            ],
            "verification_result_sha256": registration["originating_verification_copy"][
                "verification_result_sha256"
            ],
            "provenance": "copied-attested-synthetic",
        },
        "design": {
            "campaign_type": campaign["campaign_type"],
            "scheduled_attempts": 4,
            "method_authority": "held",
            "science_protocol_sha256": registration["reveal"][
                "science_protocol_sha256"
            ],
            "task_set_sha256": registration["reveal"]["task_set_sha256"],
            "assignment_schedule_sha256": digest(schedule),
        },
        "attrition": attrition,
        "provenance": {
            "gateway_open_receipts": [
                item["open_receipt_sha256"] for item in gateway_opens
            ],
            "gateway_receipts": [
                item["observation_receipt_sha256"] for item in gateway
            ],
            "gateway_closure_receipts": [
                item["closure_receipt_sha256"] for item in gateway_closures
            ],
            "editing_harness_validation_receipts": [
                item["validation_receipt_sha256"] for item in descriptor_validations
            ],
            "harness_completion_receipts": [
                item["completion_receipt_sha256"] for item in completions
            ],
            "provenance_upgrades": 0,
        },
        "analysis": {
            "status": "not_evaluable",
            "statistics_emitted": 0,
            "reason_codes": reasons,
        },
        "verification": {
            "contract_schema_version": CONTRACT_V2_SCHEMA_VERSION,
            "contract_schema_sha256": contract_schema_sha256(),
            "verifier_implementation_version": VERIFIER_IMPLEMENTATION_VERSION,
            "verifier_implementation_bundle_sha256": verifier_implementation_bundle_sha256(),
            "analysis_result_sha256": digest(analysis),
            "decision_receipt_sha256": digest(decision),
        },
        "limitations": [
            "Synthetic structure only; no real request, response, task, grader, model, or deployment observation.",
            "No inferential basis, enforcing test, replicate policy, margin, or minimum practical benefit is selected.",
            "Copied verifier metadata is informational and is not independent cryptographic verification.",
            "The registry verification result refuses under D2; no operational signer identity, issuer, trust policy, signature, or trusted timestamp is claimed.",
            "Editing-harness, evaluation-harness, and gateway owner receipt schemas and provenance classes are synthetic unratified fixtures, not operational adapters.",
            "Operational adoption must validate exact owner receipts against frozen owner schemas and must not trust copied source envelopes as verification inputs.",
        ],
    }
    return {
        "schema_version": CONTRACT_V2_SCHEMA_VERSION,
        "contract_status": "normative_draft",
        "provenance": "synthetic",
        "operational_authority": False,
        "campaign": campaign,
        "verifier": verifier,
        "science_protocol": protocol,
        "task_set_reveal": task_set,
        "registration": registration,
        "assignment_schedule": schedule,
        "attempts": attempts,
        "attrition": attrition,
        "gateway_invocation_opens": gateway_opens,
        "gateway_observations": gateway,
        "gateway_invocation_closures": gateway_closures,
        "editing_harness_descriptor_validations": descriptor_validations,
        "harness_completion_observations": completions,
        "analysis_result": analysis,
        "decision_receipt": decision,
        "human_report": report,
        "sanitization": {
            "schema_version": "agentic-coding-evaluation-lab.sanitization.v2.0.0-draft.1",
            "status": "public-safe",
            "checked": True,
            "redactions_required": False,
            "notes": "synthetic structure-only fixture",
        },
    }


def main() -> int:
    document = build()
    verified = recompute_or_refuse(document)
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_bytes(canonical_json_bytes(document))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        render_markdown(
            verified.human_report, evidence_sha256=verified.evidence_sha256
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
