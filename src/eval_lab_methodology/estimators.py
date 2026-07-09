"""Additive enhanced estimators for new analyses.

The functions in this module are intentionally labeled as enhanced methods. They
are not a restatement of earlier recorded runs that used the light primitives.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


Number = int | float


class OptionalDependencyError(ImportError):
    """Raised when an optional estimator backend is not installed."""


@dataclass(frozen=True)
class WilcoxonResult:
    """Two-sided Wilcoxon signed-rank result over paired deltas."""

    statistic: float
    p_value: float
    n: int
    zero_deltas: int
    tie_groups: int
    method: str
    label: str = "enhanced:wilcoxon-signed-rank"


@dataclass(frozen=True)
class BootstrapResult:
    """Seeded percentile interval from hierarchical task/replicate resampling."""

    estimate: float | None
    ci_low: float | None
    ci_high: float | None
    iterations: int
    seed: int
    alpha: float
    tasks: int
    replicates: int
    method: str = "enhanced:two-stage-bootstrap"


@dataclass(frozen=True)
class PowerPoint:
    """Estimated power for one task-count candidate."""

    tasks: int
    replicates: int
    estimated_power: float
    simulations: int


@dataclass(frozen=True)
class PowerSimulationResult:
    """Simulation-based task count plan."""

    planned_n: int | None
    target_power: float
    margin: float
    incumbent_rate: float
    candidate_rate: float
    seed: int
    grid: tuple[PowerPoint, ...]
    method: str = "enhanced:power-simulation"


@dataclass(frozen=True)
class GLMMResult:
    """Optional statsmodels-backed mixed-effects logistic result."""

    formula: str
    backend: str
    converged: bool | None
    parameters: Mapping[str, float]
    summary: str
    method: str = "enhanced:glmm-logistic"


def wilcoxon_signed_rank(
    deltas: Sequence[Number],
    *,
    exact_n_limit: int = 50,
) -> WilcoxonResult:
    """Two-sided Wilcoxon signed-rank test without SciPy.

    Zero deltas are dropped. Tied absolute deltas receive average ranks. For up
    to ``exact_n_limit`` nonzero pairs, p-values use the exact sign-assignment
    distribution; above that, the function uses a normal approximation.
    """

    nonzero = [float(delta) for delta in deltas if delta != 0]
    zero_deltas = len(deltas) - len(nonzero)
    if not nonzero:
        return WilcoxonResult(
            statistic=0.0,
            p_value=1.0,
            n=0,
            zero_deltas=zero_deltas,
            tie_groups=0,
            method="exact",
        )

    ranks, tie_groups = _average_abs_ranks(nonzero)
    w_plus = sum(rank for rank, delta in zip(ranks, nonzero, strict=True) if delta > 0)
    total = sum(ranks)
    statistic = min(w_plus, total - w_plus)

    if len(nonzero) <= exact_n_limit:
        p_value = _wilcoxon_exact_p_value(ranks, statistic)
        method = "exact"
    else:
        p_value = _wilcoxon_normal_p_value(ranks, w_plus)
        method = "normal-approximation"

    return WilcoxonResult(
        statistic=statistic,
        p_value=p_value,
        n=len(nonzero),
        zero_deltas=zero_deltas,
        tie_groups=tie_groups,
        method=method,
    )


def two_stage_bootstrap(
    outcomes: Mapping[str, Sequence[Number]] | Sequence[Sequence[Number]],
    *,
    statistic: Callable[[Sequence[float]], float] = statistics.fmean,
    iterations: int = 2000,
    seed: int = 12345,
    alpha: float = 0.05,
) -> BootstrapResult:
    """Seeded two-stage percentile bootstrap over tasks, then replicates.

    ``outcomes`` is a mapping or sequence where each item is one task and each
    task contains replicate-level paired deltas or other numeric outcomes.
    """

    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    tasks = _normalize_task_outcomes(outcomes)
    if not tasks:
        return BootstrapResult(
            estimate=None,
            ci_low=None,
            ci_high=None,
            iterations=iterations,
            seed=seed,
            alpha=alpha,
            tasks=0,
            replicates=0,
        )

    flattened = [value for task in tasks for value in task]
    estimate = statistic(flattened)
    rng = random.Random(seed)
    means: list[float] = []
    task_count = len(tasks)
    for _ in range(iterations):
        sample: list[float] = []
        for _ in range(task_count):
            task = tasks[rng.randrange(task_count)]
            replicate_count = len(task)
            sample.extend(task[rng.randrange(replicate_count)] for _ in range(replicate_count))
        means.append(statistic(sample))

    means.sort()
    lo_idx = max(0, int((alpha / 2) * iterations))
    hi_idx = min(iterations - 1, int((1 - alpha / 2) * iterations))
    return BootstrapResult(
        estimate=estimate,
        ci_low=means[lo_idx],
        ci_high=means[hi_idx],
        iterations=iterations,
        seed=seed,
        alpha=alpha,
        tasks=task_count,
        replicates=len(flattened),
    )


def power_simulation(
    *,
    incumbent_rate: float,
    candidate_rate: float,
    margin: float,
    task_counts: Sequence[int] = (4, 8, 12, 16, 20, 24, 32, 40, 48, 64),
    replicates: int = 2,
    target_power: float = 0.8,
    simulations: int = 200,
    bootstrap_iterations: int = 300,
    seed: int = 12345,
    alpha: float = 0.05,
) -> PowerSimulationResult:
    """Estimate planned task count under the bootstrap lower-bound gate."""

    _validate_probability("incumbent_rate", incumbent_rate)
    _validate_probability("candidate_rate", candidate_rate)
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    if not 0 < target_power <= 1:
        raise ValueError("target_power must be in (0, 1]")

    rng = random.Random(seed)
    grid: list[PowerPoint] = []
    planned_n: int | None = None
    for task_count in task_counts:
        if task_count <= 0:
            raise ValueError("task_counts must contain positive integers")
        passes = 0
        for _ in range(simulations):
            simulated = _simulate_paired_binary_deltas(
                task_count=task_count,
                replicates=replicates,
                incumbent_rate=incumbent_rate,
                candidate_rate=candidate_rate,
                rng=rng,
            )
            result = two_stage_bootstrap(
                simulated,
                iterations=bootstrap_iterations,
                seed=rng.randrange(2**31),
                alpha=alpha,
            )
            if result.ci_low is not None and result.ci_low > margin:
                passes += 1
        estimated_power = passes / simulations
        grid.append(
            PowerPoint(
                tasks=task_count,
                replicates=replicates,
                estimated_power=estimated_power,
                simulations=simulations,
            )
        )
        if planned_n is None and estimated_power >= target_power:
            planned_n = task_count

    return PowerSimulationResult(
        planned_n=planned_n,
        target_power=target_power,
        margin=margin,
        incumbent_rate=incumbent_rate,
        candidate_rate=candidate_rate,
        seed=seed,
        grid=tuple(grid),
    )


def fit_glmm_logistic(
    records: Iterable[Mapping[str, Any]],
    *,
    success_col: str = "success",
    model_col: str = "model",
    task_col: str = "task",
) -> GLMMResult:
    """Fit ``success ~ model + (1 | task)`` with optional statsmodels imports."""

    rows = list(records)
    if not rows:
        raise ValueError("records must not be empty")

    try:
        import pandas as pd
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except ModuleNotFoundError as exc:
        raise OptionalDependencyError(
            "fit_glmm_logistic requires the optional 'glmm' extra: "
            "pandas and statsmodels"
        ) from exc

    frame = pd.DataFrame.from_records(rows)
    required = {success_col, model_col, task_col}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"records missing required columns: {sorted(missing)}")

    formula = f"{success_col} ~ C({model_col})"
    variance_components = {"task": f"0 + C({task_col})"}
    model = BinomialBayesMixedGLM.from_formula(formula, variance_components, frame)
    fit = model.fit_vb()
    params = getattr(fit, "params", [])
    names = list(getattr(getattr(fit, "model", None), "exog_names", []))
    parameters = {
        names[index] if index < len(names) else f"param_{index}": float(value)
        for index, value in enumerate(params)
    }
    optim_retvals = getattr(fit, "optim_retvals", None)
    converged = None
    if isinstance(optim_retvals, Mapping):
        success = optim_retvals.get("success")
        converged = bool(success) if success is not None else None

    return GLMMResult(
        formula=f"{formula} + (1 | {task_col})",
        backend="statsmodels.BinomialBayesMixedGLM.fit_vb",
        converged=converged,
        parameters=parameters,
        summary=str(fit.summary()),
    )


def _average_abs_ranks(deltas: Sequence[float]) -> tuple[list[float], int]:
    indexed = sorted((abs(delta), index) for index, delta in enumerate(deltas))
    ranks = [0.0] * len(indexed)
    tie_groups = 0
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][0] == indexed[start][0]:
            end += 1
        average_rank = (start + 1 + end) / 2
        if end - start > 1:
            tie_groups += 1
        for _, original_index in indexed[start:end]:
            ranks[original_index] = average_rank
        start = end
    return ranks, tie_groups


def _wilcoxon_exact_p_value(ranks: Sequence[float], statistic: float) -> float:
    scaled_ranks = [int(round(rank * 2)) for rank in ranks]
    observed = int(round(statistic * 2))
    total = sum(scaled_ranks)
    distribution: dict[int, int] = {0: 1}
    for rank in scaled_ranks:
        next_distribution = distribution.copy()
        for rank_sum, count in distribution.items():
            next_distribution[rank_sum + rank] = next_distribution.get(rank_sum + rank, 0) + count
        distribution = next_distribution

    extreme = sum(
        count
        for rank_sum, count in distribution.items()
        if rank_sum <= observed or rank_sum >= total - observed
    )
    return min(1.0, extreme / (2 ** len(scaled_ranks)))


def _wilcoxon_normal_p_value(ranks: Sequence[float], w_plus: float) -> float:
    total = sum(ranks)
    mean = total / 2
    variance = sum(rank * rank for rank in ranks) / 4
    if variance == 0:
        return 1.0
    correction = 0.5 if w_plus > mean else -0.5 if w_plus < mean else 0.0
    z = (w_plus - mean - correction) / math.sqrt(variance)
    return min(1.0, math.erfc(abs(z) / math.sqrt(2)))


def _normalize_task_outcomes(
    outcomes: Mapping[str, Sequence[Number]] | Sequence[Sequence[Number]],
) -> list[list[float]]:
    if isinstance(outcomes, Mapping):
        raw_tasks = [outcomes[key] for key in sorted(outcomes)]
    else:
        raw_tasks = list(outcomes)

    tasks: list[list[float]] = []
    for index, task in enumerate(raw_tasks):
        values = [float(value) for value in task]
        if not values:
            raise ValueError(f"task {index} has no replicate outcomes")
        tasks.append(values)
    return tasks


def _validate_probability(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in [0, 1]")


def _simulate_paired_binary_deltas(
    *,
    task_count: int,
    replicates: int,
    incumbent_rate: float,
    candidate_rate: float,
    rng: random.Random,
) -> list[list[float]]:
    simulated: list[list[float]] = []
    for _ in range(task_count):
        task_deltas: list[float] = []
        for _ in range(replicates):
            incumbent = 1.0 if rng.random() < incumbent_rate else 0.0
            candidate = 1.0 if rng.random() < candidate_rate else 0.0
            task_deltas.append(candidate - incumbent)
        simulated.append(task_deltas)
    return simulated
