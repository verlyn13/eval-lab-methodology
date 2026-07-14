"""Experimental paired-binary trinomial machinery for design-only analysis.

Everything in this module is a *computation*: an integer dynamic program (DP)
that deterministically enumerates a finite discrete distribution with exact
``fractions.Fraction`` probabilities, or an exact tail/critical-value lookup
over such an enumerated distribution. Deterministic enumeration is a statement
about how numbers are computed. It is not a statement about inference: whether
a test built from an enumerated reference distribution controls Type I error
depends on explicitly stated sampling assumptions, which are documented and
assessed where each test is constructed — never conferred by the enumeration
itself. In particular, nothing here claims finite-sample validity for the weak
composite average-effect null; that question is treated separately in the
accompanying method-note tranche.

Model conventions (shared across the tranche):

- A per-task paired difference ``d_i`` takes values in ``{-1, 0, +1}`` with
  ``P(d_i = +1) = p_plus``, ``P(d_i = -1) = p_minus``, and
  ``P(d_i = 0) = 1 - p_plus - p_minus``.
- ``Delta = p_plus - p_minus`` (mean difference) and
  ``pi_d = p_plus + p_minus`` (discordance probability).
- The suite statistic is ``S = sum_i d_i = n_plus - n_minus``.

Design-only, synthetic-only: this module neither reads nor produces
measurements of any real system. Exact inputs are ``Fraction``/``int`` end to
end; ``float`` inputs are rejected so exact arithmetic stays exact.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

__all__ = [
    "LfcCalibration",
    "boundary_configuration",
    "collapse_counts_to_sum",
    "counts_distribution",
    "critical_value",
    "exact_power",
    "is_attainable_shift",
    "lfc_calibrate",
    "replicate_lattice",
    "signflip_pvalue",
    "signflip_rejection_probability",
    "sum_distribution",
    "tail_probability",
]


def _exact(value: Fraction | int, name: str) -> Fraction:
    """Coerce ``value`` to ``Fraction``, rejecting floats to preserve exactness."""
    if isinstance(value, float):
        raise TypeError(f"{name} must be an exact rational (Fraction or int), not float")
    return Fraction(value)


def _cell_weights(p_plus: Fraction, p_minus: Fraction) -> tuple[int, int, int, int]:
    """Validate one task's cell probabilities; return integer weights over a common base.

    Returns ``(w_plus, w_minus, w_zero, q)`` with ``w_plus + w_minus + w_zero == q`` and
    ``p_plus == w_plus / q`` etc., so the DP can run in pure integer arithmetic.
    """
    if p_plus < 0 or p_minus < 0:
        raise ValueError("p_plus and p_minus must be nonnegative")
    if p_plus + p_minus > 1:
        raise ValueError("p_plus + p_minus must not exceed 1")
    q = math.lcm(p_plus.denominator, p_minus.denominator)
    w_plus = p_plus.numerator * (q // p_plus.denominator)
    w_minus = p_minus.numerator * (q // p_minus.denominator)
    return w_plus, w_minus, q - w_plus - w_minus, q


def sum_distribution(n: int, p_plus: Fraction, p_minus: Fraction) -> dict[int, Fraction]:
    """Deterministically enumerate the exact distribution of ``S = sum_i d_i``.

    Integer-DP convolution of ``n`` i.i.d. trinomial tasks: per-step
    probabilities become integer weights over a common denominator ``q``; the
    DP convolves in integer arithmetic; the result is reduced to ``Fraction``
    probabilities over ``q**n``. Zero-probability support points are omitted,
    and the returned probabilities sum to exactly ``Fraction(1)``.

    This enumerates a model distribution; it asserts nothing about the
    validity of any test that uses it.

    Raises ``ValueError`` unless ``n >= 1``, ``p_plus >= 0``, ``p_minus >= 0``,
    and ``p_plus + p_minus <= 1``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    p_plus = _exact(p_plus, "p_plus")
    p_minus = _exact(p_minus, "p_minus")
    w_plus, w_minus, w_zero, q = _cell_weights(p_plus, p_minus)
    steps = tuple(
        (offset, weight)
        for offset, weight in ((1, w_plus), (-1, w_minus), (0, w_zero))
        if weight
    )
    dp: dict[int, int] = {0: 1}
    for _ in range(n):
        nxt: dict[int, int] = {}
        for s, w in dp.items():
            for offset, weight in steps:
                key = s + offset
                nxt[key] = nxt.get(key, 0) + w * weight
        dp = nxt
    denominator = q**n
    return {s: Fraction(w, denominator) for s, w in sorted(dp.items())}


