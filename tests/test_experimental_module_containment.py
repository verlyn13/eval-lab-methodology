"""Containment checks for repository-only method-tranche computations."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for search_root in (ROOT, ROOT / "src"):
    if str(search_root) not in sys.path:
        sys.path.insert(0, str(search_root))

import build_backend
from eval_lab_methodology import __core_content_hash__, __core_version__
from eval_lab_methodology._version import _HASHED_SOURCE_FILES


EXPERIMENTAL_MODULES = {"dependence.py", "paired_trinomial.py"}


class ExperimentalModuleContainmentTests(unittest.TestCase):
    def test_experimental_modules_are_outside_core_hash_preimage(self) -> None:
        self.assertEqual(__core_version__, "0.2.0")
        self.assertEqual(
            __core_content_hash__,
            "sha256:7ec59090e3196b225ca2d68bc76cb6703b867f259f87e9d9e2bcafce896bf6ca",
        )
        self.assertTrue(
            EXPERIMENTAL_MODULES.isdisjoint(_HASHED_SOURCE_FILES),
            "repository-only experiments must not enter the 0.2.0 core hash preimage",
        )
        for module in EXPERIMENTAL_MODULES:
            self.assertTrue((ROOT / "analysis" / "_method_tranche" / module).is_file())
            self.assertFalse((ROOT / "src" / "eval_lab_methodology" / module).exists())

    def test_versioned_wheel_excludes_experimental_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel_name = build_backend.build_wheel(directory)
            self.assertEqual(wheel_name, "eval_lab_methodology-0.2.0-py3-none-any.whl")
            with zipfile.ZipFile(Path(directory) / wheel_name) as wheel:
                names = set(wheel.namelist())
                metadata = wheel.read(
                    "eval_lab_methodology-0.2.0.dist-info/METADATA"
                ).decode("utf-8")

        self.assertIn("Version: 0.2.0\n", metadata)
        for module in EXPERIMENTAL_MODULES:
            self.assertNotIn(f"eval_lab_methodology/{module}", names)
        self.assertFalse(any("_method_tranche" in name for name in names))


if __name__ == "__main__":
    unittest.main()
