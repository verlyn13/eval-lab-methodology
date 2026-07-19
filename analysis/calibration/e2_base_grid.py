"""Exact E2 leading-rule specification and synthetic base-grid generator."""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations, product
from typing import Any

SAMPLE_SIZES = (20, 40, 60)
INCUMBENT_SUCCESS = (
    Fraction(3, 10),
    Fraction(1, 2),
    Fraction(7, 10),
    Fraction(9, 10),
)
MEAN_EFFECTS = (
    Fraction(0, 1),
    Fraction(1, 40),
    Fraction(1, 20),
    Fraction(1, 10),
    Fraction(1, 5),
)
HETEROGENEITY_WIDTH = Fraction(1, 10)
PERTURBATION_RATES = (
    Fraction(0, 1),
    Fraction(1, 100),
    Fraction(1, 20),
    Fraction(1, 10),
)
PERTURBATION_MECHANISMS = (
    "terminal_failure_symmetric",
    "terminal_failure_candidate_only",
    "terminal_failure_incumbent_only",
    "evidence_missing_symmetric",
    "evidence_missing_common_cause",
    "evidence_missing_candidate_only",
    "evidence_missing_incumbent_only",
)


def fraction_text(value: Fraction) -> str:
    """Serialize an exact rational in its reduced numerator/denominator form."""

    return f"{value.numerator}/{value.denominator}"


def exact_conditional_p_value(candidate_wins: int, incumbent_wins: int) -> Fraction:
    """Return the one-sided exact conditional sign-test p-value."""

    if candidate_wins < 0 or incumbent_wins < 0:
        raise ValueError("discordant counts must be non-negative")
    discordant = candidate_wins + incumbent_wins
    if discordant == 0:
        return Fraction(1, 1)
    numerator = sum(
        math.comb(discordant, value) for value in range(candidate_wins, discordant + 1)
    )
    return Fraction(numerator, 2**discordant)


def exact_conditional_rejects(
    candidate_wins: int,
    incumbent_wins: int,
    *,
    alpha: Fraction = Fraction(1, 20),
) -> bool:
    """Apply the frozen non-randomized one-sided rejection rule."""

    return exact_conditional_p_value(candidate_wins, incumbent_wins) <= alpha


def effect_patterns(mean_effect: Fraction) -> list[dict[str, Any]]:
    """Generate the four ratified class-effect families and named rotations."""

    width = HETEROGENEITY_WIDTH
    raw: dict[str, list[tuple[Fraction, ...]]] = {
        "homogeneous": [(mean_effect,) * 4],
        "balanced_opposing": [
            tuple(
                mean_effect + width if index in high else mean_effect - width
                for index in range(4)
            )
            for high in combinations(range(4), 2)
        ],
        # Rotations remain distinct design cells even when a zero mean makes
        # their numerical effect vectors identical.
        "sparse_benefit": [
            tuple(
                4 * mean_effect if index == active else Fraction(0)
                for index in range(4)
            )
            for active in range(4)
        ],
        "one_class_harm": [
            tuple(
                mean_effect - width if index == harmed else mean_effect + width / 3
                for index in range(4)
            )
            for harmed in range(4)
        ],
    }
    patterns: list[dict[str, Any]] = []
    for family, rotations in raw.items():
        for rotation_index, rotation in enumerate(rotations, start=1):
            if sum(rotation, Fraction(0)) / 4 != mean_effect:
                raise AssertionError(
                    "effect pattern does not preserve the equal-class estimand"
                )
            patterns.append(
                {
                    "family": family,
                    "rotation": rotation_index,
                    "class_effects": list(rotation),
                }
            )
    return patterns


def discordance_interval(
    incumbent_success: Fraction, effect: Fraction
) -> tuple[Fraction, Fraction] | None:
    """Return the full feasible paired discordance interval for one class."""

    lower = abs(effect)
    upper = min(
        2 * incumbent_success + effect,
        2 * (1 - incumbent_success) - effect,
    )
    if lower > upper:
        return None
    return lower, upper


def paired_outcomes(
    incumbent_success: Fraction,
    effect: Fraction,
    discordance: Fraction,
) -> dict[str, Fraction]:
    """Construct the exact paired binary cell probabilities."""

    interval = discordance_interval(incumbent_success, effect)
    if interval is None or not interval[0] <= discordance <= interval[1]:
        raise ValueError("discordance is outside the feasible interval")
    p10 = (discordance + effect) / 2
    p01 = (discordance - effect) / 2
    p11 = incumbent_success - p01
    p00 = 1 - incumbent_success - p10
    cells = {"p10": p10, "p01": p01, "p11": p11, "p00": p00}
    if any(value < 0 for value in cells.values()) or sum(cells.values()) != 1:
        raise AssertionError("paired-outcome construction is not a probability vector")
    return cells


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _scenario_id(value: dict[str, Any]) -> str:
    return "e2-base-" + hashlib.sha256(_canonical_bytes(value)).hexdigest()[:16]


