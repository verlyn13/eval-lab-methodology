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


class CalibrationSapTests(unittest.TestCase):
    def test_saps_are_explicitly_unregistered_and_public_safe(self) -> None:
        for path in SAP_FILES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn(
                    "Status:** Candidate protocol — not preregistered; no observations authorized.",
                    text,
                )
                self.assertNotIn("Status:** Preregistered Draft", text)
                assert_publication_content_is_safe(text)

    def test_e1_uses_m_one_and_fixed_terminal_counts(self) -> None:
        text = (SAP_DIR / "e1-lane-a-aa-sap.md").read_text(encoding="utf-8")
        self.assertIn("`m = 1`", text)
        self.assertIn("120 sessions total", text)
        self.assertIn("240 terminal arm attempts total", text)
        self.assertIn("actual chronological session position", text)
        self.assertIn("`INVARIANCE_NOT_REFUTED`", text)
        self.assertIn("`INVARIANCE_REFUTED`", text)
        self.assertIn("`APPARATUS_NOT_ADMISSIBLE`", text)
        self.assertIn("`NOT_EVALUABLE`", text)
        self.assertNotIn("objective is to estimate", text.lower())
        self.assertNotIn("pearson correlation", text.lower())

    def test_e4_and_e2_numbers_are_labeled_candidate(self) -> None:
        e4 = (SAP_DIR / "e4-grader-validation-sap.md").read_text(encoding="utf-8")
        e2 = (SAP_DIR / "e2-operating-characteristics-sap.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("160 authored output records", e4)
        self.assertIn("planned candidate values", e4)
        self.assertIn("10,000 planned simulation draws", e2)
        self.assertIn("planned candidate value", e2)
        self.assertIn("must be committed", e2)


if __name__ == "__main__":
    unittest.main()
