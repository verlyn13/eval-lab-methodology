from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.publication_safety import (
    assert_publication_content_is_safe,
    normalized_name_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_methodology_report.py"
SAMPLE = ROOT / "evidence" / "sample-lab-report.json"
REPORT = ROOT / "reports" / "methodology-report.qmd"


class ReportRenderLayerTests(unittest.TestCase):
    def test_validate_only_accepts_public_safe_sample(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--evidence", str(SAMPLE), "--validate-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("validated public-safe evidence", completed.stdout)

    def test_validate_only_refuses_non_public_safe_json(self) -> None:
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        invalid = copy.deepcopy(sample)
        invalid["manifest"]["sanitization"]["status"] = "pending"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "non-public-safe.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence",
                    str(path),
                    "--validate-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public-safe", completed.stderr)

    def test_validate_only_refuses_independent_content_leak(self) -> None:
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        sample["manifest"]["identity_domain"]["reason"] = (
            "synthetic leak probe at https://example.internal/v1"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "content-leak.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence",
                    str(path),
                    "--validate-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("independent recursive content scan", completed.stderr)

    def test_content_scan_refuses_hash_only_private_name_match(self) -> None:
        marker = "synthetic-public-boundary-marker"
        with self.assertRaisesRegex(
            ValueError, "hashed private-identifier denylist"
        ) as raised:
            assert_publication_content_is_safe(
                {"text": marker},
                private_name_sha256s=frozenset({normalized_name_sha256(marker)}),
            )
        self.assertNotIn(marker, str(raised.exception))

    def test_report_contains_required_verbatim_labels(self) -> None:
        qmd = REPORT.read_text(encoding="utf-8")
        for needle in (
            "enforcing:superiority-by-margin",
            "bootstrap_ci_low_gt_margin",
            "enhanced:two-stage-bootstrap",
            "enhanced:wilcoxon-signed-rank",
            "enhanced:glmm-logistic",
            "alternative:",
            "sign['alternative']",
            "reported_only:{text(sign['reported_only'])}",
            "does not gate",
            "non-gating additive estimator",
        ):
            self.assertIn(needle, qmd)


if __name__ == "__main__":
    unittest.main()
