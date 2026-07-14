"""Pure, deterministic recompute-or-refuse logic for Contract B v2 draft.

The verifier accepts exact JSON bytes, rejects duplicate keys and non-finite
numbers, validates every cross-artifact join, independently derives the
attrition, analysis, decision, and human-report models, and compares producer
claims byte-for-byte after canonical encoding.  No inferential method is
installed: the only scientifically valid draft outcome is ``NOT_EVALUABLE``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.publication_safety import assert_publication_content_is_safe

CONTRACT_V2_SCHEMA_VERSION = "agentic-coding-evaluation-lab.evidence.v2.0.0-draft.1"
ANALYSIS_RESULT_VERSION = "agentic-coding-evaluation-lab.analysis-result.v2.0.0-draft.1"
DECISION_RECEIPT_VERSION = (
    "agentic-coding-evaluation-lab.decision-receipt.v2.0.0-draft.1"
)
HUMAN_REPORT_VERSION = "agentic-coding-evaluation-lab.human-report.v2.0.0-draft.1"
VERIFIER_IMPLEMENTATION_VERSION = (
    "agentic-coding-evaluation-lab.contract-v2-verifier.v2.0.0-draft.1"
)
EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION = "eval-registry.registration-receipt.v1"
EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256 = (
    "sha256:0b8da51cd642ef04af884c2ceb70489be3843a8d562a44b16025d0ce6f632b2d"
)
EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION = "eval-registry.verification-result.v1"
EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256 = (
    "sha256:e7f1813769276deb8faa8dbfe3f8ded54eafceed611500bb7e94290c24a73bbc"
)
EVAL_REGISTRY_PLAN_DOMAIN = "eval-registry.plan.v1\x00"
EVAL_REGISTRY_TASK_SET_DOMAIN = "eval-registry.task-set.v1\x00"
EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN = "eval-registry.campaign-family.v1\x00"
GATEWAY_ORDERED_CALL_BINDINGS_DOMAIN = (
    "agentic-coding-evaluation-lab.gateway-ordered-call-bindings.v2.0.0-draft.1\x00"
)
SYNTHETIC_HELD_METHOD_VERSION = "synthetic-held-method-placeholder"
SYNTHETIC_HELD_METHOD_SHA256 = (
    "sha256:41633d855dab29ef06292445d5a55dcdef63f8e14d432acc6a07ea6b3b3363ec"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_SCHEMA_PATH = REPO_ROOT / "evidence" / "schema-v2.0.0-draft.1.json"
VERIFIER_IMPLEMENTATION_FILES = (
    "analysis/contract_v2/verification.py",
    "analysis/contract_v2/report.py",
    "scripts/publication_safety.py",
)

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_HMAC_SHA256 = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")
_UUID_URN = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_REASONS = ("METHOD_AUTHORITY_HELD", "R1_R2_R4_HELD")
_TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_status",
    "provenance",
    "operational_authority",
    "campaign",
    "verifier",
    "science_protocol",
    "task_set_reveal",
    "registration",
    "assignment_schedule",
    "attempts",
    "attrition",
    "gateway_invocation_opens",
    "gateway_observations",
    "gateway_invocation_closures",
    "editing_harness_descriptor_validations",
    "harness_completion_observations",
    "analysis_result",
    "decision_receipt",
    "human_report",
    "sanitization",
}


class VerificationRefusal(ValueError):
    """Raised when exact evidence cannot be independently verified."""


@dataclass(frozen=True)
class VerifiedContractV2:
    """A verified synthetic draft and its independently recomputed products."""

    evidence_sha256: str
    analysis_result: dict[str, Any]
    analysis_result_sha256: str
    decision_receipt: dict[str, Any]
    decision_receipt_sha256: str
    human_report: dict[str, Any]
    human_report_sha256: str


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationRefusal(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise VerificationRefusal(f"non-finite JSON number is forbidden: {value}")


def load_json_exact(payload: bytes) -> dict[str, Any]:
    """Decode exact UTF-8 JSON with duplicate-key and non-finite refusal."""

    try:
        decoded = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerificationRefusal("evidence must be UTF-8 JSON") from exc
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_non_finite,
        )
    except json.JSONDecodeError as exc:
        raise VerificationRefusal(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationRefusal("evidence root must be an object")
    _assert_finite(value, "$")
    return value


def _assert_finite(value: Any, path: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise VerificationRefusal(f"{path} contains a non-finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, f"{path}[{index}]")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the draft's deterministic UTF-8 JSON representation."""

    _assert_finite(value, "$")
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def gateway_ordered_call_bindings_sha256(
    calls: list[tuple[str, str]],
) -> str:
    """Bind ordered request identifiers to their owner observation receipts."""

    bindings = [
        {
            "request_id": request_id,
            "observation_receipt_sha256": receipt_sha256,
        }
        for request_id, receipt_sha256 in calls
    ]
    return sha256_bytes(
        GATEWAY_ORDERED_CALL_BINDINGS_DOMAIN.encode("utf-8")
        + canonical_json_bytes(bindings)
    )


def _validate_contract_schema(document: dict[str, Any]) -> None:
    """Require Draft 2020-12 validation on the exact verification path."""

    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        raise VerificationRefusal(
            "Draft 2020-12 validation requires jsonschema; install the project dev dependencies"
        ) from exc
    try:
        schema = load_json_exact(CONTRACT_SCHEMA_PATH.read_bytes())
        validator = jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        )
        validator.check_schema(schema)
        validator.validate(document)
    except OSError as exc:
        raise VerificationRefusal(
            f"cannot read Contract B v2 schema: {CONTRACT_SCHEMA_PATH}"
        ) from exc
    except (jsonschema.SchemaError, jsonschema.ValidationError) as exc:
        location = "$"
        if exc.absolute_path:
            location += "".join(
                f"[{item}]" if isinstance(item, int) else f".{item}"
                for item in exc.absolute_path
            )
        raise VerificationRefusal(
            f"Draft 2020-12 schema validation failed at {location}: {exc.message}"
        ) from exc


def contract_schema_sha256() -> str:
    """Digest the immutable schema bytes, separately from verifier implementation."""

    return sha256_bytes(CONTRACT_SCHEMA_PATH.read_bytes())


def verifier_implementation_manifest() -> list[dict[str, str]]:
    """Return the ordered path-and-byte-digest manifest for enforcing code."""

    return [
        {
            "path": relative_path,
            "sha256": sha256_bytes((REPO_ROOT / relative_path).read_bytes()),
        }
        for relative_path in VERIFIER_IMPLEMENTATION_FILES
    ]


def verifier_implementation_bundle_sha256() -> str:
    """Digest the verifier, report renderer, and publication-safety manifest."""

    return _canonical_sha256(verifier_implementation_manifest())


def _hmac_commitment(*, nonce_hex: str, domain: str, exact_bytes: bytes) -> str:
    try:
        nonce = bytes.fromhex(nonce_hex)
    except ValueError as exc:
        raise VerificationRefusal("reveal nonce must be lowercase hexadecimal") from exc
    if not nonce or nonce_hex != nonce.hex():
        raise VerificationRefusal(
            "reveal nonce must be non-empty lowercase hexadecimal"
        )
    digest = hmac.new(
        nonce,
        domain.encode("utf-8") + exact_bytes,
        hashlib.sha256,
    ).hexdigest()
    return "hmac-sha256:" + digest


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationRefusal(message)


def _expect_object(value: Any, path: str) -> dict[str, Any]:
    _expect(isinstance(value, dict), f"{path} must be an object")
    return value


def _expect_array(value: Any, path: str) -> list[Any]:
    _expect(isinstance(value, list), f"{path} must be an array")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], path: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    _expect(not missing, f"{path} missing keys: {', '.join(missing)}")
    _expect(not extra, f"{path} has unknown keys: {', '.join(extra)}")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _is_hmac_sha256(value: Any) -> bool:
    return isinstance(value, str) and _HMAC_SHA256.fullmatch(value) is not None


