"""Dependency-free primitives carried into the public core."""

from __future__ import annotations

import math
import random
import statistics

_BOOTSTRAP_ITERATIONS = 2000
_BOOTSTRAP_SEED = 12345


def wilson_interval(successes: int, n: int, *, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (no SciPy; clamped to [0, 1])."""
    if n <= 0:
        return (0.0, 0.0)
    phat = successes / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def sign_test(deltas: list[float]) -> tuple[int, int, int, float]:
    """Two-sided sign test over paired deltas: returns (wins, losses, ties, p_value)."""
    wins = sum(1 for d in deltas if d > 0)
    losses = sum(1 for d in deltas if d < 0)
    ties = sum(1 for d in deltas if d == 0)
    n = wins + losses
    if n == 0:
        return (wins, losses, ties, 1.0)
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5**n)
    return (wins, losses, ties, min(1.0, 2.0 * tail))


def bootstrap_ci(
    deltas: list[float],
    *,
    iterations: int = _BOOTSTRAP_ITERATIONS,
    seed: int = _BOOTSTRAP_SEED,
    alpha: float = 0.05,
) -> tuple[float | None, float | None]:
    """Percentile bootstrap CI for the mean paired delta (seeded => reproducible)."""
    n = len(deltas)
    if n == 0:
        return (None, None)
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(deltas[rng.randrange(n)] for _ in range(n)) for _ in range(iterations)
    )
    lo_idx = max(0, int((alpha / 2) * iterations))
    hi_idx = min(iterations - 1, int((1 - alpha / 2) * iterations))
    return (means[lo_idx], means[hi_idx])
