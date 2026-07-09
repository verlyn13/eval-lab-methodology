# Roadmap — the statistical + reporting core

This repository is today a methodology write-up with reproducible figures. This
file is the roadmap for what it becomes: an infra-agnostic **statistical and
reporting core** for evidence-gated model/harness promotion — real, tested code
plus a Quarto report — that anyone can run with no access to private
infrastructure. Read `AGENTS.md` first; it defines the boundary and the honesty and
sanitization rules that gate every commit here. This file says what to build and in
what order.

Everything here is world-readable. Treat every commit as a public release.

## Where things stand

Present and working:

- The methodology write-up (`README.md`), with a worked false-positive no-go and a
  worked live no-go, both carrying real recorded numbers.
- `evidence/data.json` — the sanitized values the figures render from — and two
  prose worked-example write-ups.
- `figures/generate.py` — a standard-library SVG generator that renders the figures
  from `evidence/data.json`. It performs **no statistics**; it draws numbers that
  already exist.

Not yet built (the work this roadmap covers):

- The statistical core as importable, tested code (today the estimators exist only
  as prose in the write-up).
- A versioned evidence-JSON schema that carries **raw per-task outcomes**, so every
  published interval is recomputable from the artifact rather than asserted.
- A Quarto report that renders a full campaign from an evidence JSON.
- A runnable `example/` a reviewer can clone and run against an open model or a
  public API.
- Packaging, a lockfile, and CI.

## The target

An importable package that implements, on run-level binary outcomes with replicates
nested in tasks:

- **Wilson score intervals** for the marginal per-model, per-class proportions.
- A **two-stage (hierarchical) bootstrap** — resample tasks, then resample
  replicates within each task — so within-task replicate noise is propagated rather
  than collapsed. Seeded.
- **Wilcoxon signed-rank** on the per-task deltas — magnitude-aware, replacing the
  direction-only sign test as the primary paired test.
- A **mixed-effects logistic regression (GLMM)** wrapper, `success ~ model + (1 |
  task)`, as the primary model that uses every run.
- A **superiority-by-margin** decision rule: promote iff the interval's lower bound
  exceeds the practically-important margin δ0. This is a single clean rule.
- A **simulation-based power analysis** — power vs number of tasks at a few
  replicate counts — so run sizes are chosen, not guessed.
- Optional, later: a Bayesian posterior `P(Δ > δ0)` with a ROPE, and an IRT
  (Rasch / 2PL) treatment of task difficulty vs model ability.

Plus unit tests against textbook cases, the Quarto report, the runnable `example/`,
and CI.

## The evidence-JSON contract

One schema is the interface between the analysis code, the reports, and any
deployment that produces data. It is a superset of today's `evidence/data.json`:

- **Raw per-task outcome arrays** (per model, per task, per replicate), so the
  estimators are reproducible from published data.
- A **reproducibility manifest**: seeds, task-set hash, model versions, and — when a
  run used real hardware — the hardware type, cost, and a **pre-flight
  model-resolution result** confirming each model actually served (not a silent
  fallback).

The schema is versioned and lives in this repo (`evidence/schema.json`). Both the
estimators and the Quarto report validate against it. Synthetic-data instances are
fully public; any real-run instance is sanitized before it lands here.

## Build order

1. **Core + tests.** Stand up the package; implement Wilson, the two-stage
   bootstrap, Wilcoxon, the GLMM wrapper, the superiority-by-margin rule, and the
   power simulation. Unit-test each against known cases. Add packaging, a lockfile,
   and CI. Acceptance: `pip install` + `pytest` green from a clean clone.
2. **Evidence schema + Quarto report.** Define `evidence/schema.json`; build the
   report (`report.qmd` + `_quarto.yml`) rendering, per campaign: the manifest, the
   capability table with Wilson CIs, a per-class forest plot, Δ with the δ0 margin
   line and its interval, the reliability/latency/cost distributions, the power
   curve, and the decision under the pre-registered rule. Ship a **synthetic-data
   example report** — fully public, no scrub needed. Acceptance: `quarto render`
   produces the report from a synthetic evidence JSON.
3. **Runnable example.** A minimal reproducible eval against an open-source model or
   a public API, with a lockfile, a "how to run," and seeded output. Acceptance: it
   runs from a clean clone and reproduces its published numbers.
4. **Real-run results (contributed).** Sanitized results and rendered reports from a
   real hardware campaign, produced by the private deployment that this core serves,
   arrive after the deployment's own review and the sanitization pass in `AGENTS.md`.
   They augment the synthetic example so the lead example becomes a real result.

## Two invariants the roadmap must preserve

These are recorded facts about the worked examples. Contributors must not silently
change them:

- The paired **sign test is two-sided and reported alongside** the decision — it
  does **not** gate promotion. The significance mechanism in the worked gate is the
  **seeded bootstrap CI lower bound relative to zero (and, going forward, to the
  margin)**. Do not describe the sign test as one-sided or as the gating test.
- The live worked example has **no latency overrun**. Its `latency_slo` is **n/a**
  because the candidate produced zero successes, so there was no latency to
  measure — the fail-closed "non-evaluable is not a pass" rule. The SLO itself is
  60,000 ms per success.

## Upgrade forward; do not rewrite history

The write-up's recorded results were computed with a direction-only **sign test**
and a **single-stage** seeded percentile bootstrap. The estimators above (two-stage
bootstrap, Wilcoxon, GLMM) are **additions**, applied to new analyses and labeled as
such. Do not retroactively relabel the published examples as if they used methods
they did not. Adding capability never licenses restating past results as stronger
than they were — the honesty rules in `AGENTS.md` are the point of this artifact.