def _validate_provenance_fact(
    value: Any,
    *,
    path: str,
    expected_receipt: str,
    expected_observer: str,
) -> None:
    fact = _expect_object(value, path)
    _exact_keys(
        fact,
        {
            "schema_version",
            "field",
            "value",
            "provenance",
            "custody",
            "originating_observer",
            "originating_receipt_sha256",
            "source",
        },
        path,
    )
    _expect(
        fact["schema_version"]
        == "agentic-coding-evaluation-lab.provenance-fact.v2.0.0-draft.1",
        f"{path} schema version mismatch",
    )
    _expect(
        fact["provenance"] in {"measured", "derived", "attested"},
        f"{path}.provenance is invalid",
    )
    _expect(fact["custody"] == "copied", f"{path} must preserve copied custody")
    _expect(
        fact["originating_observer"] == expected_observer,
        f"{path} observer join mismatch",
    )
    _expect(
        fact["originating_receipt_sha256"] == expected_receipt,
        f"{path} originating receipt mismatch",
    )
    source = _expect_object(fact["source"], f"{path}.source")
    _exact_keys(
        source,
        {"schema_version", "observer", "provenance", "receipt_sha256"},
        f"{path}.source",
    )
    _expect(
        source["schema_version"]
        == "agentic-coding-evaluation-lab.source-provenance.v2.0.0-draft.1",
        f"{path}.source schema version mismatch",
    )
    _expect(
        source["observer"] == fact["originating_observer"],
        f"{path} source observer mismatch",
    )
    _expect(
        source["provenance"] == fact["provenance"], f"{path} may not upgrade provenance"
    )
    _expect(
        source["receipt_sha256"] == fact["originating_receipt_sha256"],
        f"{path} must preserve the source receipt",
    )


