# E2 operating-characteristics statistical analysis plan

## Metadata and claim boundary

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 0.2.0-candidate.3
- **Status:** Candidate protocol — offline design freeze implemented; not preregistered; no observations authorized.
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

The leading candidate is `exact_conditional_sign_v1`, a `delta_0 = 0` exact conditional paired
binary (McNemar/sign-equivalent) test for the equal-class mean candidate-minus-incumbent success
estimand. It uses fixed horizon `N`, `N / 4` planned pairs per class, a one-sided
candidate-superiority direction, and nominal `alpha = 0.05`. The statistic is candidate wins among
discordant pairs and the p-value is the exact upper binomial tail conditional on the discordant
count. Ties remain in the evidence and are conditioned out; zero discordant pairs gives p-value
one. There are no interim looks, optional stopping, continuity correction, mid-p adjustment, or
randomized rejection.

Conditional exactness follows under discordant-sign symmetry. It is not automatically a validity
proof for every class-heterogeneous equal-class-mean null. E2 must establish control for that
registered estimand-relative null and cannot upgrade the narrower symmetry result into a general
claim.

A bounded-mean betting procedure and any positive-margin rule remain held design slots. Neither may
be implemented or simulated until it has an explicit estimand, horizon or stopping rule,
missingness policy, nuisance treatment, and immutable implementation.

Each candidate rule has its own null/alternative partition. For example, an effect cell may be an
alternative for a zero-margin rule and a null cell for a positive-margin rule.

## Base scenario grid

The frozen feasibility grid crosses:

- total task-pair counts `N` in `{20, 40, 60}` with equal planned class weighting;
- incumbent success probabilities in `{0.30, 0.50, 0.70, 0.90}`;
- mean candidate-minus-incumbent effects in `{0.00, 0.025, 0.05, 0.10, 0.20}`;
- heterogeneity amplitude `h = 0.10` and these rotations: homogeneous `[delta, delta, delta,
  delta]` once; balanced opposing `[delta+h, delta+h, delta-h, delta-h]` for all six choices of the
  elevated classes; sparse benefit `[4*delta, 0, 0, 0]` for all four benefited classes; and
  one-class harm `[delta+h/3, delta+h/3, delta+h/3, delta-h]` for all four harmed classes;
- terminal missing/failure rates in `{0.00, 0.01, 0.05, 0.10}` under arm-symmetric and
  arm-asymmetric mechanisms; and
- the feasible paired-outcome discordance nuisance domain for every rule-relative null cell.

`N = 60` is a hypothetical feasibility point. The current suite is frozen at 40; a real study with
`N > 40` requires a separately governed suite expansion under the per-class sampling frame.

For incumbent success probability `p`, class effect `delta_k`, and discordance `d_k`, define
`p10 = (d_k + delta_k) / 2`, `p01 = (d_k - delta_k) / 2`, `p11 = p - p01`, and
`p00 = 1 - p - p10`. The full feasible interval is
`abs(delta_k) <= d_k <= min(2*p + delta_k, 2*(1-p) - delta_k)`. Construction uses exact rational
arithmetic. Impossible combinations are omitted by an explicit deterministic rule and listed in
the scenario manifest. The root seed remains the UTF-8 string `lane-a-e2-oc-v1`; any future seeded
cell derives from the root and canonical cell JSON using SHA-256.

The repository-versioned generator enumerates 717 feasible base scenarios and 183 explicit
omissions from 900 named scenario cells. Rotations remain named cells even when their numerical
vectors coincide at zero effect. These are design records, not simulation results.

## Nuisance maximization and Type I control

Type I error is evaluated at the supremum over the feasible discordance nuisance domain for every
rule-relative null cell. Use analytic or exact maximization where available. Otherwise freeze the
numerical domain, tolerance, convergence tests, boundary checks, and implementation by digest.

For `exact_conditional_sign_v1`, use exact finite convolution over the registered paired
multinomial cells. Do not use Monte Carlo where the probability is exactly computable. For a rule
whose Type I error is analytically computable, compute it exactly. The nominal level is 0.05; the
`0.06` empirical ceiling is an implementation-correctness gate, not a substitute for the rule's
analytic validity proof. The substantive risk for a valid exact rule is conservativeness and low
power, which must be reported.

The candidate nuisance maximizer is certified interval branch-and-bound over the full Cartesian
product of class-specific feasible intervals, using rational endpoint evaluation, outward-rounded
probability bounds, deterministic subdivision, exact checks at candidate maxima, and a certified
supremum gap at most `1e-8`. If the certified bounds straddle 0.06, the cell is `NOT_EVALUABLE`.
The design is frozen, but its result-producing implementation remains required before a registered
E2 result.

Where Monte Carlo is required for admission, use simultaneous one-sided upper confidence bounds
across all registered null cells. A rule is not eligible merely because every per-cell point
estimate is below `0.06`. The simultaneous method, confidence family, multiplicity allocation, and
draw-escalation rule must be frozen before execution. Increase beyond 10,000 draws for a cell when
the registered rule places its upper bound near the admission boundary.

## Missingness policies and outputs

For the leading rule, a retained, gradeable terminal failure is `Y = 0` for that arm. A missing
terminal row, invalid provenance, absent grade, or unjoinable record makes the realized rule
application `NOT_EVALUABLE`. It performs no complete-case dropping, favorable imputation, or silent
pair replacement.

Separately apply rates `{0.00, 0.01, 0.05, 0.10}` to gradeable terminal failures under symmetric,
candidate-only, and incumbent-only transformations and to evidence missingness under independent
arm-symmetric, common-cause pair-level, candidate-only, and incumbent-only transformations. Do not
collapse failure and missing evidence. Report mutually exclusive unconditional `REJECT`,
`DO_NOT_REJECT`, and `NOT_EVALUABLE` probabilities that sum to one, plus conditional-on-evaluable
rejection as diagnostic only. Missingness-induced refusal cannot be credited as Type I control.

For every rule and cell, report the exact rejection probability or simulation rejection count/rate,
uncertainty calculation, null/alternative label, power or Type I interpretation, refusal frequency,
decision frequency, class-specific error, and sensitivity to grader/apparatus violations.

Canonical outputs use sorted-key compact UTF-8 JSON, exactly one trailing newline, and reduced
numerator/denominator strings for rational probabilities. The registered packet includes all cell
records, aggregate tables, code and dependency digests, scenario manifest, seeds, and report bytes.
Independent recomputation must reproduce it exactly. A producer claim that differs from
recomputation makes E2 `NOT_EVALUABLE`.

The content-free rule, grid, perturbation axis, nuisance-maximizer contract, and source digests are
repository-versioned in
[`analysis/calibration-freeze.v1.json`](../../analysis/calibration-freeze.v1.json). Recompute it
with `PYTHONPATH=src python -m analysis.run_calibration_freeze --check`. The artifact is synthetic
design only: it contains no operating-characteristic result, admits no rule, and selects no powered
method.

## Hard stops and remaining freeze work

E2 is `NOT_EVALUABLE` if a required accepted E4/E1 input is absent, a rule/grid digest differs from
registration, any cell is skipped, required draws are incomplete, the nuisance supremum is not
established, or exact recomputation fails. Partial diagnostics are retained separately and cannot
become the registered result.

Before registration, reviewers must complete and digest-freeze the exact convolution and certified
nuisance-maximizer implementations, rule-relative null labels, result schema, compute budget, and
report bytes. Held alternative rules require their missing specifications before any implementation
work begins. E4/E1 sensitivity transformations remain frozen in design but cannot execute until
accepted inputs exist.
