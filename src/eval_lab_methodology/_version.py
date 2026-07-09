"""Core version and content marker."""

from __future__ import annotations

import hashlib
from pathlib import Path

__core_version__ = "0.1.0"

_HASHED_SOURCE_FILES = (
    "__init__.py",
    "_version.py",
    "decision.py",
    "estimators.py",
    "primitives.py",
    "schema_contract.py",
)


def core_content_hash() -> str:
    """Return a stable sha256 marker for the public core source content."""

    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    digest.update(f"core-version:{__core_version__}\n".encode("utf-8"))
    for relative in _HASHED_SOURCE_FILES:
        digest.update(f"file:{relative}\n".encode("utf-8"))
        digest.update((root / relative).read_bytes())
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


__core_content_hash__ = core_content_hash()
