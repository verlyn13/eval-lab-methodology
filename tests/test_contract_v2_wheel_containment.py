"""The v2 draft and experimental tranche must not enter frozen package 0.2.0."""

from __future__ import annotations

import unittest
from pathlib import Path

from eval_lab_methodology import __core_content_hash__, __core_version__

ROOT = Path(__file__).resolve().parents[1]


class ContractV2WheelContainmentTests(unittest.TestCase):
    def test_frozen_core_markers_do_not_change(self) -> None:
        self.assertEqual(__core_version__, "0.2.0")
        self.assertEqual(
            __core_content_hash__,
            "sha256:7ec59090e3196b225ca2d68bc76cb6703b867f259f87e9d9e2bcafce896bf6ca",
        )

    def test_repository_only_modules_are_outside_package(self) -> None:
        package = ROOT / "src" / "eval_lab_methodology"
        self.assertFalse((package / "contract_v2").exists())
        self.assertFalse((package / "paired_trinomial.py").exists())
        self.assertFalse((package / "dependence.py").exists())
        self.assertTrue(
            (ROOT / "analysis" / "contract_v2" / "verification.py").is_file()
        )


if __name__ == "__main__":
    unittest.main()
