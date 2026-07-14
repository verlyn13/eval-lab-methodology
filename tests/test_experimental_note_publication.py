"""Public-site and honesty guards for the experimental inference note."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExperimentalNotePublicationTests(unittest.TestCase):
    def test_note_is_in_site_render_and_navigation(self) -> None:
        quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
        path = "reports/experimental-inference-note.qmd"
        self.assertGreaterEqual(quarto.count(path), 2)
        self.assertIn("Experimental inference", quarto)

    def test_note_pins_the_committed_results_bytes(self) -> None:
        results = (ROOT / "analysis" / "method-tranche-results.json").read_bytes()
        digest = hashlib.sha256(results).hexdigest()
        note = (ROOT / "reports" / "experimental-inference-note.qmd").read_text(
            encoding="utf-8"
        )
        self.assertIn(f'EXPECTED_RESULTS_SHA256 = "{digest}"', note)

    def test_public_surfaces_do_not_select_a_successor_method(self) -> None:
        surfaces = [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "PLAN.md").read_text(encoding="utf-8"),
            (ROOT / "index.qmd").read_text(encoding="utf-8"),
            (ROOT / "reports" / "experimental-inference-note.qmd").read_text(
                encoding="utf-8"
            ),
        ]
        readme, plan, index, note = surfaces
        self.assertIn("are under explicit scientific review and are not selected", readme)
        self.assertIn("No enforcing test", plan)
        self.assertIn("No successor method is selected", " ".join(index.split()))
        self.assertIn("No method is selected", note)
        self.assertIn("Exact arithmetic", note)
        self.assertIn("common i.i.d. paired-trinomial model", note)
        self.assertIn("finite nuisance grid", note)

    def test_historical_gate_is_labeled_historical(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        plan = (ROOT / "PLAN.md").read_text(encoding="utf-8")
        index = (ROOT / "index.qmd").read_text(encoding="utf-8")
        self.assertIn("## The historical statistical promotion gate", readme)
        self.assertIn("historical implementation truth", plan)
        self.assertIn("historical 0.2.0 core", index)


if __name__ == "__main__":
    unittest.main()
