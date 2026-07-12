from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dev dependency
    jsonschema = None

from eval_lab_methodology import (
    CONFORMANCE_IDENTITY_DOMAIN_SHA256,
    EVIDENCE_SCHEMA_VERSION,
    EvidenceValidationError,
    __core_content_hash__,
    __core_version__,
    bootstrap_ci,
    sign_test,
    superiority_by_margin,
    two_stage_bootstrap,
    validate_evidence_report,
    wilcoxon_signed_rank,
    wilson_interval,
)


ROOT = Path(__file__).resolve().parents[1]


class SchemaAndVersionTests(unittest.TestCase):
    def test_core_markers_are_queryable_and_stable(self) -> None:
        self.assertEqual(__core_version__, "0.2.0")
        self.assertRegex(__core_content_hash__, r"^sha256:[0-9a-f]{64}$")

    def test_schema_is_versioned_and_sample_validates(self) -> None:
        schema = json.loads((ROOT / "evidence" / "schema.json").read_text(encoding="utf-8"))
        sample = json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], "urn:agentic-coding-evaluation-lab:evidence:1.1.0")
        self.assertEqual(schema["properties"]["schema_version"]["const"], EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(sample["schema_version"], EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(sample["core"]["core_version"], __core_version__)
        self.assertEqual(sample["core"]["core_content_hash"], __core_content_hash__)

        identity_domain = sample["manifest"]["identity_domain"]
        self.assertEqual(identity_domain["status"], "matched")
        self.assertEqual(
            identity_domain["identity_domain_sha256"],
            CONFORMANCE_IDENTITY_DOMAIN_SHA256,
        )
        self.assertEqual(
            identity_domain["observed_identity_domain_sha256s"],
            [CONFORMANCE_IDENTITY_DOMAIN_SHA256],
        )

        validate_evidence_report(sample)

    def test_validator_fails_closed_on_missing_raw_outcomes(self) -> None:
        sample = json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))
        invalid = copy.deepcopy(sample)
        invalid.pop("raw_outcomes")
        with self.assertRaises(EvidenceValidationError):
            validate_evidence_report(invalid)

    def test_validator_fails_closed_on_empty_identity_domain(self) -> None:
        invalid = self._sample()
        invalid["manifest"]["identity_domain"] = {}
        with self.assertRaisesRegex(EvidenceValidationError, "identity_domain.status is required"):
            validate_evidence_report(invalid)

    def test_validator_fails_closed_on_empty_core_and_report_objects(self) -> None:
        for key in ("core", "report", "manifest"):
            invalid = self._sample()
            invalid[key] = {}
            with self.assertRaises(EvidenceValidationError, msg=f"empty {key} must not validate"):
                validate_evidence_report(invalid)

    def test_validator_rejects_matched_with_mismatched_domain_hashes(self) -> None:
        other = "sha256:" + "9" * 64
        for key in ("candidate_identity_domain_sha256", "incumbent_identity_domain_sha256"):
            invalid = self._sample()
            invalid["manifest"]["identity_domain"][key] = other
            with self.assertRaisesRegex(
                EvidenceValidationError,
                f"{key} must equal identity_domain_sha256 when status is matched",
            ):
                validate_evidence_report(invalid)

    def test_validator_rejects_matched_hash_missing_from_observed(self) -> None:
        other = "sha256:" + "9" * 64
        invalid = self._sample()
        invalid["manifest"]["identity_domain"]["observed_identity_domain_sha256s"] = [other]
        with self.assertRaisesRegex(
            EvidenceValidationError,
            "must appear in observed_identity_domain_sha256s when status is matched",
        ):
            validate_evidence_report(invalid)

    def test_validator_accepts_bridge_authorized_and_rejects_empty_bridge_fields(self) -> None:
        document = self._bridge_authorized_sample()
        validate_evidence_report(document)

        for key in ("bridge_id", "reason", "authorized_by"):
            invalid = self._bridge_authorized_sample()
            invalid["manifest"]["identity_domain"]["bridge_authorization"][key] = ""
            with self.assertRaisesRegex(
                EvidenceValidationError,
                f"bridge_authorization.{key} must be a non-empty string",
            ):
                validate_evidence_report(invalid)

    def test_validator_rejects_bridge_authorized_with_null_bridge(self) -> None:
        invalid = self._bridge_authorized_sample()
        invalid["manifest"]["identity_domain"]["bridge_authorization"] = None
        with self.assertRaisesRegex(
            EvidenceValidationError,
            "bridge_authorization must be an object",
        ):
            validate_evidence_report(invalid)

    @unittest.skipUnless(jsonschema is not None, "jsonschema is not installed")
    def test_schema_json_enforces_status_conditional_identity_domain_rules(self) -> None:
        schema = json.loads((ROOT / "evidence" / "schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

        validator.validate(self._sample())
        validator.validate(self._bridge_authorized_sample())

        matched_without_hash = self._sample()
        matched_without_hash["manifest"]["identity_domain"]["identity_domain_sha256"] = None

        matched_with_bridge = self._sample()
        matched_with_bridge["manifest"]["identity_domain"]["bridge_authorization"] = {
            "bridge_id": "bridge-001",
            "reason": "not allowed when matched",
        }

        bridge_without_authorization = self._bridge_authorized_sample()
        bridge_without_authorization["manifest"]["identity_domain"]["bridge_authorization"] = None

        for name, invalid in (
            ("matched with null identity_domain_sha256", matched_without_hash),
            ("matched with non-null bridge_authorization", matched_with_bridge),
            ("bridge-authorized with null bridge_authorization", bridge_without_authorization),
        ):
            with self.assertRaises(jsonschema.ValidationError, msg=name):
                validator.validate(invalid)

    def _sample(self) -> dict:
        return json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))

    def _bridge_authorized_sample(self) -> dict:
        document = self._sample()
        identity_domain = document["manifest"]["identity_domain"]
        identity_domain["status"] = "bridge-authorized"
        identity_domain["identity_domain_sha256"] = None
        identity_domain["incumbent_identity_domain_sha256"] = "sha256:" + "9" * 64
        identity_domain["observed_identity_domain_sha256s"] = [
            identity_domain["candidate_identity_domain_sha256"],
            identity_domain["incumbent_identity_domain_sha256"],
        ]
        identity_domain["bridge_authorization"] = {
            "bridge_id": "bridge-001",
            "reason": "synthetic example of an explicitly authorized cross-domain comparison",
            "authorized_by": "methodology owner",
        }
        return document

    def test_sample_report_numbers_recompute_from_raw_outcomes(self) -> None:
        sample = json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))
        raw = sample["raw_outcomes"]

        incumbent_successes = [
            replicate["incumbent"]["success"]
            for task in raw
            for replicate in task["replicates"]
        ]
        candidate_successes = [
            replicate["candidate"]["success"]
            for task in raw
            for replicate in task["replicates"]
        ]
        task_deltas = {
            task["task_id"]: [
                replicate["candidate"]["success"] - replicate["incumbent"]["success"]
                for replicate in task["replicates"]
            ]
            for task in raw
        }
        task_mean_deltas = [sum(values) / len(values) for values in task_deltas.values()]

        stats = sample["report"]["statistics"]
        incumbent = stats["capability"]["incumbent"]
        candidate = stats["capability"]["candidate"]
        self.assertEqual(incumbent["successes"], sum(incumbent_successes))
        self.assertEqual(candidate["successes"], sum(candidate_successes))
        self.assertEqual(incumbent["wilson"]["low"], wilson_interval(sum(incumbent_successes), 6)[0])
        self.assertEqual(candidate["wilson"]["high"], wilson_interval(sum(candidate_successes), 6)[1])

        single_stage_ci = bootstrap_ci(
            [delta for values in task_deltas.values() for delta in values],
            seed=12345,
        )
        self.assertLessEqual(single_stage_ci[0], stats["paired_delta"]["point_estimate"])

        two_stage = two_stage_bootstrap(task_deltas, iterations=2000, seed=12345)
        self.assertEqual(two_stage.estimate, stats["enhanced_estimators"]["two_stage_bootstrap"]["estimate"])
        self.assertEqual(two_stage.ci_low, stats["enhanced_estimators"]["two_stage_bootstrap"]["ci"]["low"])
        self.assertEqual(two_stage.ci_high, stats["enhanced_estimators"]["two_stage_bootstrap"]["ci"]["high"])

        wins, losses, ties, p_value = sign_test(task_mean_deltas)
        decision = sample["report"]["decision"]
        self.assertEqual((wins, losses, ties, p_value), (1, 0, 2, 1.0))
        self.assertTrue(decision["sign_test"]["reported_only"])

        wilcoxon = wilcoxon_signed_rank(task_mean_deltas)
        self.assertEqual(wilcoxon.statistic, stats["enhanced_estimators"]["wilcoxon_signed_rank"]["statistic"])
        self.assertEqual(wilcoxon.p_value, stats["enhanced_estimators"]["wilcoxon_signed_rank"]["p_value"])

        gate = superiority_by_margin(
            stats["paired_delta"]["point_estimate"],
            (two_stage.ci_low, two_stage.ci_high),
            margin=decision["margin"],
        )
        self.assertFalse(gate.promote)
        self.assertEqual(gate.promote, decision["promote"])


if __name__ == "__main__":
    unittest.main()
