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
        self.assertIn("No accepted successor estimand", readme)
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
        self.assertIn("historical superiority helper", readme)
        self.assertIn("lower bound is strictly greater than the supplied margin", readme)
        self.assertIn("historical implementation truth", plan)
        self.assertIn("not tagged or published to a package registry", index)

    def test_public_status_refuses_unearned_readiness_claims(self) -> None:
        status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        index = (ROOT / "index.qmd").read_text(encoding="utf-8")
        identity = (ROOT / "identity-domain.qmd").read_text(encoding="utf-8")
        errata = (ROOT / "ERRATA.md").read_text(encoding="utf-8")

        self.assertIn(
            "not ready for a powered scientific promotion decision",
            " ".join(status.split()),
        )
        self.assertIn("raw per-attempt outcomes required to recompute", status)
        self.assertIn("no defensible powered real-model result", readme)
        self.assertIn("No powered, scientifically admissible model comparison", index)
        self.assertIn("necessary, not sufficient", identity)
        self.assertIn("does not prove numerical equivalence", errata)

        public_overviews = "\n".join((status, readme, index, identity))
        self.assertNotIn("released 0.2.0", public_overviews)
        self.assertNotIn("Calibrated small-n statistics", public_overviews)
        self.assertNotIn("everything that can change the numerics", public_overviews)

    def test_historical_examples_use_the_implemented_rule_without_model_claims(self) -> None:
        example = (ROOT / "evidence" / "false-positive-representative.md").read_text(
            encoding="utf-8"
        )
        data = (ROOT / "evidence" / "data.json").read_text(encoding="utf-8")
        figure_source = (ROOT / "figures" / "generate.py").read_text(encoding="utf-8")
        combined = "\n".join((example, data, figure_source))

        self.assertIn("ci_low > margin", example)
        self.assertNotIn("delta > band AND CI low > 0", combined)
        self.assertNotIn("significantly worse", combined)
        self.assertNotIn("caught the false positive", combined)
        self.assertNotIn("recommends the switch", combined)


if __name__ == "__main__":
    unittest.main()
