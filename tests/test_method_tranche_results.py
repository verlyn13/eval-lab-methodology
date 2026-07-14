"""Reproducibility tests for the committed method-tranche results artifact.

The committed JSON must be byte-for-byte reproducible from the committed,
seeded runner.  Reproducibility is a computation property (deterministic
enumeration and seeded simulation); these tests assert nothing about the
statistical validity of any rule the payload describes.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_RESULTS_PATH = _REPO_ROOT / "analysis" / "method-tranche-results.json"

from analysis import run_method_tranche

EXPECTED_LABELS = {
    "design_only": True,
    "synthetic_only": True,
    "informs_never_selects": True,
    "no_claim_about_any_real_system": True,
    "delta0_0_10": "retired as enforcing target; mechanics only",
    "enumeration_is_not_exactness": True,
    "ruling_status": "R1/R2/R4 held; held means not decided",
}
EXPECTED_CITATIONS = [
    {
        "name": "science-layer-consult-r1-r5.md",
        "sha256": "60409acec91e6aa02d4d39f8cfd4bc1f43b17031b1752da24f2f2e67f8aa896a",
    },
    {
        "name": "suite_power.py",
        "sha256": "bb534d7d908f64e01e45d2a039806fba22b54c994af9beb8713395f9ec53ff5a",
    },
]
EXPECTED_SCENARIO_FAMILIES = {
    "null_boundary",
    "heterogeneity",
    "lattice",
    "margin_feasibility",
    "superiority_mpib",
    "nondeterminism_floor",
    "cross_task_dependence",
}


class MethodTrancheResultsTests(unittest.TestCase):
    """Byte-level reproducibility and schema checks for the committed artifact."""

    runner = None
    committed_text: str = ""
    committed: dict = {}
    recomputed: dict = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = run_method_tranche
        cls.committed_text = _RESULTS_PATH.read_text(encoding="utf-8")
        cls.committed = json.loads(cls.committed_text)
        cls.recomputed = cls.runner.compute_results(cls.runner.SEED)

    def test_recomputed_payload_matches_committed_payload(self) -> None:
        self.assertEqual(self.recomputed, self.committed)

    def test_serialized_bytes_round_trip(self) -> None:
        rendered = json.dumps(self.recomputed, indent=2, sort_keys=True) + "\n"
        self.assertEqual(rendered, self.committed_text)

    def test_schema_tag_and_seed(self) -> None:
        self.assertEqual(self.committed["schema"], "method-tranche-results/v1")
        self.assertEqual(self.committed["seed"], 20260713)
        self.assertEqual(self.committed["seed"], self.runner.SEED)
        self.assertEqual(self.committed["generator"], "analysis/run_method_tranche.py")

    def test_honesty_labels_present_and_pinned(self) -> None:
        self.assertEqual(self.committed["labels"], EXPECTED_LABELS)

    def test_citations_are_name_and_sha256_only(self) -> None:
        self.assertEqual(self.committed["citations"], EXPECTED_CITATIONS)
        for record in self.committed["citations"]:
            self.assertEqual(sorted(record), ["name", "sha256"])

    def test_all_scenario_families_present(self) -> None:
        self.assertEqual(
            set(self.committed["scenarios"]), EXPECTED_SCENARIO_FAMILIES
        )

    def test_check_mode_accepts_matching_bytes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "results.json"
            artifact.write_bytes(b"canonical\n")
            before = artifact.stat()
            with (
                mock.patch.object(self.runner, "RESULTS_PATH", artifact),
                mock.patch.object(
                    self.runner,
                    "render_results_bytes",
                    return_value=b"canonical\n",
                ),
            ):
                self.assertEqual(self.runner.main(["--check"]), 0)
            self.assertEqual(artifact.read_bytes(), b"canonical\n")
            self.assertEqual(artifact.stat().st_mtime_ns, before.st_mtime_ns)

    def test_check_mode_fails_closed_without_rewriting_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "results.json"
            artifact.write_bytes(b"committed\n")
            with (
                mock.patch.object(self.runner, "RESULTS_PATH", artifact),
                mock.patch.object(
                    self.runner,
                    "render_results_bytes",
                    return_value=b"different\n",
                ),
            ):
                self.assertEqual(self.runner.main(["--check"]), 1)
            self.assertEqual(artifact.read_bytes(), b"committed\n")


if __name__ == "__main__":
    unittest.main()
