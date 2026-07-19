"""Regenerate or verify the public E4/E2 offline design-freeze artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from analysis.calibration.e2_base_grid import (
    generate_base_grid,
    nuisance_maximizer_contract,
    perturbation_design,
    rule_specification,
)
from analysis.calibration.e4_corpus import corpus_schema, freeze_configuration

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis" / "calibration-freeze.v1.json"
BOUND_SOURCES = (
    ROOT / "analysis" / "calibration" / "e4_corpus.py",
    ROOT / "analysis" / "calibration" / "e2_base_grid.py",
)


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    """Encode canonical compact JSON with exactly one trailing newline."""

    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _object_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def build_artifact() -> dict[str, Any]:
    """Build the content-free design artifact from bound source bytes."""

    scenarios, omissions = generate_base_grid()
    e4_schema = corpus_schema()
    e4_configuration = freeze_configuration()
    e2_rule = rule_specification()
    e2_grid = {
        "root_seed_utf8": "lane-a-e2-oc-v1",
        "scenario_count": len(scenarios),
        "omission_count": len(omissions),
        "scenarios": scenarios,
        "omissions": omissions,
    }
    e2_perturbations = perturbation_design()
    e2_maximizer = nuisance_maximizer_contract()
    return {
        "artifact_version": "lane-a-calibration-offline-freeze.v1",
        "claim_boundary": {
            "artifact_kind": "synthetic_design_only",
            "registered": False,
            "observations_authorized": False,
            "contains_authored_corpus_records": False,
            "contains_operating_characteristic_results": False,
            "admits_grader": False,
            "selects_powered_method": False,
            "scientific_verdict": False,
        },
        "source_digests": {
            path.relative_to(ROOT).as_posix(): _digest(path) for path in BOUND_SOURCES
        },
        "component_digests": {
            "e4_schema": _object_digest(e4_schema),
            "e4_freeze_configuration": _object_digest(e4_configuration),
            "e2_rule": _object_digest(e2_rule),
            "e2_grid": _object_digest(e2_grid),
            "e2_perturbations": _object_digest(e2_perturbations),
            "e2_nuisance_maximizer": _object_digest(e2_maximizer),
        },
        "dependency_profile": {
            "runtime_dependencies": [],
            "python_requires": ">=3.11",
        },
        "e4": {
            "schema": e4_schema,
            "freeze_configuration": e4_configuration,
        },
        "e2": {
            "rule": e2_rule,
            "grid": e2_grid,
            "perturbations": e2_perturbations,
            "nuisance_maximizer": e2_maximizer,
        },
        "recomputation": {
            "command": "PYTHONPATH=src python -m analysis.run_calibration_freeze --check",
            "producer_claim_differs_from_recomputation": "NOT_EVALUABLE",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="refuse when the committed artifact differs; never rewrite it",
    )
    arguments = parser.parse_args()
    expected = canonical_bytes(build_artifact())

    if arguments.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print(f"calibration freeze mismatch: {OUTPUT}")
            return 1
        print(f"calibration freeze matches: {OUTPUT}")
        return 0

    OUTPUT.write_bytes(expected)
    print(f"wrote calibration freeze: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