def _validate_registration(document: dict[str, Any]) -> None:
    registration = _expect_object(document["registration"], "$.registration")
    _exact_keys(
        registration,
        {
            "schema_version",
            "owner_contract",
            "receipt_copy",
            "originating_verification_copy",
            "reveal",
        },
        "$.registration",
    )
    _expect(
        registration["schema_version"]
        == "agentic-coding-evaluation-lab.registration-binding.v2.0.0-draft.1",
        "registration binding schema version mismatch",
    )
    owner_contract = _expect_object(
        registration["owner_contract"], "$.registration.owner_contract"
    )
    _exact_keys(
        owner_contract,
        {
            "schema_version",
            "registration_schema_version",
            "registration_schema_sha256",
            "verification_schema_version",
            "verification_schema_sha256",
            "operational_adapter_status",
        },
        "$.registration.owner_contract",
    )
    _expect(
        owner_contract["schema_version"]
        == "agentic-coding-evaluation-lab.registry-contract-binding.v2.0.0-draft.1",
        "registry owner-contract binding schema version mismatch",
    )
    _expect(
        owner_contract["registration_schema_version"]
        == EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        "registry registration schema version mismatch",
    )
    _expect(
        owner_contract["registration_schema_sha256"]
        == EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256,
        "registry registration schema digest mismatch",
    )
    _expect(
        owner_contract["verification_schema_version"]
        == EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
        "registry verification schema version mismatch",
    )
    _expect(
        owner_contract["verification_schema_sha256"]
        == EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256,
        "registry verification schema digest mismatch",
    )
    _expect(
        owner_contract["operational_adapter_status"] == "synthetic-non-authoritative",
        "registry adapter must remain synthetic and non-authoritative",
    )

    receipt_copy = _expect_object(
        registration["receipt_copy"], "$.registration.receipt_copy"
    )
    _exact_keys(
        receipt_copy,
        {
            "schema_version",
            "exact_receipt_json_utf8",
            "registration_receipt_sha256",
            "custody",
            "provenance",
        },
        "$.registration.receipt_copy",
    )
    _expect(
        receipt_copy["schema_version"]
        == "agentic-coding-evaluation-lab.exact-registration-receipt-copy.v2.0.0-draft.1",
        "registration receipt copy schema version mismatch",
    )
    _expect(receipt_copy["custody"] == "copied", "registration receipt must be copied")
    _expect(
        receipt_copy["provenance"] == "attested",
        "registration receipt provenance must remain attested",
    )
    exact_receipt_text = receipt_copy["exact_receipt_json_utf8"]
    _expect(
        isinstance(exact_receipt_text, str),
        "registration receipt exact bytes must be UTF-8 text",
    )
    exact_receipt_bytes = exact_receipt_text.encode("utf-8")
    _expect(
        sha256_bytes(exact_receipt_bytes)
        == receipt_copy["registration_receipt_sha256"],
        "registration receipt exact-byte digest mismatch",
    )
    payload = load_json_exact(exact_receipt_bytes)
    _exact_keys(
        payload,
        {
            "schema_version",
            "campaign_id",
            "plan_commitment",
            "task_set_commitment",
            "methodology",
            "campaign_family_commitment",
            "attempt_ordinal",
            "signer_policy",
            "signature_bundle",
            "verification_result",
        },
        "$.registration.receipt_copy.exact_receipt_json_utf8",
    )
    _expect(
        payload["schema_version"] == EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        "registration receipt owner schema version mismatch",
    )
    _expect(
        isinstance(payload["campaign_id"], str)
        and _UUID_URN.fullmatch(payload["campaign_id"]) is not None,
        "registration receipt campaign id is not an opaque UUID URN",
    )
    campaign = document["campaign"]
    _expect(
        payload["campaign_id"] == campaign["campaign_id"], "receipt campaign mismatch"
    )
    _expect(
        payload["attempt_ordinal"] == campaign["attempt_ordinal"],
        "receipt ordinal mismatch",
    )
    methodology = _expect_object(
        payload["methodology"],
        "$.registration.receipt_copy.exact_receipt_json_utf8.methodology",
    )
    _exact_keys(
        methodology,
        {"version", "method_sha256"},
        "$.registration.receipt_copy.exact_receipt_json_utf8.methodology",
    )
    _expect(
        methodology["version"] == SYNTHETIC_HELD_METHOD_VERSION,
        "synthetic held methodology version mismatch",
    )
    _expect(
        methodology["method_sha256"] == SYNTHETIC_HELD_METHOD_SHA256,
        "synthetic held methodology digest mismatch",
    )
    for name, expected_domain in (
        ("plan_commitment", EVAL_REGISTRY_PLAN_DOMAIN),
        ("task_set_commitment", EVAL_REGISTRY_TASK_SET_DOMAIN),
    ):
        binding = _expect_object(
            payload[name],
            f"$.registration.receipt_copy.exact_receipt_json_utf8.{name}",
        )
        _exact_keys(
            binding,
            {"algorithm", "domain", "value"},
            f"$.registration.receipt_copy.exact_receipt_json_utf8.{name}",
        )
        _expect(binding["algorithm"] == "hmac-sha256", f"{name} algorithm mismatch")
        _expect(binding["domain"] == expected_domain, f"{name} domain mismatch")
        _expect(_is_hmac_sha256(binding["value"]), f"{name} value must be HMAC-SHA256")

    family_binding = _expect_object(
        payload["campaign_family_commitment"],
        "$.registration.receipt_copy.exact_receipt_json_utf8.campaign_family_commitment",
    )
    _exact_keys(
        family_binding,
        {"algorithm", "domain", "value"},
        "$.registration.receipt_copy.exact_receipt_json_utf8.campaign_family_commitment",
    )
    _expect(
        family_binding["algorithm"] == "hmac-sha256",
        "campaign-family commitment algorithm mismatch",
    )
    _expect(
        family_binding["domain"] == EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
        "campaign-family commitment domain mismatch",
    )
    _expect(
        family_binding["value"] == campaign["campaign_family_commitment"],
        "receipt family mismatch",
    )
    _expect(
        _is_hmac_sha256(family_binding["value"]),
        "campaign-family commitment value must be HMAC-SHA256",
    )
    signer_policy = _expect_object(
        payload["signer_policy"],
        "$.registration.receipt_copy.exact_receipt_json_utf8.signer_policy",
    )
    _exact_keys(
        signer_policy,
        {
            "certificate_identity",
            "oidc_issuer",
            "trust_policy_version",
            "trust_policy_sha256",
        },
        "$.registration.receipt_copy.exact_receipt_json_utf8.signer_policy",
    )
    _expect(
        signer_policy
        == {
            "certificate_identity": "urn:synthetic:unconfigured-certificate-identity",
            "oidc_issuer": "urn:synthetic:unconfigured-oidc-issuer",
            "trust_policy_version": "synthetic-d2-unconfigured",
            "trust_policy_sha256": "sha256:" + "c" * 64,
        },
        "synthetic receipt must not claim an operational signer policy",
    )
    signature_bundle = _expect_object(
        payload["signature_bundle"],
        "$.registration.receipt_copy.exact_receipt_json_utf8.signature_bundle",
    )
    _exact_keys(
        signature_bundle,
        {"kind", "path"},
        "$.registration.receipt_copy.exact_receipt_json_utf8.signature_bundle",
    )
    _expect(
        signature_bundle
        == {"kind": "sigstore-bundle", "path": "signature.bundle.json"},
        "registration signature-bundle reference mismatch",
    )
    verification_reference = _expect_object(
        payload["verification_result"],
        "$.registration.receipt_copy.exact_receipt_json_utf8.verification_result",
    )
    _exact_keys(
        verification_reference,
        {"path", "authoritative"},
        "$.registration.receipt_copy.exact_receipt_json_utf8.verification_result",
    )
    _expect(
        verification_reference == {"path": "verification.json", "authoritative": False},
        "registration verification-result reference mismatch",
    )

    verification = _expect_object(
        registration["originating_verification_copy"],
        "$.registration.originating_verification_copy",
    )
    _exact_keys(
        verification,
        {
            "schema_version",
            "exact_verification_json_utf8",
            "verification_result_sha256",
            "custody",
            "provenance",
        },
        "$.registration.originating_verification_copy",
    )
    _expect(
        verification["schema_version"]
        == "agentic-coding-evaluation-lab.exact-verification-result-copy.v2.0.0-draft.1",
        "originating verification copy schema version mismatch",
    )
    _expect(verification["custody"] == "copied", "verification receipt must be copied")
    _expect(
        verification["provenance"] == "attested",
        "verification provenance must remain attested",
    )
    exact_verification_text = verification["exact_verification_json_utf8"]
    _expect(
        isinstance(exact_verification_text, str),
        "verification result exact bytes must be UTF-8 text",
    )
    exact_verification_bytes = exact_verification_text.encode("utf-8")
    _expect(
        sha256_bytes(exact_verification_bytes)
        == verification["verification_result_sha256"],
        "verification-result exact-byte digest mismatch",
    )
    verification_result = load_json_exact(exact_verification_bytes)
    _exact_keys(
        verification_result,
        {
            "schema_version",
            "authoritative",
            "record_schema_version",
            "signed_record_sha256",
            "signature_bundle_sha256",
            "trust_policy_sha256",
            "verdict",
            "verified_tsa_time",
            "checks",
            "reasons",
        },
        "$.registration.originating_verification_copy.exact_verification_json_utf8",
    )
    _expect(
        verification_result["schema_version"]
        == EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
        "verification-result owner schema version mismatch",
    )
    _expect(
        verification_result["authoritative"] is False,
        "copied verifier output is informational",
    )
    _expect(
        verification_result["record_schema_version"]
        == EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        "verification-result record schema mismatch",
    )
    _expect(
        verification_result["signed_record_sha256"]
        == receipt_copy["registration_receipt_sha256"],
        "verification-to-registration digest mismatch",
    )
    _expect(
        _is_sha256(verification_result["signature_bundle_sha256"]),
        "verification signature-bundle digest must be SHA-256",
    )
    _expect(
        verification_result["trust_policy_sha256"]
        == signer_policy["trust_policy_sha256"],
        "verification trust-policy digest mismatch",
    )
    _expect(
        verification_result["verdict"] == "refused",
        "D2 synthetic verification result must refuse",
    )
    _expect(
        verification_result["verified_tsa_time"] is None,
        "D2 synthetic verification must not claim a TSA time",
    )
    checks = _expect_object(
        verification_result["checks"],
        "$.registration.originating_verification_copy.exact_verification_json_utf8.checks",
    )
    expected_checks = {
        "exact_schema",
        "signature",
        "certificate_identity",
        "oidc_issuer",
        "certificate_chain",
        "tsa_signature",
        "tsa_imprint_is_signature_bytes",
        "certificate_valid_at_tsa_time",
        "transparency_inclusion",
        "transparency_checkpoint",
    }
    _exact_keys(checks, expected_checks, "verification-result checks")
    _expect(
        all(value == "not_checked" for value in checks.values()),
        "D2 synthetic verification checks must remain not_checked",
    )
    reasons = _expect_array(verification_result["reasons"], "verification reasons")
    _expect(
        reasons == ["synthetic D2 structure; no operational trust policy"],
        "D2 synthetic verification refusal reason mismatch",
    )

    reveal = _expect_object(registration["reveal"], "$.registration.reveal")
    _exact_keys(
        reveal,
        {
            "schema_version",
            "status",
            "plan_nonce_hex",
            "task_set_nonce_hex",
            "science_protocol_exact_json_utf8",
            "task_set_exact_json_utf8",
            "science_protocol_sha256",
            "task_set_sha256",
        },
        "$.registration.reveal",
    )
    _expect(
        reveal["schema_version"]
        == "agentic-coding-evaluation-lab.registration-reveal.v2.0.0-draft.1",
        "registration reveal schema version mismatch",
    )
    _expect(
        reveal["status"] == "synthetic_commitments_verified",
        "reveal status is not synthetic_commitments_verified",
    )
    science_protocol_bytes = reveal["science_protocol_exact_json_utf8"].encode("utf-8")
    task_set_bytes = reveal["task_set_exact_json_utf8"].encode("utf-8")
    revealed_protocol = load_json_exact(science_protocol_bytes)
    revealed_task_set = load_json_exact(task_set_bytes)
    _expect(
        revealed_protocol == document["science_protocol"],
        "science protocol exact-byte reveal does not match bound document",
    )
    _expect(
        revealed_task_set == document["task_set_reveal"],
        "task-set exact-byte reveal does not match bound document",
    )
    _expect(
        reveal["science_protocol_sha256"] == sha256_bytes(science_protocol_bytes),
        "science protocol reveal digest mismatch",
    )
    _expect(
        reveal["task_set_sha256"] == sha256_bytes(task_set_bytes),
        "task-set reveal digest mismatch",
    )
    plan_binding = payload["plan_commitment"]
    task_binding = payload["task_set_commitment"]
    _expect(
        _is_hmac_sha256(plan_binding["value"]), "plan commitment must be HMAC-SHA256"
    )
    _expect(
        _is_hmac_sha256(task_binding["value"]), "task commitment must be HMAC-SHA256"
    )
    _expect(
        _hmac_commitment(
            nonce_hex=reveal["plan_nonce_hex"],
            domain=plan_binding["domain"],
            exact_bytes=science_protocol_bytes,
        )
        == plan_binding["value"],
        "science protocol hiding commitment mismatch",
    )
    _expect(
        _hmac_commitment(
            nonce_hex=reveal["task_set_nonce_hex"],
            domain=task_binding["domain"],
            exact_bytes=task_set_bytes,
        )
        == task_binding["value"],
        "task-set hiding commitment mismatch",
    )


