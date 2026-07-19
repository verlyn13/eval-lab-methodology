"""Public-safety and claim-boundary checks for candidate calibration SAPs."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.publication_safety import assert_publication_content_is_safe

ROOT = Path(__file__).resolve().parents[1]
SAP_DIR = ROOT / "docs" / "preregistrations"
SAP_FILES = (
    SAP_DIR / "calibration-sap.md",
    SAP_DIR / "e4-grader-validation-sap.md",
    SAP_DIR / "e1-lane-a-aa-sap.md",
    SAP_DIR / "e2-operating-characteristics-sap.md",
)
DESIGN_STATUS = (
    "Status:** Candidate protocol — design decisions incorporated; "
    "not preregistered; no observations authorized."
)
OFFLINE_FREEZE_STATUS = (
    "Status:** Candidate protocol — offline design freeze implemented; "
    "not preregistered; no observations authorized."
)


class CalibrationSapTests(unittest.TestCase):
    def test_saps_are_unregistered_non_authorizing_and_public_safe(self) -> None:
        for path in SAP_FILES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                expected = (
                    DESIGN_STATUS
                    if path.name == "e1-lane-a-aa-sap.md"
                    else OFFLINE_FREEZE_STATUS
                )
                self.assertIn(expected, text)
                self.assertNotIn("Status:** Preregistered", text)
                assert_publication_content_is_safe(text)

    def test_umbrella_declares_dependency_and_opaque_profile(self) -> None:
        text = (SAP_DIR / "calibration-sap.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("E4 and E1 may proceed independently", text)
        self.assertIn("base operating-characteristics grid", text)
        self.assertIn("opaque registered input", text)
        self.assertIn("before the E4/E1 results are observed", normalized)

    def test_e1_localizes_exact_identity_and_uses_session_pairs(self) -> None:
        text = (SAP_DIR / "e1-lane-a-aa-sap.md").read_text(encoding="utf-8")
        self.assertIn("`m = 1`", text)
        self.assertIn("120 sessions total", text)
        self.assertIn("120 primary cross-arm comparisons", text)
        self.assertIn("240 terminal arm attempts total", text)
        self.assertIn("actual chronological session position", text)
        self.assertIn("`ENGINE_STAGE_DIVERGENCE_UNDER_REGISTERED_APPARATUS`", text)
        self.assertIn("authoritative, request-bound evidence", text)
        self.assertIn("Timing is corroborative only", text)
        self.assertIn("approximately `3 / 120 = 2.5%`", text)
        self.assertIn("repeated-task dependence", text)
        self.assertNotIn("engine_nondeterminism", text)

    def test_e1_conservative_state_precedence_is_explicit(self) -> None:
        text = (SAP_DIR / "e1-lane-a-aa-sap.md").read_text(encoding="utf-8")
        states = [
            "1. `NOT_EVALUABLE`",
            "2. `APPARATUS_NOT_ADMISSIBLE`",
            "3. `INVARIANCE_REFUTED`",
            "4. `INVARIANCE_NOT_REFUTED`",
        ]
        positions = [text.index(state) for state in states]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("including a failure that co-occurs with divergence", text)

    def test_e4_certifies_overall_gold_populations_and_freezes_strata(self) -> None:
        text = (SAP_DIR / "e4-grader-validation-sap.md").read_text(encoding="utf-8")
        self.assertIn("a minimum final corpus of 160 records", text)
        self.assertIn("at least 80 adjudicated-positive", text)
        self.assertIn("`positive_boundary`", text)
        self.assertIn("`negative_near_miss`", text)
        self.assertIn("compute cell and edge-category deficits jointly", text)
        self.assertIn("overall adjudicated-positive population", text)
        self.assertIn("point sensitivity is at least 0.90", text)
        self.assertIn("point specificity is at least 0.95", text)
        self.assertIn("false-pass avoidance", text)
        self.assertIn("at least two effective", text)
        self.assertIn("48 person-hours", text)
        self.assertIn("overall ambiguity fraction at most 0.10", text)
        self.assertIn("fraction at most 0.20", text)

    def test_e2_uses_rule_relative_exact_or_simultaneous_admission(self) -> None:
        text = (SAP_DIR / "e2-operating-characteristics-sap.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(text.split())
        self.assertIn("exact conditional paired binary", normalized)
        self.assertIn("remain held design slots", text)
        self.assertIn("rule-relative null cell", text)
        self.assertIn("supremum over the feasible discordance nuisance domain", text)
        self.assertIn("simultaneous one-sided upper confidence bounds", text)
        self.assertIn("10,000 draws", text)
        self.assertIn("`N = 60` is a hypothetical feasibility point", text)
        self.assertIn("producer claim that differs from recomputation", normalized)
        self.assertIn("`exact_conditional_sign_v1`", text)
        self.assertIn("717 feasible base scenarios", text)
        self.assertIn("183 explicit", text)
        self.assertIn("certified interval branch-and-bound", text)
        self.assertIn("synthetic design only", normalized)


if __name__ == "__main__":
    unittest.main()