def counts_distribution(
    task_params: Sequence[tuple[Fraction, Fraction]],
) -> dict[tuple[int, int], Fraction]:
    """Deterministically enumerate the exact joint distribution of ``(n_plus, n_minus)``.

    Tasks are independent and may be non-identical: ``task_params[i]`` is task
    ``i``'s ``(p_plus_i, p_minus_i)``. The DP walks the tasks with state
    ``(n_plus, n_minus)`` in integer arithmetic over the product of per-task
    denominators. The i.i.d. case is obtained by passing ``n`` copies of one
    parameter pair. This is the tranche's single heterogeneity primitive.

    Zero-probability support points are omitted; probabilities sum to exactly
    ``Fraction(1)``. Enumeration of the model distribution only — no validity
    claim for any test built on it.

    Raises ``ValueError`` if ``task_params`` is empty or any pair violates
    ``p_plus >= 0``, ``p_minus >= 0``, ``p_plus + p_minus <= 1``.
    """
    params = list(task_params)
    if not params:
        raise ValueError("task_params must contain at least one task")
    dp: dict[tuple[int, int], int] = {(0, 0): 1}
    denominator = 1
    for raw_plus, raw_minus in params:
        p_plus = _exact(raw_plus, "p_plus")
        p_minus = _exact(raw_minus, "p_minus")
        w_plus, w_minus, w_zero, q = _cell_weights(p_plus, p_minus)
        nxt: dict[tuple[int, int], int] = {}
        for (n_plus, n_minus), w in dp.items():
            if w_plus:
                key = (n_plus + 1, n_minus)
                nxt[key] = nxt.get(key, 0) + w * w_plus
            if w_minus:
                key = (n_plus, n_minus + 1)
                nxt[key] = nxt.get(key, 0) + w * w_minus
            if w_zero:
                key = (n_plus, n_minus)
                nxt[key] = nxt.get(key, 0) + w * w_zero
        dp = nxt
        denominator *= q
    return {key: Fraction(w, denominator) for key, w in sorted(dp.items())}


def collapse_counts_to_sum(
    counts: Mapping[tuple[int, int], Fraction],
) -> dict[int, Fraction]:
    """Collapse a ``(n_plus, n_minus)`` counts distribution to the distribution of ``S``.

    ``S = n_plus - n_minus``; probabilities are added exactly and
    zero-probability points are omitted.
    """
    accumulator: dict[int, Fraction] = {}
    for (n_plus, n_minus), probability in counts.items():
        s = n_plus - n_minus
        accumulator[s] = accumulator.get(s, Fraction(0)) + probability
    return {s: p for s, p in sorted(accumulator.items()) if p != 0}


def tail_probability(dist: Mapping[int, Fraction], critical: int) -> Fraction:
    """Exact upper-tail probability ``P(S >= critical)`` of an enumerated distribution.

    "Exact" refers to the arithmetic over the supplied model distribution, not
    to any property of a test that compares a statistic against ``critical``.
    """
    total = Fraction(0)
    for s, probability in dist.items():
        if s >= critical:
            total += probability
    return total


