"""Promotion decision rules for public reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuperiorityDecision:
    """Result of the enforcing superiority-by-margin rule."""

    promote: bool
    point_estimate: float | None
    ci_low: float | None
    ci_high: float | None
    margin: float
    rule: str = "bootstrap_ci_low_gt_margin"
    label: str = "enforcing:superiority-by-margin"


def superiority_by_margin(
    point_estimate: float | None,
    ci: tuple[float | None, float | None],
    *,
    margin: float,
) -> SuperiorityDecision:
    """Promote only when the bootstrap CI lower bound is strictly above margin."""

    ci_low, ci_high = ci
    promote = point_estimate is not None and ci_low is not None and ci_low > margin
    return SuperiorityDecision(
        promote=promote,
        point_estimate=point_estimate,
        ci_low=ci_low,
        ci_high=ci_high,
        margin=margin,
    )