def _validate_protocol_and_schedule(document: dict[str, Any]) -> None:
    campaign = _expect_object(document["campaign"], "$.campaign")
    _exact_keys(
        campaign,
        {
            "schema_version",
            "campaign_id",
            "campaign_type",
            "campaign_family_commitment",
            "attempt_ordinal",
        },
        "$.campaign",
    )
    _expect(
        campaign["schema_version"]
        == "agentic-coding-evaluation-lab.campaign.v2.0.0-draft.1",
        "campaign schema version mismatch",
    )
    _expect(
        isinstance(campaign["campaign_id"], str) and bool(campaign["campaign_id"]),
        "campaign id must be non-empty",
    )
    _expect(
        campaign["campaign_type"] == "synthetic_contract_check",
        "campaign type mismatch",
    )
    _expect(
        _is_hmac_sha256(campaign["campaign_family_commitment"]),
        "campaign family must be HMAC-SHA256",
    )
    _expect(
        isinstance(campaign["attempt_ordinal"], int)
        and not isinstance(campaign["attempt_ordinal"], bool)
        and 1 <= campaign["attempt_ordinal"] <= 9007199254740991,
        "attempt ordinal must be a positive JSON-safe integer",
    )

    task_set = _expect_object(document["task_set_reveal"], "$.task_set_reveal")
    _exact_keys(task_set, {"schema_version", "tasks"}, "$.task_set_reveal")
    _expect(
        task_set["schema_version"]
        == "agentic-coding-evaluation-lab.task-set-reveal.v2.0.0-draft.1",
        "task-set schema version mismatch",
    )
    tasks = _expect_array(task_set["tasks"], "$.task_set_reveal.tasks")
    _expect(bool(tasks), "task-set reveal must not be empty")
    task_ids: set[str] = set()
    for index, task_value in enumerate(tasks):
        task = _expect_object(task_value, f"$.task_set_reveal.tasks[{index}]")
        _exact_keys(
            task,
            {"schema_version", "task_id", "task_class"},
            f"$.task_set_reveal.tasks[{index}]",
        )
        _expect(
            task["schema_version"]
            == "agentic-coding-evaluation-lab.task-descriptor.v2.0.0-draft.1",
            "task descriptor schema version mismatch",
        )
        _expect(
            isinstance(task["task_id"], str) and bool(task["task_id"]),
            "task id must be non-empty",
        )
        _expect(
            isinstance(task["task_class"], str) and bool(task["task_class"]),
            "task class must be non-empty",
        )
        _expect(task["task_id"] not in task_ids, "duplicate task id")
        task_ids.add(task["task_id"])

    protocol = _expect_object(document["science_protocol"], "$.science_protocol")
    _exact_keys(
        protocol,
        {
            "schema_version",
            "campaign_id",
            "campaign_type",
            "target_task_universe",
            "outcome_definition",
            "estimand",
            "method",
            "replicate_policy",
            "margin",
            "mpib",
            "missingness_policy",
            "assignment_schedule_sha256",
            "task_set_sha256",
        },
        "$.science_protocol",
    )
    _expect(
        protocol["schema_version"]
        == "agentic-coding-evaluation-lab.science-protocol.v2.0.0-draft.1",
        "science protocol schema version mismatch",
    )
    _expect(
        protocol["campaign_id"] == document["campaign"]["campaign_id"],
        "protocol campaign mismatch",
    )
    for field in ("estimand", "method", "replicate_policy", "margin", "mpib"):
        held = _expect_object(protocol[field], f"$.science_protocol.{field}")
        _exact_keys(
            held,
            {"schema_version", "status", "specification"},
            f"$.science_protocol.{field}",
        )
        _expect(
            held["schema_version"]
            == "agentic-coding-evaluation-lab.held-decision-input.v2.0.0-draft.1",
            f"science protocol {field} schema version mismatch",
        )
        _expect(held["status"] == "held", f"science protocol {field} must remain held")
        _expect(
            held["specification"] is None,
            f"science protocol {field} must not select a value",
        )
    _expect(
        protocol["task_set_sha256"] == _canonical_sha256(document["task_set_reveal"]),
        "protocol task-set binding mismatch",
    )
    _expect(
        protocol["campaign_type"] == "synthetic_contract_check",
        "draft fixture campaign type must be synthetic_contract_check",
    )

    schedule = _expect_object(document["assignment_schedule"], "$.assignment_schedule")
    _exact_keys(
        schedule,
        {"schema_version", "assignment_mechanism", "units"},
        "$.assignment_schedule",
    )
    _expect(
        schedule["schema_version"]
        == "agentic-coding-evaluation-lab.assignment-schedule.v2.0.0-draft.1",
        "assignment schedule schema version mismatch",
    )
    _expect(
        isinstance(schedule["assignment_mechanism"], str)
        and bool(schedule["assignment_mechanism"]),
        "assignment mechanism must be non-empty",
    )
    units = _expect_array(schedule["units"], "$.assignment_schedule.units")
    _expect(bool(units), "assignment schedule must not be empty")
    pairs: set[str] = set()
    scheduled_tasks: set[str] = set()
    attempt_ids: set[str] = set()
    for index, unit_value in enumerate(units):
        unit = _expect_object(unit_value, f"$.assignment_schedule.units[{index}]")
        _exact_keys(
            unit,
            {
                "schema_version",
                "task_pair_id",
                "task_id",
                "session_id",
                "arm_order",
                "attempt_ids",
            },
            f"$.assignment_schedule.units[{index}]",
        )
        _expect(
            unit["schema_version"]
            == "agentic-coding-evaluation-lab.assignment-unit.v2.0.0-draft.1",
            "assignment unit schema version mismatch",
        )
        _expect(unit["task_pair_id"] not in pairs, "duplicate task_pair_id")
        _expect(unit["task_id"] in task_ids, "assignment references unknown task")
        _expect(unit["task_id"] not in scheduled_tasks, "task scheduled more than once")
        _expect(
            isinstance(unit["session_id"], str) and bool(unit["session_id"]),
            "session id must be non-empty",
        )
        order = unit["arm_order"]
        _expect(
            order in (["incumbent", "candidate"], ["candidate", "incumbent"]),
            "invalid arm order",
        )
        ids = _expect_object(
            unit["attempt_ids"], f"$.assignment_schedule.units[{index}].attempt_ids"
        )
        _exact_keys(
            ids,
            {"schema_version", "incumbent", "candidate"},
            f"$.assignment_schedule.units[{index}].attempt_ids",
        )
        _expect(
            ids["schema_version"]
            == "agentic-coding-evaluation-lab.assignment-attempt-ids.v2.0.0-draft.1",
            "assignment attempt-id mapping schema version mismatch",
        )
        for arm in ("incumbent", "candidate"):
            _expect(
                isinstance(ids[arm], str) and bool(ids[arm]),
                "scheduled attempt id must be non-empty",
            )
            _expect(ids[arm] not in attempt_ids, "scheduled attempt id reused")
            attempt_ids.add(ids[arm])
        pairs.add(unit["task_pair_id"])
        scheduled_tasks.add(unit["task_id"])
    _expect(
        scheduled_tasks == task_ids,
        "assignment schedule must cover the revealed task set exactly",
    )
    _expect(
        protocol["assignment_schedule_sha256"]
        == _canonical_sha256(document["assignment_schedule"]),
        "protocol assignment-schedule binding mismatch",
    )


