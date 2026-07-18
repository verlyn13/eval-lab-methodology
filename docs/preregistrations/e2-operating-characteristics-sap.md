# E2 operating-characteristics statistical analysis plan

## Metadata and claim boundary

- **Date:** 2026-07-17
- **Version:** 0.1.0-candidate.1
- **Status:** Candidate protocol — not preregistered; no observations authorized.
- **Study type:** Deterministic synthetic simulation; no model or provider execution.

Every value below is a **planned candidate value**. E2 compares candidate decision rules; it does
not select one, settle R1/R2/R4, or produce model-performance evidence.

## Objective

E2 estimates operating characteristics of exact, hash-bound candidate rule implementations under
the finite 40-task, four-class design. It evaluates Type I error, power, missingness, grader error,
heterogeneity, and residual apparatus sensitivity before any powered protocol can be considered.

No rule is currently accepted. E2 cannot run until the candidate implementations, estimands,
nuisance handling, and simulation distributions are frozen by exact digest. A result for an
unfrozen or approximate stand-in does not apply to the later powered rule.

## Candidate scenario grid

The proposed grid crosses:

- total task-pair counts `N` in `{20, 40, 60}` with equal planned class weighting;
- incumbent success probabilities in `{0.30, 0.50, 0.70, 0.90}`;
- mean candidate-minus-incumbent effects in `{0.00, 0.025, 0.05, 0.10, 0.20}`;
- effect patterns: homogeneous, balanced opposing class effects, sparse benefit, and one-class harm;
- terminal missing/failure rates in `{0.00, 0.01, 0.05, 0.10}` under registered arm-symmetric and
  arm-asymmetric mechanisms;
- grader-error matrices from the accepted E4 result plus registered boundary sensitivity cases; and
- exact apparatus invariance plus registered divergence cases derived from the accepted E1 result.

Impossible probability combinations are omitted by an explicit deterministic rule and listed in
the scenario manifest. Each retained cell receives 10,000 planned simulation draws. The root seed is
the UTF-8 string `lane-a-e2-oc-v1`; a cell seed is derived from the root seed and canonical cell JSON
using SHA-256. Simulation order cannot affect a cell's draws.

The grid, probability model, paired-outcome construction, missingness mechanism, and candidate-rule
implementations require formal methodology review before registration.

## Outputs

For every candidate rule and scenario cell, report rejection count, empirical rejection rate, Monte
Carlo standard error, and an exact binomial confidence interval. Label null cells as Type I error and
alternative cells as power. Also report refusal/`NOT_EVALUABLE` frequency, decision frequency,
class-specific error, and sensitivity to grader and apparatus violations.

All cell-level records, aggregate tables, code digests, dependency lock, scenario manifest, seeds,
and report bytes must be committed as a deterministic recomputation packet by a future registered
E2 study. That packet must regenerate exactly under the registered environment.

## Candidate admission criterion

Using a one-sided nominal level of 0.05, a candidate rule is eligible for the later coupled ruling
only if the one-sided 95% exact-binomial upper confidence bound on its Type I error is at most 0.06
in **every** registered null cell. Power has no pass threshold in this candidate; it is reported with
feasibility and practical-benefit consequences.

The 0.06 bound, grid, draw count, and interval choice remain formal decisions. Eligibility is not
selection: the later ruling must consider validity assumptions, power, feasibility, E4/E1 results,
and practical benefit together.

## Missing inputs and hard stops

E2 is `NOT_EVALUABLE` if an accepted E4/E1 input is required but absent, a rule or grid digest does
not match registration, any registered cell is skipped, the draw count is incomplete, an output
cannot be exactly regenerated, or a producer claim differs from independent recomputation. Stop on
the first integrity mismatch and preserve the partial diagnostic separately from the registered
result.

Before registration, reviewers must freeze the candidate rule set, complete bounded-mean
alternative, continuous nuisance-boundary treatment, cell generator, draw count, error criterion,
compute/wall-time budget, output schema, and independent recomputation command.
