# E2 operating-characteristics statistical analysis plan

## Metadata and claim boundary

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 0.2.0-candidate.2
- **Status:** Candidate protocol — design decisions incorporated; not preregistered; no observations authorized.
- **Study type:** Deterministic synthetic simulation; no model or provider execution.

E2 compares candidate decision rules. It does not select a powered method or produce
model-performance evidence.

## Objective and phases

E2 characterizes finite-sample Type I error, power, conservativeness, missingness behavior, grader
error, heterogeneity, and residual apparatus sensitivity for the finite four-class design.

E2 is divided into:

1. a base grid using frozen synthetic paired-outcome distributions, perfect grading, and exact
   apparatus identity; and
2. sensitivity cells using accepted E4 grader-error matrices and accepted E1 apparatus behavior.

The base phase may execute after its own registration without E4/E1 results. The sensitivity
transformation, input schema, and boundary cases must be frozen before E4/E1 results are observed;
the sensitivity cells execute only after those accepted inputs exist.

## Candidate rule set

The leading candidate is the `delta_0 = 0` exact conditional paired binary
(McNemar/sign-equivalent) test. Its estimand, fixed horizon, two-sided or one-sided direction,
missingness policy, and exact implementation must be frozen by digest.

A bounded-mean betting procedure and any positive-margin rule remain held design slots. Neither may
be implemented or simulated until it has an explicit estimand, horizon or stopping rule,
missingness policy, nuisance treatment, and immutable implementation.

Each candidate rule has its own null/alternative partition. For example, an effect cell may be an
alternative for a zero-margin rule and a null cell for a positive-margin rule.

## Base scenario grid

The proposed feasibility grid crosses:

- total task-pair counts `N` in `{20, 40, 60}` with equal planned class weighting;
- incumbent success probabilities in `{0.30, 0.50, 0.70, 0.90}`;
- mean candidate-minus-incumbent effects in `{0.00, 0.025, 0.05, 0.10, 0.20}`;
- effect patterns: homogeneous, balanced opposing class effects, sparse benefit, and one-class harm;
- terminal missing/failure rates in `{0.00, 0.01, 0.05, 0.10}` under arm-symmetric and
  arm-asymmetric mechanisms; and
- the feasible paired-outcome discordance nuisance domain for every rule-relative null cell.

`N = 60` is a hypothetical feasibility point. The current suite is frozen at 40; a real study with
`N > 40` requires a separately governed suite expansion under the per-class sampling frame.

Impossible probability combinations are omitted by an explicit deterministic rule and listed in
the scenario manifest. Simulation cells use 10,000 draws unless the registered boundary rule
requires more. The root seed is the UTF-8 string `lane-a-e2-oc-v1`; cell seeds derive from the root
seed and canonical cell JSON using SHA-256.

## Nuisance maximization and Type I control

Type I error is evaluated at the supremum over the feasible discordance nuisance domain for every
rule-relative null cell. Use analytic or exact maximization where available. Otherwise freeze the
numerical domain, tolerance, convergence tests, boundary checks, and implementation by digest.

For a rule whose Type I error is analytically computable, compute it exactly. The nominal level is
0.05; the `0.06` empirical ceiling is an implementation-correctness gate, not a substitute for the
rule's analytic validity proof. The substantive risk for a valid exact rule is conservativeness and
low power, which must be reported.

Where Monte Carlo is required for admission, use simultaneous one-sided upper confidence bounds
across all registered null cells. A rule is not eligible merely because every per-cell point
estimate is below `0.06`. The simultaneous method, confidence family, multiplicity allocation, and
draw-escalation rule must be frozen before execution. Increase beyond 10,000 draws for a cell when
the registered rule places its upper bound near the admission boundary.

## Missingness policies and outputs

Every rule specifies one immutable missingness policy, such as dropping the pair, counting a
terminal failure against an arm, or a fully defined imputation rule. E2 stress-tests that policy
under symmetric and asymmetric mechanisms; it never chooses the most favorable policy after
simulation.

For every rule and cell, report the exact rejection probability or simulation rejection count/rate,
uncertainty calculation, null/alternative label, power or Type I interpretation, refusal frequency,
decision frequency, class-specific error, and sensitivity to grader/apparatus violations.

The registered packet includes all cell records, aggregate tables, code and dependency digests,
scenario manifest, seeds, and report bytes. Independent recomputation must reproduce it exactly. A
producer claim that differs from recomputation makes E2 `NOT_EVALUABLE`.

## Hard stops and remaining freeze work

E2 is `NOT_EVALUABLE` if a required accepted E4/E1 input is absent, a rule/grid digest differs from
registration, any cell is skipped, required draws are incomplete, the nuisance supremum is not
established, or exact recomputation fails. Partial diagnostics are retained separately and cannot
become the registered result.

Before registration, reviewers must freeze the exact conditional-rule specification, rule-relative
null partitions, nuisance maximizer, base cell generator, per-rule missingness policies, error
criterion, compute budget, output schema, and recomputation command. Held alternative rules require
their missing specifications before any implementation work begins.