def generate_base_grid() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate all feasible exact-base scenarios and explicit omissions."""

    included: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    for sample_size, incumbent_success, mean_effect in product(
        SAMPLE_SIZES, INCUMBENT_SUCCESS, MEAN_EFFECTS
    ):
        if sample_size % 4:
            raise AssertionError("equal class weighting requires N divisible by four")
        for pattern in effect_patterns(mean_effect):
            core = {
                "sample_size": sample_size,
                "per_class_sample_size": sample_size // 4,
                "sample_size_above_current_suite_requires_expansion": sample_size > 40,
                "incumbent_success": fraction_text(incumbent_success),
                "mean_effect": fraction_text(mean_effect),
                "rule_relative_label": (
                    "null_boundary" if mean_effect == 0 else "alternative"
                ),
                "effect_family": pattern["family"],
                "rotation": pattern["rotation"],
                "class_effects": [
                    fraction_text(value) for value in pattern["class_effects"]
                ],
            }
            intervals = [
                discordance_interval(incumbent_success, effect)
                for effect in pattern["class_effects"]
            ]
            scenario_id = _scenario_id(core)
            if any(interval is None for interval in intervals):
                omitted.append(
                    {
                        "scenario_id": scenario_id,
                        **core,
                        "reason": "empty_class_specific_discordance_domain",
                    }
                )
                continue
            included.append(
                {
                    "scenario_id": scenario_id,
                    **core,
                    "class_specific_discordance_intervals": [
                        {
                            "lower": fraction_text(interval[0]),
                            "upper": fraction_text(interval[1]),
                        }
                        for interval in intervals
                        if interval is not None
                    ],
                }
            )
    return included, omitted


def perturbation_design() -> dict[str, Any]:
    """Return the factored perturbation axis without manufacturing result cells."""

    declared = [
        {"mechanism": mechanism, "rate": fraction_text(rate)}
        for mechanism, rate in product(PERTURBATION_MECHANISMS, PERTURBATION_RATES)
    ]
    canonical = [{"mechanism": "none", "rate": "0/1"}] + [
        {"mechanism": mechanism, "rate": fraction_text(rate)}
        for mechanism, rate in product(PERTURBATION_MECHANISMS, PERTURBATION_RATES[1:])
    ]
    return {
        "declared_factors": declared,
        "canonical_factors": canonical,
        "mechanism_definitions": {
            "terminal_failure_symmetric": (
                "independently convert a successful gradeable outcome to failure "
                "in each arm at the common rate"
            ),
            "terminal_failure_candidate_only": (
                "convert a successful candidate outcome to gradeable failure"
            ),
            "terminal_failure_incumbent_only": (
                "convert a successful incumbent outcome to gradeable failure"
            ),
            "evidence_missing_symmetric": (
                "independent arm-level missingness events at the common marginal rate; "
                "either event makes the rule application NOT_EVALUABLE"
            ),
            "evidence_missing_common_cause": (
                "one pair-level event makes both arms unavailable and the rule "
                "application NOT_EVALUABLE"
            ),
            "evidence_missing_candidate_only": (
                "one candidate-arm event makes the rule application NOT_EVALUABLE"
            ),
            "evidence_missing_incumbent_only": (
                "one incumbent-arm event makes the rule application NOT_EVALUABLE"
            ),
        },
        "zero_rate_canonicalization": (
            "all zero-rate mechanisms map to the single exact-base factor"
        ),
        "outcomes": ["REJECT", "DO_NOT_REJECT", "NOT_EVALUABLE"],
        "unconditional_outcomes_are_mutually_exclusive_and_sum_to_one": True,
        "conditional_on_evaluable_is_diagnostic_only": True,
        "type_i_admission_uses": "exact_base_no_missingness_cell",
        "missingness_refusal_cannot_be_credited_as_type_i_control": True,
    }


def rule_specification() -> dict[str, Any]:
    """Return the ratified exact-rule and unresolved validity boundary."""

    return {
        "rule_id": "exact_conditional_sign_v1",
        "estimand": "equal_class_mean_candidate_minus_incumbent_success",
        "horizon": "fixed",
        "planned_pairs_per_class": "N/4",
        "direction": "one_sided_candidate_superiority",
        "margin": "0/1",
        "nominal_alpha": "1/20",
        "discordant_success": "candidate_win",
        "ties": "retained_then_conditioned_out",
        "zero_discordant_p_value": "1/1",
        "mid_p": False,
        "randomization": False,
        "interim_looks": False,
        "optional_stopping": False,
        "continuity_correction": False,
        "terminal_gradeable_failure": "arm_outcome_zero",
        "missing_or_invalid_evidence": "NOT_EVALUABLE",
        "drop_pairs": False,
        "imputation": False,
        "validity_boundary": (
            "analytic exactness requires discordant-sign symmetry; E2 must assess "
            "the class-heterogeneous estimand null"
        ),
        "powered_method_selected": False,
    }


def nuisance_maximizer_contract() -> dict[str, Any]:
    """Return the frozen maximizer requirements, not a claimed result."""

    return {
        "domain": "full_class_specific_cartesian_product",
        "endpoint_representation": "reduced_rational",
        "method": "certified_branch_and_bound",
        "probability_bounds": "outward",
        "subdivision": "deterministic",
        "certified_supremum_gap_at_most": "1/100000000",
        "exact_candidate_checks": True,
        "admission_ceiling": "3/50",
        "ceiling_straddle": "NOT_EVALUABLE",
        "implementation_status": "required_before_registered_E2_result",
        "future_nonexact_monte_carlo": {
            "draws_per_cell": 10000,
            "simultaneous_one_sided_bound_method": "must_be_separately_frozen",
            "draw_escalation_rule": "must_be_separately_frozen",
        },
    }