def _validate_attempts_and_observations(document: dict[str, Any]) -> dict[str, Any]:
    schedule = _expect_object(document["assignment_schedule"], "$.assignment_schedule")
    units = _expect_array(schedule["units"], "$.assignment_schedule.units")
    scheduled: dict[str, tuple[str, str, str, str, int]] = {}
    for unit in units:
        unit = _expect_object(unit, "$.assignment_schedule.units[]")
        task_pair_id = unit["task_pair_id"]
        session_id = unit["session_id"]
        order = unit["arm_order"]
        _expect(
            order in (["incumbent", "candidate"], ["candidate", "incumbent"]),
            "invalid arm order",
        )
        for position, arm in enumerate(order, start=1):
            attempt_id = unit["attempt_ids"][arm]
            _expect(attempt_id not in scheduled, "duplicate scheduled attempt")
            scheduled[attempt_id] = (
                task_pair_id,
                session_id,
                unit["task_id"],
                arm,
                position,
            )

    attempts = _expect_array(document["attempts"], "$.attempts")
    seen: dict[str, dict[str, Any]] = {}
    for attempt_value in attempts:
        attempt = _expect_object(attempt_value, "$.attempts[]")
        _exact_keys(
            attempt,
            {
                "schema_version",
                "attempt_id",
                "task_pair_id",
                "task_id",
                "session_id",
                "arm",
                "attempt_index",
                "attempt_position_in_pair",
                "status",
                "error_class",
            },
            "$.attempts[]",
        )
        _expect(
            attempt["schema_version"]
            == "agentic-coding-evaluation-lab.attempt.v2.0.0-draft.1",
            "attempt schema version mismatch",
        )
        attempt_id = attempt["attempt_id"]
        _expect(attempt_id not in seen, "duplicate attempt_id")
        _expect(attempt_id in scheduled, "attempt is absent from assignment schedule")
        pair, session, task_id, arm, position = scheduled[attempt_id]
        _expect(attempt["task_pair_id"] == pair, "attempt task-pair mismatch")
        _expect(attempt["session_id"] == session, "attempt session mismatch")
        _expect(attempt["task_id"] == task_id, "attempt task mismatch")
        _expect(attempt["arm"] == arm, "attempt arm mismatch")
        _expect(
            isinstance(attempt["attempt_index"], int)
            and not isinstance(attempt["attempt_index"], bool)
            and attempt["attempt_index"] >= 1,
            "attempt index must be positive integer",
        )
        _expect(
            attempt["attempt_position_in_pair"] == position, "attempt order mismatch"
        )
        _expect(
            attempt["status"]
            in {"succeeded", "failed", "timeout", "oom", "gateway_error"},
            "invalid attempt status",
        )
        if attempt["status"] == "succeeded":
            _expect(
                attempt["error_class"] is None, "successful attempt carries error class"
            )
        else:
            _expect(
                isinstance(attempt["error_class"], str) and attempt["error_class"],
                "failed attempt lacks error class",
            )
        seen[attempt_id] = attempt
    _expect(set(seen) == set(scheduled), "scheduled/observed attempt set mismatch")

    all_receipts: set[str] = {
        document["registration"]["receipt_copy"]["registration_receipt_sha256"],
        document["registration"]["originating_verification_copy"][
            "verification_result_sha256"
        ],
    }
    descriptor_required_facts = {
        "invocation_id",
        "invocation_descriptor_sha256",
        "descriptor_schema_sha256",
        "validator_sha256",
        "runtime_version_sha256",
        "retry_policy",
        "descriptor_valid",
    }
    descriptor_by_attempt: dict[str, str] = {}
    invocation_to_attempt: dict[str, str] = {}
    for item_value in _expect_array(
        document["editing_harness_descriptor_validations"],
        "$.editing_harness_descriptor_validations",
    ):
        item = _expect_object(item_value, "$.editing_harness_descriptor_validations[]")
        _exact_keys(
            item,
            {
                "schema_version",
                "attempt_id",
                "invocation_id",
                "observer",
                "owner_receipt_schema_version",
                "owner_schema_status",
                "validation_receipt_sha256",
                "facts",
            },
            "$.editing_harness_descriptor_validations[]",
        )
        _expect(
            item["schema_version"]
            == "agentic-coding-evaluation-lab.editing-harness-descriptor-validation.v2.0.0-draft.1",
            "editing-harness descriptor validation schema version mismatch",
        )
        attempt_id = item["attempt_id"]
        invocation_id = item["invocation_id"]
        receipt = item["validation_receipt_sha256"]
        _expect(
            attempt_id in seen, "editing-harness descriptor validation orphan attempt"
        )
        _expect(
            attempt_id not in descriptor_by_attempt,
            "editing-harness descriptor validation duplicate attempt join",
        )
        _expect(
            isinstance(invocation_id, str) and bool(invocation_id),
            "editing-harness invocation id must be non-empty",
        )
        _expect(
            invocation_id not in invocation_to_attempt,
            "editing-harness invocation id must be unique",
        )
        _expect(
            _is_sha256(receipt),
            "editing-harness descriptor validation receipt must be SHA-256",
        )
        _expect(receipt not in all_receipts, "receipt digest reused across planes")
        _expect(
            item["observer"] == "editing-harness-owner-validator",
            "editing-harness descriptor validator observer mismatch",
        )
        _expect(
            item["owner_receipt_schema_version"]
            == "synthetic.editing-harness.descriptor-validation.v1",
            "editing-harness descriptor-validation synthetic owner schema mismatch",
        )
        _expect(
            item["owner_schema_status"] == "synthetic-fixture-unratified",
            "editing-harness owner schema must remain unratified synthetic fixture",
        )
        facts = _expect_array(
            item["facts"], "$.editing_harness_descriptor_validations[].facts"
        )
        fact_names: set[str] = set()
        for fact_index, fact in enumerate(facts):
            _validate_provenance_fact(
                fact,
                path=f"$.editing_harness_descriptor_validations[].facts[{fact_index}]",
                expected_receipt=receipt,
                expected_observer="editing-harness-owner-validator",
            )
            _expect(
                fact["field"] not in fact_names,
                "editing-harness descriptor validation duplicate fact field",
            )
            fact_names.add(fact["field"])
        _expect(
            fact_names == descriptor_required_facts,
            "editing-harness descriptor validation required fact set mismatch",
        )
        fact_values = {fact["field"]: fact["value"] for fact in facts}
        _expect(
            fact_values["invocation_id"] == invocation_id,
            "editing-harness descriptor invocation fact does not join validation",
        )
        _expect(
            _is_sha256(fact_values["invocation_descriptor_sha256"]),
            "editing-harness invocation descriptor must be SHA-256",
        )
        for field in (
            "descriptor_schema_sha256",
            "validator_sha256",
            "runtime_version_sha256",
        ):
            _expect(
                _is_sha256(fact_values[field]),
                f"editing-harness {field} must be SHA-256",
            )
        _expect(
            fact_values["retry_policy"] == "exposed",
            "editing-harness retry policy must be exposed",
        )
        _expect(
            fact_values["descriptor_valid"] is True,
            "editing-harness descriptor validation did not pass",
        )
        descriptor_by_attempt[attempt_id] = invocation_id
        invocation_to_attempt[invocation_id] = attempt_id
        all_receipts.add(receipt)
    _expect(
        set(descriptor_by_attempt) == set(seen),
        "editing-harness descriptor validations do not cover every attempt",
    )

    completion_required_facts = {
        "invocation_id",
        "process_completed",
        "completion_status",
        "exit_code",
    }
    completed_attempts: set[str] = set()
    for item_value in _expect_array(
        document["harness_completion_observations"],
        "$.harness_completion_observations",
    ):
        item = _expect_object(item_value, "$.harness_completion_observations[]")
        _exact_keys(
            item,
            {
                "schema_version",
                "attempt_id",
                "invocation_id",
                "observer",
                "owner_receipt_schema_version",
                "owner_schema_status",
                "completion_receipt_sha256",
                "facts",
            },
            "$.harness_completion_observations[]",
        )
        _expect(
            item["schema_version"]
            == "agentic-coding-evaluation-lab.harness-completion-observation.v2.0.0-draft.1",
            "harness completion schema version mismatch",
        )
        attempt_id = item["attempt_id"]
        invocation_id = item["invocation_id"]
        receipt = item["completion_receipt_sha256"]
        _expect(attempt_id in seen, "harness completion orphan attempt")
        _expect(
            invocation_to_attempt.get(invocation_id) == attempt_id,
            "harness completion does not join descriptor invocation",
        )
        _expect(
            attempt_id not in completed_attempts,
            "harness completion duplicate attempt join",
        )
        _expect(_is_sha256(receipt), "harness completion receipt must be SHA-256")
        _expect(receipt not in all_receipts, "receipt digest reused across planes")
        _expect(
            item["observer"] == "evaluation-harness",
            "harness completion observer mismatch",
        )
        _expect(
            item["owner_receipt_schema_version"]
            == "synthetic.evaluation-harness.completion.v1",
            "harness completion synthetic owner schema mismatch",
        )
        _expect(
            item["owner_schema_status"] == "synthetic-fixture-unratified",
            "harness completion owner schema must remain unratified synthetic fixture",
        )
        facts = _expect_array(
            item["facts"], "$.harness_completion_observations[].facts"
        )
        fact_names: set[str] = set()
        for fact_index, fact in enumerate(facts):
            _validate_provenance_fact(
                fact,
                path=f"$.harness_completion_observations[].facts[{fact_index}]",
                expected_receipt=receipt,
                expected_observer="evaluation-harness",
            )
            _expect(
                fact["field"] not in fact_names,
                "harness completion duplicate fact field",
            )
            fact_names.add(fact["field"])
        _expect(
            fact_names == completion_required_facts,
            "harness completion required fact set mismatch",
        )
        fact_values = {fact["field"]: fact["value"] for fact in facts}
        _expect(
            fact_values["invocation_id"] == invocation_id,
            "harness completion invocation fact does not join observation",
        )
        _expect(
            fact_values["process_completed"] is True,
            "harness process completion was not observed",
        )
        attempt = seen[attempt_id]
        _expect(
            fact_values["completion_status"] == attempt["status"],
            "harness completion status does not join attempt status",
        )
        exit_code = fact_values["exit_code"]
        _expect(
            isinstance(exit_code, int) and not isinstance(exit_code, bool),
            "harness completion exit code must be integer",
        )
        if attempt["status"] == "succeeded":
            _expect(exit_code == 0, "successful harness completion must exit zero")
        else:
            _expect(exit_code != 0, "failed harness completion must exit nonzero")
        completed_attempts.add(attempt_id)
        all_receipts.add(receipt)
    _expect(
        completed_attempts == set(seen),
        "harness completions do not cover every attempt",
    )

    open_required_facts = {"invocation_id", "invocation_opened"}
    gateway_open_receipts: dict[str, str] = {}
    opened_attempts: set[str] = set()
    for item_value in _expect_array(
        document["gateway_invocation_opens"],
        "$.gateway_invocation_opens",
    ):
        item = _expect_object(item_value, "$.gateway_invocation_opens[]")
        _exact_keys(
            item,
            {
                "schema_version",
                "attempt_id",
                "invocation_id",
                "observer",
                "owner_receipt_schema_version",
                "owner_schema_status",
                "open_receipt_sha256",
                "facts",
            },
            "$.gateway_invocation_opens[]",
        )
        _expect(
            item["schema_version"]
            == "agentic-coding-evaluation-lab.gateway-invocation-open.v2.0.0-draft.1",
            "gateway invocation open schema version mismatch",
        )
        attempt_id = item["attempt_id"]
        invocation_id = item["invocation_id"]
        receipt = item["open_receipt_sha256"]
        _expect(attempt_id in seen, "gateway invocation open orphan attempt")
        _expect(
            invocation_to_attempt.get(invocation_id) == attempt_id,
            "gateway open does not join editing-harness invocation",
        )
        _expect(
            attempt_id not in opened_attempts,
            "gateway invocation open duplicate attempt join",
        )
        _expect(_is_sha256(receipt), "gateway open receipt must be SHA-256")
        _expect(receipt not in all_receipts, "receipt digest reused across planes")
        _expect(
            item["observer"] == "openai-compatible-gateway",
            "gateway invocation open observer mismatch",
        )
        _expect(
            item["owner_receipt_schema_version"]
            == "synthetic.gateway.invocation-open.v1",
            "gateway open synthetic owner schema mismatch",
        )
        _expect(
            item["owner_schema_status"] == "synthetic-fixture-unratified",
            "gateway open owner schema must remain unratified synthetic fixture",
        )
        facts = _expect_array(item["facts"], "$.gateway_invocation_opens[].facts")
        fact_names: set[str] = set()
        for fact_index, fact in enumerate(facts):
            _validate_provenance_fact(
                fact,
                path=f"$.gateway_invocation_opens[].facts[{fact_index}]",
                expected_receipt=receipt,
                expected_observer="openai-compatible-gateway",
            )
            _expect(
                fact["field"] not in fact_names,
                "gateway invocation open duplicate fact field",
            )
            fact_names.add(fact["field"])
        _expect(
            fact_names == open_required_facts,
            "gateway invocation open required fact set mismatch",
        )
        fact_values = {fact["field"]: fact["value"] for fact in facts}
        _expect(
            fact_values["invocation_id"] == invocation_id,
            "gateway open invocation fact does not join observation",
        )
        _expect(
            fact_values["invocation_opened"] is True,
            "gateway invocation was not opened",
        )
        gateway_open_receipts[invocation_id] = receipt
        opened_attempts.add(attempt_id)
        all_receipts.add(receipt)
    _expect(
        opened_attempts == set(seen),
        "gateway invocation opens do not cover every attempt",
    )

    gateway_required_facts = {
        "invocation_id",
        "request_id",
        "call_ordinal",
        "request_attempt_count",
        "request_attempt_vector",
        "fallback_used",
    }
    request_ids: set[str] = set()
    call_ordinals_by_invocation: dict[str, set[int]] = {}
    gateway_calls_by_invocation: dict[str, list[tuple[int, str, str]]] = {}
    gateway_retry_attempts = 0
    for item_value in _expect_array(
        document["gateway_observations"], "$.gateway_observations"
    ):
        item = _expect_object(item_value, "$.gateway_observations[]")
        _exact_keys(
            item,
            {
                "schema_version",
                "attempt_id",
                "invocation_id",
                "request_id",
                "call_ordinal",
                "observer",
                "owner_receipt_schema_version",
                "owner_schema_status",
                "observation_receipt_sha256",
                "facts",
            },
            "$.gateway_observations[]",
        )
        _expect(
            item["schema_version"]
            == "agentic-coding-evaluation-lab.gateway-observation.v2.0.0-draft.1",
            "gateway_observations schema version mismatch",
        )
        attempt_id = item["attempt_id"]
        invocation_id = item["invocation_id"]
        request_id = item["request_id"]
        call_ordinal = item["call_ordinal"]
        receipt = item["observation_receipt_sha256"]
        _expect(attempt_id in seen, "gateway_observations orphan attempt")
        _expect(
            invocation_to_attempt.get(invocation_id) == attempt_id,
            "gateway invocation does not join editing-harness invocation",
        )
        _expect(
            isinstance(request_id, str) and bool(request_id),
            "gateway request id must be non-empty",
        )
        _expect(request_id not in request_ids, "gateway request id must be unique")
        _expect(
            isinstance(call_ordinal, int)
            and not isinstance(call_ordinal, bool)
            and call_ordinal >= 1,
            "gateway call ordinal must be positive integer",
        )
        invocation_ordinals = call_ordinals_by_invocation.setdefault(
            invocation_id, set()
        )
        _expect(
            call_ordinal not in invocation_ordinals,
            "gateway call ordinal must be unique within invocation",
        )
        _expect(_is_sha256(receipt), "gateway receipt must be SHA-256")
        _expect(receipt not in all_receipts, "receipt digest reused across planes")
        _expect(
            item["observer"] == "openai-compatible-gateway",
            "gateway_observations observer mismatch",
        )
        _expect(
            item["owner_receipt_schema_version"]
            == "synthetic.gateway.call-observation.v1",
            "gateway call synthetic owner schema mismatch",
        )
        _expect(
            item["owner_schema_status"] == "synthetic-fixture-unratified",
            "gateway call owner schema must remain unratified synthetic fixture",
        )
        facts = _expect_array(item["facts"], "$.gateway_observations[].facts")
        fact_names: set[str] = set()
        for fact_index, fact in enumerate(facts):
            _validate_provenance_fact(
                fact,
                path=f"$.gateway_observations[].facts[{fact_index}]",
                expected_receipt=receipt,
                expected_observer="openai-compatible-gateway",
            )
            _expect(
                fact["field"] not in fact_names,
                "gateway_observations duplicate fact field",
            )
            fact_names.add(fact["field"])
        _expect(
            fact_names == gateway_required_facts,
            "gateway_observations required fact set mismatch",
        )
        fact_values = {fact["field"]: fact["value"] for fact in facts}
        _expect(
            fact_values["invocation_id"] == invocation_id,
            "gateway invocation fact does not join observation",
        )
        _expect(
            fact_values["request_id"] == request_id,
            "gateway request fact does not join observation",
        )
        _expect(
            fact_values["call_ordinal"] == call_ordinal,
            "gateway call-ordinal fact does not join observation",
        )
        request_attempt_count = fact_values["request_attempt_count"]
        _expect(
            isinstance(request_attempt_count, int)
            and not isinstance(request_attempt_count, bool)
            and request_attempt_count >= 1,
            "gateway request attempt count must be positive integer",
        )
        request_attempt_vector = _expect_array(
            fact_values["request_attempt_vector"],
            "gateway request attempt vector",
        )
        _expect(
            len(request_attempt_vector) == request_attempt_count,
            "gateway request attempt vector length mismatch",
        )
        for vector_index, vector_item_value in enumerate(
            request_attempt_vector, start=1
        ):
            vector_item = _expect_object(
                vector_item_value, "gateway request attempt vector[]"
            )
            _exact_keys(
                vector_item,
                {"attempt_ordinal", "outcome", "error_class"},
                "gateway request attempt vector[]",
            )
            _expect(
                isinstance(vector_item["attempt_ordinal"], int)
                and not isinstance(vector_item["attempt_ordinal"], bool)
                and vector_item["attempt_ordinal"] == vector_index,
                "gateway request attempt vector ordinals must be contiguous",
            )
            _expect(
                vector_item["outcome"] in {"succeeded", "failed"},
                "gateway request attempt outcome is invalid",
            )
            if vector_item["outcome"] == "succeeded":
                _expect(
                    vector_item["error_class"] is None,
                    "successful gateway request attempt carries error class",
                )
            else:
                _expect(
                    isinstance(vector_item["error_class"], str)
                    and bool(vector_item["error_class"]),
                    "failed gateway request attempt lacks error class",
                )
        _expect(
            fact_values["fallback_used"] is False,
            "scientific mode forbids gateway fallback",
        )
        request_ids.add(request_id)
        invocation_ordinals.add(call_ordinal)
        gateway_calls_by_invocation.setdefault(invocation_id, []).append(
            (call_ordinal, request_id, receipt)
        )
        gateway_retry_attempts += request_attempt_count - 1
        all_receipts.add(receipt)
    for ordinals in call_ordinals_by_invocation.values():
        _expect(
            ordinals == set(range(1, len(ordinals) + 1)),
            "gateway call ordinals must be contiguous within invocation",
        )

    closure_required_facts = {
        "invocation_id",
        "open_receipt_sha256",
        "invocation_closed",
        "gateway_call_count",
        "ordered_request_ids_sha256",
        "ordered_call_bindings_sha256",
    }
    closed_attempts: set[str] = set()
    for item_value in _expect_array(
        document["gateway_invocation_closures"],
        "$.gateway_invocation_closures",
    ):
        item = _expect_object(item_value, "$.gateway_invocation_closures[]")
        _exact_keys(
            item,
            {
                "schema_version",
                "attempt_id",
                "invocation_id",
                "observer",
                "owner_receipt_schema_version",
                "owner_schema_status",
                "closure_receipt_sha256",
                "facts",
            },
            "$.gateway_invocation_closures[]",
        )
        _expect(
            item["schema_version"]
            == "agentic-coding-evaluation-lab.gateway-invocation-closure.v2.0.0-draft.1",
            "gateway invocation closure schema version mismatch",
        )
        attempt_id = item["attempt_id"]
        invocation_id = item["invocation_id"]
        receipt = item["closure_receipt_sha256"]
        _expect(attempt_id in seen, "gateway invocation closure orphan attempt")
        _expect(
            invocation_to_attempt.get(invocation_id) == attempt_id,
            "gateway closure does not join editing-harness invocation",
        )
        _expect(
            attempt_id not in closed_attempts,
            "gateway invocation closure duplicate attempt join",
        )
        _expect(_is_sha256(receipt), "gateway closure receipt must be SHA-256")
        _expect(receipt not in all_receipts, "receipt digest reused across planes")
        _expect(
            item["observer"] == "openai-compatible-gateway",
            "gateway invocation closure observer mismatch",
        )
        _expect(
            item["owner_receipt_schema_version"]
            == "synthetic.gateway.invocation-closure.v1",
            "gateway closure synthetic owner schema mismatch",
        )
        _expect(
            item["owner_schema_status"] == "synthetic-fixture-unratified",
            "gateway closure owner schema must remain unratified synthetic fixture",
        )
        facts = _expect_array(item["facts"], "$.gateway_invocation_closures[].facts")
        fact_names: set[str] = set()
        for fact_index, fact in enumerate(facts):
            _validate_provenance_fact(
                fact,
                path=f"$.gateway_invocation_closures[].facts[{fact_index}]",
                expected_receipt=receipt,
                expected_observer="openai-compatible-gateway",
            )
            _expect(
                fact["field"] not in fact_names,
                "gateway invocation closure duplicate fact field",
            )
            fact_names.add(fact["field"])
        _expect(
            fact_names == closure_required_facts,
            "gateway invocation closure required fact set mismatch",
        )
        fact_values = {fact["field"]: fact["value"] for fact in facts}
        _expect(
            fact_values["invocation_id"] == invocation_id,
            "gateway closure invocation fact does not join observation",
        )
        _expect(
            fact_values["open_receipt_sha256"] == gateway_open_receipts[invocation_id],
            "gateway closure does not bind its invocation-open receipt",
        )
        _expect(
            fact_values["invocation_closed"] is True,
            "gateway invocation call set is not closed",
        )
        actual_calls = sorted(gateway_calls_by_invocation.get(invocation_id, []))
        actual_request_ids = [request_id for _, request_id, _ in actual_calls]
        actual_call_bindings = [
            (request_id, receipt_sha256)
            for _, request_id, receipt_sha256 in actual_calls
        ]
        gateway_call_count = fact_values["gateway_call_count"]
        _expect(
            isinstance(gateway_call_count, int)
            and not isinstance(gateway_call_count, bool)
            and gateway_call_count >= 0,
            "gateway closure call count must be non-negative integer",
        )
        _expect(
            gateway_call_count == len(actual_request_ids),
            "gateway closure call count mismatch",
        )
        _expect(
            fact_values["ordered_request_ids_sha256"]
            == _canonical_sha256(actual_request_ids),
            "gateway closure ordered-request digest mismatch",
        )
        _expect(
            fact_values["ordered_call_bindings_sha256"]
            == gateway_ordered_call_bindings_sha256(actual_call_bindings),
            "gateway closure ordered-call binding digest mismatch",
        )
        if not actual_request_ids:
            attempt = seen[attempt_id]
            _expect(
                attempt["status"] == "failed"
                and attempt["error_class"] == "pre_dispatch_failure",
                "zero-call invocation is allowed only for pre-dispatch failure",
            )
        closed_attempts.add(attempt_id)
        all_receipts.add(receipt)
    _expect(
        closed_attempts == set(seen),
        "gateway invocation closures do not cover every attempt",
    )

    counts = Counter(item["status"] for item in attempts)
    failures = [
        {
            "attempt_id": item["attempt_id"],
            "status": item["status"],
            "error_class": item["error_class"],
        }
        for item in attempts
        if item["status"] != "succeeded"
    ]
    return {
        "schema_version": "agentic-coding-evaluation-lab.attrition.v2.0.0-draft.1",
        "scheduled_attempts": len(scheduled),
        "observed_attempts": len(attempts),
        "terminal_status_counts": {name: counts[name] for name in sorted(counts)},
        "failures": failures,
        "excluded_attempt_ids": [],
        "retry_attempts": gateway_retry_attempts,
    }


