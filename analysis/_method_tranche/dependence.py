"""Experimental dependence and nondeterminism-floor machinery (design-only).

This module supplies two families of design tools used by the methodology
tranche:

1. **Dependence / design-effect machinery** — the design-effect relation
   ``DEFF = 1 + (m - 1) * rho``, an exchangeable within-session mixture model at
   the ``Delta = 0`` null boundary with a closed-form mixture weight hitting a
   target within-session correlation ``rho``, seeded Monte Carlo suite
   simulation, and size-distortion estimation under a caller-supplied rejection
   rule (including a one-sided normal-approximation z rule as one such rule).
2. **Nondeterminism-floor propagation** — exact ``fractions.Fraction``
   arithmetic for how a measured apparatus nondeterminism floor ``epsilon``
   transforms joint paired-outcome cells (attenuating the mean difference
   ``Delta`` linearly: ``Delta' = (1 - 2*epsilon) * Delta``), induces
   repeat-run disagreement, and yields an exact binomial alarm threshold
   derived from the floor (never from zero). A separate helper reports the
   quadratic factor ``(1 - 2*epsilon)**2`` that applies to covariance-type
   quantities only — it is not the attenuation of ``Delta``.

Honesty and scope notes (they apply to every function below):

- Everything here is a **deterministic computation or a seeded Monte Carlo
  estimate under an explicitly stated synthetic model**. No number produced by
  this module describes any real system, campaign, or live run.
- Computation claims and inference claims are kept separate. Computing a
  rejection rate, tail probability, or threshold exactly (or estimating it by
  seeded simulation) says nothing, by itself, about whether the underlying
  rejection rule has valid finite-sample Type I error control for any null
  hypothesis; any such validity claim must be justified separately under
  explicitly stated assumptions.
- Nothing in this module selects or installs an inferential basis, test,
  replicate policy, margin, or alarm policy; it computes the operating
  characteristics that inform such decisions elsewhere.

Standard library only. This module intentionally does not import any other
statistics module from this package.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction

__all__ = [
    "SessionLayout",
    "SizeDistortionResult",
    "alarm_threshold",
    "covariance_attenuation_factor",
    "design_effect",
    "disagreement_probability",
    "floor_transformed_cells",
    "session_mixture_weight",
    "simulate_session_differences",
    "size_distortion",
    "z_test_rejects",
]


@dataclass(frozen=True)
class SessionLayout:
    """A session layout: ``sessions`` sessions of ``pairs_per_session`` intact task pairs.

    Each task pair (both arms of one task) is co-located within a single
    session; sessions are the candidate dependence unit. ``n_pairs`` is the
    total number of task pairs in the suite draw.
    """

    sessions: int
    pairs_per_session: int

    def __post_init__(self) -> None:
        if self.sessions < 1:
            raise ValueError("sessions must be >= 1")
        if self.pairs_per_session < 1:
            raise ValueError("pairs_per_session must be >= 1")

    @property
    def n_pairs(self) -> int:
        """Total number of task pairs: ``sessions * pairs_per_session``."""
        return self.sessions * self.pairs_per_session


def design_effect(m: int, rho: float) -> float:
    """Design effect ``DEFF = 1 + (m - 1) * rho`` for ``m`` units sharing correlation ``rho``.

    ``m`` is the number of exchangeable units per cluster (e.g., task pairs per
    session) and ``rho`` the within-cluster correlation. This is a closed-form
    variance-inflation identity for exchangeable within-cluster correlation; it
    is a property of the stated dependence model, not a validity claim about
    any test.

    Requires ``m >= 1`` and ``0 <= rho <= 1``.
    """
    if m < 1:
        raise ValueError("m must be >= 1")
    if not 0.0 <= rho <= 1.0:
        raise ValueError("rho must satisfy 0 <= rho <= 1")
    return 1.0 + (m - 1) * rho


def session_mixture_weight(rho: float, pi_d: float) -> float:
    """Mixture weight ``lam`` giving within-session correlation exactly ``rho`` at ``Delta = 0``.

    Under the exchangeable within-session mixture model used by
    :func:`simulate_session_differences` — with probability ``lam`` a pair's
    difference copies the session sign ``B`` (a session-by-arm interaction),
    otherwise it is an independent trinomial draw at the ``Delta = 0`` boundary
    with discordance ``pi_d`` — the per-pair differences have mean zero,
    within-session covariance ``lam**2``, and variance
    ``lam + (1 - lam) * pi_d``, so the within-session correlation is
    ``rho = lam**2 / (lam + (1 - lam) * pi_d)``.

    Solving that quadratic for the nonnegative root gives the closed form
    ``lam = (rho*(1 - pi_d) + sqrt(rho**2 * (1 - pi_d)**2 + 4*rho*pi_d)) / 2``.

    Documented property of this synthetic model: it preserves ``Delta = 0``
    exactly, but it inflates the marginal discordance from ``pi_d`` to
    ``lam + (1 - lam) * pi_d`` (the session-copy branch is always discordant).

    Requires ``0 <= rho < 1`` and ``0 < pi_d <= 1``; returns ``0.0`` when
    ``rho == 0``; raises ``ValueError`` if the implied weight would exceed 1.
    """
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must satisfy 0 <= rho < 1")
    if not 0.0 < pi_d <= 1.0:
        raise ValueError("pi_d must satisfy 0 < pi_d <= 1")
    if rho == 0.0:
        return 0.0
    lam = (rho * (1.0 - pi_d) + math.sqrt(rho * rho * (1.0 - pi_d) ** 2 + 4.0 * rho * pi_d)) / 2.0
    if lam > 1.0:
        raise ValueError("no feasible mixture weight lam <= 1 for these inputs")
    return lam


def simulate_session_differences(
    layout: SessionLayout,
    *,
    rho: float,
    pi_d: float,
    rng: random.Random,
) -> list[int]:
    """One synthetic suite draw of paired differences under the ``Delta = 0`` boundary.

    The draw order below is exact and is part of the committed specification
    (seeded reproducibility depends on it). For each session, first draw the
    session sign ``B``: ``B = +1`` if ``rng.random() < 0.5`` else ``-1``. Then,
    for each pair in that session, draw ``u = rng.random()``; if ``u < lam``
    (with ``lam = session_mixture_weight(rho, pi_d)``) the pair's difference is
    ``B`` — a session-by-arm interaction that pairing does not cancel —
    otherwise draw ``v = rng.random()`` and emit ``+1`` if ``v < pi_d / 2``,
    ``-1`` if ``v < pi_d``, else ``0``.

    Returns ``layout.n_pairs`` values in ``{-1, 0, +1}``, sessions in order,
    pairs in order within each session. This simulates a stated synthetic
    dependence model; it makes no claim about any real serving stack.
    """
    lam = session_mixture_weight(rho, pi_d)
    half_pi_d = pi_d / 2.0
    differences: list[int] = []
    for _ in range(layout.sessions):
        session_sign = 1 if rng.random() < 0.5 else -1
        for _ in range(layout.pairs_per_session):
            u = rng.random()
            if u < lam:
                differences.append(session_sign)
            else:
                v = rng.random()
                if v < half_pi_d:
                    differences.append(1)
                elif v < pi_d:
                    differences.append(-1)
                else:
                    differences.append(0)
    return differences


@dataclass(frozen=True)
class SizeDistortionResult:
    """Seeded Monte Carlo estimate of a rejection rule's rejection rate under the mixture model.

    ``rejection_rate`` is a Monte Carlo estimate of the rule's rejection
    probability under the stated synthetic ``Delta = 0`` boundary model — a
    computed operating characteristic, not a statement that the rule is (or is
    not) a valid test of any null hypothesis.
    """

    sessions: int
    pairs_per_session: int
    rho: float
    pi_d: float
    n_sims: int
    seed: int
    rejections: int
    rejection_rate: float
    mc_standard_error: float
    deff: float


def size_distortion(
    layout: SessionLayout,
    *,
    rho: float,
    pi_d: float,
    rule: Callable[[Sequence[int]], bool],
    n_sims: int,
    seed: int,
) -> SizeDistortionResult:
    """Seeded Monte Carlo rejection rate of ``rule`` under the ``Delta = 0`` mixture model.

    Draws ``n_sims`` independent synthetic suites via
    :func:`simulate_session_differences` from ``random.Random(seed)`` and counts
    how often the caller-supplied rejection rule fires. Reports the Monte Carlo
    rate, its binomial standard error ``sqrt(rate * (1 - rate) / n_sims)``, and
    the design effect ``design_effect(layout.pairs_per_session, rho)``.

    The estimate quantifies size distortion of the supplied rule under this
    synthetic dependence model; it neither validates nor invalidates the rule
    as an inferential procedure — that is a separate question answered under
    explicitly stated assumptions.
    """
    if n_sims < 1:
        raise ValueError("n_sims must be >= 1")
    rng = random.Random(seed)
    rejections = 0
    for _ in range(n_sims):
        differences = simulate_session_differences(layout, rho=rho, pi_d=pi_d, rng=rng)
        if rule(differences):
            rejections += 1
    rejection_rate = rejections / n_sims
    mc_standard_error = math.sqrt(rejection_rate * (1.0 - rejection_rate) / n_sims)
    return SizeDistortionResult(
        sessions=layout.sessions,
        pairs_per_session=layout.pairs_per_session,
        rho=rho,
        pi_d=pi_d,
        n_sims=n_sims,
        seed=seed,
        rejections=rejections,
        rejection_rate=rejection_rate,
        mc_standard_error=mc_standard_error,
        deff=design_effect(layout.pairs_per_session, rho),
    )


def z_test_rejects(
    differences: Sequence[int] | Sequence[float],
    *,
    alpha: float,
    mu0: float = 0.0,
) -> bool:
    """One-sided upper normal-approximation paired rule: does it reject at level ``alpha``?

    Computes the paired z statistic ``(mean - mu0) / (sd / sqrt(n))`` with the
    sample mean (``statistics.fmean``) and the ``n - 1``-denominator sample
    standard deviation (``statistics.stdev``), and compares it against
    ``statistics.NormalDist().inv_cdf(1 - alpha)``. If ``sd == 0`` the rule
    degenerates to ``mean > mu0``.

    This is the advisory-style normal-approximation diagnostic evaluated as a
    candidate rejection rule. Its guarantee, if any, is asymptotic and requires
    independence assumptions that must be stated separately; evaluating the
    rule here is a computation and confers no finite-sample validity.

    Requires ``len(differences) >= 2`` and ``0 < alpha < 1``.
    """
    n = len(differences)
    if n < 2:
        raise ValueError("differences must contain at least 2 values")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    mean = statistics.fmean(differences)
    sd = statistics.stdev(differences)
    if sd == 0.0:
        return mean > mu0
    z = (mean - mu0) / (sd / math.sqrt(n))
    return z > statistics.NormalDist().inv_cdf(1.0 - alpha)


def _validate_epsilon(epsilon: Fraction) -> None:
    if not 0 <= epsilon < Fraction(1, 2):
        raise ValueError("epsilon must satisfy 0 <= epsilon < 1/2")


def covariance_attenuation_factor(epsilon: Fraction) -> Fraction:
    """Exact quadratic factor ``(1 - 2*epsilon)**2`` for covariance-type quantities.

    ``(1 - 2*epsilon)**2`` is the classical attenuation factor for a
    covariance-type paired quantity when each of the two measurements entering
    it is independently flipped with probability ``epsilon``. It is **not**
    the attenuation of the mean difference ``Delta``: under the per-arm flip
    channel implemented by :func:`floor_transformed_cells`, ``Delta``
    attenuates **linearly** — the transformed cells satisfy
    ``p10' - p01' = (1 - 2*epsilon) * (p10 - p01)`` exactly, an identity
    verified in the committed tests
    (``test_channel_shrinks_the_cell_difference_linearly``). No stated model
    in this package attenuates ``Delta`` quadratically. Exact ``Fraction``
    arithmetic under the stated synthetic floor model; a computed model
    property, not an inference claim about any test.

    Requires ``0 <= epsilon < 1/2``.
    """
    _validate_epsilon(epsilon)
    return (1 - 2 * epsilon) ** 2


def floor_transformed_cells(
    cells: tuple[Fraction, Fraction, Fraction, Fraction],
    epsilon: Fraction,
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    """Push joint paired-outcome cells through independent per-arm outcome flips, exactly.

    ``cells`` are the joint paired-outcome probabilities in the order
    ``(p11, p10, p01, p00)`` — so ``p10 = p_plus`` and ``p01 = p_minus``. Each
    arm's binary outcome is independently flipped with probability ``epsilon``
    (the binary channel ``K(epsilon)``), and the joint transform
    ``K(epsilon) tensor K(epsilon)`` is applied with exact ``Fraction``
    arithmetic. The output is an exact probability simplex in the same cell
    order.

    This deterministically computes the transformed cells of the stated
    synthetic floor model; how the transformed cells affect any rule's
    operating characteristics is a separate computation, and the validity of
    any such rule is a separate inference question.

    Requires ``0 <= epsilon < 1/2``, nonnegative cells summing exactly to 1.
    """
    _validate_epsilon(epsilon)
    if len(cells) != 4:
        raise ValueError("cells must have exactly 4 entries (p11, p10, p01, p00)")
    if any(cell < 0 for cell in cells):
        raise ValueError("cells must be nonnegative")
    if sum(cells) != 1:
        raise ValueError("cells must sum exactly to 1")

    outcome_pairs = ((1, 1), (1, 0), (0, 1), (0, 0))
    keep = 1 - epsilon

    def channel(observed: int, true: int) -> Fraction:
        return keep if observed == true else epsilon

    transformed = []
    for x, y in outcome_pairs:
        total = Fraction(0)
        for (a, b), cell in zip(outcome_pairs, cells):
            total += channel(x, a) * channel(y, b) * cell
        transformed.append(total)
    return (transformed[0], transformed[1], transformed[2], transformed[3])


def disagreement_probability(epsilon: Fraction) -> Fraction:
    """Exact probability ``2*epsilon*(1 - epsilon)`` that two greedy repeats of one run disagree.

    Under the stated floor model — each repeat's binary outcome independently
    flipped with probability ``epsilon`` — two repeats of the same underlying
    run disagree with probability ``2*epsilon*(1 - epsilon)``. Exact
    ``Fraction`` arithmetic; a model property, not an inference claim.

    Requires ``0 <= epsilon < 1/2``.
    """
    _validate_epsilon(epsilon)
    return 2 * epsilon * (1 - epsilon)


def alarm_threshold(n_repeat_pairs: int, epsilon: Fraction, alpha: Fraction) -> int:
    """Smallest alarm count ``k`` whose false-alarm probability under the floor is ``<= alpha``.

    With ``n_repeat_pairs`` independent repeat pairs and per-pair disagreement
    probability ``q = disagreement_probability(epsilon)``, returns the smallest
    ``k >= 0`` such that ``P(Binomial(n_repeat_pairs, q) >= k) <= alpha``,
    computed exactly with ``math.comb`` and ``Fraction`` arithmetic. Semantics:
    the apparatus alarm fires at ``>= k`` observed repeat disagreements, and
    its false-alarm probability under the measured floor is at most ``alpha``.

    The threshold is derived from the measured floor, never from zero: at
    ``epsilon = 0`` the result is 1 (the from-zero policy — any disagreement
    alarms), which callers contrast with floor-derived thresholds. The exact
    binomial tail computation is deterministic; whether the floor model itself
    is adequate for a given apparatus is an empirical question outside this
    function.

    Requires ``n_repeat_pairs >= 1``, ``0 <= epsilon < 1/2``, ``0 < alpha < 1``.
    """
    if n_repeat_pairs < 1:
        raise ValueError("n_repeat_pairs must be >= 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    q = disagreement_probability(epsilon)
    n = n_repeat_pairs
    tails = [Fraction(0)] * (n + 2)
    running = Fraction(0)
    for j in range(n, -1, -1):
        running += math.comb(n, j) * q**j * (1 - q) ** (n - j)
        tails[j] = running
    for k in range(n + 2):
        if tails[k] <= alpha:
            return k
    raise AssertionError("unreachable: the empty tail is always <= alpha")
