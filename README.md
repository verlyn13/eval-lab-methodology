# Agentic-Coding Evaluation Lab — methodology write-up

## Abstract

This repository documents an evidence-gated way to decide whether to change a
coding-agent default: which model, or which model-plus-harness combination, to
deploy. Its released 0.2.0 core implements the project's **historical** gate and
worked examples. The next inferential method, replicate policy, and practical-
benefit rule are under explicit scientific review and are not selected. The
single strongest result here is a defensible refusal to overclaim, not a
speedup. No performance or alignment improvement deltas are claimed anywhere in
this document. The story is evidence discipline, reproducibility, provenance,
and machine-checked refusal.

> **Current method status:** the bootstrap/margin gate below records historical
> implementation truth; it is not authorized for a new powered scientific
> claim. The public
> [experimental inference note](reports/experimental-inference-note.qmd)
> demonstrates that bit-exact enumeration does not itself guarantee valid
> inference, narrows every claim to its stated synthetic model, and leaves the
> enforcing method undecided. Its candidate code is repository-only and is not
> shipped in the 0.2.0 wheel.

This repository is a standalone artifact extracted from a larger private stack.
The sibling services it coordinates with (an OpenAI-compatible LLM gateway for
transport, an editing harness, and an operational trace/context state service)
are described here functionally, not exposed. Durable campaign evidence is owned
by the evaluation lab itself, and sanitized copies are published back here after
review.

## What is in this repo

- `README.md`: the methodology write-up (this file).
- `src/eval_lab_methodology/`: the importable, dependency-free public
  statistical core.
- `evidence/schema.json`: the versioned public evidence contract for report
  `model_dump()` output, raw per-task/per-replicate outcomes, and reproducibility
  manifests.
- `reports/methodology-report.qmd`: the parameterized Quarto report that renders
  a full campaign from an evidence JSON. Rendered example reports and the
  methodology site are published at
  <https://jvjohnson.dev/eval-lab-methodology/>.
- `reports/experimental-inference-note.qmd`: a synthetic, executable methods
  review that informs—but does not make—the next statistical decision.
- `analysis/_method_tranche/`: repository-only candidate calculations for that
  note. They are excluded from the released wheel and core hash.
- `evidence/`: the sanitized recorded values behind the two worked examples, and
  the small data file the figures are generated from.
- `figures/`: two figures generated reproducibly from `evidence/data.json`, plus
  the script that regenerates them.
- `LICENSE`: Apache-2.0.

## Public core API

The canonical public core is importable as `eval_lab_methodology`. Its light
primitives have no runtime dependencies:

- `wilson_interval(successes, n)`
- `sign_test(deltas)` - two-sided, reported only
- `bootstrap_ci(deltas, seed=12345)` - seeded percentile interval

Additive enhanced estimators are clearly labeled in their return objects:
`wilcoxon_signed_rank`, `two_stage_bootstrap`, `power_simulation`, and
`fit_glmm_logistic`. The GLMM wrapper imports `pandas` and `statsmodels` only
inside the function and raises `OptionalDependencyError` when the optional
backend is absent.

Offline parity checks can assert:

```python
from eval_lab_methodology import __core_content_hash__, __core_version__
```

