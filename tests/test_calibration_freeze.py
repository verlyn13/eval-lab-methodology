"""Exact checks for the public E4/E2 offline design freeze."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

import jsonschema

from analysis import run_calibration_freeze
from analysis.calibration.e2_base_grid import (
    effect_patterns,
    exact_conditional_p_value,
    exact_conditional_rejects,
    generate_base_grid,
    paired_outcomes,
)
from analysis.calibration.e4_corpus import (
    CLASS_IDS,
    EDGE_CATEGORIES,
    EFFECTIVE_STRATA,
    construction_failures,
    corpus_schema,
    summarize,
    top_up_targets,
)

ROOT = Path(__file__).resolve().parents[1]


def _valid_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    ordinal = 1
    for class_id in CLASS_IDS:
        for stratum in EFFECTIVE_STRATA:
            for offset in range(10):
                is_edge = stratum in {"positive_boundary", "negative_near_miss"}
                records.append(
                    {
                        "record_id": f"{class_id}-{stratum}-{offset:02d}",
                        "corpus_ordinal": ordinal,
                        "class_id": class_id,
                        "author_intended_label": stratum.startswith("positive_"),
                        "author_intended_stratum": stratum,
                        "author_intended_edge_category": EDGE_CATEGORIES[offset % 4]
                        if is_edge
                        else None,
                        "adjudicated_label": stratum.startswith("positive_"),
                        "effective_stratum": stratum,
                        "effective_edge_category": EDGE_CATEGORIES[offset % 4]
                        if is_edge
                        else None,
                        "primary_ambiguity_flags": [False, False],
                        "review_complete": True,
                        "unresolved": False,
                    }
                )
                ordinal += 1
    return records


class E4CorpusFreezeTests(unittest.TestCase):
    def test_schema_accepts_generic_content_free_manifest(self) -> None:
        manifest = {
            "schema_version": "e4-corpus-manifest.v1",
            "records": _valid_records(),
        }
        jsonschema.Draft202012Validator(corpus_schema()).validate(manifest)

    def test_empty_corpus_joint_top_up_is_exactly_160_not_double_counted(self) -> None:
        targets = top_up_targets([])
        self.assertEqual(len(targets), 160)
        self.assertEqual(
            [target["corpus_ordinal"] for target in targets], list(range(1, 161))
        )
        by_cell: dict[tuple[str, str], int] = {}
        for target in targets:
            key = (target["class_id"], target["effective_stratum"])
            by_cell[key] = by_cell.get(key, 0) + 1
        self.assertEqual(set(by_cell.values()), {10})
        self.assertEqual(len(by_cell), 16)
        observed_cells = list(
            dict.fromkeys(
                (item["class_id"], item["effective_stratum"]) for item in targets
            )
        )
        expected_cells = [
            (class_id, stratum)
            for class_id in CLASS_IDS
            for stratum in EFFECTIVE_STRATA
        ]
        self.assertEqual(observed_cells, expected_cells)

    def test_complete_balanced_corpus_meets_construction_checks(self) -> None:
        records = _valid_records()
        self.assertEqual(construction_failures(records), [])
        summary = summarize(records)
        self.assertEqual(summary["adjudicated_positive"], 80)
        self.assertEqual(summary["adjudicated_negative"], 80)
        self.assertEqual(summary["ambiguity_fraction"], Fraction(0))

    def test_ambiguity_is_union_based_and_cell_limit_fails_closed(self) -> None:
        records = _valid_records()
        for index, flags in enumerate(([True, False], [False, True], [True, True])):
            records[index]["primary_ambiguity_flags"] = flags
        summary = summarize(records)
        self.assertEqual(summary["ambiguous"], 3)
        self.assertEqual(summary["ambiguity_fraction"], Fraction(3, 160))
        self.assertIn(
            "cell_ambiguity_above_limit:class_1:positive_clear",
            construction_failures(records),
        )

    def test_author_intent_disagreement_is_reported_not_used_as_gold(self) -> None:
        records = _valid_records()
        records[0]["author_intended_label"] = False
        summary = summarize(records)
        self.assertEqual(summary["author_adjudicator_disagreements"], 1)
        self.assertEqual(
            summary["author_adjudicator_disagreement_fraction"], Fraction(1, 160)
        )
        self.assertEqual(construction_failures(records), [])

    def test_corpus_ordinals_must_be_canonical_and_ordered(self) -> None:
        records = _valid_records()
        records[0]["corpus_ordinal"], records[1]["corpus_ordinal"] = 2, 1
        self.assertIn("corpus_ordinals_not_canonical", construction_failures(records))


class E2BaseGridTests(unittest.TestCase):
    def test_exact_conditional_rule_is_one_sided_and_nonrandomized(self) -> None:
        self.assertEqual(exact_conditional_p_value(0, 0), Fraction(1))
        self.assertEqual(exact_conditional_p_value(5, 0), Fraction(1, 32))
        self.assertTrue(exact_conditional_rejects(5, 0))
        self.assertFalse(exact_conditional_rejects(4, 1))

    def test_effect_families_preserve_equal_class_mean(self) -> None:
        for effect in (Fraction(0), Fraction(1, 40), Fraction(1, 5)):
            patterns = effect_patterns(effect)
            self.assertEqual(len(patterns), 15)
            self.assertEqual(
                {pattern["family"] for pattern in patterns},
                {
                    "homogeneous",
                    "balanced_opposing",
                    "sparse_benefit",
                    "one_class_harm",
                },
            )
            for pattern in patterns:
                self.assertEqual(sum(pattern["class_effects"]) / 4, effect)

    def test_paired_probability_construction_is_exact(self) -> None:
        cells = paired_outcomes(Fraction(1, 2), Fraction(1, 10), Fraction(1, 5))
        self.assertEqual(
            cells,
            {
                "p10": Fraction(3, 20),
                "p01": Fraction(1, 20),
                "p11": Fraction(9, 20),
                "p00": Fraction(7, 20),
            },
        )
        self.assertEqual(sum(cells.values()), 1)

    def test_base_grid_lists_every_feasible_scenario_or_omission(self) -> None:
        scenarios, omissions = generate_base_grid()
        self.assertEqual(len(scenarios), 717)
        self.assertEqual(len(omissions), 183)
        self.assertEqual(len(scenarios) + len(omissions), 900)
        self.assertEqual(
            {item["reason"] for item in omissions},
            {"empty_class_specific_discordance_domain"},
        )
        self.assertEqual(
            {item["rule_relative_label"] for item in scenarios},
            {"null_boundary", "alternative"},
        )
        self.assertTrue(
            all(
                item["sample_size_above_current_suite_requires_expansion"]
                == (item["sample_size"] > 40)
                for item in scenarios + omissions
            )
        )


class CalibrationArtifactTests(unittest.TestCase):
    def test_committed_artifact_recomputes_exactly_and_is_non_authorizing(self) -> None:
        path = ROOT / "analysis" / "calibration-freeze.v1.json"
        self.assertEqual(
            path.read_bytes(),
            run_calibration_freeze.canonical_bytes(
                run_calibration_freeze.build_artifact()
            ),
        )
        artifact = json.loads(path.read_text(encoding="utf-8"))
        boundary = artifact["claim_boundary"]
        self.assertEqual(boundary["artifact_kind"], "synthetic_design_only")
        self.assertFalse(boundary["registered"])
        self.assertFalse(boundary["observations_authorized"])
        self.assertFalse(boundary["contains_authored_corpus_records"])
        self.assertFalse(boundary["contains_operating_characteristic_results"])
        self.assertFalse(boundary["scientific_verdict"])
        self.assertEqual(
            set(artifact["component_digests"]),
            {
                "e4_schema",
                "e4_freeze_configuration",
                "e2_rule",
                "e2_grid",
                "e2_perturbations",
                "e2_nuisance_maximizer",
            },
        )
        self.assertEqual(artifact["dependency_profile"]["runtime_dependencies"], [])

    def test_check_mode_refuses_mismatch_without_rewriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            original = b'{"stale":true}\n'
            path.write_bytes(original)
            with (
                mock.patch.object(run_calibration_freeze, "OUTPUT", path),
                mock.patch.object(sys, "argv", ["run_calibration_freeze", "--check"]),
            ):
                self.assertEqual(run_calibration_freeze.main(), 1)
            self.assertEqual(path.read_bytes(), original)

    def test_artifact_has_no_corpus_record_payload(self) -> None:
        artifact = copy.deepcopy(run_calibration_freeze.build_artifact())
        self.assertNotIn("records", artifact["e4"])
        self.assertEqual(artifact["e2"]["grid"]["scenario_count"], 717)
        self.assertEqual(artifact["e2"]["grid"]["omission_count"], 183)


if __name__ == "__main__":
    unittest.main()
