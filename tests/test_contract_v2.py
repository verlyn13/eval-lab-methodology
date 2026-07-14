"""Contract B v2 draft conformance, recomputation, and tamper refusal."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema

from analysis.contract_v2 import (
    CONTRACT_V2_SCHEMA_VERSION,
    VerificationRefusal,
    canonical_json_bytes,
    recompute_or_refuse,
    sha256_bytes,
    verify_exact_bytes,
)
from analysis.contract_v2.report import render_markdown
from analysis.contract_v2.verification import (
    EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
    EVAL_REGISTRY_PLAN_DOMAIN,
    EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256,
    EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
    EVAL_REGISTRY_TASK_SET_DOMAIN,
    EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256,
    EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
    VERIFIER_IMPLEMENTATION_FILES,
    _expected_analysis,
    _expected_decision,
    _expected_human_report,
    _validate_attempts_and_observations,
    gateway_ordered_call_bindings_sha256,
    verifier_implementation_bundle_sha256,
    verifier_implementation_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
V1_SCHEMA = ROOT / "evidence" / "schema.json"
V2_SCHEMA = ROOT / "evidence" / "schema-v2.0.0-draft.1.json"
FIXTURE = ROOT / "evidence" / "contract-v2" / "synthetic-not-evaluable.json"
REPORT = ROOT / "evidence" / "contract-v2" / "synthetic-not-evaluable-report.md"


class ContractV2Tests(unittest.TestCase):
    def fixture(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def assert_refused(self, document: dict, message: str) -> None:
        with self.assertRaisesRegex(VerificationRefusal, message):
            recompute_or_refuse(document)

    @staticmethod
    def fact(observation: dict, field: str) -> dict:
        return next(item for item in observation["facts"] if item["field"] == field)

    @staticmethod
    def rederive(document: dict) -> None:
        attrition = _validate_attempts_and_observations(document)
        analysis = _expected_analysis(document, attrition)
        decision = _expected_decision(analysis)
        document["attrition"] = attrition
        document["analysis_result"] = analysis
        document["decision_receipt"] = decision
        document["human_report"] = _expected_human_report(
            document, attrition, analysis, decision
        )

    @staticmethod
    def rederive_producer_claims_without_observation_validation(document: dict) -> None:
        """Simulate a producer rewriting every derived claim around bad input."""

        attrition = document["attrition"]
        analysis = _expected_analysis(document, attrition)
        decision = _expected_decision(analysis)
        document["analysis_result"] = analysis
        document["decision_receipt"] = decision
        document["human_report"] = _expected_human_report(
            document, attrition, analysis, decision
        )

    def receipt_payload(self, document: dict) -> dict:
        return json.loads(
            document["registration"]["receipt_copy"]["exact_receipt_json_utf8"]
        )

    def verification_result(self, document: dict) -> dict:
        return json.loads(
            document["registration"]["originating_verification_copy"][
                "exact_verification_json_utf8"
            ]
        )

    def set_verification_result(self, document: dict, result: dict) -> None:
        exact = canonical_json_bytes(result).decode("utf-8")
        copy_record = document["registration"]["originating_verification_copy"]
        copy_record["exact_verification_json_utf8"] = exact
        copy_record["verification_result_sha256"] = sha256_bytes(exact.encode("utf-8"))

    def set_receipt_payload(
        self,
        document: dict,
        payload: dict,
        *,
        pretty: bool = False,
    ) -> None:
        exact = (
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            if pretty
            else canonical_json_bytes(payload).decode("utf-8")
        )
        receipt_copy = document["registration"]["receipt_copy"]
        receipt_copy["exact_receipt_json_utf8"] = exact
        receipt_digest = sha256_bytes(exact.encode("utf-8"))
        receipt_copy["registration_receipt_sha256"] = receipt_digest
        result = self.verification_result(document)
        result["signed_record_sha256"] = receipt_digest
        self.set_verification_result(document, result)

    def update_gateway_closure(self, document: dict, invocation_id: str) -> None:
        calls = sorted(
            (
                item["call_ordinal"],
                item["request_id"],
                item["observation_receipt_sha256"],
            )
            for item in document["gateway_observations"]
            if item["invocation_id"] == invocation_id
        )
        closure = next(
            item
            for item in document["gateway_invocation_closures"]
            if item["invocation_id"] == invocation_id
        )
        self.fact(closure, "gateway_call_count")["value"] = len(calls)
        self.fact(closure, "ordered_request_ids_sha256")["value"] = sha256_bytes(
            canonical_json_bytes([request_id for _, request_id, _ in calls])
        )
        self.fact(closure, "ordered_call_bindings_sha256")["value"] = (
            gateway_ordered_call_bindings_sha256(
                [
                    (request_id, receipt_sha256)
                    for _, request_id, receipt_sha256 in calls
                ]
            )
        )

    def append_gateway_call(
        self,
        document: dict,
        source_index: int = 0,
        *,
        update_closure: bool = True,
    ) -> dict:
        call = copy.deepcopy(document["gateway_observations"][source_index])
        call["request_id"] += "-second"
        call["call_ordinal"] = 2
        receipt = sha256_bytes(call["request_id"].encode("utf-8"))
        call["observation_receipt_sha256"] = receipt
        for fact in call["facts"]:
            fact["originating_receipt_sha256"] = receipt
            fact["source"]["receipt_sha256"] = receipt
            if fact["field"] == "request_id":
                fact["value"] = call["request_id"]
            elif fact["field"] == "call_ordinal":
                fact["value"] = 2
        document["gateway_observations"].append(call)
        if update_closure:
            self.update_gateway_closure(document, call["invocation_id"])
        return call

    def test_v2_is_immutable_draft_beside_unchanged_v1(self) -> None:
        v1 = json.loads(V1_SCHEMA.read_text(encoding="utf-8"))
        v2 = json.loads(V2_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(v1["$id"], "urn:agentic-coding-evaluation-lab:evidence:1.1.0")
        self.assertEqual(v1["properties"]["schema_version"]["const"], "1.1.0")
        self.assertEqual(
            v2["$id"],
            "urn:agentic-coding-evaluation-lab:evidence:2.0.0-draft.1",
        )
        self.assertEqual(
            v2["properties"]["schema_version"]["const"], CONTRACT_V2_SCHEMA_VERSION
        )
        self.assertIn(
            "normative *draft*",
            (ROOT / "analysis" / "contract_v2" / "__init__.py").read_text(),
        )

    def test_json_schema_accepts_fixture(self) -> None:
        schema = json.loads(V2_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(self.fixture())

    def test_verify_exact_bytes_refuses_schema_only_invalid_input(self) -> None:
        document = self.fixture()
        document["sanitization"]["notes"] = 123
        with self.assertRaisesRegex(
            VerificationRefusal, "Draft 2020-12 schema validation failed"
        ):
            verify_exact_bytes(canonical_json_bytes(document))

    def test_exact_fixture_recomputes_not_evaluable(self) -> None:
        first = verify_exact_bytes(FIXTURE.read_bytes())
        second = verify_exact_bytes(FIXTURE.read_bytes())
        self.assertEqual(first, second)
        self.assertEqual(first.decision_receipt["outcome"], "NOT_EVALUABLE")
        self.assertIsNone(first.decision_receipt["enforcing_rule"])
        self.assertIsNone(first.decision_receipt["promotion_recommendation"])
        self.assertEqual(first.analysis_result["statistics"], {})

    def test_fixture_binds_exact_schema_and_implementation_bundle(self) -> None:
        document = self.fixture()
        schema_digest = sha256_bytes(V2_SCHEMA.read_bytes())
        expected_manifest = [
            {
                "path": relative_path,
                "sha256": sha256_bytes((ROOT / relative_path).read_bytes()),
            }
            for relative_path in VERIFIER_IMPLEMENTATION_FILES
        ]
        self.assertEqual(
            document["human_report"]["verification"]["contract_schema_sha256"],
            schema_digest,
        )
        owner = document["registration"]["owner_contract"]
        self.assertEqual(
            owner["registration_schema_version"],
            EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION,
        )
        self.assertEqual(
            owner["registration_schema_sha256"],
            EVAL_REGISTRY_REGISTRATION_SCHEMA_SHA256,
        )
        self.assertEqual(
            owner["verification_schema_version"],
            EVAL_REGISTRY_VERIFICATION_SCHEMA_VERSION,
        )
        self.assertEqual(
            owner["verification_schema_sha256"],
            EVAL_REGISTRY_VERIFICATION_SCHEMA_SHA256,
        )
        self.assertEqual(expected_manifest, verifier_implementation_manifest())
        self.assertEqual(
            document["verifier"]["implementation_files"], expected_manifest
        )
        self.assertEqual(
            document["verifier"]["implementation_bundle_sha256"],
            verifier_implementation_bundle_sha256(),
        )
        self.assertEqual(document["verifier"]["custody"], "repository-only")
        self.assertEqual(document["verifier"]["release_status"], "unreleased-draft")

    def test_committed_report_is_pure_recomputation(self) -> None:
        verified = verify_exact_bytes(FIXTURE.read_bytes())
        rendered = render_markdown(
            verified.human_report,
            evidence_sha256=verified.evidence_sha256,
        )
        self.assertEqual(rendered, REPORT.read_text(encoding="utf-8"))
        self.assertIn("**NOT_EVALUABLE**", rendered)
        self.assertIn("No enforcing test", rendered)
        self.assertIn("Verifier/report/safety implementation bundle", rendered)
        self.assertEqual(
            verified.human_report["verification"][
                "verifier_implementation_bundle_sha256"
            ],
            verifier_implementation_bundle_sha256(),
        )

    def test_human_report_is_a_public_site_target(self) -> None:
        quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
        report_path = "reports/contract-v2-not-evaluable.qmd"
        self.assertGreaterEqual(quarto.count(report_path), 2)
        qmd = (ROOT / report_path).read_text(encoding="utf-8")
        self.assertIn("verify_exact_bytes", qmd)
        self.assertIn("NOT_EVALUABLE", qmd)

    def test_duplicate_json_keys_refuse(self) -> None:
        payload = FIXTURE.read_bytes().replace(
            b'{"analysis_result":',
            b'{"schema_version":"duplicate","analysis_result":',
            1,
        )
        with self.assertRaisesRegex(VerificationRefusal, "duplicate JSON key"):
            verify_exact_bytes(payload)

    def test_stale_schema_refuses(self) -> None:
        document = self.fixture()
        document["schema_version"] = "1.1.0"
        self.assert_refused(document, "stale or unknown")

    def test_nested_unknown_keys_refuse(self) -> None:
        mutations = (
            (lambda item: item["campaign"], "campaign"),
            (lambda item: item["task_set_reveal"]["tasks"][0], "task"),
            (lambda item: item["assignment_schedule"]["units"][0], "unit"),
            (lambda item: item["attempts"][0], "attempt"),
            (lambda item: item["gateway_invocation_opens"][0], "gateway-open"),
            (lambda item: item["gateway_observations"][0], "gateway"),
            (
                lambda item: item["gateway_invocation_closures"][0],
                "gateway-closure",
            ),
            (
                lambda item: item["editing_harness_descriptor_validations"][0],
                "descriptor-validation",
            ),
            (
                lambda item: item["harness_completion_observations"][0],
                "harness-completion",
            ),
            (lambda item: item["gateway_observations"][0]["facts"][0], "fact"),
            (lambda item: item["sanitization"], "sanitization"),
        )
        for select, label in mutations:
            with self.subTest(label=label):
                document = self.fixture()
                select(document)["unknown"] = "forbidden"
                self.assert_refused(document, "unknown keys: unknown")

    def test_nested_schema_version_tamper_refuses(self) -> None:
        mutations = (
            lambda item: item["science_protocol"],
            lambda item: item["task_set_reveal"]["tasks"][0],
            lambda item: item["assignment_schedule"]["units"][0],
            lambda item: item["attempts"][0],
            lambda item: item["gateway_invocation_opens"][0],
            lambda item: item["gateway_observations"][0],
            lambda item: item["gateway_invocation_closures"][0],
            lambda item: item["editing_harness_descriptor_validations"][0],
            lambda item: item["harness_completion_observations"][0],
            lambda item: item["gateway_observations"][0]["facts"][0],
            lambda item: item["sanitization"],
        )
        for index, select in enumerate(mutations):
            with self.subTest(index=index):
                document = self.fixture()
                select(document)["schema_version"] = "stale"
                self.assert_refused(document, "schema version mismatch")

    def test_missing_registration_refuses(self) -> None:
        document = self.fixture()
        document.pop("registration")
        self.assert_refused(document, "missing keys: registration")

    def test_registration_exact_receipt_byte_tamper_refuses(self) -> None:
        document = self.fixture()
        copy_record = document["registration"]["receipt_copy"]
        copy_record["exact_receipt_json_utf8"] += " "
        self.assert_refused(document, "registration receipt exact-byte digest mismatch")

    def test_registry_receipt_uses_actual_v1_domains_and_exact_byte_digest(
        self,
    ) -> None:
        document = self.fixture()
        payload = self.receipt_payload(document)
        self.assertEqual(
            payload["schema_version"], EVAL_REGISTRY_REGISTRATION_SCHEMA_VERSION
        )
        self.assertEqual(
            payload["plan_commitment"]["domain"], EVAL_REGISTRY_PLAN_DOMAIN
        )
        self.assertEqual(
            payload["task_set_commitment"]["domain"], EVAL_REGISTRY_TASK_SET_DOMAIN
        )
        self.assertEqual(
            payload["campaign_family_commitment"]["domain"],
            EVAL_REGISTRY_CAMPAIGN_FAMILY_DOMAIN,
        )
        exact = document["registration"]["receipt_copy"]["exact_receipt_json_utf8"]
        self.assertEqual(
            document["registration"]["receipt_copy"]["registration_receipt_sha256"],
            sha256_bytes(exact.encode("utf-8")),
        )

    def test_noncanonical_inner_receipt_bytes_remain_exactly_bound(self) -> None:
        document = self.fixture()
        self.set_receipt_payload(document, self.receipt_payload(document), pretty=True)
        self.rederive(document)
        self.assertEqual(
            recompute_or_refuse(document).decision_receipt["outcome"],
            "NOT_EVALUABLE",
        )

    def test_verification_result_join_tamper_refuses(self) -> None:
        document = self.fixture()
        result = self.verification_result(document)
        result["signed_record_sha256"] = "sha256:" + "9" * 64
        self.set_verification_result(document, result)
        self.assert_refused(document, "verification-to-registration digest mismatch")

    def test_self_reported_verification_cannot_become_authoritative(self) -> None:
        document = self.fixture()
        result = self.verification_result(document)
        result["authoritative"] = True
        self.set_verification_result(document, result)
        self.assert_refused(document, "informational")

    def test_reveal_tamper_refuses(self) -> None:
        document = self.fixture()
        document["registration"]["reveal"]["plan_nonce_hex"] = "33" * 32
        self.assert_refused(document, "science protocol hiding commitment mismatch")

    def test_commitment_algorithm_and_domain_are_pinned(self) -> None:
        for field, value, message in (
            ("algorithm", "other", "algorithm mismatch"),
            ("domain", "wrong-domain", "domain mismatch"),
        ):
            document = self.fixture()
            payload = self.receipt_payload(document)
            payload["plan_commitment"][field] = value
            self.set_receipt_payload(document, payload)
            self.assert_refused(document, message)

    def test_d2_verification_cannot_claim_tsa_time(self) -> None:
        document = self.fixture()
        result = self.verification_result(document)
        result["verified_tsa_time"] = "2026-01-01T00:00:00Z"
        self.set_verification_result(document, result)
        self.assert_refused(document, "must not claim a TSA time")

    def test_d2_verification_must_refuse(self) -> None:
        document = self.fixture()
        result = self.verification_result(document)
        result["verdict"] = "verified"
        self.set_verification_result(document, result)
        self.assert_refused(document, "must refuse")

    def test_d2_verification_refusal_reason_is_closed(self) -> None:
        document = self.fixture()
        result = self.verification_result(document)
        result["reasons"] = ["different synthetic reason"]
        self.set_verification_result(document, result)
        self.assert_refused(document, "refusal reason mismatch")

    def test_registration_attempt_ordinal_is_json_safe(self) -> None:
        document = self.fixture()
        document["campaign"]["attempt_ordinal"] = 9007199254740992
        payload = self.receipt_payload(document)
        payload["attempt_ordinal"] = 9007199254740992
        self.set_receipt_payload(document, payload)
        self.assert_refused(document, "JSON-safe integer")

    def test_assignment_schedule_tamper_refuses(self) -> None:
        document = self.fixture()
        document["assignment_schedule"]["units"][0]["session_id"] = "changed-session"
        self.assert_refused(document, "assignment-schedule binding mismatch")

    def test_attempt_pair_or_session_tamper_refuses(self) -> None:
        document = self.fixture()
        document["attempts"][0]["session_id"] = "wrong-session"
        self.assert_refused(document, "attempt session mismatch")

    def test_missing_scheduled_attempt_refuses(self) -> None:
        document = self.fixture()
        document["attempts"].pop()
        self.assert_refused(document, "scheduled/observed attempt set mismatch")

    def test_observation_orphan_refuses(self) -> None:
        for key in (
            "gateway_invocation_opens",
            "gateway_observations",
            "gateway_invocation_closures",
            "editing_harness_descriptor_validations",
            "harness_completion_observations",
        ):
            document = self.fixture()
            document[key][0]["attempt_id"] = "orphan"
            self.assert_refused(document, "orphan attempt")

    def test_observation_required_fact_sets_are_exact(self) -> None:
        for key in (
            "gateway_invocation_opens",
            "gateway_observations",
            "gateway_invocation_closures",
            "editing_harness_descriptor_validations",
            "harness_completion_observations",
        ):
            document = self.fixture()
            document[key][0]["facts"].pop()
            self.assert_refused(document, "required fact set mismatch")

    def test_unratified_owner_fixtures_cannot_claim_operational_schema(self) -> None:
        for key in (
            "gateway_invocation_opens",
            "gateway_observations",
            "gateway_invocation_closures",
            "editing_harness_descriptor_validations",
            "harness_completion_observations",
        ):
            with self.subTest(key=key):
                document = self.fixture()
                document[key][0]["owner_schema_status"] = "operational"
                self.assert_refused(
                    document, "must remain unratified synthetic fixture"
                )

    def test_aider_owner_receipt_validates_descriptor_but_does_not_claim_execution(
        self,
    ) -> None:
        fields = {
            fact["field"]
            for fact in self.fixture()["editing_harness_descriptor_validations"][0][
                "facts"
            ]
        }
        self.assertEqual(
            fields,
            {
                "invocation_id",
                "invocation_descriptor_sha256",
                "descriptor_schema_sha256",
                "validator_sha256",
                "runtime_version_sha256",
                "retry_policy",
                "descriptor_valid",
            },
        )
        self.assertNotIn("internal_retry_count", fields)
        self.assertNotIn("process_completed", fields)

    def test_harness_completion_is_separate_from_descriptor_validation(self) -> None:
        document = self.fixture()
        completion = document["harness_completion_observations"][0]
        fields = {fact["field"] for fact in completion["facts"]}
        self.assertEqual(
            fields,
            {"invocation_id", "process_completed", "completion_status", "exit_code"},
        )
        self.assertNotEqual(
            completion["completion_receipt_sha256"],
            document["editing_harness_descriptor_validations"][0][
                "validation_receipt_sha256"
            ],
        )

    def test_gateway_calls_are_one_to_many_per_harness_invocation(self) -> None:
        document = self.fixture()
        call = self.append_gateway_call(document)
        self.rederive(document)
        verified = recompute_or_refuse(document)
        self.assertEqual(
            call["invocation_id"], document["gateway_observations"][0]["invocation_id"]
        )
        self.assertEqual(len(document["gateway_observations"]), 5)
        self.assertEqual(verified.analysis_result["status"], "not_evaluable")

    def test_gateway_request_attempt_vector_owns_retry_count(self) -> None:
        document = self.fixture()
        observation = document["gateway_observations"][0]
        self.fact(observation, "request_attempt_count")["value"] = 2
        self.fact(observation, "request_attempt_vector")["value"].append(
            {
                "attempt_ordinal": 2,
                "outcome": "succeeded",
                "error_class": None,
            }
        )
        self.rederive(document)
        self.assertEqual(document["attrition"]["retry_attempts"], 1)
        self.assertEqual(
            recompute_or_refuse(document).decision_receipt["outcome"],
            "NOT_EVALUABLE",
        )

    def test_gateway_fallback_refuses_even_with_rederived_producer_claims(self) -> None:
        document = self.fixture()
        observation = document["gateway_observations"][0]
        self.fact(observation, "fallback_used")["value"] = True
        self.rederive_producer_claims_without_observation_validation(document)
        self.assert_refused(document, "scientific mode forbids gateway fallback")

    def test_gateway_request_ids_and_call_ordinals_are_unique(self) -> None:
        for field, message in (
            ("request_id", "request id must be unique"),
            ("call_ordinal", "call ordinal must be unique"),
        ):
            with self.subTest(field=field):
                document = self.fixture()
                call = self.append_gateway_call(document)
                original = document["gateway_observations"][0]
                call[field] = original[field]
                self.fact(call, field)["value"] = original[field]
                self.assert_refused(document, message)

    def test_gateway_call_ordinals_are_contiguous(self) -> None:
        document = self.fixture()
        call = self.append_gateway_call(document)
        call["call_ordinal"] = 3
        self.fact(call, "call_ordinal")["value"] = 3
        self.assert_refused(document, "call ordinals must be contiguous")

    def test_gateway_open_and_closure_receipts_are_distinct_and_bound(self) -> None:
        document = self.fixture()
        opened = document["gateway_invocation_opens"][0]
        closed = document["gateway_invocation_closures"][0]
        self.assertNotEqual(
            opened["open_receipt_sha256"], closed["closure_receipt_sha256"]
        )
        self.assertEqual(
            self.fact(closed, "open_receipt_sha256")["value"],
            opened["open_receipt_sha256"],
        )

    def test_gateway_closure_refuses_missing_last_call(self) -> None:
        document = self.fixture()
        self.append_gateway_call(document)
        document["gateway_observations"].pop()
        self.assert_refused(document, "closure call count mismatch")

    def test_gateway_closure_refuses_false_count_or_digest(self) -> None:
        for field, value, message in (
            ("gateway_call_count", 2, "closure call count mismatch"),
            (
                "ordered_request_ids_sha256",
                "sha256:" + "0" * 64,
                "closure ordered-request digest mismatch",
            ),
            (
                "ordered_call_bindings_sha256",
                "sha256:" + "1" * 64,
                "closure ordered-call binding digest mismatch",
            ),
        ):
            with self.subTest(field=field):
                document = self.fixture()
                closure = document["gateway_invocation_closures"][0]
                self.fact(closure, field)["value"] = value
                self.assert_refused(document, message)

    def test_gateway_closure_refuses_call_receipt_substitution(self) -> None:
        document = self.fixture()
        observation = document["gateway_observations"][0]
        replacement = "sha256:" + "2" * 64
        observation["observation_receipt_sha256"] = replacement
        for fact in observation["facts"]:
            fact["originating_receipt_sha256"] = replacement
            fact["source"]["receipt_sha256"] = replacement
        self.rederive_producer_claims_without_observation_validation(document)
        self.assert_refused(document, "closure ordered-call binding digest mismatch")

    def test_zero_call_pre_dispatch_failure_is_retained_and_evaluable_as_structure(
        self,
    ) -> None:
        document = self.fixture()
        attempt_id = document["gateway_observations"][0]["attempt_id"]
        invocation_id = document["gateway_observations"][0]["invocation_id"]
        document["gateway_observations"] = [
            item
            for item in document["gateway_observations"]
            if item["invocation_id"] != invocation_id
        ]
        self.update_gateway_closure(document, invocation_id)
        closure = next(
            item
            for item in document["gateway_invocation_closures"]
            if item["invocation_id"] == invocation_id
        )
        self.assertEqual(
            self.fact(closure, "ordered_call_bindings_sha256")["value"],
            gateway_ordered_call_bindings_sha256([]),
        )
        attempt = next(
            item for item in document["attempts"] if item["attempt_id"] == attempt_id
        )
        attempt["status"] = "failed"
        attempt["error_class"] = "pre_dispatch_failure"
        completion = next(
            item
            for item in document["harness_completion_observations"]
            if item["attempt_id"] == attempt_id
        )
        self.fact(completion, "completion_status")["value"] = "failed"
        self.fact(completion, "exit_code")["value"] = 1
        self.rederive(document)
        verified = recompute_or_refuse(document)
        self.assertEqual(document["attrition"]["terminal_status_counts"]["failed"], 1)
        self.assertEqual(verified.decision_receipt["outcome"], "NOT_EVALUABLE")

    def test_zero_call_success_refuses(self) -> None:
        document = self.fixture()
        invocation_id = document["gateway_observations"][0]["invocation_id"]
        document["gateway_observations"] = [
            item
            for item in document["gateway_observations"]
            if item["invocation_id"] != invocation_id
        ]
        self.update_gateway_closure(document, invocation_id)
        self.assert_refused(
            document, "zero-call invocation is allowed only for pre-dispatch failure"
        )

    def test_gateway_closure_must_bind_its_open_receipt(self) -> None:
        document = self.fixture()
        closure = document["gateway_invocation_closures"][0]
        self.fact(closure, "open_receipt_sha256")["value"] = "sha256:" + "0" * 64
        self.assert_refused(document, "does not bind its invocation-open receipt")

    def test_gateway_invocation_must_join_descriptor_invocation(self) -> None:
        document = self.fixture()
        observation = document["gateway_observations"][0]
        observation["invocation_id"] = "unowned-invocation"
        self.fact(observation, "invocation_id")["value"] = "unowned-invocation"
        self.assert_refused(document, "does not join editing-harness invocation")

    def test_receipt_digest_cannot_be_reused_across_planes(self) -> None:
        document = self.fixture()
        gateway_receipt = document["gateway_observations"][0][
            "observation_receipt_sha256"
        ]
        descriptor = document["editing_harness_descriptor_validations"][0]
        descriptor["validation_receipt_sha256"] = gateway_receipt
        for fact in descriptor["facts"]:
            fact["originating_receipt_sha256"] = gateway_receipt
            fact["source"]["receipt_sha256"] = gateway_receipt
        self.assert_refused(document, "reused across planes")

    def test_attempt_task_arm_and_positive_index_are_bound(self) -> None:
        for field, value, message in (
            ("task_id", "wrong-task", "attempt task mismatch"),
            ("arm", "candidate", "attempt arm mismatch"),
            ("attempt_index", 0, "positive integer"),
        ):
            document = self.fixture()
            document["attempts"][0][field] = value
            self.assert_refused(document, message)

    def test_gateway_attempt_count_must_join_attempt_vector(self) -> None:
        document = self.fixture()
        self.fact(document["gateway_observations"][0], "request_attempt_count")[
            "value"
        ] = 2
        self.assert_refused(document, "vector length mismatch")

    def test_provenance_upgrade_refuses(self) -> None:
        document = self.fixture()
        fact = document["editing_harness_descriptor_validations"][0]["facts"][0]
        self.assertEqual(fact["source"]["provenance"], "derived")
        fact["provenance"] = "measured"
        self.assert_refused(document, "may not upgrade provenance")

    def test_originating_receipt_rewrite_refuses(self) -> None:
        document = self.fixture()
        document["gateway_observations"][0]["facts"][0][
            "originating_receipt_sha256"
        ] = "sha256:" + "8" * 64
        self.assert_refused(document, "originating receipt mismatch")

    def test_attrition_claim_tamper_refuses(self) -> None:
        document = self.fixture()
        document["attrition"]["observed_attempts"] = 3
        self.assert_refused(document, "producer attrition")

    def test_analysis_claim_tamper_refuses(self) -> None:
        document = self.fixture()
        document["analysis_result"]["statistics"] = {"p_value": "0.01"}
        self.assert_refused(document, "producer analysis")

    def test_decision_claim_tamper_refuses(self) -> None:
        document = self.fixture()
        document["decision_receipt"]["outcome"] = "PROMOTE"
        self.assert_refused(document, "producer decision")

    def test_human_report_claim_tamper_refuses(self) -> None:
        document = self.fixture()
        document["human_report"]["decision"] = "PROMOTE"
        self.assert_refused(document, "producer human-report")

    def test_producer_public_safe_boolean_cannot_bypass_content_scan(self) -> None:
        document = self.fixture()
        document["human_report"]["limitations"][0] = "probe https://example.internal/v1"
        self.assert_refused(document, "publication boundary refusal")

    def test_noncanonical_exact_bytes_refuse(self) -> None:
        pretty = json.dumps(self.fixture(), indent=2).encode("utf-8")
        with self.assertRaisesRegex(VerificationRefusal, "canonical encoding"):
            verify_exact_bytes(pretty)

    def test_registry_owner_schema_digest_tamper_refuses(self) -> None:
        document = self.fixture()
        document["registration"]["owner_contract"]["registration_schema_sha256"] = (
            "sha256:" + "7" * 64
        )
        self.assert_refused(document, "registry registration schema digest mismatch")

    def test_duplicate_key_in_exact_registry_receipt_refuses(self) -> None:
        document = self.fixture()
        copy_record = document["registration"]["receipt_copy"]
        exact = copy_record["exact_receipt_json_utf8"]
        exact = '{"attempt_ordinal":99,' + exact[1:]
        receipt_digest = sha256_bytes(exact.encode("utf-8"))
        copy_record["exact_receipt_json_utf8"] = exact
        copy_record["registration_receipt_sha256"] = receipt_digest
        result = self.verification_result(document)
        result["signed_record_sha256"] = receipt_digest
        self.set_verification_result(document, result)
        self.assert_refused(document, "duplicate JSON key")

    def test_verifier_implementation_manifest_tamper_refuses(self) -> None:
        document = self.fixture()
        document["verifier"]["implementation_files"][0]["sha256"] = "sha256:" + "7" * 64
        self.assert_refused(document, "implementation file manifest mismatch")

    def test_verifier_implementation_bundle_digest_tamper_refuses(self) -> None:
        document = self.fixture()
        document["verifier"]["implementation_bundle_sha256"] = "sha256:" + "7" * 64
        self.assert_refused(document, "implementation bundle digest mismatch")

    def test_report_only_content_cannot_influence_decision(self) -> None:
        document = self.fixture()
        original = recompute_or_refuse(document).decision_receipt
        changed = copy.deepcopy(document)
        changed["human_report"]["title"] = "outcome-aware producer title"
        with self.assertRaises(VerificationRefusal):
            recompute_or_refuse(changed)
        self.assertEqual(original["outcome"], "NOT_EVALUABLE")

    def test_canonical_round_trip_is_byte_stable(self) -> None:
        payload = FIXTURE.read_bytes()
        self.assertEqual(canonical_json_bytes(json.loads(payload)), payload)


if __name__ == "__main__":
    unittest.main()
