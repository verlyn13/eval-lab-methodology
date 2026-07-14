"""Tests for the dependence / design-effect and nondeterminism-floor machinery.

All fixtures are synthetic and seeded. Where a Monte Carlo estimate is checked
against an exact reference, the reference is computed inline in this file with
``math.comb`` and ``fractions.Fraction`` (no import from any other statistics
module in this package). Exactness assertions below concern computation only;
none of them assert inferential validity of any rejection rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import math
import random
import unittest
from fractions import Fraction

from analysis._method_tranche.dependence import (
    SessionLayout,
    alarm_threshold,
    covariance_attenuation_factor,
    design_effect,
    disagreement_probability,
    floor_transformed_cells,
    session_mixture_weight,
    simulate_session_differences,
    size_distortion,
    z_test_rejects,
)


def _exact_boundary_sum_tail(n: int, pi_d: Fraction, critical: int) -> Fraction:
    """Inline exact P(sum of n i.i.d. Delta=0 boundary differences >= critical).

    Each difference is +1 with probability pi_d/2, -1 with probability pi_d/2,
    and 0 otherwise. Computed here with math.comb and Fraction only, as an
    independent reference for the rho=0 Monte Carlo check.
    """
    p_sign = pi_d / 2
    p_zero = 1 - pi_d
    total = Fraction(0)
    for n_plus in range(n + 1):
        for n_minus in range(n + 1 - n_plus):
            if n_plus - n_minus >= critical:
                n_zeros = n - n_plus - n_minus
                ways = math.comb(n, n_plus) * math.comb(n - n_plus, n_minus)
                total += ways * p_sign ** (n_plus + n_minus) * p_zero**n_zeros
    return total


def _exact_binomial_tail(n: int, q: Fraction, k: int) -> Fraction:
    """Inline exact P(Binomial(n, q) >= k) with math.comb and Fraction only."""
    total = Fraction(0)
    for j in range(k, n + 1):
        total += math.comb(n, j) * q**j * (1 - q) ** (n - j)
    return total


class SessionLayoutTests(unittest.TestCase):
    def test_n_pairs_is_product_of_sessions_and_pairs(self) -> None:
        self.assertEqual(SessionLayout(sessions=1, pairs_per_session=40).n_pairs, 40)
        self.assertEqual(SessionLayout(sessions=4, pairs_per_session=10).n_pairs, 40)

    def test_invalid_layouts_raise(self) -> None:
        with self.assertRaises(ValueError):
            SessionLayout(sessions=0, pairs_per_session=10)
        with self.assertRaises(ValueError):
            SessionLayout(sessions=2, pairs_per_session=0)


class DesignEffectTests(unittest.TestCase):
    def test_exact_values(self) -> None:
        self.assertEqual(design_effect(40, 0.05), 2.95)
        self.assertEqual(design_effect(40, 0.05), 1 + (40 - 1) * 0.05)
        self.assertEqual(design_effect(1, 0.9), 1.0)
        self.assertEqual(design_effect(10, 0.0), 1.0)
        self.assertEqual(design_effect(20, 1.0), 20.0)
        for m in (1, 10, 20, 40):
            for rho in (0.0, 0.01, 0.02, 0.05, 0.10, 1.0):
                self.assertEqual(design_effect(m, rho), 1 + (m - 1) * rho)

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            design_effect(0, 0.05)
        with self.assertRaises(ValueError):
            design_effect(10, -0.01)
        with self.assertRaises(ValueError):
            design_effect(10, 1.01)


class SessionMixtureWeightTests(unittest.TestCase):
    def test_weight_satisfies_target_correlation_identity(self) -> None:
        for rho in (0.01, 0.02, 0.05, 0.10, 0.5, 0.9):
            for pi_d in (0.05, 0.3, 0.5, 1.0):
                lam = session_mixture_weight(rho, pi_d)
                self.assertGreater(lam, 0.0)
                self.assertLess(lam, 1.0)
                implied_rho = lam * lam / (lam + (1.0 - lam) * pi_d)
                self.assertLessEqual(abs(implied_rho - rho), 1e-12)

    def test_zero_correlation_gives_zero_weight(self) -> None:
        self.assertEqual(session_mixture_weight(0.0, 0.3), 0.0)

    def test_infeasible_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            session_mixture_weight(1.0, 0.3)
        with self.assertRaises(ValueError):
            session_mixture_weight(-0.01, 0.3)
        with self.assertRaises(ValueError):
            session_mixture_weight(0.05, 0.0)
        with self.assertRaises(ValueError):
            session_mixture_weight(0.05, 1.5)


class SimulateSessionDifferencesTests(unittest.TestCase):
    def test_same_seed_gives_identical_draws(self) -> None:
        layout = SessionLayout(sessions=4, pairs_per_session=10)
        first = simulate_session_differences(
            layout, rho=0.05, pi_d=0.3, rng=random.Random(20260713)
        )
        second = simulate_session_differences(
            layout, rho=0.05, pi_d=0.3, rng=random.Random(20260713)
        )
        self.assertEqual(first, second)

    def test_values_and_length(self) -> None:
        for sessions, pairs in ((1, 40), (2, 20), (4, 10)):
            layout = SessionLayout(sessions=sessions, pairs_per_session=pairs)
            draws = simulate_session_differences(
                layout, rho=0.10, pi_d=0.3, rng=random.Random(7)
            )
            self.assertEqual(len(draws), layout.n_pairs)
            self.assertTrue(set(draws) <= {-1, 0, 1})


class SizeDistortionTests(unittest.TestCase):
    def test_same_seed_gives_identical_result(self) -> None:
        layout = SessionLayout(sessions=2, pairs_per_session=20)
        kwargs = dict(rho=0.05, pi_d=0.3, rule=lambda d: sum(d) >= 6, n_sims=500, seed=11)
        self.assertEqual(size_distortion(layout, **kwargs), size_distortion(layout, **kwargs))

    def test_result_fields_are_consistent(self) -> None:
        layout = SessionLayout(sessions=2, pairs_per_session=20)
        result = size_distortion(
            layout, rho=0.05, pi_d=0.3, rule=lambda d: sum(d) >= 6, n_sims=500, seed=11
        )
        self.assertEqual(result.sessions, 2)
        self.assertEqual(result.pairs_per_session, 20)
        self.assertEqual(result.n_sims, 500)
        self.assertEqual(result.seed, 11)
        self.assertEqual(result.rejection_rate, result.rejections / 500)
        self.assertEqual(
            result.mc_standard_error,
            math.sqrt(result.rejection_rate * (1.0 - result.rejection_rate) / 500),
        )
        self.assertEqual(result.deff, design_effect(20, 0.05))

    def test_independent_case_agrees_with_inline_exact_tail(self) -> None:
        # At rho=0 the draws are i.i.d. boundary trinomials, so the Monte Carlo
        # rejection rate of the rule sum(d) >= k must sit within 3 Monte Carlo
        # standard errors of the exact tail computed inline in this file.
        layout = SessionLayout(sessions=2, pairs_per_session=10)
        critical = 4
        n_sims = 4000
        result = size_distortion(
            layout,
            rho=0.0,
            pi_d=0.3,
            rule=lambda d: sum(d) >= critical,
            n_sims=n_sims,
            seed=20260713,
        )
        exact = _exact_boundary_sum_tail(layout.n_pairs, Fraction(3, 10), critical)
        exact_float = float(exact)
        tolerance = 3.0 * math.sqrt(exact_float * (1.0 - exact_float) / n_sims)
        self.assertLessEqual(abs(result.rejection_rate - exact_float), tolerance)
        self.assertEqual(result.deff, 1.0)

    def test_invalid_n_sims_raises(self) -> None:
        layout = SessionLayout(sessions=1, pairs_per_session=10)
        with self.assertRaises(ValueError):
            size_distortion(
                layout, rho=0.0, pi_d=0.3, rule=lambda d: True, n_sims=0, seed=1
            )


class ZTestRejectsTests(unittest.TestCase):
    def test_degenerate_sd_branch_compares_mean_to_mu0(self) -> None:
        self.assertTrue(z_test_rejects([1, 1, 1, 1], alpha=0.05))
        self.assertFalse(z_test_rejects([0, 0, 0], alpha=0.05))
        self.assertFalse(z_test_rejects([1, 1, 1, 1], alpha=0.05, mu0=1.0))

    def test_hand_computed_z_statistic_cases(self) -> None:
        # differences [1, 1, 1, 0]: mean 0.75, sample sd 0.5, z = 3.0 exactly.
        self.assertTrue(z_test_rejects([1, 1, 1, 0], alpha=0.05))
        # inv_cdf(0.999) ~ 3.0902 > 3.0, so the same data fail at alpha=0.001.
        self.assertFalse(z_test_rejects([1, 1, 1, 0], alpha=0.001))
        # mean equal to mu0 gives z = 0: no rejection.
        self.assertFalse(z_test_rejects([1, -1, 0, 0], alpha=0.05))
        self.assertFalse(z_test_rejects([1, 1, 1, 0], alpha=0.05, mu0=0.75))

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            z_test_rejects([1], alpha=0.05)
        with self.assertRaises(ValueError):
            z_test_rejects([1, 0], alpha=0.0)
        with self.assertRaises(ValueError):
            z_test_rejects([1, 0], alpha=1.0)


class FloorPropagationTests(unittest.TestCase):
    BASE_CELLS = (Fraction(2, 5), Fraction(3, 10), Fraction(0), Fraction(3, 10))

    def test_covariance_attenuation_factor_closed_form(self) -> None:
        # The quadratic factor applies to covariance-type quantities only; the
        # mean difference Delta attenuates linearly under the flip channel
        # (test_channel_shrinks_the_cell_difference_linearly below).
        self.assertEqual(covariance_attenuation_factor(Fraction(0)), Fraction(1))
        self.assertEqual(
            covariance_attenuation_factor(Fraction(1, 100)), Fraction(2401, 2500)
        )
        for eps in (Fraction(1, 100), Fraction(1, 50), Fraction(1, 20)):
            self.assertEqual(covariance_attenuation_factor(eps), (1 - 2 * eps) ** 2)
        with self.assertRaises(ValueError):
            covariance_attenuation_factor(Fraction(1, 2))
        with self.assertRaises(ValueError):
            covariance_attenuation_factor(Fraction(-1, 100))

    def test_transformed_cells_stay_an_exact_simplex(self) -> None:
        for eps in (Fraction(0), Fraction(1, 100), Fraction(1, 50), Fraction(1, 20)):
            cells = floor_transformed_cells(self.BASE_CELLS, eps)
            self.assertEqual(len(cells), 4)
            for cell in cells:
                self.assertIsInstance(cell, Fraction)
                self.assertGreaterEqual(cell, 0)
            self.assertEqual(sum(cells), Fraction(1))

    def test_zero_floor_is_the_identity_transform(self) -> None:
        self.assertEqual(floor_transformed_cells(self.BASE_CELLS, Fraction(0)), self.BASE_CELLS)

    def test_hand_computed_cell_at_one_twentieth(self) -> None:
        # p11' = (19/20)^2 * 2/5 + (19/20)(1/20) * 3/10 + (1/20)^2 * 3/10 = 47/125.
        cells = floor_transformed_cells(self.BASE_CELLS, Fraction(1, 20))
        self.assertEqual(cells[0], Fraction(47, 125))

    def test_channel_shrinks_the_cell_difference_linearly(self) -> None:
        # The attenuation of the mean difference under the per-arm flip
        # channel: the transformed p10' - p01' equals exactly
        # (1 - 2*eps) * (p10 - p01) — Delta attenuates LINEARLY. The quadratic
        # covariance_attenuation_factor applies to covariance-type quantities
        # only; both are computed model quantities, not validity claims.
        for eps in (Fraction(1, 100), Fraction(1, 50), Fraction(1, 20)):
            cells = floor_transformed_cells(self.BASE_CELLS, eps)
            expected = (1 - 2 * eps) * (self.BASE_CELLS[1] - self.BASE_CELLS[2])
            self.assertEqual(cells[1] - cells[2], expected)

    def test_invalid_cells_raise(self) -> None:
        with self.assertRaises(ValueError):
            floor_transformed_cells(
                (Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(-1, 2)),
                Fraction(1, 100),
            )
        with self.assertRaises(ValueError):
            floor_transformed_cells(
                (Fraction(1, 2), Fraction(1, 4), Fraction(1, 8), Fraction(1, 16)),
                Fraction(1, 100),
            )

    def test_disagreement_probability_values(self) -> None:
        self.assertEqual(disagreement_probability(Fraction(0)), Fraction(0))
        self.assertEqual(disagreement_probability(Fraction(1, 100)), Fraction(99, 5000))
        self.assertEqual(disagreement_probability(Fraction(1, 20)), Fraction(19, 200))


class AlarmThresholdTests(unittest.TestCase):
    def test_zero_floor_alarms_on_any_disagreement(self) -> None:
        for n in (40, 80, 120):
            self.assertEqual(alarm_threshold(n, Fraction(0), Fraction(1, 20)), 1)

    def test_threshold_is_monotone_in_the_floor(self) -> None:
        thresholds = [
            alarm_threshold(80, eps, Fraction(1, 20))
            for eps in (Fraction(0), Fraction(1, 100), Fraction(1, 50), Fraction(1, 20))
        ]
        self.assertEqual(sorted(thresholds), thresholds)
        # A material floor moves the threshold strictly above the from-zero policy.
        self.assertGreater(thresholds[-1], 1)

    def test_threshold_is_the_minimal_level_alpha_count(self) -> None:
        alpha = Fraction(1, 20)
        for n in (40, 80, 120):
            for eps in (Fraction(1, 100), Fraction(1, 50), Fraction(1, 20)):
                k = alarm_threshold(n, eps, alpha)
                q = disagreement_probability(eps)
                self.assertLessEqual(_exact_binomial_tail(n, q, k), alpha)
                self.assertGreater(k, 0)
                self.assertGreater(_exact_binomial_tail(n, q, k - 1), alpha)

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            alarm_threshold(0, Fraction(1, 100), Fraction(1, 20))
        with self.assertRaises(ValueError):
            alarm_threshold(40, Fraction(1, 2), Fraction(1, 20))
        with self.assertRaises(ValueError):
            alarm_threshold(40, Fraction(1, 100), Fraction(0))
        with self.assertRaises(ValueError):
            alarm_threshold(40, Fraction(1, 100), Fraction(1))


if __name__ == "__main__":
    unittest.main()
