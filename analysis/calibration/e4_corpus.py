"""Public E4 corpus-manifest contract and deterministic construction checks."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from typing import Any

CLASS_IDS = tuple(f"class_{index}" for index in range(1, 5))
EFFECTIVE_STRATA = (
    "positive_clear",
    "positive_boundary",
    "negative_clear",
    "negative_near_miss",
)
EDGE_CATEGORIES = (
    "functional_edge",
    "scope_edge",
    "regression_edge",
    "artifact_edge",
)
EDGE_STRATA = ("positive_boundary", "negative_near_miss")

MINIMUM_PER_CLASS_STRATUM = 10
MINIMUM_PER_EDGE_CATEGORY = 2
MINIMUM_POSITIVE = 80
MINIMUM_NEGATIVE = 80
MAX_AMBIGUITY_OVERALL = Fraction(1, 10)
MAX_AMBIGUITY_PER_CELL = Fraction(1, 5)
REVIEW_HOUR_CEILING = 48


def corpus_schema() -> dict[str, Any]:
    """Return the versioned public schema for content-free E4 record metadata."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://jvjohnson.dev/eval-lab-methodology/schema/e4-corpus-manifest.v1.json",
        "title": "E4 corpus manifest v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "records"],
        "properties": {
            "schema_version": {"const": "e4-corpus-manifest.v1"},
            "records": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "record_id",
                        "corpus_ordinal",
                        "class_id",
                        "author_intended_label",
                        "author_intended_stratum",
                        "author_intended_edge_category",
                        "adjudicated_label",
                        "effective_stratum",
                        "effective_edge_category",
                        "primary_ambiguity_flags",
                        "review_complete",
                        "unresolved",
                    ],
                    "properties": {
                        "record_id": {"type": "string", "minLength": 1},
                        "corpus_ordinal": {"type": "integer", "minimum": 1},
                        "class_id": {"enum": list(CLASS_IDS)},
                        "author_intended_label": {"type": "boolean"},
                        "author_intended_stratum": {"enum": list(EFFECTIVE_STRATA)},
                        "author_intended_edge_category": {
                            "oneOf": [
                                {"enum": list(EDGE_CATEGORIES)},
                                {"type": "null"},
                            ]
                        },
                        "adjudicated_label": {"type": "boolean"},
                        "effective_stratum": {"enum": list(EFFECTIVE_STRATA)},
                        "effective_edge_category": {
                            "oneOf": [
                                {"enum": list(EDGE_CATEGORIES)},
                                {"type": "null"},
                            ]
                        },
                        "primary_ambiguity_flags": {
                            "type": "array",
                            "prefixItems": [
                                {"type": "boolean"},
                                {"type": "boolean"},
                            ],
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "review_complete": {"type": "boolean"},
                        "unresolved": {"type": "boolean"},
                    },
                },
            },
        },
    }


def freeze_configuration() -> dict[str, Any]:
    """Return the ratified E4 design constants without reviewer or corpus data."""

    return {
        "classes": list(CLASS_IDS),
        "effective_strata": list(EFFECTIVE_STRATA),
        "edge_categories": list(EDGE_CATEGORIES),
        "minimum_effective_records_per_class_stratum": (MINIMUM_PER_CLASS_STRATUM),
        "minimum_records_per_edge_category_in_edge_cell": (MINIMUM_PER_EDGE_CATEGORY),
        "minimum_adjudicated_positive": MINIMUM_POSITIVE,
        "minimum_adjudicated_negative": MINIMUM_NEGATIVE,
        "ambiguity_definition": "union_of_either_primary_reviewer_flag",
        "maximum_overall_ambiguity_fraction": "1/10",
        "maximum_class_stratum_ambiguity_fraction": "1/5",
        "reviewers": {
            "primary_count": 2,
            "adjudicator_count": 1,
            "conflict_rule": (
                "no reviewer or adjudicator may assess a record, task contract, "
                "or grader behavior they authored or implemented"
            ),
            "qualification_records_per_reviewer": 16,
            "qualification_minimum_correct": 15,
            "qualification_failure_near_miss_records": 8,
            "qualification_failure_near_miss_minimum_correct": 8,
            "qualification_packets": "separate_non_overlapping",
            "qualification_records_enter_e4": False,
        },
        "review_person_hour_ceiling": REVIEW_HOUR_CEILING,
        "top_up": {
            "append_only": True,
            "priority": "edge_category_deficits_then_cell_deficits",
            "residual_cell_allocation": "edge_category_round_robin",
            "double_counting": "forbidden",
            "authors_blinded_to": [
                "machine_grades",
                "reviewer_rationales",
                "outcome_aggregates",
            ],
        },
    }


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return record["class_id"], record["effective_stratum"]