def _analysis_input(
    document: dict[str, Any], attrition: dict[str, Any]
) -> dict[str, Any]:
    return {
        "campaign": document["campaign"],
        "verifier": document["verifier"],
        "science_protocol": document["science_protocol"],
        "registration": document["registration"],
        "assignment_schedule": document["assignment_schedule"],
        "attempts": document["attempts"],
        "attrition": attrition,
        "gateway_invocation_opens": document["gateway_invocation_opens"],
        "gateway_observations": document["gateway_observations"],
        "gateway_invocation_closures": document["gateway_invocation_closures"],
        "editing_harness_descriptor_validations": document[
            "editing_harness_descriptor_validations"
        ],
        "harness_completion_observations": document["harness_completion_observations"],
    }


def _expected_analysis(
    document: dict[str, Any], attrition: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": ANALYSIS_RESULT_VERSION,
        "analysis_input_sha256": _canonical_sha256(
            _analysis_input(document, attrition)
        ),
        "status": "not_evaluable",
        "method_authority": "held",
        "method_id": None,
        "statistics": {},
        "reason_codes": list(_REASONS),
    }


def _expected_decision(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": DECISION_RECEIPT_VERSION,
        "analysis_result_sha256": _canonical_sha256(analysis),
        "outcome": "NOT_EVALUABLE",
        "enforcing_rule": None,
        "promotion_recommendation": None,
        "reason_codes": list(_REASONS),
    }


