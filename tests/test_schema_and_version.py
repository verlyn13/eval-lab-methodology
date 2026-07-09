from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from eval_lab_methodology import (
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
        self.assertEqual(__core_version__, "0.1.0")
        self.assertRegex(__core_content_hash__, r"^sha256:[0-9a-f]{64}$")

    def test_schema_is_versioned_and_sample_validates(self) -> None:
        schema = json.loads((ROOT / "evidence" / "schema.json").read_text(encoding="utf-8"))
        sample = json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], "urn:agentic-coding-evaluation-lab:evidence:1.0.0")
        self.assertEqual(schema["properties"]["schema_version"]["const"], EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(sample["schema_version"], EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(sample["core"]["core_version"], __core_version__)
        self.assertEqual(sample["core"]["core_content_hash"], __core_content_hash__)

        validate_evidence_report(sample)

    def test_validator_fails_closed_on_missing_raw_outcomes(self) -> None:
        sample = json.loads((ROOT / "evidence" / "sample-lab-report.json").read_text(encoding="utf-8"))
        invalid = copy.deepcopy(sample)
        invalid.pop("raw_outcomes")
        with self.assertRaises(EvidenceValidationError):
            validate_evidence_report(invalid)

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
