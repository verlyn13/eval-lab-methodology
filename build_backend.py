"""Minimal in-tree PEP 517 backend for the pure-Python public core."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path
from typing import Any

NAME = "eval-lab-methodology"
NORMALIZED_NAME = "eval_lab_methodology"
VERSION = "0.2.0"
DIST_INFO = f"{NORMALIZED_NAME}-{VERSION}.dist-info"
ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT / "src" / "eval_lab_methodology"


def get_requires_for_build_wheel(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    return []


def get_requires_for_build_sdist(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    dist_info = Path(metadata_directory) / DIST_INFO
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(_metadata(), encoding="utf-8")
    (dist_info / "WHEEL").write_text(_wheel_metadata(), encoding="utf-8")
    return DIST_INFO


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    wheel_name = f"{NORMALIZED_NAME}-{VERSION}-py3-none-any.whl"
    wheel_path = Path(wheel_directory) / wheel_name
    rows: list[tuple[str, str, str]] = []
    payloads: list[tuple[str, bytes]] = []

    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if path.is_file() and not _is_bytecode(path):
            arcname = (
                f"eval_lab_methodology/{path.relative_to(PACKAGE_ROOT).as_posix()}"
            )
            payloads.append((arcname, path.read_bytes()))

    payloads.extend(
        [
            (f"{DIST_INFO}/METADATA", _metadata().encode("utf-8")),
            (f"{DIST_INFO}/WHEEL", _wheel_metadata().encode("utf-8")),
        ]
    )

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for arcname, content in payloads:
            wheel.writestr(arcname, content)
            rows.append((arcname, _record_hash(content), str(len(content))))

        record_name = f"{DIST_INFO}/RECORD"
        rows.append((record_name, "", ""))
        wheel.writestr(record_name, _record(rows).encode("utf-8"))

    return wheel_name


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    sdist_name = f"{NORMALIZED_NAME}-{VERSION}.tar.gz"
    sdist_path = Path(sdist_directory) / sdist_name
    prefix = f"{NORMALIZED_NAME}-{VERSION}"
    include_roots = [
        "src",
        "tests",
        "evidence/schema.json",
        "evidence/sample-lab-report.json",
        "README.md",
        "PLAN.md",
        "LICENSE",
        "pyproject.toml",
        "build_backend.py",
    ]
    with tarfile.open(sdist_path, "w:gz") as tar:
        for relative in include_roots:
            path = ROOT / relative
            if path.is_dir():
                for item in sorted(path.rglob("*")):
                    if item.is_file() and not _is_bytecode(item):
                        tar.add(
                            item,
                            arcname=f"{prefix}/{item.relative_to(ROOT).as_posix()}",
                        )
            elif path.is_file():
                tar.add(path, arcname=f"{prefix}/{relative}")
    return sdist_name


def _is_bytecode(path: Path) -> bool:
    """True for interpreter-state files that must never ship in artifacts."""

    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def _metadata() -> str:
    return "\n".join(
        [
            "Metadata-Version: 2.3",
            f"Name: {NAME}",
            f"Version: {VERSION}",
            "Summary: Public statistical and reporting core for the Agentic-Coding Evaluation Lab methodology.",
            "Author: Verlyn Nash",
            "License-Expression: Apache-2.0",
            "Requires-Python: >=3.11",
            "Provides-Extra: glmm",
            "Requires-Dist: pandas>=2.0; extra == 'glmm'",
            "Requires-Dist: statsmodels>=0.14; extra == 'glmm'",
            "Provides-Extra: dev",
            "Requires-Dist: jsonschema>=4.22; extra == 'dev'",
            "Requires-Dist: pytest>=8.0; extra == 'dev'",
            "",
        ]
    )


def _wheel_metadata() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: eval-lab-methodology-build-backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )


def _record_hash(content: bytes) -> str:
    digest = hashlib.sha256(content).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"sha256={encoded}"


def _record(rows: list[tuple[str, str, str]]) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerows(rows)
    return stream.getvalue()
