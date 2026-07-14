"""Immutable repository delivery contract for Contract B v2 draft.1."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import build_backend
from analysis.contract_v2 import verify_exact_bytes
from analysis.contract_v2.report import render_markdown
from analysis.contract_v2.verification import verifier_implementation_bundle_sha256
from eval_lab_methodology import __core_content_hash__, __core_version__
from scripts.publication_safety import assert_publication_content_is_safe

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence" / "contract-v2" / "delivery-manifest.v1.json"

EXPECTED_RUNTIME_PATHS = (
    "analysis/__init__.py",
    "analysis/contract_v2/__init__.py",
    "analysis/contract_v2/verification.py",
    "analysis/contract_v2/report.py",
    "scripts/publication_safety.py",
    "evidence/schema-v2.0.0-draft.1.json",
)
EXPECTED_RUNTIME_BUNDLE_SHA256 = (
    "sha256:67de3fef0fae06337f94117a51b948686aeec326717d0be85c4837ada1b45f3f"
)
EXPECTED_IMPLEMENTATION_BUNDLE_SHA256 = (
    "sha256:c1a01cebecbb685c158e7fa0a6fe5084fcbc08c54b3b41d169e9ce7c6a5f9899"
)
EXPECTED_CORE_CONTENT_HASH = (
    "sha256:7ec59090e3196b225ca2d68bc76cb6703b867f259f87e9d9e2bcafce896bf6ca"
)
EXPECTED_WHEEL_MEMBERS = {
    "eval_lab_methodology/__init__.py",
    "eval_lab_methodology/_version.py",
    "eval_lab_methodology/decision.py",
    "eval_lab_methodology/estimators.py",
    "eval_lab_methodology/identity_domain.py",
    "eval_lab_methodology/primitives.py",
    "eval_lab_methodology/py.typed",
    "eval_lab_methodology/schema_contract.py",
    "eval_lab_methodology-0.2.0.dist-info/METADATA",
    "eval_lab_methodology-0.2.0.dist-info/RECORD",
    "eval_lab_methodology-0.2.0.dist-info/WHEEL",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class ContractV2DeliveryManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_bytes = MANIFEST.read_bytes()
        self.manifest = json.loads(self.manifest_bytes)

    def copy_runtime_tree(self, destination: Path) -> None:
        for entry in self.manifest["runtime_files"]:
            source = ROOT / entry["path"]
            target = destination / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def assert_runtime_tree_matches(
        self,
        root: Path,
        *,
        exact_layout: bool = False,
    ) -> None:
        actual_manifest = []
        for entry in self.manifest["runtime_files"]:
            path = root / entry["path"]
            self.assertTrue(path.is_file())
            self.assertFalse(path.is_symlink())
            digest = sha256_bytes(path.read_bytes())
            self.assertEqual(digest, entry["sha256"])
            actual_manifest.append({"path": entry["path"], "sha256": digest})
        self.assertEqual(
            sha256_bytes(canonical_json_bytes(actual_manifest)),
            self.manifest["runtime_bundle_sha256"],
        )
        if exact_layout:
            actual_paths = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file() or path.is_symlink()
            }
            expected_paths = {
                entry["path"] for entry in self.manifest["runtime_files"]
            }
            self.assertEqual(actual_paths, expected_paths)

    def test_manifest_is_canonical_exact_keyed_and_public_safe(self) -> None:
        self.assertEqual(self.manifest_bytes, canonical_json_bytes(self.manifest))
        self.assertEqual(
            set(self.manifest),
            {
                "conformance",
                "contract",
                "core",
                "delivery_revision",
                "implementation_bundle_sha256",
                "license",
                "runtime",
                "runtime_bundle_sha256",
                "runtime_files",
                "schema_version",
                "source",
            },
        )
        self.assertEqual(
            self.manifest["schema_version"],
            "eval-lab-methodology.contract-b-v2-delivery.v1",
        )
        self.assertEqual(self.manifest["delivery_revision"], 1)
        assert_publication_content_is_safe(self.manifest)

    def test_contract_status_and_source_are_explicit(self) -> None:
        self.assertEqual(
            self.manifest["contract"],
            {
                "distribution_status": "repository-only-unreleased-draft",
                "operational_authority": False,
                "publication_status": "public-repository-published",
                "schema_sha256": (
                    "sha256:2b9a6befee9cf96bcef309aface080bf536c01b59e6a4351498c41fd4c4e4c23"
                ),
                "schema_version": (
                    "agentic-coding-evaluation-lab.evidence.v2.0.0-draft.1"
                ),
                "status": "normative_draft",
            },
        )
        self.assertEqual(
            self.manifest["source"],
            {
                "commit": "e2f18da39aa1f5558a12cf960a4d39853cec0ee9",
                "tree": "dc5272314605ca70d6ab6aaef07add29ab2c5402",
            },
        )

    def test_runtime_layout_entrypoints_and_dependency_are_explicit(self) -> None:
        self.assertEqual(
            self.manifest["runtime"],
            {
                "dependencies": [{"name": "jsonschema", "specifier": ">=4.22"}],
                "import_root": ".",
                "layout": "preserve-relative-paths",
                "python": ">=3.11",
                "render_entrypoint": (
                    "analysis.contract_v2.report:render_markdown"
                ),
                "verify_entrypoint": "analysis.contract_v2:verify_exact_bytes",
            },
        )

    def test_runtime_paths_and_bytes_match_the_frozen_manifest(self) -> None:
        entries = self.manifest["runtime_files"]
        self.assertEqual(
            tuple(entry["path"] for entry in entries),
            EXPECTED_RUNTIME_PATHS,
        )
        self.assertEqual(len({entry["path"] for entry in entries}), len(entries))
        for entry in entries:
            path = PurePosixPath(entry["path"])
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)
        self.assert_runtime_tree_matches(ROOT)
        self.assertEqual(
            self.manifest["runtime_bundle_sha256"],
            EXPECTED_RUNTIME_BUNDLE_SHA256,
        )
        self.assertEqual(
            self.manifest["implementation_bundle_sha256"],
            EXPECTED_IMPLEMENTATION_BUNDLE_SHA256,
        )
        self.assertEqual(
            verifier_implementation_bundle_sha256(),
            EXPECTED_IMPLEMENTATION_BUNDLE_SHA256,
        )

    def test_frozen_core_and_license_remain_separate(self) -> None:
        self.assertEqual(__core_version__, "0.2.0")
        self.assertEqual(__core_content_hash__, EXPECTED_CORE_CONTENT_HASH)
        self.assertEqual(
            self.manifest["core"],
            {"content_hash": EXPECTED_CORE_CONTENT_HASH, "version": "0.2.0"},
        )
        license_record = self.manifest["license"]
        self.assertEqual(license_record["spdx"], "Apache-2.0")
        self.assertEqual(
            sha256_bytes((ROOT / license_record["path"]).read_bytes()),
            license_record["sha256"],
        )
        self.assertFalse(
            (ROOT / "src" / "eval_lab_methodology" / "contract_v2").exists()
        )

    def test_versioned_wheel_contains_only_the_frozen_core(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel_name = build_backend.build_wheel(directory)
            self.assertEqual(wheel_name, "eval_lab_methodology-0.2.0-py3-none-any.whl")
            with zipfile.ZipFile(Path(directory) / wheel_name) as wheel:
                names = set(wheel.namelist())

        self.assertEqual(names, EXPECTED_WHEEL_MEMBERS)
        self.assertFalse(any("contract_v2" in name for name in names))
        self.assertFalse(any("delivery-manifest" in name for name in names))
        self.assertFalse(any("schema-v2.0.0-draft.1" in name for name in names))

    def test_conformance_fixture_and_report_match_exact_bytes(self) -> None:
        conformance = self.manifest["conformance"]
        fixture_path = ROOT / conformance["fixture"]["path"]
        report_path = ROOT / conformance["golden_report"]["path"]
        self.assertEqual(
            sha256_bytes(fixture_path.read_bytes()),
            conformance["fixture"]["sha256"],
        )
        self.assertEqual(
            sha256_bytes(report_path.read_bytes()),
            conformance["golden_report"]["sha256"],
        )
        verified = verify_exact_bytes(fixture_path.read_bytes())
        self.assertEqual(
            verified.decision_receipt["outcome"],
            conformance["expected_outcome"],
        )
        rendered = render_markdown(
            verified.human_report,
            evidence_sha256=verified.evidence_sha256,
        )
        self.assertEqual(rendered, report_path.read_text(encoding="utf-8"))

    def test_preserved_layout_imports_and_verifies_in_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_runtime_tree(root)
            self.assert_runtime_tree_matches(root, exact_layout=True)
            for section in ("fixture", "golden_report"):
                entry = self.manifest["conformance"][section]
                target = root / entry["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / entry["path"], target)

            program = """
