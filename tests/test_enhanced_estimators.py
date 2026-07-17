from __future__ import annotations

import importlib.util
import unittest

from eval_lab_methodology import (
    OptionalDependencyError,
    fit_glmm_logistic,
    power_simulation,
    two_stage_bootstrap,
    wilcoxon_signed_rank,
)


class EnhancedEstimatorTests(unittest.TestCase):
    def test_wilcoxon_all_positive_is_exact_two_sided(self) -> None:
        result = wilcoxon_signed_rank([1.0, 2.0, 3.0])
        self.assertEqual(result.label, "enhanced:wilcoxon-signed-rank")
        self.assertEqual(result.method, "exact")
        self.assertEqual(result.statistic, 0.0)
        self.assertEqual(result.p_value, 0.25)
        self.assertEqual(result.n, 3)
        self.assertEqual(result.zero_deltas, 0)

    def test_wilcoxon_drops_zeroes_and_handles_ties(self) -> None:
        result = wilcoxon_signed_rank([0.0, 1.0, 1.0, -1.0, -1.0])
        self.assertEqual(result.n, 4)
        self.assertEqual(result.zero_deltas, 1)
        self.assertEqual(result.tie_groups, 1)
        self.assertEqual(result.statistic, 5.0)
        self.assertEqual(result.p_value, 1.0)

    def test_two_stage_bootstrap_is_seeded_and_labeled(self) -> None:
        outcomes = {"task-b": [0.0, 0.0], "task-a": [1.0, 1.0]}
        first = two_stage_bootstrap(outcomes, iterations=100, seed=99)
        second = two_stage_bootstrap(outcomes, iterations=100, seed=99)
        self.assertEqual(first, second)
        self.assertEqual(first.method, "enhanced:two-stage-bootstrap")
        self.assertEqual(first.estimate, 0.5)
        self.assertLessEqual(first.ci_low, 0.5)
        self.assertGreaterEqual(first.ci_high, 0.5)
        self.assertEqual(first.tasks, 2)
        self.assertEqual(first.replicates, 4)

    def test_two_stage_bootstrap_empty_returns_empty_interval(self) -> None:
        result = two_stage_bootstrap([], iterations=10)
        self.assertIsNone(result.estimate)
        self.assertIsNone(result.ci_low)
        self.assertIsNone(result.ci_high)
        self.assertEqual(result.tasks, 0)

    def test_power_simulation_returns_planned_n(self) -> None:
        result = power_simulation(
            incumbent_rate=0.0,
            candidate_rate=1.0,
            margin=0.1,
            task_counts=(2, 4),
            replicates=1,
            target_power=1.0,
            simulations=5,
            bootstrap_iterations=10,
            seed=1,
        )
        self.assertEqual(result.method, "enhanced:power-simulation")
        self.assertEqual(result.planned_n, 2)
        self.assertEqual([point.estimated_power for point in result.grid], [1.0, 1.0])

    def test_glmm_wrapper_has_clean_optional_dependency_boundary(self) -> None:
        records = [
            {"success": 1, "model": "candidate", "task": "task-1"},
            {"success": 0, "model": "incumbent", "task": "task-1"},
        ]
        if importlib.util.find_spec("statsmodels") is None:
            with self.assertRaises(OptionalDependencyError):
                fit_glmm_logistic(records)
        else:
            self.assertRaises(ValueError, fit_glmm_logistic, [])


if __name__ == "__main__":
    unittest.main()