def critical_value(dist: Mapping[int, Fraction], alpha: Fraction) -> int:
    """Smallest integer ``c`` with ``tail_probability(dist, c) <= alpha``.

    Searched over ``[min(support), max(support) + 1]``; ``max(support) + 1``
    (a rule that never rejects) always satisfies the constraint, so a value is
    always returned. Requires ``0 < alpha < 1``. A computation over the
    supplied distribution only: whether the resulting rule controls Type I
    error for any hypothesis depends on whether ``dist`` is a defensible null
    distribution under stated assumptions.
    """
    alpha = _exact(alpha, "alpha")
    if not 0 < alpha < 1:
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    if not dist:
        raise ValueError("dist must be non-empty")
    support = sorted(dist)
    suffix = [Fraction(0)] * (len(support) + 1)
    for i in range(len(support) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + dist[support[i]]
    for c in range(support[0], support[-1] + 2):
        if suffix[bisect_left(support, c)] <= alpha:
            return c
    raise AssertionError("unreachable: the tail at max(support) + 1 is exactly zero")


def boundary_configuration(delta0: Fraction, pi_d: Fraction) -> tuple[Fraction, Fraction]:
    """Composite-null boundary point with mean difference ``delta0`` and discordance ``pi_d``.

    Returns ``(p_plus, p_minus) = ((pi_d + delta0) / 2, (pi_d - delta0) / 2)``,
    the unique trinomial cell configuration with ``Delta = delta0`` and
    ``pi_d`` total discordance. Requires ``0 <= delta0 <= pi_d <= 1``.
    """
    delta0 = _exact(delta0, "delta0")
    pi_d = _exact(pi_d, "pi_d")
    if not 0 <= delta0 <= pi_d <= 1:
        raise ValueError("required: 0 <= delta0 <= pi_d <= 1")
    return ((pi_d + delta0) / 2, (pi_d - delta0) / 2)


@dataclass(frozen=True)
class LfcCalibration:
    """Result of calibrating ``S >= c`` over the composite-null boundary by grid supremum.

    ``sizes_by_pi_d`` holds ``(pi_d, size at critical_value)`` pairs in grid
    order; ``sup_size`` is their maximum and ``lfc_pi_d`` the first grid point
    attaining it. The least-favorable configuration is *found* on the supplied
    grid, never assumed; adequacy of the grid for the continuous boundary is a
    design question the caller must assess, not something the enumeration
    settles. No validity claim for the weak composite null is implied.
    """

    n: int
    delta0: Fraction
    alpha: Fraction
    critical_value: int
    sup_size: Fraction
    lfc_pi_d: Fraction
    sizes_by_pi_d: tuple[tuple[Fraction, Fraction], ...]


def lfc_calibrate(
    n: int,
    delta0: Fraction,
    alpha: Fraction,
    *,
    pi_d_grid: Sequence[Fraction] | None = None,
) -> LfcCalibration:
    """Calibrate the rule ``S >= c`` over the boundary of ``H0: Delta <= delta0``.

    For ascending candidate ``c`` starting at ``-n``, the supremum over the
    ``pi_d`` grid of the exact boundary rejection probability
    ``tail_probability(sum_distribution(n, *boundary_configuration(delta0, pi_d)), c)``
    is computed; the first ``c`` whose supremum is ``<= alpha`` is returned
    together with the per-grid-point sizes at that ``c``. The default grid
    contains ``delta0`` exactly when ``delta0 > 0``, followed by every strictly
    larger ``Fraction(k, 100)`` through ``1``. When ``delta0 == 0``, the
    degenerate ``pi_d = 0`` point is excluded and the grid runs from ``1/100``
    through ``1``. Thus a non-hundredth ``delta0`` is never silently rounded
    away from its own boundary grid.

    The least-favorable configuration is located by this grid supremum; the
    maximum-discordance point is deliberately not hard-coded, because lattice
    parity can move the supremum to an interior grid point. All probabilities
    are enumerated deterministically in integer arithmetic; nothing here makes
    the calibrated rule a valid test of the weak composite null — that depends
    on the sampling assumptions stated where the rule is proposed.

    Interior-null coverage on each grid line (derivation): for fixed ``pi_d``,
    ``P(S >= c)`` is nondecreasing in ``Delta`` under the i.i.d. trinomial
    model — increasing ``Delta`` at fixed ``pi_d`` moves cell probability mass
    from the ``-1`` cell to the ``+1`` cell with the ``0`` cell unchanged, so
    a direct coupling (one shared uniform draw per task) makes each difference,
    and hence ``S``, pointwise no smaller. The boundary size bound at a grid
    point ``(delta0, pi_d)`` therefore extends to every interior null point
    ``Delta <= delta0`` on that grid line (verified exactly in the committed
    tests). What this derivation does not settle is the adequacy of the finite
    ``pi_d`` grid for the continuous boundary — that remains a design
    judgment.

    Requires ``n >= 1``, ``0 <= delta0 <= 1``, ``0 < alpha < 1``, and a
    non-empty grid whose points satisfy ``delta0 <= pi_d <= 1``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    delta0 = _exact(delta0, "delta0")
    alpha = _exact(alpha, "alpha")
    if not 0 <= delta0 <= 1:
        raise ValueError("delta0 must satisfy 0 <= delta0 <= 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    if pi_d_grid is None:
        start = max(1, math.ceil(100 * delta0))
        hundredths = tuple(
            point
            for k in range(start, 101)
            if (point := Fraction(k, 100)) > delta0
        )
        grid: tuple[Fraction, ...] = (
            hundredths if delta0 == 0 else (delta0, *hundredths)
        )
    else:
        grid = tuple(_exact(p, "pi_d") for p in pi_d_grid)
        if not grid:
            raise ValueError("pi_d_grid must be non-empty")
    # Boundary distributions do not depend on the candidate c: enumerate each
    # once, keep sorted support plus exact suffix sums for O(log) tail lookups.
    tails: list[tuple[list[int], list[Fraction]]] = []
    for pi_d in grid:
        dist = sum_distribution(n, *boundary_configuration(delta0, pi_d))
        support = sorted(dist)
        suffix = [Fraction(0)] * (len(support) + 1)
        for i in range(len(support) - 1, -1, -1):
            suffix[i] = suffix[i + 1] + dist[support[i]]
        tails.append((support, suffix))
    for c in range(-n, n + 2):
        sizes = tuple(
            suffix[bisect_left(support, c)] for support, suffix in tails
        )
        sup_size = max(sizes)
        if sup_size <= alpha:
            return LfcCalibration(
                n=n,
                delta0=delta0,
                alpha=alpha,
                critical_value=c,
                sup_size=sup_size,
                lfc_pi_d=grid[sizes.index(sup_size)],
                sizes_by_pi_d=tuple(zip(grid, sizes)),
            )
    raise AssertionError("unreachable: the supremum size at c = n + 1 is exactly zero")


def exact_power(n: int, p_plus: Fraction, p_minus: Fraction, critical: int) -> Fraction:
    """Rejection probability of ``S >= critical``, computed exactly under the model.

    Convenience composition of :func:`sum_distribution` and
    :func:`tail_probability`. "Exact" describes the arithmetic under the
    stated i.i.d. trinomial sampling model, not any validity guarantee of the
    rule being evaluated.
    """
    return tail_probability(sum_distribution(n, p_plus, p_minus), critical)


@lru_cache(maxsize=None)
def _signflip_pvalue_scaled(
    n_plus: int, n_zero: int, n_minus: int, numerator: int, denominator: int
) -> Fraction:
    """Cached integer-DP core of :func:`signflip_pvalue` (arguments pre-validated)."""
    n = n_plus + n_zero + n_minus
    # Absolute residuals |d - delta0| scaled by delta0's denominator so all
    # reference-sum support points are integers.
    groups = (
        (n_plus, denominator - numerator),  # |1 - delta0| * denominator
        (n_zero, numerator),  # |0 - delta0| * denominator
        (n_minus, denominator + numerator),  # |-1 - delta0| * denominator
    )
    t_obs = denominator * (n_plus - n_minus) - n * numerator
    dist: dict[int, int] = {0: 1}
    for count, value in groups:
        if count == 0:
            continue
        # Within a group all residuals are equal, so flipping k of `count`
        # signs gives sum (2k - count) * value with multiplicity C(count, k).
        group: dict[int, int] = {}
        for k in range(count + 1):
            s = (2 * k - count) * value
            group[s] = group.get(s, 0) + math.comb(count, k)
        nxt: dict[int, int] = {}
        for s0, w0 in dist.items():
            for s1, w1 in group.items():
                key = s0 + s1
                nxt[key] = nxt.get(key, 0) + w0 * w1
        dist = nxt
    favourable = sum(w for s, w in dist.items() if s >= t_obs)
    return Fraction(favourable, 2**n)


def signflip_pvalue(n_plus: int, n_zero: int, n_minus: int, delta0: Fraction) -> Fraction:
    """Exact one-sided (upper) p-value of the shifted sign-flip statistic.

    With ``n = n_plus + n_zero + n_minus`` observed differences, the observed
    statistic is ``T_obs = (n_plus - n_minus) - n * delta0`` and the reference
    distribution is that of ``sum_i eps_i * |d_i - delta0|`` over all ``2**n``
    uniform sign vectors ``eps in {-1, +1}**n``, holding the observed
    ``|d_i - delta0|`` magnitudes fixed. The reference distribution is
    enumerated deterministically by a three-group binomial convolution over
    the residual multiset (values scaled to integers by ``delta0``'s
    denominator; multiplicities from ``math.comb``), and the returned p-value
    is the exact ``P_ref(T_ref >= T_obs)``.

    This deterministically enumerates the sign-flip reference distribution;
    it does NOT confer weak-null exactness. Whether a test based on this
    p-value is valid for any null — in particular the weak composite null
    ``H0: Delta <= delta0`` — depends on an explicitly stated symmetry or
    exchangeability assumption about the paired differences, not on the
    enumeration.

    Requires nonnegative counts with ``n >= 1`` and ``0 <= delta0 <= 1``.
    """
    if n_plus < 0 or n_zero < 0 or n_minus < 0:
        raise ValueError("counts must be nonnegative")
    n = n_plus + n_zero + n_minus
    if n < 1:
        raise ValueError("at least one observed difference is required")
    delta0 = _exact(delta0, "delta0")
    if not 0 <= delta0 <= 1:
        raise ValueError("delta0 must satisfy 0 <= delta0 <= 1")
    return _signflip_pvalue_scaled(
        int(n_plus), int(n_zero), int(n_minus), delta0.numerator, delta0.denominator
    )


def signflip_rejection_probability(
    counts: Mapping[tuple[int, int], Fraction],
    *,
    n: int,
    delta0: Fraction,
    alpha: Fraction,
) -> Fraction:
    """Exact ``P(signflip_pvalue <= alpha)`` under an enumerated counts distribution.

    ``counts`` is a ``(n_plus, n_minus)`` distribution as produced by
    :func:`counts_distribution` (i.i.d. or heterogeneous). ``n`` is the
    caller-supplied task count; it is deliberately explicit because reachable
    support need not reveal tasks whose discordance probability is zero.
    ``n_zero = n - n_plus - n_minus`` per support point.

    The result is the exact rejection probability of the sign-flip rule under
    the supplied sampling model — a computed operating characteristic. It is
    not a claim that the rule is a valid level-``alpha`` test of any null.

    Requires ``n >= 1``, a non-empty ``counts`` with nonnegative keys whose
    discordant count does not exceed ``n``, and ``0 < alpha < 1``.
    """
    delta0 = _exact(delta0, "delta0")
    alpha = _exact(alpha, "alpha")
    if not 0 < alpha < 1:
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    if n < 1:
        raise ValueError("n must be >= 1")
    if not counts:
        raise ValueError("counts must be non-empty")
    for n_plus, n_minus in counts:
        if n_plus < 0 or n_minus < 0:
            raise ValueError("counts keys must be nonnegative")
        if n_plus + n_minus > n:
            raise ValueError("counts keys must not exceed the explicit task count n")
    total = Fraction(0)
    for (n_plus, n_minus), probability in counts.items():
        if signflip_pvalue(n_plus, n - n_plus - n_minus, n_minus, delta0) <= alpha:
            total += probability
    return total


def replicate_lattice(m: int) -> tuple[Fraction, ...]:
    """Attainable per-task mean-difference values with ``m`` replicates per arm.

    With per-task success proportions on ``{0, 1/m, ..., 1}``, the paired
    mean difference lies on ``(-m..m)/m`` — step ``1/m`` over ``[-1, 1]``.
    ``m = 2`` gives the ``{0, 1/2, 1}`` proportion lattice and ``m = 3`` the
    ``{0, 1/3, 2/3, 1}`` lattice. Requires ``m >= 1``.
    """
    if m < 1:
        raise ValueError("m must be >= 1")
    return tuple(Fraction(k, m) for k in range(-m, m + 1))


def is_attainable_shift(delta: Fraction, m: int) -> bool:
    """Whether ``delta`` is an exact point of ``replicate_lattice(m)``.

    True iff ``delta * m`` is an integer and ``|delta| <= 1``. A statement
    about lattice membership only — it neither justifies nor criticizes any
    margin choice. Requires ``m >= 1``.
    """
    if m < 1:
        raise ValueError("m must be >= 1")
    delta = _exact(delta, "delta")
    if abs(delta) > 1:
        return False
    return (delta * m).denominator == 1