from pathlib import Path
import analysis.contract_v2.verification as implementation
from analysis.contract_v2 import verify_exact_bytes
from analysis.contract_v2.report import render_markdown

root = Path.cwd().resolve()
assert Path(implementation.__file__).resolve().is_relative_to(root)
fixture = root / "evidence/contract-v2/synthetic-not-evaluable.json"
report = root / "evidence/contract-v2/synthetic-not-evaluable-report.md"
verified = verify_exact_bytes(fixture.read_bytes())
assert verified.decision_receipt["outcome"] == "NOT_EVALUABLE"
assert render_markdown(
    verified.human_report,
    evidence_sha256=verified.evidence_sha256,
) == report.read_text(encoding="utf-8")
"""
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [sys.executable, "-c", program],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_isolated_verifier_refuses_when_jsonschema_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_runtime_tree(root)
            fixture = self.manifest["conformance"]["fixture"]
            fixture_path = root / fixture["path"]
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / fixture["path"], fixture_path)

            program = """
import importlib.abc
import sys
from pathlib import Path

class BlockJsonschema(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "jsonschema" or fullname.startswith("jsonschema."):
            raise ModuleNotFoundError("jsonschema blocked by conformance test")
        return None

sys.meta_path.insert(0, BlockJsonschema())
from analysis.contract_v2 import VerificationRefusal, verify_exact_bytes

fixture = Path("evidence/contract-v2/synthetic-not-evaluable.json")
try:
    verify_exact_bytes(fixture.read_bytes())
except VerificationRefusal as exc:
    assert "Draft 2020-12 validation requires jsonschema" in str(exc)
else:
    raise AssertionError("missing jsonschema was not refused")
"""
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [sys.executable, "-c", program],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_every_runtime_file_mutation_or_deletion_breaks_parity(self) -> None:
        for entry in self.manifest["runtime_files"]:
            for operation in ("mutate", "delete"):
                with self.subTest(path=entry["path"], operation=operation):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        self.copy_runtime_tree(root)
                        target = root / entry["path"]
                        if operation == "mutate":
                            target.write_bytes(target.read_bytes() + b"\n")
                        else:
                            target.unlink()
                        with self.assertRaises(AssertionError):
                            self.assert_runtime_tree_matches(root, exact_layout=True)

    def test_unexpected_runtime_file_breaks_exact_layout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_runtime_tree(root)
            unexpected = root / "analysis" / "contract_v2" / "unexpected.py"
            unexpected.write_text("raise RuntimeError\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                self.assert_runtime_tree_matches(root, exact_layout=True)


if __name__ == "__main__":
    unittest.main()