Local verification:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m analysis.run_method_tranche --check
python -m pip wheel . --no-deps -w /tmp/eval-lab-methodology-wheel
```

### Identity domains

Runs are score-comparable only when their `identity_domain_sha256` values match
exactly (or an explicit bridge authorization is recorded downstream). An
identity domain is a structural fingerprint of everything that can change
numerics — engine and version, serving and base-image digests, engine wheel
hash, GPU hardware, model artifacts, and launch configuration — with run ids
and timestamps excluded by construction. The canonical rule is
`"sha256:" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))`.
The normative definition, the fail-closed validator, and the frozen cross-repo
conformance vector live in
[`src/eval_lab_methodology/identity_domain.py`](src/eval_lab_methodology/identity_domain.py);
the rendered spec page is at
<https://jvjohnson.dev/eval-lab-methodology/identity-domain.html>. An
engine or hardware bump is a re-baseline, not a comparable run.

## The problem

Most decisions about which coding agent, or which model-plus-harness
combination, to deploy are made on vibes. A model feels sharper this week. A
harness seems to edit more cleanly. Someone reads a benchmark headline, and a
default gets changed. The change is rarely instrumented, rarely reproducible,
and rarely reversible on evidence. When the agent later regresses on real work,
nobody can say what moved or why.

The Agentic-Coding Evaluation Lab replaces that habit with an evidence-gated
decision. The thesis is narrow and testable. The incumbent configuration stays
unless a fixed, reproducible evaluation produces evidence that a candidate is
demonstrably better on the axes that matter, and does not regress on the things
that must not break. The challenger carries the burden of proof. The lab is an
evaluation, governance, and evidence layer. It is explicitly not a router, an
editing harness, a memory service, or a weight store. Its output is not a faster
agent. Its output is a defensible go/no-go decision with the evidence attached.

## Architecture as separation of concerns

The lab is one service in a small local stack, and the boundaries are the point.
Transport and control live in a separate OpenAI-compatible gateway that owns
routing, provider resolution, and capability aliasing. Editing and diff
application live in a separate harness, under evaluation. Operational traces and
context live in a separate state service with bounded retention; durable
campaign evidence belongs to the lab's own evidence layer as validated
artifacts. The lab itself only measures, and it writes its findings into that
evidence layer. Transport, editing, and trace storage are separately-maintained
components. The lab is the evaluation and evidence layer that composes with
them. It is not a single program that owns routing, editing, and trace storage.

This separation is not tidiness for its own sake. It is a validity requirement.
If the thing that measures a system is entangled with the thing being measured,
the measurement is not trustworthy. The harness can flatter itself, and a
promotion decision can be contaminated by the very component whose promotion is
in question. By pushing routing into the gateway and editing into its own
harness, the lab can swap the model or the editing strategy underneath a fixed
measurement protocol, and attribute the resulting difference to that swap rather
than to a change in how it measured. Independence of measurement from the
measured is what lets a result be read as evidence about the model instead of an
artifact of the test rig.

## What the historical worked examples measured

Evaluation is split along two axes, because a single number hides the tradeoff
that actually drives deployment risk.

- The historical reliability battery (12 tasks) asks whether the agent can do
  the plumbing
  correctly and repeatably: native tool-call reliability, and edit/diff
  reliability. These are the failure modes that silently corrupt work. A
  malformed tool call. A diff that does not apply cleanly. Reliability is the
  floor.
- The historical capability battery (20 tasks, five per task-class across four
  classes: small edits, multi-file refactors, repo reasoning, and fixing a
  failing test) asks whether the agent can accomplish task-class work at all.
  This is the ceiling, organized by class of task rather than a single aggregate
  score.

Both axes matter because they trade against each other. A more capable model
that is less reliable can be a net regression in practice. A rock-solid harness
that cannot complete the task class is useless. Measuring them separately keeps
the tradeoff visible to the decision instead of averaging it away.

Those counts describe the released examples, not a current powered design. A
future class-balanced suite, its task-selection record, and its inferential
basis remain in preparation and cannot support a powered claim until the
scientific decision package is complete.

## The historical statistical promotion gate

The section below describes the released 0.2.0 implementation and preserves
the methods used by the recorded worked examples. It is historical, not the
current authority for a new powered claim. The experimental inference note and
its later complete package must be reviewed before a successor rule can be
selected.

The intellectual core of the lab is the promotion gate. It turns per-task
outcomes into a go/no-go decision using methods chosen for what small-n
evaluation actually is, each with limits stated plainly.

- Wilson score intervals for proportions. Reliability is a count of successes
  over a small number of trials. At small n the textbook Wald interval is badly
  miscalibrated. It under-covers, and near 0% or 100% it produces bounds outside
  [0, 1] or collapses to zero width. The Wilson interval inverts the score test,
  stays inside [0, 1], and keeps sensible coverage at the extremes where
  reliability results tend to sit. It is implemented directly, with no SciPy
  dependency. Its limit: it is still a normal approximation, it can be asymmetric
  and mildly conservative at very small n, and it assumes independent trials. It
  is also honest about scope. A rate pooled over a fixed, curated battery of
  heterogeneous tasks is a suite-level summary of run-to-run behavior on those
  tasks, not an inference about reliability on unseen tasks. For anything finer,
  per-task or stratified rates are the honest granularity.
- Seeded bootstrap confidence intervals. For statistics with no clean closed
  form, such as the mean paired success delta between a candidate and the
  incumbent, the lab resamples the observed outcomes to get a distribution-free
  interval (2000 iterations, fixed seed). The seed is fixed on purpose. The
  reported interval is then exactly reproducible by anyone who re-runs it, which
  makes reproducibility a property of the evidence rather than a claim about it.
  Its limits: the bootstrap cannot invent information the sample does not
  contain, so at small n the interval is wide, which is honest rather than a
  defect. It is also unreliable for extreme tail percentiles, so tail latency is
  reported as raw order statistics rather than bootstrapped.
- A paired sign test, reported alongside. Because each task is run on both the
  candidate and the incumbent, the comparison is naturally paired: same task,
  same difficulty. The two-sided sign test uses only the direction of each
  per-task difference. It assumes nothing about the distribution of scores and is
  robust to outliers and to the fact that task scores are not interval-scaled.
  This lab reports it as a companion diagnostic. It is not the gate's decision
  rule. The binding significance criterion is the bootstrap interval described
  below.

These compose into a conjunctive, fail-closed gate. A candidate is promoted only
if every one of five criteria holds.

1. `beats_incumbent_beyond_band`: the mean paired success delta exceeds the
   tolerance band (default 0.10) AND the bootstrap CI lower bound is above zero.
   A mean gain that clears the band is not enough on its own. The interval must
   also exclude zero.
2. `reliability_class_ge_incumbent`: the candidate's tool-call reliability class
   is at least the incumbent's.
3. `latency_slo`: the candidate meets the local latency budget.
4. `no_regression_must_not_break`: the candidate is at least the incumbent on
   every task in a designated must-not-break subset.
5. `replicates_ge_2`: at least two replicates (three preferred).

Any single failure is a no-go. A criterion that cannot be evaluated is not a
pass, and therefore is also a no-go. The gate is deliberately biased toward the
incumbent because the costs are asymmetric. A bad promotion silently degrades
every downstream task. A missed promotion costs only a delay.

The two recorded decisions below are both no-go. The figure shows why: the
representative case's interval touches zero, and the live case's interval sits
entirely below zero.

![Promotion gate decision for both worked examples: paired success delta, candidate minus incumbent, with the seeded bootstrap confidence interval. The representative case has a positive mean that clears the band but a confidence interval whose lower bound is zero. The live case has a negative mean with the whole interval below zero. Both are no-go.](figures/promotion-gate-decision.svg)

## Worked example one: the gate caught a false positive

The strongest thing the lab demonstrates is a refusal that a naive process would
have gotten wrong.

Run on representative data, the capability layer ranked a 32B candidate
(`qwen2.5-coder-32b`) above the incumbent: 82% overall against 70%, and a role
recommendation to switch, with a margin of +0.12 flagged "confident." A
capability-only decision would flip the default right there. The candidate is
bigger, newer, and scores higher on the table.

![Representative capability by task-class, incumbent versus the 32B candidate, across fix-failing-test, multi-file refactor, repo reasoning, and small edit, plus an overall bar. The candidate is at or above the incumbent in every class and higher overall. Produced with a stubbed harness on representative data.](figures/capability-by-class.svg)

The promotion gate, applied to the same kind of paired data, returned NO-GO. It
failed `beats_incumbent_beyond_band`. The mean paired delta cleared the
tolerance band, but the seeded bootstrap CI lower bound sat at zero, so the gain
was not statistically distinguishable from no gain at that sample size. The
significance floor (a bootstrap lower bound strictly above zero) is exactly the
check a capability ranking alone does not make. A higher mean is not the same as
a real difference. The gate is what tells them apart.

The valuable output here is not a performance improvement. There was none, and
the lab claims none. The valuable output is a defensible decision: a bigger,
newer model was declined on stated, reproducible evidence rather than adopted on
enthusiasm. In evaluation work a well-grounded no-go is a first-class result.

Both the capability ranking and the gate behavior above were produced with a
stubbed editing harness on representative data. They demonstrate how the gate is
designed to behave, not a measured live model comparison. That distinction is
kept explicit on purpose. See `evidence/false-positive-representative.md`.

## Worked example two: a live no-go, with its caveats

One promotion run was executed end to end over the real editing harness and the
real gateway (`qwen2.5-coder-32b` as candidate against the local incumbent, four
tasks, two replicates). It returned NO-GO, failing three criteria:

- `beats_incumbent_beyond_band`: paired delta -0.500, bootstrap CI lower bound
  -0.875. The candidate was significantly worse, not better.
- `latency_slo`: n/a. The candidate produced no successes, so there was no
  latency to measure, and a criterion that cannot be evaluated is not a pass.
- `no_regression_must_not_break`: the candidate regressed on must-not-break
  tasks.

The honest caveat that must travel with this run: the candidate's 0% task
success was partly a transport artifact, not purely model quality. The local
Ollama adapter was dropping tool calls at the time, which the harness records as
`transport_blocked` rather than as a model failure. So this no-go was partly a
transport limitation of the local path, not a clean statement about the model.
That transport limitation was later addressed upstream in the gateway, and the
lab's `transport_blocked` classification for that path has since been retired.
This run is also small-n: four tasks by two replicates. It is a demonstration
that the gate refuses a worse candidate with the interval entirely below zero,
not a benchmark result. See `evidence/live-smoke-no-go.md`.

## Alignment-relevant governance built into the harness

The harness carries controls that are evaluation-integrity and safety
mechanisms, not hygiene, because each one protects a specific property that a
promotion decision depends on.

- Fail-closed model-provenance hash verification. Before an evaluation runs, the
  model descriptor is checked against a content hash in a provenance manifest. A
  mismatch refuses the run. This guarantees the thing measured is the thing
  named, so a result can be attributed to a known artifact.
- Default-deny command allowlisting. The harness can execute only commands on an
  explicit allowlist. Everything else is denied. This bounds what an
  agent-under-evaluation can do to the host and keeps the harness from being an
  open execution surface.
- Per-task workspace isolation. Each task is materialized into its own throwaway
  workspace, so runs cannot contaminate each other. Isolation removes state
  leakage between runs, which is a necessary condition for treating repeated runs
  as independent trials. It does not by itself make heterogeneous tasks
  exchangeable draws from a population. That is a separate, weaker assumption the
  pooled statistics rest on, and the statistics section flags it.
- Explicit egress boundaries. There is a defined, tested egress policy primitive
  that makes the outbound surface of a run explicit and reviewable. It is a
  tested primitive, not OS-level or network-level enforcement, and it is stated
  that way. It does not stop an attacker with host access.
- A no-commit fitness gate. An architectural fitness function enforces that the
  measurement layer never auto-commits to the repositories it evaluates. The lab
  produces evidence, not commits. This preserves non-interference and clean
  provenance.

## Honest limitations

This section is the point, not a disclaimer.

- The lab measures methodology discipline and produces promotion evidence. It
  does not demonstrate a measured downstream improvement in agent task
  performance. No such delta is claimed. The honest story is discipline,
  traceability, provenance, and enforcement.
- The capability tables and the false-positive worked example were produced with
  a stubbed editing harness on representative data. They show the design behavior
  of the gate, not a live model A/B. The one live promotion run is small-n (four
  tasks, two replicates) and carried a transport artifact, described above.
- A full custom autonomous coding-agent loop is designed and planned only, and
  ADR-gated. It is not running.
- The egress boundary is a tested primitive, not enforced at the OS or network
  level.
- The corpus is small: 12 reliability and 20 capability tasks. The gate is honest
  about the wide intervals that small n implies. These suites are a disciplined
  instrument, not a frontier benchmark. The instrument is built so that adding
  tasks is cheap, which is the whole reason to build custom tooling rather than
  script one-off runs. The corpus size reflects the time available to a single
  operator, not a ceiling in the tooling.
- This is self-directed research on personal infrastructure by a single operator,
  built unfunded and on personal time alongside a full-time teaching load. It is
  not employment, client work, a staffed team, or a product. That is rather the
  point. This is what evidence-gated evaluation discipline looks like when one
  person builds it out of pocket, and the obvious next step is doing this work
  resourced and full-time.

## Reproducing the figures and numbers

The two figures in `figures/` are generated from `evidence/data.json`, which
holds the sanitized recorded values behind both worked examples. Regenerate them
with the standard library only, no third-party dependencies:

```bash
python3 figures/generate.py
```

The reported bootstrap intervals are seeded (2000 iterations, fixed seed 12345)
so that anyone who re-runs the evaluation gets the same interval. Reproducibility
is a property of the evidence, not a claim about it.

## Scope and provenance

This was built solo, unfunded, on personal time. That is signal of
self-direction, not an excuse, and not the headline. This repository is an
extracted standalone artifact. The full system it comes from coordinates with
separately-maintained private services (an OpenAI-compatible LLM gateway for
transport and control, an editing harness under evaluation, and an operational
trace/context state service), which are described here functionally rather than
exposed.

## Why this transfers

Scale changes the sample size and the infrastructure. It does not change the
validity requirements. Separating measurement from the measured, composing
calibrated small-n statistics into an auditable fail-closed go/no-go, and
building provenance, isolation, and fail-closed integrity checks into the harness
are exactly the disciplines that frontier-scale evaluation depends on. They are
the same reasons a serious lab can trust a promotion decision instead of a vibe.

## License

Apache-2.0. See `LICENSE`.
