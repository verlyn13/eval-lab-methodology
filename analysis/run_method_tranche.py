"""Seeded scenario runner for the interim method-note tranche.

Composes the exact paired-trinomial machinery and the dependence /
design-effect machinery into one committed results payload covering the
tranche's operating-characteristic scenario families:

- ``null_boundary``: rejection behavior of candidate rules at and near
  the boundary of the composite null ``H0: Delta <= delta0``.
- ``heterogeneity``: task-level effects varying across tasks while the
  suite mean sits at the boundary.
- ``lattice``: replicate-lattice mechanics for a constant shift.
- ``margin_feasibility``: the power frontier for every construction
  evaluated in this tranche (the LFC-calibrated rule, the shifted
  sign-flip rule, and the normal-approximation z rule; the bounded-mean
  methods are deferred with required content 7), plus the independently
  derived falsifiable cross-check against the cited decision inputs.
- ``superiority_mpib``: a superiority rule at zero, stated separately
  from an operator-defined MPIB decision rule (grid of consequences
  only; the MPIB value is an operator input).
- ``nondeterminism_floor``: propagation of a measured apparatus floor
  into the effective cells and into alarm thresholds derived from the
  floor, never from zero.
- ``cross_task_dependence``: seeded Monte Carlo size distortion under
  within-session correlation across session layouts.

Honesty discipline, embedded in the payload and repeated here:

- Design-only, synthetic-only: every number is produced by this
  committed, seeded code; no claim is made about any real system.
- Computation and inference are distinct claims.  Deterministic
  integer/Fraction enumeration ("exact" in serialized records) describes
  arithmetic only; it does not confer finite-sample validity on any rule
  for the weak (composite average-effect) null.  Validity requires
  stated assumptions and is assessed in the accompanying method note.
- The coupled R1/R2/R4 rulings are held; held means not decided.  This
  payload informs that ruling and selects nothing: no inferential basis,
  test, replicate policy, margin, or MPIB value is chosen here.
- ``delta0 = 1/10`` is retired as an enforcing target and appears only
  so its lattice and feasibility mechanics can be studied.
- ``0.193`` is a falsifiable cross-check value, not a target: the power
  here is derived independently and any disagreement is reported, never
  tuned away.  Decision inputs are cited by filename and SHA-256 only.

Canonical verification command (never writes):
``PYTHONPATH=src python -m analysis.run_method_tranche --check``

Regeneration command (explicitly rewrites the committed artifact):
``PYTHONPATH=src python -m analysis.run_method_tranche``
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from analysis._method_tranche.dependence import (
    SessionLayout,
    alarm_threshold,
    covariance_attenuation_factor,
    design_effect,
    disagreement_probability,
    floor_transformed_cells,
    size_distortion,
    z_test_rejects,
)
from analysis._method_tranche.paired_trinomial import (
    LfcCalibration,
    boundary_configuration,
    collapse_counts_to_sum,
    counts_distribution,
    exact_power,
    is_attainable_shift,
    lfc_calibrate,
    replicate_lattice,
    signflip_rejection_probability,
    sum_distribution,
    tail_probability,
)

# --- Pinned design constants (every grid in the payload traces here) ---

SEED = 20260713
ALPHA = Fraction(1, 20)
N_GRID = (20, 40, 60)
# Retired as an enforcing or powered-promotion target; kept only so the
# tranche can study its lattice and feasibility mechanics.
DELTA0_RETIRED = Fraction(1, 10)
DELTA0_GRID = (Fraction(0), DELTA0_RETIRED)

SIZE_PID_GRID = (
    Fraction(1, 10),
    Fraction(3, 10),
    Fraction(1, 2),
    Fraction(7, 10),
    Fraction(9, 10),
    Fraction(1, 1),
)
NEAR_BOUNDARY_OFFSETS = (Fraction(0), Fraction(-1, 20), Fraction(-1, 10))
SIGNFLIP_PID_GRID = (Fraction(3, 10), Fraction(1, 2), Fraction(7, 10), Fraction(1, 1))

FEAS_DELTA_GRID = (
    Fraction(3, 20),
    Fraction(1, 5),
    Fraction(1, 4),
    Fraction(3, 10),
    Fraction(7, 20),
    Fraction(2, 5),
)
FEAS_PID_GRID = (Fraction(1, 5), Fraction(3, 10), Fraction(2, 5), Fraction(1, 2))

MPIB_GRID = (
    Fraction(1, 20),
    Fraction(1, 10),
    Fraction(3, 20),
    Fraction(1, 5),
    Fraction(1, 4),
)
MPIB_TRUE_DELTAS = (Fraction(0), Fraction(1, 10), Fraction(1, 5), Fraction(3, 10))
MPIB_PI_D = Fraction(3, 10)

FLOOR_GRID = (Fraction(1, 100), Fraction(1, 50), Fraction(1, 20))
# (p11, p10, p01, p00): a documented synthetic choice with
# Delta = 3/10 and pi_d = 3/10.
FLOOR_BASE_CELLS = (Fraction(2, 5), Fraction(3, 10), Fraction(0), Fraction(3, 10))
REPEAT_PAIRS_GRID = (40, 80, 120)

RHO_GRID = (0.01, 0.02, 0.05, 0.10)
LAYOUTS = ((1, 40), (2, 20), (4, 10))  # (sessions, pairs_per_session)
DEP_PI_D = 0.30
N_SIMS = 5000

# Synthetic 40-task profiles: (name, delta0, blocks) with blocks of
# (task_count, p_plus, p_minus).  Suite-mean Delta sits exactly at the
# named boundary in every profile.
HETEROGENEITY_PROFILES: tuple[
    tuple[str, Fraction, tuple[tuple[int, Fraction, Fraction], ...]], ...
] = (
    (
        "hom-boundary-0.10",
        DELTA0_RETIRED,
        ((40,) + boundary_configuration(DELTA0_RETIRED, Fraction(3, 10)),),
    ),
    (
        "het-two-block-0.10",
        DELTA0_RETIRED,
        ((20, Fraction(9, 20), Fraction(1, 20)), (20, Fraction(1, 20), Fraction(1, 4))),
    ),
    (
        "het-extreme-0.10",
        DELTA0_RETIRED,
        ((24, Fraction(1, 2), Fraction(0)), (16, Fraction(0), Fraction(1, 2))),
    ),
    (
        "hom-boundary-zero",
        Fraction(0),
        ((40, Fraction(3, 20), Fraction(3, 20)),),
    ),
    (
        "het-two-block-zero",
        Fraction(0),
        ((20, Fraction(7, 20), Fraction(1, 20)), (20, Fraction(1, 20), Fraction(7, 20))),
    ),
)

DECISION_INPUT_CITATIONS: tuple[dict[str, str], ...] = (
    {
        "name": "science-layer-consult-r1-r5.md",
        "sha256": "60409acec91e6aa02d4d39f8cfd4bc1f43b17031b1752da24f2f2e67f8aa896a",
    },
    {
        "name": "suite_power.py",
        "sha256": "bb534d7d908f64e01e45d2a039806fba22b54c994af9beb8713395f9ec53ff5a",
    },
)

RESULTS_PATH = Path(__file__).resolve().parent / "method-tranche-results.json"


# --- Serialization helpers ---


def _frac(value: Fraction) -> dict[str, Any]:
    """Serialize an exactly computed rational quantity.

    ``exact`` records the rational arithmetic result; ``value`` is its
    nearest float.  "Exact" here is a computation statement about the
    arithmetic, never a validity claim about any statistical rule.
    """
    return {"exact": f"{value.numerator}/{value.denominator}", "value": float(value)}


def _citations() -> list[dict[str, str]]:
    return [dict(record) for record in DECISION_INPUT_CITATIONS]


def _paired_params(delta: Fraction, pi_d: Fraction) -> tuple[Fraction, Fraction]:
    """(p_plus, p_minus) with p_plus - p_minus = delta and p_plus + p_minus = pi_d.

    Handles negative ``delta`` (interior of the composite null) by
    mirroring the boundary parameterization.
    """
    if delta >= 0:
        return boundary_configuration(delta, pi_d)
    mirrored_plus, mirrored_minus = boundary_configuration(-delta, pi_d)
    return (mirrored_minus, mirrored_plus)


def _iid_counts(
    n: int,
    p_plus: Fraction,
    p_minus: Fraction,
    cache: dict[tuple[int, Fraction, Fraction], dict[tuple[int, int], Fraction]],
) -> dict[tuple[int, int], Fraction]:
    key = (n, p_plus, p_minus)
    if key not in cache:
        cache[key] = counts_distribution([(p_plus, p_minus)] * n)
    return cache[key]


def _z_rejection_probability(
    counts: dict[tuple[int, int], Fraction],
    *,
    n: int,
    alpha: float,
    mu0: float,
) -> Fraction:
    """Rejection probability of the normal-approximation z rule.

    Computed by deterministic enumeration over the (n_plus, n_minus)
    counts distribution: the z statistic depends on the differences only
    through their counts, so a representative ordering suffices.  The
    enumeration is arithmetic only; the z rule itself remains an
    approximation whose validity is assessed in the method note.
    """
    total = Fraction(0)
    for (n_plus, n_minus), probability in sorted(counts.items()):
        differences = [1] * n_plus + [-1] * n_minus + [0] * (n - n_plus - n_minus)
        if z_test_rejects(differences, alpha=alpha, mu0=mu0):
            total += probability
    return total


# --- Scenario families ---


def _null_boundary(
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
    counts_cache: dict[tuple[int, Fraction, Fraction], dict[tuple[int, int], Fraction]],
) -> list[dict[str, Any]]:
    """Rejection behavior at and near the composite-null boundary."""
    records: list[dict[str, Any]] = []
    for n in N_GRID:
        for delta0 in DELTA0_GRID:
            calibration = calibrations[(n, delta0)]
            sizes = dict(calibration.sizes_by_pi_d)
            summary = [
                {"pi_d": _frac(pi_d), "size": _frac(sizes[pi_d])}
                for pi_d in SIZE_PID_GRID
            ]
            near_boundary: list[dict[str, Any]] = []
            for offset in NEAR_BOUNDARY_OFFSETS:
                delta = delta0 + offset
                cells: list[dict[str, Any]] = []
                for pi_d in SIZE_PID_GRID:
                    if pi_d < abs(delta):
                        cells.append({"pi_d": _frac(pi_d), "skipped": True})
                        continue
                    p_plus, p_minus = _paired_params(delta, pi_d)
                    counts = _iid_counts(n, p_plus, p_minus, counts_cache)
                    lfc_rejection = tail_probability(
                        collapse_counts_to_sum(counts), calibration.critical_value
                    )
                    z_rejection = _z_rejection_probability(
                        counts, n=n, alpha=float(ALPHA), mu0=float(delta0)
                    )
                    cells.append(
                        {
                            "pi_d": _frac(pi_d),
                            "skipped": False,
                            "lfc_calibrated_rejection": _frac(lfc_rejection),
                            "normal_approx_rejection": _frac(z_rejection),
                        }
                    )
                near_boundary.append(
                    {"offset": _frac(offset), "true_delta": _frac(delta), "cells": cells}
                )
            record: dict[str, Any] = {
                "n": n,
                "delta0": _frac(delta0),
                "alpha": _frac(ALPHA),
                "calibration": {
                    "critical_value": calibration.critical_value,
                    "sup_size": _frac(calibration.sup_size),
                    "lfc_pi_d": _frac(calibration.lfc_pi_d),
                    "boundary_sizes_on_summary_grid": summary,
                    "note": (
                        "critical value calibrated by grid supremum over the null "
                        "boundary; the least-favorable pi_d is found, not assumed"
                    ),
                },
                "near_boundary_rejection": near_boundary,
            }
            signflip_cells = []
            for pi_d in SIGNFLIP_PID_GRID:
                p_plus, p_minus = boundary_configuration(delta0, pi_d)
                counts = _iid_counts(n, p_plus, p_minus, counts_cache)
                signflip_cells.append(
                    {
                        "pi_d": _frac(pi_d),
                        "size": _frac(
                            signflip_rejection_probability(
                                counts, n=n, delta0=delta0, alpha=ALPHA
                            )
                        ),
                    }
                )
            record["signflip_size_at_boundary"] = signflip_cells
            records.append(record)
    return records


def _heterogeneity(
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
) -> list[dict[str, Any]]:
    """Task-level effect heterogeneity with the suite mean at the boundary."""
    records: list[dict[str, Any]] = []
    for name, delta0, blocks in HETEROGENEITY_PROFILES:
        task_params: list[tuple[Fraction, Fraction]] = []
        for count, p_plus, p_minus in blocks:
            task_params.extend([(p_plus, p_minus)] * count)
        n = len(task_params)
        counts = counts_distribution(task_params)
        calibration = calibrations[(n, delta0)]
        mean_delta = sum(
            (Fraction(count) * (p_plus - p_minus) for count, p_plus, p_minus in blocks),
            Fraction(0),
        ) / Fraction(n)
        records.append(
            {
                "profile": name,
                "n": n,
                "delta0": _frac(delta0),
                "alpha": _frac(ALPHA),
                "suite_mean_delta": _frac(mean_delta),
                "blocks": [
                    {"tasks": count, "p_plus": _frac(p_plus), "p_minus": _frac(p_minus)}
                    for count, p_plus, p_minus in blocks
                ],
                "lfc_calibrated": {
                    "critical_value": calibration.critical_value,
                    "rejection_probability": _frac(
                        tail_probability(
                            collapse_counts_to_sum(counts), calibration.critical_value
                        )
                    ),
                },
                "signflip_shifted": {
                    "rejection_probability": _frac(
                        signflip_rejection_probability(
                            counts, n=n, delta0=delta0, alpha=ALPHA
                        )
                    )
                },
                "normal_approx": {
                    "rejection_probability": _frac(
                        _z_rejection_probability(
                            counts, n=n, alpha=float(ALPHA), mu0=float(delta0)
                        )
                    )
                },
            }
        )
    return records


def _lattice() -> dict[str, Any]:
    """Replicate-lattice mechanics for a constant per-task shift of 1/10."""
    lattices = [
        {"m": m, "values": [_frac(value) for value in replicate_lattice(m)]}
        for m in (2, 3)
    ]
    attainability = []
    for m in (1, 2, 3):
        points = replicate_lattice(m)
        min_gap = min(abs(point - DELTA0_RETIRED) for point in points)
        attainability.append(
            {
                "m": m,
                "shift": _frac(DELTA0_RETIRED),
                "attainable": is_attainable_shift(DELTA0_RETIRED, m),
                "min_abs_gap": _frac(min_gap),
            }
        )
    return {
        "lattices": lattices,
        "constant_shift_attainability": attainability,
        "note": (
            "a constant additive task-level shift of 1/10 is off the replicate "
            "lattice for m in {1, 2, 3}; delta0 = 1/10 is retired as an enforcing "
            "target, so this family studies lattice mechanics only"
        ),
    }


def _margin_feasibility(
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
    counts_cache: dict[tuple[int, Fraction, Fraction], dict[tuple[int, int], Fraction]],
) -> dict[str, Any]:
    """Power frontier for every construction evaluated in this tranche.

    Each non-skipped cell carries the exact rejection probability of all
    three candidate rules on the same alternative: the LFC-calibrated rule
    (``power``), the shifted sign-flip rule (``signflip_shifted_power``),
    and the normal-approximation z rule (``normal_approx_power``).  The
    latter two are not level-alpha rules on the composite-null boundary
    (see the ``null_boundary`` sizes), so their power is not a
    like-for-like comparison against the calibrated rule.  The bounded-mean
    methods (required content 7) are the only authorized deferral.  Also
    returns the independently derived falsifiable cross-check.
    """
    frontier: list[dict[str, Any]] = []
    for n in N_GRID:
        for delta0 in DELTA0_GRID:
            calibration = calibrations[(n, delta0)]
            cells: list[dict[str, Any]] = []
            for delta in FEAS_DELTA_GRID:
                for pi_d in FEAS_PID_GRID:
                    if pi_d < abs(delta):
                        cells.append(
                            {
                                "true_delta": _frac(delta),
                                "pi_d": _frac(pi_d),
                                "skipped": True,
                            }
                        )
                        continue
                    p_plus, p_minus = boundary_configuration(delta, pi_d)
                    counts = _iid_counts(n, p_plus, p_minus, counts_cache)
                    cells.append(
                        {
                            "true_delta": _frac(delta),
                            "pi_d": _frac(pi_d),
                            "skipped": False,
                            "power": _frac(
                                exact_power(n, p_plus, p_minus, calibration.critical_value)
                            ),
                            "signflip_shifted_power": _frac(
                                signflip_rejection_probability(
                                    counts, n=n, delta0=delta0, alpha=ALPHA
                                )
                            ),
                            "normal_approx_power": _frac(
                                _z_rejection_probability(
                                    counts, n=n, alpha=float(ALPHA), mu0=float(delta0)
                                )
                            ),
                        }
                    )
            frontier.append(
                {
                    "n": n,
                    "delta0": _frac(delta0),
                    "alpha": _frac(ALPHA),
                    "critical_value": calibration.critical_value,
                    "power_cells": cells,
                }
            )
    check_calibration = calibrations[(40, DELTA0_RETIRED)]
    check_p_plus, check_p_minus = boundary_configuration(Fraction(3, 10), Fraction(3, 10))
    derived_power = exact_power(
        40, check_p_plus, check_p_minus, check_calibration.critical_value
    )
    # The commission describes the comparison construction as calibrated at
    # the maximum-discordance boundary point (p_zero = 0).  Recompute that
    # calibration from this package's own committed code — never from the
    # unconsulted decision inputs — so the route comparison is traceable.
    max_discordance = lfc_calibrate(
        40, DELTA0_RETIRED, ALPHA, pi_d_grid=(Fraction(1),)
    )
    cross_check = {
        "n": 40,
        "delta0": _frac(DELTA0_RETIRED),
        "true_delta": _frac(Fraction(3, 10)),
        "pi_d": _frac(Fraction(3, 10)),
        "alpha": _frac(ALPHA),
        "critical_value": check_calibration.critical_value,
        "derived_power": _frac(derived_power),
        "comparison_value": 0.193,
        "abs_difference": abs(float(derived_power) - 0.193),
        "max_discordance_only_calibration": {
            "pi_d_grid": [_frac(Fraction(1))],
            "critical_value": max_discordance.critical_value,
            "size_at_pi_d_1": _frac(max_discordance.sup_size),
            "note": (
                "the commission-described comparison construction calibrates at "
                "the maximum-discordance boundary point; this record recomputes "
                "that calibration from this package's own committed code and "
                "asserts nothing about the contents of the unconsulted decision "
                "inputs"
            ),
        },
        "agreement_note": (
            "independently derived falsifiable cross-check; disagreement reported, "
            "never tuned"
        ),
        "citations": _citations(),
    }
    return {
        "frontier": frontier,
        "cross_check": cross_check,
        "comparator_note": (
            "each non-skipped frontier cell reports all three candidate rules "
            "evaluated in this tranche on the same alternative; the shifted "
            "sign-flip and normal-approximation rules exceed the nominal level "
            "at parts of the composite-null boundary (null_boundary family), so "
            "their power is not a like-for-like comparison among level-alpha "
            "rules; bounded-mean methods are deferred with required content 7"
        ),
    }


def _superiority_mpib(
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
) -> dict[str, Any]:
    """Superiority at zero, separately from an operator-defined MPIB rule."""
    calibration = calibrations[(40, Fraction(0))]
    c0 = calibration.critical_value
    boundary_size = [
        {"pi_d": _frac(pi_d), "size": _frac(exact_power(40, pi_d / 2, pi_d / 2, c0))}
        for pi_d in SIZE_PID_GRID
    ]
    power_cells: list[dict[str, Any]] = []
    for delta in FEAS_DELTA_GRID:
        for pi_d in FEAS_PID_GRID:
            if pi_d < abs(delta):
                power_cells.append(
                    {"true_delta": _frac(delta), "pi_d": _frac(pi_d), "skipped": True}
                )
                continue
            p_plus, p_minus = boundary_configuration(delta, pi_d)
            power_cells.append(
                {
                    "true_delta": _frac(delta),
                    "pi_d": _frac(pi_d),
                    "skipped": False,
                    "power": _frac(exact_power(40, p_plus, p_minus, c0)),
                }
            )
    joint: list[dict[str, Any]] = []
    for true_delta in MPIB_TRUE_DELTAS:
        p_plus, p_minus = boundary_configuration(true_delta, MPIB_PI_D)
        distribution = sum_distribution(40, p_plus, p_minus)
        for mpib in MPIB_GRID:
            point_threshold = math.ceil(40 * mpib)
            joint_threshold = max(c0, point_threshold)
            joint.append(
                {
                    "true_delta": _frac(true_delta),
                    "pi_d": _frac(MPIB_PI_D),
                    "mpib": _frac(mpib),
                    "point_estimate_threshold": point_threshold,
                    "joint_threshold": joint_threshold,
                    "p_joint_pass": _frac(tail_probability(distribution, joint_threshold)),
                    "p_point_estimate_only": _frac(
                        tail_probability(distribution, point_threshold)
                    ),
                }
            )
    return {
        "n": 40,
        "delta0": _frac(Fraction(0)),
        "alpha": _frac(ALPHA),
        "critical_value": c0,
        "sup_size": _frac(calibration.sup_size),
        "boundary_size": boundary_size,
        "power_cells": power_cells,
        "joint_with_mpib_rule": joint,
        "label": "MPIB value is an operator input; grid states consequences only",
        "note": (
            "joint pass requires rejecting H0: Delta <= 0 at the calibrated critical "
            "value AND a point estimate S/40 >= mpib; two candidate components are "
            "evaluated separately, neither is accepted, and no margin is folded into "
            "the confirmatory null"
        ),
    }


def _nondeterminism_floor(
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
) -> dict[str, Any]:
    """Measured-floor propagation: cells, power, and alarm thresholds."""
    c0 = calibrations[(40, Fraction(0))].critical_value
    base_p11, base_p10, base_p01, base_p00 = FLOOR_BASE_CELLS
    cells: list[dict[str, Any]] = []
    for epsilon in FLOOR_GRID:
        t11, t10, t01, t00 = floor_transformed_cells(FLOOR_BASE_CELLS, epsilon)
        p_plus, p_minus = t10, t01
        cells.append(
            {
                "epsilon": _frac(epsilon),
                # Under the stated per-arm flip channel the mean difference
                # attenuates LINEARLY: implied delta below equals
                # (1 - 2*epsilon) * (3/10) exactly (committed alongside as
                # linear_attenuated_delta).  The quadratic factor applies to
                # covariance-type quantities only and is NOT the attenuation
                # of delta.
                "linear_attenuated_delta": _frac((1 - 2 * epsilon) * Fraction(3, 10)),
                "covariance_attenuation_factor": _frac(
                    covariance_attenuation_factor(epsilon)
                ),
                "transformed_cells": {
                    "p11": _frac(t11),
                    "p10": _frac(t10),
                    "p01": _frac(t01),
                    "p00": _frac(t00),
                },
                "implied": {
                    "p_plus": _frac(p_plus),
                    "p_minus": _frac(p_minus),
                    "delta": _frac(p_plus - p_minus),
                    "pi_d": _frac(p_plus + p_minus),
                },
                "superiority_power_at_c0": _frac(exact_power(40, p_plus, p_minus, c0)),
                "repeat_disagreement_probability": _frac(
                    disagreement_probability(epsilon)
                ),
                "alarm_thresholds": [
                    {
                        "n_repeat_pairs": n_pairs,
                        "floor_derived_threshold": alarm_threshold(
                            n_pairs, epsilon, ALPHA
                        ),
                        "from_zero_threshold": alarm_threshold(
                            n_pairs, Fraction(0), ALPHA
                        ),
                    }
                    for n_pairs in REPEAT_PAIRS_GRID
                ],
            }
        )
    return {
        "base_cells": {
            "p11": _frac(base_p11),
            "p10": _frac(base_p10),
            "p01": _frac(base_p01),
            "p00": _frac(base_p00),
        },
        "base_delta": _frac(Fraction(3, 10)),
        "base_pi_d": _frac(Fraction(3, 10)),
        "critical_value_at_zero": c0,
        "alpha": _frac(ALPHA),
        "cells": cells,
        "attenuation_note": (
            "under the stated per-arm flip channel the mean difference "
            "attenuates linearly, delta' = (1 - 2*epsilon) * delta, which equals "
            "the implied delta of the transformed cells exactly; the quadratic "
            "covariance_attenuation_factor (1 - 2*epsilon)**2 applies to "
            "covariance-type quantities only and is not the attenuation of delta"
        ),
        "note": (
            "alarm thresholds are derived from the measured floor, never from zero; "
            "the from-zero column is shown only as the contrast the held R2 "
            "amendments rule out"
        ),
    }


def _cross_task_dependence(
    seed: int,
    calibrations: dict[tuple[int, Fraction], LfcCalibration],
) -> dict[str, Any]:
    """Seeded Monte Carlo size distortion under within-session correlation."""
    c0 = calibrations[(40, Fraction(0))].critical_value

    def exact_critical_rule(differences: list[int]) -> bool:
        return sum(differences) >= c0

    def normal_approx_rule(differences: list[int]) -> bool:
        return z_test_rejects(differences, alpha=0.05)

    rules = (
        ("exact_critical", exact_critical_rule),
        ("normal_approx", normal_approx_rule),
    )
    cells: list[dict[str, Any]] = []
    cell_index = 0
    for rule_name, rule in rules:
        for rho in RHO_GRID:
            for sessions, pairs_per_session in LAYOUTS:
                layout = SessionLayout(
                    sessions=sessions, pairs_per_session=pairs_per_session
                )
                cell_seed = seed * 100 + cell_index
                result = size_distortion(
                    layout,
                    rho=rho,
                    pi_d=DEP_PI_D,
                    rule=rule,
                    n_sims=N_SIMS,
                    seed=cell_seed,
                )
                record: dict[str, Any] = dataclasses.asdict(result)
                record["n_pairs"] = layout.n_pairs
                record["cell_index"] = cell_index
                record["rule"] = rule_name
                record["nominal_alpha"] = 0.05
                if (
                    rule_name == "normal_approx"
                    and rho == 0.05
                    and sessions == 1
                    and pairs_per_session == 40
                ):
                    record["independent_verification_cell"] = True
                    record["note"] = (
                        "independent synthetic verification cell; the value is "
                        "derived solely from this committed seeded code"
                    )
                cells.append(record)
                cell_index += 1
    deff_table = [
        {"pairs_per_session": m, "rho": rho, "deff": design_effect(m, rho)}
        for m in (10, 20, 40)
        for rho in RHO_GRID
    ]
    return {
        "pi_d": DEP_PI_D,
        "n_sims": N_SIMS,
        "nominal_alpha": 0.05,
        "critical_value_at_zero": c0,
        "rules": [name for name, _ in rules],
        "cell_order": (
            "cell_index enumerates the product (rule, rho, layout) with rules and "
            "grids in their pinned order; cell seed = seed * 100 + cell_index"
        ),
        "design_effect_table": deff_table,
        "cells": cells,
        "note": (
            "'exact_critical' names the critical value computed by deterministic "
            "enumeration at the Delta <= 0 boundary under cross-task independence; "
            "simulating it under within-session dependence measures how far that "
            "independence-derived size travels, and claims no validity under "
            "dependence"
        ),
    }


# --- Payload assembly ---


def compute_results(seed: int = SEED) -> dict[str, Any]:
    """Compute the full tranche payload (pure; deterministic given seed)."""
    calibrations: dict[tuple[int, Fraction], LfcCalibration] = {}
    for n in N_GRID:
        for delta0 in DELTA0_GRID:
            calibrations[(n, delta0)] = lfc_calibrate(n, delta0, ALPHA)
    counts_cache: dict[
        tuple[int, Fraction, Fraction], dict[tuple[int, int], Fraction]
    ] = {}
    return {
        "schema": "method-tranche-results/v1",
        "seed": seed,
        "generator": "analysis/run_method_tranche.py",
        "labels": {
            "design_only": True,
            "synthetic_only": True,
            "informs_never_selects": True,
            "no_claim_about_any_real_system": True,
            "delta0_0_10": "retired as enforcing target; mechanics only",
            "enumeration_is_not_exactness": True,
            "ruling_status": "R1/R2/R4 held; held means not decided",
        },
        "citations": _citations(),
        "scenarios": {
            "null_boundary": _null_boundary(calibrations, counts_cache),
            "heterogeneity": _heterogeneity(calibrations),
            "lattice": _lattice(),
            "margin_feasibility": _margin_feasibility(calibrations, counts_cache),
            "superiority_mpib": _superiority_mpib(calibrations),
            "nondeterminism_floor": _nondeterminism_floor(calibrations),
            "cross_task_dependence": _cross_task_dependence(seed, calibrations),
        },
    }


def render_results_bytes(seed: int = SEED) -> bytes:
    """Return the canonical serialized results bytes for ``seed``."""
    payload = compute_results(seed)
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def check_committed_results(seed: int = SEED) -> bool:
    """Compare canonical bytes to the committed artifact without writing it."""
    expected = render_results_bytes(seed)
    try:
        committed = RESULTS_PATH.read_bytes()
    except FileNotFoundError:
        print(f"missing committed results artifact: {RESULTS_PATH}", file=sys.stderr)
        return False
    if committed != expected:
        print(
            "committed method-tranche results differ from canonical regenerated bytes",
            file=sys.stderr,
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    """Check without writing, or explicitly regenerate the committed artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare committed and canonical bytes; never write the artifact",
    )
    args = parser.parse_args(argv)
    if args.check:
        return 0 if check_committed_results() else 1
    RESULTS_PATH.write_bytes(render_results_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