def _expected_human_report(
    document: dict[str, Any],
    attrition: dict[str, Any],
    analysis: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    registration = document["registration"]
    gateway_open_receipts = [
        item["open_receipt_sha256"] for item in document["gateway_invocation_opens"]
    ]
    gateway_receipts = [
        item["observation_receipt_sha256"] for item in document["gateway_observations"]
    ]
    gateway_closure_receipts = [
        item["closure_receipt_sha256"]
        for item in document["gateway_invocation_closures"]
    ]
    descriptor_validation_receipts = [
        item["validation_receipt_sha256"]
        for item in document["editing_harness_descriptor_validations"]
    ]
    completion_receipts = [
        item["completion_receipt_sha256"]
        for item in document["harness_completion_observations"]
    ]
    return {
        "schema_version": HUMAN_REPORT_VERSION,
        "title": "Synthetic Contract B v2 refusal example",
        "decision": decision["outcome"],
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
            "campaign_type": document["campaign"]["campaign_type"],
            "scheduled_attempts": attrition["scheduled_attempts"],
            "method_authority": "held",
            "science_protocol_sha256": registration["reveal"][
                "science_protocol_sha256"
            ],
            "task_set_sha256": registration["reveal"]["task_set_sha256"],
            "assignment_schedule_sha256": _canonical_sha256(
                document["assignment_schedule"]
            ),
        },
        "attrition": attrition,
        "provenance": {
            "gateway_open_receipts": gateway_open_receipts,
            "gateway_receipts": gateway_receipts,
            "gateway_closure_receipts": gateway_closure_receipts,
            "editing_harness_validation_receipts": descriptor_validation_receipts,
            "harness_completion_receipts": completion_receipts,
            "provenance_upgrades": 0,
        },
        "analysis": {
            "status": "not_evaluable",
            "statistics_emitted": 0,
            "reason_codes": list(_REASONS),
        },
        "verification": {
            "contract_schema_version": CONTRACT_V2_SCHEMA_VERSION,
            "contract_schema_sha256": contract_schema_sha256(),
            "verifier_implementation_version": VERIFIER_IMPLEMENTATION_VERSION,
            "verifier_implementation_bundle_sha256": verifier_implementation_bundle_sha256(),
            "analysis_result_sha256": _canonical_sha256(analysis),
            "decision_receipt_sha256": _canonical_sha256(decision),
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


def recompute_or_refuse(document: dict[str, Any]) -> VerifiedContractV2:
    """Recompute every derived product or refuse the complete draft bundle."""

    _exact_keys(document, _TOP_LEVEL_KEYS, "$")
    _expect(
        document["schema_version"] == CONTRACT_V2_SCHEMA_VERSION,
        "stale or unknown v2 schema",
    )
    _expect(
        document["contract_status"] == "normative_draft",
        "contract status must be normative_draft",
    )
    _expect(document["provenance"] == "synthetic", "draft fixture must be synthetic")
    _expect(
        document["operational_authority"] is False,
        "draft must not claim operational authority",
    )
    verifier = _expect_object(document["verifier"], "$.verifier")
    _exact_keys(
        verifier,
        {
            "implementation_version",
            "implementation_files",
            "implementation_bundle_sha256",
            "custody",
            "release_status",
        },
        "$.verifier",
    )
    _expect(
        verifier["implementation_version"] == VERIFIER_IMPLEMENTATION_VERSION,
        "verifier implementation version mismatch",
    )
    _expect(
        verifier["implementation_files"] == verifier_implementation_manifest(),
        "verifier implementation file manifest mismatch",
    )
    _expect(
        verifier["implementation_bundle_sha256"]
        == verifier_implementation_bundle_sha256(),
        "verifier implementation bundle digest mismatch",
    )
    _expect(
        verifier["custody"] == "repository-only",
        "verifier custody must be repository-only",
    )
    _expect(
        verifier["release_status"] == "unreleased-draft",
        "verifier must remain unreleased draft",
    )
    sanitization = _expect_object(document["sanitization"], "$.sanitization")
    _exact_keys(
        sanitization,
        {"schema_version", "status", "checked", "redactions_required", "notes"},
        "$.sanitization",
    )
    _expect(
        sanitization["schema_version"]
        == "agentic-coding-evaluation-lab.sanitization.v2.0.0-draft.1",
        "sanitization schema version mismatch",
    )
    try:
        assert_publication_content_is_safe(document)
    except ValueError as exc:
        raise VerificationRefusal(f"publication boundary refusal: {exc}") from exc
    _expect(
        sanitization.get("status") == "public-safe",
        "sanitization status is not public-safe",
    )
    _expect(sanitization.get("checked") is True, "sanitization must be checked")
    _expect(
        sanitization.get("redactions_required") is False, "redactions remain required"
    )

    _validate_protocol_and_schedule(document)
    _validate_registration(document)
    attrition = _validate_attempts_and_observations(document)
    _expect(
        canonical_json_bytes(attrition) == canonical_json_bytes(document["attrition"]),
        "producer attrition does not match independent recomputation",
    )
    analysis = _expected_analysis(document, attrition)
    _expect(
        canonical_json_bytes(analysis)
        == canonical_json_bytes(document["analysis_result"]),
        "producer analysis does not match independent recomputation",
    )
    decision = _expected_decision(analysis)
    _expect(
        canonical_json_bytes(decision)
        == canonical_json_bytes(document["decision_receipt"]),
        "producer decision does not match independent recomputation",
    )
    report = _expected_human_report(document, attrition, analysis, decision)
    _expect(
        canonical_json_bytes(report) == canonical_json_bytes(document["human_report"]),
        "producer human-report model does not match independent recomputation",
    )
    return VerifiedContractV2(
        evidence_sha256=_canonical_sha256(document),
        analysis_result=analysis,
        analysis_result_sha256=_canonical_sha256(analysis),
        decision_receipt=decision,
        decision_receipt_sha256=_canonical_sha256(decision),
        human_report=report,
        human_report_sha256=_canonical_sha256(report),
    )


def verify_exact_bytes(payload: bytes) -> VerifiedContractV2:
    """Strict exact-byte entry point used by CLI, tests, and report rendering."""

    document = load_json_exact(payload)
    _expect(
        canonical_json_bytes(document) == payload,
        "evidence bytes are not in the required canonical encoding",
    )
    _validate_contract_schema(document)
    verified = recompute_or_refuse(document)
    return VerifiedContractV2(
        evidence_sha256=sha256_bytes(payload),
        analysis_result=verified.analysis_result,
        analysis_result_sha256=verified.analysis_result_sha256,
        decision_receipt=verified.decision_receipt,
        decision_receipt_sha256=verified.decision_receipt_sha256,
        human_report=verified.human_report,
        human_report_sha256=verified.human_report_sha256,
    )
