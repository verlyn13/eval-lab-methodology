from __future__ import annotations

import unittest

from eval_lab_methodology import (
    bootstrap_ci,
    sign_test,
    superiority_by_margin,
    wilson_interval,
)


class PrimitiveParityTests(unittest.TestCase):
    def test_wilson_interval_matches_reference_outputs(self) -> None:
        self.assertEqual(wilson_interval(0, 0), (0.0, 0.0))
        self.assertEqual(
            wilson_interval(5, 10), (0.23658959361548731, 0.7634104063845126)
        )
        self.assertEqual(wilson_interval(10, 10), (0.7224598312333834, 1.0))
        self.assertEqual(wilson_interval(0, 10), (0.0, 0.2775401687666166))

    def test_sign_test_is_two_sided_and_reference_compatible(self) -> None:
        self.assertEqual(sign_test([0.5, 0.3, 0.2]), (3, 0, 0, 0.25))
        self.assertEqual(sign_test([1.0, -1.0, 0.0, 0.0]), (1, 1, 2, 1.0))
        self.assertEqual(sign_test([]), (0, 0, 0, 1.0))

    def test_seeded_percentile_bootstrap_matches_reference_outputs(self) -> None:
        self.assertEqual(bootstrap_ci([]), (None, None))
        self.assertEqual(bootstrap_ci([1.0, 1.0, 0.0, 1.0]), (0.25, 1.0))
        self.assertEqual(bootstrap_ci([1.0, 1.0, 1.0]), (1.0, 1.0))
        self.assertEqual(bootstrap_ci([-1.0, 0.0, 1.0]), (-1.0, 1.0))
        self.assertEqual(
            bootstrap_ci([1.0, 0.0, -1.0], iterations=20, seed=7, alpha=0.1),
            (-0.3333333333333333, 1.0),
        )

    def test_sign_test_is_not_the_gate(self) -> None:
        _, _, _, p_value = sign_test([0.2, 0.2])
        self.assertEqual(p_value, 0.5)

        decision = superiority_by_margin(0.2, (0.11, 0.3), margin=0.1)
        self.assertTrue(decision.promote)
        self.assertEqual(decision.rule, "bootstrap_ci_low_gt_margin")

        boundary = superiority_by_margin(0.2, (0.1, 0.3), margin=0.1)
        self.assertFalse(boundary.promote)


if __name__ == "__main__":
    unittest.main()
