"""Tests for the exact paired-binary trinomial machinery.

Every comparison is exact ``Fraction`` equality against an independent
brute-force enumeration or an inline hand computation. The tests check
*computations* (deterministic enumeration of model distributions and of the
sign-flip reference distribution); they assert nothing about the validity of
any test construction for any null hypothesis.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import itertools
import math
import unittest
from fractions import Fraction

from analysis._method_tranche.paired_trinomial import (
    boundary_configuration,
    collapse_counts_to_sum,
    counts_distribution,
    critical_value,
    exact_power,
    is_attainable_shift,
    lfc_calibrate,
    replicate_lattice,
    signflip_pvalue,
    signflip_rejection_probability,
    sum_distribution,
    tail_probability,
)

ALPHA = Fraction(1, 20)


def _outcome_probability(d: int, p_plus: Fraction, p_minus: Fraction) -> Fraction:
    if d == 1:
        return p_plus
    if d == -1:
        return p_minus
    return 1 - p_plus - p_minus


def _brute_force_sum(
    task_params: list[tuple[Fraction, Fraction]],
) -> dict[int, Fraction]:
    """Exact distribution of S by explicit 3**n outcome enumeration."""
    accumulator: dict[int, Fraction] = {}
    for combo in itertools.product((-1, 0, 1), repeat=len(task_params)):
        probability = Fraction(1)
        for (p_plus, p_minus), d in zip(task_params, combo):
            probability *= _outcome_probability(d, p_plus, p_minus)
        if probability == 0:
            continue
        s = sum(combo)
        accumulator[s] = accumulator.get(s, Fraction(0)) + probability
    return accumulator


def _brute_force_counts(
    task_params: list[tuple[Fraction, Fraction]],
) -> dict[tuple[int, int], Fraction]:
    """Exact joint (n_plus, n_minus) distribution by explicit 3**n enumeration."""
    accumulator: dict[tuple[int, int], Fraction] = {}
    for combo in itertools.product((-1, 0, 1), repeat=len(task_params)):
        probability = Fraction(1)
        for (p_plus, p_minus), d in zip(task_params, combo):
            probability *= _outcome_probability(d, p_plus, p_minus)
        if probability == 0:
            continue
        key = (combo.count(1), combo.count(-1))
        accumulator[key] = accumulator.get(key, Fraction(0)) + probability
    return accumulator


def _brute_force_signflip_pvalue(
    n_plus: int, n_zero: int, n_minus: int, delta0: Fraction
) -> Fraction:
    """Sign-flip p-value by explicit enumeration of all 2**n sign vectors."""
    values = [Fraction(1)] * n_plus + [Fraction(0)] * n_zero + [Fraction(-1)] * n_minus
    n = len(values)
    residuals = [abs(v - delta0) for v in values]
    t_obs = sum(values) - n * delta0
    favourable = 0
    for signs in itertools.product((1, -1), repeat=n):
        t_ref = sum(eps * r for eps, r in zip(signs, residuals))
        if t_ref >= t_obs:
            favourable += 1
    return Fraction(favourable, 2**n)


class SumDistributionTests(unittest.TestCase):
    def test_matches_brute_force_enumeration_up_to_n_six(self) -> None:
        p_plus, p_minus = Fraction(2, 5), Fraction(1, 5)
        for n in range(1, 7):
            expected = _brute_force_sum([(p_plus, p_minus)] * n)
            self.assertEqual(sum_distribution(n, p_plus, p_minus), expected)

    def test_matches_brute_force_with_degenerate_cells(self) -> None:
        for p_plus, p_minus in (
            (Fraction(1, 3), Fraction(0)),
            (Fraction(0), Fraction(1, 4)),
            (Fraction(1, 2), Fraction(1, 2)),
            (Fraction(0), Fraction(0)),
        ):
            expected = _brute_force_sum([(p_plus, p_minus)] * 4)
            self.assertEqual(sum_distribution(4, p_plus, p_minus), expected)

    def test_probabilities_sum_to_exactly_one(self) -> None:
        for p_plus, p_minus in (
            (Fraction(2, 5), Fraction(1, 5)),
            (Fraction(1, 2), Fraction(1, 2)),
            (Fraction(1, 7), Fraction(2, 7)),
        ):
            dist = sum_distribution(7, p_plus, p_minus)
            self.assertEqual(sum(dist.values()), Fraction(1))

    def test_zero_probability_support_points_are_omitted(self) -> None:
        no_losses = sum_distribution(5, Fraction(1, 3), Fraction(0))
        self.assertTrue(all(s >= 0 for s in no_losses))
        # With p_zero = 0 the sum keeps the parity of n: odd points are absent.
        all_discordant = sum_distribution(4, Fraction(1, 2), Fraction(1, 2))
        self.assertTrue(all(s % 2 == 0 for s in all_discordant))
        self.assertNotIn(0, sum_distribution(3, Fraction(1, 2), Fraction(1, 2)))
        self.assertNotIn(Fraction(0), all_discordant.values())

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            sum_distribution(0, Fraction(1, 4), Fraction(1, 4))
        with self.assertRaises(ValueError):
            sum_distribution(3, Fraction(-1, 4), Fraction(1, 4))
        with self.assertRaises(ValueError):
            sum_distribution(3, Fraction(3, 4), Fraction(1, 2))
        with self.assertRaises(TypeError):
            sum_distribution(3, 0.25, Fraction(1, 4))


class CountsDistributionTests(unittest.TestCase):
    HETEROGENEOUS = [
        (Fraction(1, 3), Fraction(1, 6)),
        (Fraction(1, 2), Fraction(0)),
        (Fraction(1, 10), Fraction(2, 5)),
        (Fraction(0), Fraction(1, 4)),
    ]

    def test_heterogeneous_matches_brute_force_enumeration(self) -> None:
        self.assertEqual(
            counts_distribution(self.HETEROGENEOUS),
            _brute_force_counts(self.HETEROGENEOUS),
        )

    def test_iid_matches_brute_force_enumeration(self) -> None:
        params = [(Fraction(2, 5), Fraction(1, 5))] * 5
        self.assertEqual(counts_distribution(params), _brute_force_counts(params))

    def test_probabilities_sum_to_exactly_one(self) -> None:
        self.assertEqual(
            sum(counts_distribution(self.HETEROGENEOUS).values()), Fraction(1)
        )

    def test_collapse_matches_direct_sum_distribution(self) -> None:
        p_plus, p_minus = Fraction(1, 3), Fraction(1, 6)
        counts = counts_distribution([(p_plus, p_minus)] * 6)
        self.assertEqual(
            collapse_counts_to_sum(counts), sum_distribution(6, p_plus, p_minus)
        )

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            counts_distribution([])
        with self.assertRaises(ValueError):
            counts_distribution([(Fraction(3, 4), Fraction(1, 2))])


class TailAndCriticalValueTests(unittest.TestCase):
    def test_tail_probability_hand_values(self) -> None:
        dist = sum_distribution(2, Fraction(1, 2), Fraction(1, 2))
        # Support {-2, 0, 2} with probabilities {1/4, 1/2, 1/4}.
        self.assertEqual(tail_probability(dist, -2), Fraction(1))
        self.assertEqual(tail_probability(dist, 0), Fraction(3, 4))
        self.assertEqual(tail_probability(dist, 1), Fraction(1, 4))
        self.assertEqual(tail_probability(dist, 2), Fraction(1, 4))
        self.assertEqual(tail_probability(dist, 3), Fraction(0))

    def test_tail_probability_monotone_nonincreasing_in_critical(self) -> None:
        dist = sum_distribution(9, Fraction(2, 5), Fraction(1, 5))
        for c in range(-10, 11):
            self.assertGreaterEqual(
                tail_probability(dist, c), tail_probability(dist, c + 1)
            )

    def test_critical_value_minimality(self) -> None:
        dist = sum_distribution(12, Fraction(2, 5), Fraction(1, 5))
        for alpha in (Fraction(1, 100), Fraction(1, 20), Fraction(1, 10), Fraction(1, 4)):
            c = critical_value(dist, alpha)
            self.assertLessEqual(tail_probability(dist, c), alpha)
            self.assertGreater(tail_probability(dist, c - 1), alpha)

    def test_critical_value_never_reject_when_alpha_below_max_point(self) -> None:
        dist = sum_distribution(3, Fraction(1, 2), Fraction(1, 4))
        # P(S >= 3) = 1/8 > 1/10, so only c = max(support) + 1 = 4 qualifies.
        self.assertEqual(critical_value(dist, Fraction(1, 10)), 4)
        self.assertEqual(tail_probability(dist, 4), Fraction(0))

    def test_input_validation(self) -> None:
        dist = sum_distribution(3, Fraction(1, 4), Fraction(1, 4))
        for alpha in (Fraction(0), Fraction(1), Fraction(-1, 20), Fraction(3, 2)):
            with self.assertRaises(ValueError):
                critical_value(dist, alpha)
        with self.assertRaises(ValueError):
            critical_value({}, Fraction(1, 20))


class BoundaryConfigurationTests(unittest.TestCase):
    def test_boundary_values(self) -> None:
        self.assertEqual(
            boundary_configuration(Fraction(1, 10), Fraction(3, 10)),
            (Fraction(1, 5), Fraction(1, 10)),
        )
        p_plus, p_minus = boundary_configuration(Fraction(0), Fraction(1, 2))
        self.assertEqual(p_plus, p_minus)
        self.assertEqual(p_plus + p_minus, Fraction(1, 2))
        # Maximum discordance at pi_d = 1.
        self.assertEqual(
            boundary_configuration(Fraction(1, 10), Fraction(1)),
            (Fraction(11, 20), Fraction(9, 20)),
        )

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            boundary_configuration(Fraction(1, 2), Fraction(1, 4))  # delta0 > pi_d
        with self.assertRaises(ValueError):
            boundary_configuration(Fraction(1, 10), Fraction(11, 10))  # pi_d > 1
        with self.assertRaises(ValueError):
            boundary_configuration(Fraction(-1, 10), Fraction(1, 2))  # delta0 < 0


class LfcCalibrationTests(unittest.TestCase):
    def test_sup_size_within_alpha_and_previous_candidate_violates(self) -> None:
        n, delta0 = 12, Fraction(1, 10)
        calibration = lfc_calibrate(n, delta0, ALPHA)
        self.assertLessEqual(calibration.sup_size, ALPHA)
        # Recompute the grid supremum at c - 1 independently of lfc_calibrate.
        previous_sup = max(
            tail_probability(
                sum_distribution(n, *boundary_configuration(delta0, Fraction(k, 100))),
                calibration.critical_value - 1,
            )
            for k in range(10, 101)
        )
        self.assertGreater(previous_sup, ALPHA)

    def test_critical_value_nondecreasing_as_alpha_decreases(self) -> None:
        n, delta0 = 12, Fraction(1, 10)
        criticals = [
            lfc_calibrate(n, delta0, alpha).critical_value
            for alpha in (Fraction(1, 10), Fraction(1, 20), Fraction(1, 100))
        ]
        self.assertEqual(criticals, sorted(criticals))

    def test_grid_is_reported_in_order_with_first_argmax(self) -> None:
        calibration = lfc_calibrate(12, Fraction(1, 10), ALPHA)
        grid = [pi_d for pi_d, _ in calibration.sizes_by_pi_d]
        self.assertEqual(grid, [Fraction(k, 100) for k in range(10, 101)])
        sizes = [size for _, size in calibration.sizes_by_pi_d]
        self.assertEqual(calibration.sup_size, max(sizes))
        self.assertEqual(calibration.lfc_pi_d, grid[sizes.index(max(sizes))])
        # delta0 = 0 keeps pi_d = 0 out of the default grid.
        zero = lfc_calibrate(6, Fraction(0), ALPHA)
        self.assertEqual(zero.sizes_by_pi_d[0][0], Fraction(1, 100))
        self.assertEqual(len(zero.sizes_by_pi_d), 100)

    def test_default_grid_includes_non_hundredth_delta0_exactly(self) -> None:
        delta0 = Fraction(1, 3)
        calibration = lfc_calibrate(8, delta0, ALPHA)
        grid = [pi_d for pi_d, _ in calibration.sizes_by_pi_d]
        self.assertEqual(grid[0], delta0)
        self.assertEqual(grid[1], Fraction(17, 50))
        self.assertEqual(len(grid), len(set(grid)))

    def test_derived_operating_points_at_n40(self) -> None:
        # Pinned values were derived independently from first principles; the
        # nearby published cross-check is a comparison point, never a tuning
        # target. If the implementation and these pins ever disagree, the
        # disagreement is reported — neither side is adjusted to match.
        calibration = lfc_calibrate(40, Fraction(1, 10), ALPHA)
        self.assertEqual(calibration.critical_value, 15)
        self.assertLessEqual(calibration.sup_size, ALPHA)
        self.assertAlmostEqual(float(calibration.sup_size), 0.04325358925091875, places=14)
        # The grid supremum lands adjacent to — not exactly at — maximum
        # discordance: at pi_d = 1 the support of S is even-parity only, so an
        # odd-parity boundary point just inside pi_d = 1 carries the supremum.
        # Found by the grid search, not assumed.
        self.assertEqual(calibration.lfc_pi_d, Fraction(97, 100))
        superiority = lfc_calibrate(40, Fraction(0), ALPHA)
        self.assertEqual(superiority.critical_value, 11)
        self.assertAlmostEqual(float(superiority.sup_size), 0.045117717694842636, places=14)

    def test_delta0_zero_matches_hand_computed_binomial_critical_at_pi_d_one(self) -> None:
        # At delta0 = 0 and pi_d = 1 every task is discordant, so
        # S = 2X - n with X ~ Binomial(n, 1/2): the calibrated critical value
        # must equal the binomial sign-test critical computed by hand.
        for n in (10, 15, 40):
            expected = None
            for c in range(-n, n + 2):
                k_min = max(0, -((c + n) // -2))  # ceil((c + n) / 2), integer-exact
                tail = Fraction(
                    sum(math.comb(n, x) for x in range(k_min, n + 1)), 2**n
                )
                if tail <= ALPHA:
                    expected = c
                    break
            calibration = lfc_calibrate(n, Fraction(0), ALPHA, pi_d_grid=(Fraction(1),))
            self.assertEqual(calibration.critical_value, expected)

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            lfc_calibrate(0, Fraction(1, 10), ALPHA)
        with self.assertRaises(ValueError):
            lfc_calibrate(10, Fraction(1, 10), Fraction(0))
        with self.assertRaises(ValueError):
            lfc_calibrate(10, Fraction(-1, 10), ALPHA)
        with self.assertRaises(ValueError):
            lfc_calibrate(10, Fraction(1, 10), ALPHA, pi_d_grid=())
        with self.assertRaises(ValueError):
            # Grid point below delta0 is not a boundary configuration.
            lfc_calibrate(10, Fraction(1, 10), ALPHA, pi_d_grid=(Fraction(1, 20),))


class ExactPowerTests(unittest.TestCase):
    def test_composes_sum_distribution_and_tail(self) -> None:
        p_plus, p_minus = Fraction(3, 10), Fraction(1, 10)
        self.assertEqual(
            exact_power(8, p_plus, p_minus, 3),
            tail_probability(sum_distribution(8, p_plus, p_minus), 3),
        )

    def test_derived_cross_check_power_at_n40(self) -> None:
        # Independently derived rejection probability at true Delta = 3/10,
        # pi_d = 3/10, N = 40, using the calibrated c = 15 from the composite
        # null H0: Delta <= 1/10. The published value 0.193 is a falsifiable
        # cross-check for comparison, never a target to tune toward.
        power = exact_power(40, Fraction(3, 10), Fraction(0), 15)
        self.assertAlmostEqual(float(power), 0.19255175473517602, places=14)
        # Deliberately NOT asserted here: agreement or disagreement with the
        # cited 0.193 cross-check value. That comparison is recorded in the
        # committed artifact and the method note as a reported (dis)agreement;
        # the test suite must never enforce it, or a future correction that
        # produced a disagreeing value would be forced to match instead of
        # being reported.


def _params_for_delta(delta: Fraction, pi_d: Fraction) -> tuple[Fraction, Fraction]:
    """(p_plus, p_minus) with mean difference ``delta`` (any sign) and discordance ``pi_d``."""
    if delta >= 0:
        return boundary_configuration(delta, pi_d)
    mirrored_plus, mirrored_minus = boundary_configuration(-delta, pi_d)
    return (mirrored_minus, mirrored_plus)


class TailMonotonicityInDeltaTests(unittest.TestCase):
    """P(S >= c) is nondecreasing in Delta at fixed pi_d (exact check).

    Derivation (direct coupling): fix pi_d and increase Delta; the cell
    probabilities move mass from the -1 cell to the +1 cell with the 0 cell
    unchanged, so with a common uniform draw per task the difference under the
    larger Delta is pointwise >= the difference under the smaller Delta, and
    S is pointwise >=, hence every upper tail is nondecreasing in Delta.
    Consequence: the boundary size bound at a calibration grid point
    (delta0, pi_d) extends to every interior null point Delta <= delta0 on
    that grid line; the remaining calibration caveat is grid adequacy in pi_d
    only. These are exact computations under the stated trinomial model, not
    validity claims for any composite null beyond that model.
    """

    def test_tail_nondecreasing_in_delta_at_fixed_pi_d(self) -> None:
        for n in (6, 12):
            for pi_d in (Fraction(3, 10), Fraction(1, 2), Fraction(1)):
                deltas = [
                    Fraction(k, 10)
                    for k in range(-10, 11)
                    if abs(Fraction(k, 10)) <= pi_d
                ]
                dists = [
                    sum_distribution(n, *_params_for_delta(delta, pi_d))
                    for delta in deltas
                ]
                for c in range(-n, n + 2):
                    tails = [tail_probability(dist, c) for dist in dists]
                    self.assertEqual(
                        tails,
                        sorted(tails),
                        msg=f"n={n} pi_d={pi_d} c={c}",
                    )

    def test_interior_null_size_bounded_by_boundary_size_at_calibrated_c(self) -> None:
        # The consequence used by the LFC calibration: at the calibrated c,
        # every interior null point on a grid line rejects no more often than
        # the boundary point on that line (and hence no more often than the
        # grid supremum, which is <= alpha).
        for delta0 in (Fraction(0), Fraction(1, 10)):
            calibration = lfc_calibrate(12, delta0, ALPHA)
            for pi_d, boundary_size in calibration.sizes_by_pi_d[::10]:
                for delta in (delta0 - Fraction(1, 20), Fraction(0), -pi_d):
                    if abs(delta) > pi_d:
                        continue
                    interior_size = exact_power(
                        12,
                        *_params_for_delta(delta, pi_d),
                        calibration.critical_value,
                    )
                    self.assertLessEqual(interior_size, boundary_size)
                    self.assertLessEqual(interior_size, calibration.sup_size)


class SignFlipTests(unittest.TestCase):
    def test_pvalue_matches_explicit_flip_enumeration(self) -> None:
        configurations = ((3, 2, 1), (2, 2, 2), (0, 3, 1), (4, 0, 0), (1, 1, 3))
        for n_plus, n_zero, n_minus in configurations:
            for delta0 in (Fraction(0), Fraction(1, 10), Fraction(1, 2)):
                self.assertEqual(
                    signflip_pvalue(n_plus, n_zero, n_minus, delta0),
                    _brute_force_signflip_pvalue(n_plus, n_zero, n_minus, delta0),
                    msg=f"config={(n_plus, n_zero, n_minus)} delta0={delta0}",
                )

    def test_pvalue_at_delta0_zero_reduces_to_binomial_tail(self) -> None:
        # With delta0 = 0 the zero-difference residuals vanish and the
        # reference statistic is a sum of n_plus + n_minus independent signs:
        # the p-value is the binomial sign-test tail, computed here by hand.
        n_plus, n_zero, n_minus = 7, 3, 2
        m = n_plus + n_minus
        expected = Fraction(sum(math.comb(m, k) for k in range(n_plus, m + 1)), 2**m)
        self.assertEqual(signflip_pvalue(n_plus, n_zero, n_minus, Fraction(0)), expected)

    def test_rejection_probability_matches_full_outcome_enumeration(self) -> None:
        # Every task has positive discordance probability, so the task count
        # is recoverable from the counts-distribution support.
        params = [
            (Fraction(1, 3), Fraction(1, 6)),
            (Fraction(2, 5), Fraction(1, 5)),
            (Fraction(1, 4), Fraction(1, 4)),
            (Fraction(1, 2), Fraction(1, 10)),
        ]
        counts = counts_distribution(params)
        for delta0 in (Fraction(0), Fraction(1, 10)):
            for alpha in (Fraction(1, 16), Fraction(1, 4)):
                expected = Fraction(0)
                for combo in itertools.product((-1, 0, 1), repeat=len(params)):
                    probability = Fraction(1)
                    for (p_plus, p_minus), d in zip(params, combo):
                        probability *= _outcome_probability(d, p_plus, p_minus)
                    if probability == 0:
                        continue
                    pvalue = _brute_force_signflip_pvalue(
                        combo.count(1), combo.count(0), combo.count(-1), delta0
                    )
                    if pvalue <= alpha:
                        expected += probability
                self.assertEqual(
                    signflip_rejection_probability(
                        counts, n=len(params), delta0=delta0, alpha=alpha
                    ),
                    expected,
                    msg=f"delta0={delta0} alpha={alpha}",
                )

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            signflip_pvalue(-1, 0, 1, Fraction(0))
        with self.assertRaises(ValueError):
            signflip_pvalue(0, 0, 0, Fraction(0))
        with self.assertRaises(ValueError):
            signflip_pvalue(1, 1, 1, Fraction(11, 10))
        with self.assertRaises(TypeError):
            signflip_pvalue(1, 1, 1, 0.1)
        with self.assertRaises(ValueError):
            signflip_rejection_probability(
                {}, n=1, delta0=Fraction(0), alpha=ALPHA
            )
        with self.assertRaises(ValueError):
            signflip_rejection_probability(
                {(0, 0): Fraction(1)}, n=0, delta0=Fraction(0), alpha=ALPHA
            )
        with self.assertRaises(ValueError):
            signflip_rejection_probability(
                {(1, 0): Fraction(1)},
                n=1,
                delta0=Fraction(0),
                alpha=Fraction(1),
            )
        with self.assertRaisesRegex(ValueError, "explicit task count"):
            signflip_rejection_probability(
                {(2, 0): Fraction(1)}, n=1, delta0=Fraction(0), alpha=ALPHA
            )

    def test_explicit_task_count_handles_all_concordant_support(self) -> None:
        self.assertEqual(
            signflip_rejection_probability(
                {(0, 0): Fraction(1)},
                n=4,
                delta0=Fraction(0),
                alpha=ALPHA,
            ),
            Fraction(0),
        )


class ReplicateLatticeTests(unittest.TestCase):
    def test_lattice_values(self) -> None:
        self.assertEqual(replicate_lattice(1), (Fraction(-1), Fraction(0), Fraction(1)))
        self.assertEqual(
            replicate_lattice(2),
            (
                Fraction(-1),
                Fraction(-1, 2),
                Fraction(0),
                Fraction(1, 2),
                Fraction(1),
            ),
        )
        self.assertEqual(
            replicate_lattice(3),
            (
                Fraction(-1),
                Fraction(-2, 3),
                Fraction(-1, 3),
                Fraction(0),
                Fraction(1, 3),
                Fraction(2, 3),
                Fraction(1),
            ),
        )

    def test_constant_one_tenth_shift_is_off_small_replicate_lattices(self) -> None:
        # Demonstrates the lattice mechanics only: with 1-3 replicates a
        # constant per-task shift of 1/10 is not an attainable lattice point.
        # This says nothing for or against any margin choice.
        for m in (1, 2, 3):
            self.assertFalse(is_attainable_shift(Fraction(1, 10), m))
            self.assertNotIn(Fraction(1, 10), replicate_lattice(m))
        self.assertTrue(is_attainable_shift(Fraction(1, 10), 10))

    def test_attainable_shift_edges(self) -> None:
        self.assertTrue(is_attainable_shift(Fraction(1, 2), 2))
        self.assertTrue(is_attainable_shift(Fraction(-2, 3), 3))
        self.assertTrue(is_attainable_shift(Fraction(1), 1))
        self.assertFalse(is_attainable_shift(Fraction(3, 2), 2))  # outside [-1, 1]
        self.assertFalse(is_attainable_shift(Fraction(1, 3), 2))

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            replicate_lattice(0)
        with self.assertRaises(ValueError):
            is_attainable_shift(Fraction(1, 2), 0)


if __name__ == "__main__":
    unittest.main()