def _is_ambiguous(record: dict[str, Any]) -> bool:
    return any(record["primary_ambiguity_flags"])


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize effective adjudicated counts and ambiguity using exact fractions."""

    cell_counts = Counter(_cell(record) for record in records)
    edge_counts = Counter(
        (*_cell(record), record["effective_edge_category"])
        for record in records
        if record["effective_stratum"] in EDGE_STRATA
        and record["effective_edge_category"] in EDGE_CATEGORIES
    )
    ambiguous_cell_counts = Counter(
        _cell(record) for record in records if _is_ambiguous(record)
    )
    positive = sum(record["adjudicated_label"] is True for record in records)
    negative = sum(record["adjudicated_label"] is False for record in records)
    ambiguous = sum(_is_ambiguous(record) for record in records)
    author_disagreements = sum(
        record["author_intended_label"] is not record["adjudicated_label"]
        for record in records
    )

    return {
        "record_count": len(records),
        "adjudicated_positive": positive,
        "adjudicated_negative": negative,
        "unresolved": sum(record["unresolved"] for record in records),
        "incomplete": sum(not record["review_complete"] for record in records),
        "ambiguous": ambiguous,
        "ambiguity_fraction": Fraction(ambiguous, len(records))
        if records
        else Fraction(0, 1),
        "author_adjudicator_disagreements": author_disagreements,
        "author_adjudicator_disagreement_fraction": Fraction(
            author_disagreements, len(records)
        )
        if records
        else Fraction(0, 1),
        "cell_counts": dict(cell_counts),
        "edge_counts": dict(edge_counts),
        "ambiguous_cell_counts": dict(ambiguous_cell_counts),
    }


def top_up_targets(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ordered append-only targets, accounting jointly for deficits."""

    summary = summarize(records)
    cell_counts = Counter(summary["cell_counts"])
    edge_counts = Counter(summary["edge_counts"])
    targets: list[dict[str, Any]] = []
    next_ordinal = max((record["corpus_ordinal"] for record in records), default=0) + 1

    for class_id in CLASS_IDS:
        for stratum in EFFECTIVE_STRATA:
            if stratum in EDGE_STRATA:
                for category in EDGE_CATEGORIES:
                    key = (class_id, stratum, category)
                    deficit = max(0, MINIMUM_PER_EDGE_CATEGORY - edge_counts[key])
                    for _ in range(deficit):
                        targets.append(
                            {
                                "corpus_ordinal": next_ordinal,
                                "class_id": class_id,
                                "effective_stratum": stratum,
                                "edge_category": category,
                            }
                        )
                        next_ordinal += 1
                        cell_counts[(class_id, stratum)] += 1

            deficit = max(
                0,
                MINIMUM_PER_CLASS_STRATUM - cell_counts[(class_id, stratum)],
            )
            for offset in range(deficit):
                category = (
                    EDGE_CATEGORIES[offset % len(EDGE_CATEGORIES)]
                    if stratum in EDGE_STRATA
                    else None
                )
                targets.append(
                    {
                        "corpus_ordinal": next_ordinal,
                        "class_id": class_id,
                        "effective_stratum": stratum,
                        "edge_category": category,
                    }
                )
                next_ordinal += 1
    return targets


def construction_failures(records: list[dict[str, Any]]) -> list[str]:
    """Return reasons the manifest fails frozen E4 construction prerequisites."""

    failures: list[str] = []
    identifiers = [record["record_id"] for record in records]
    if len(identifiers) != len(set(identifiers)):
        failures.append("record_ids_not_unique")
    ordinals = [record["corpus_ordinal"] for record in records]
    if ordinals != list(range(1, len(records) + 1)):
        failures.append("corpus_ordinals_not_canonical")

    for index, record in enumerate(records):
        stratum = record["effective_stratum"]
        intended_stratum = record["author_intended_stratum"]
        expected_label = stratum.startswith("positive_")
        if record["adjudicated_label"] is not expected_label:
            failures.append(f"record_{index}_label_stratum_mismatch")
        if (
            intended_stratum in EDGE_STRATA
            and record["author_intended_edge_category"] not in EDGE_CATEGORIES
        ):
            failures.append(f"record_{index}_author_edge_category_missing")
        if (
            intended_stratum not in EDGE_STRATA
            and record["author_intended_edge_category"] is not None
        ):
            failures.append(f"record_{index}_unexpected_author_edge_category")
        if (
            stratum in EDGE_STRATA
            and record["effective_edge_category"] not in EDGE_CATEGORIES
        ):
            failures.append(f"record_{index}_edge_category_missing")
        if stratum not in EDGE_STRATA and record["effective_edge_category"] is not None:
            failures.append(f"record_{index}_unexpected_edge_category")

    summary = summarize(records)
    if summary["adjudicated_positive"] < MINIMUM_POSITIVE:
        failures.append("adjudicated_positive_below_minimum")
    if summary["adjudicated_negative"] < MINIMUM_NEGATIVE:
        failures.append("adjudicated_negative_below_minimum")
    if top_up_targets(records):
        failures.append("class_stratum_or_edge_category_below_minimum")
    if summary["incomplete"]:
        failures.append("review_incomplete")
    if summary["unresolved"]:
        failures.append("adjudication_unresolved")
    if summary["ambiguity_fraction"] > MAX_AMBIGUITY_OVERALL:
        failures.append("overall_ambiguity_above_limit")

    for cell, count in summary["cell_counts"].items():
        if not count:
            continue
        ambiguous = summary["ambiguous_cell_counts"].get(cell, 0)
        if Fraction(ambiguous, count) > MAX_AMBIGUITY_PER_CELL:
            failures.append(f"cell_ambiguity_above_limit:{cell[0]}:{cell[1]}")

    return failures
