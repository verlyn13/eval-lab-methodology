# Roadmap — the statistical + reporting core

This repository is the methodology write-up plus an infra-agnostic **statistical
and reporting core** for evidence-gated model/harness promotion — real, tested
code plus a Quarto report — that anyone can run with no access to private
infrastructure. Read `AGENTS.md` first; it defines the boundary and the honesty and
sanitization rules that gate every commit here. This file records what has landed
and what remains to build, in order.

Everything here is world-readable. Treat every commit as a public release.

## Where things stand

Landed and working:

- The methodology write-up (`README.md`), with a worked false-positive no-go and a
  worked live no-go, both carrying real recorded numbers.
- `evidence/data.json` — the sanitized values the figures render from — and two
  prose worked-example write-ups.
- `figures/generate.py` — a standard-library SVG generator that renders the figures
  from `evidence/data.json`. It performs **no statistics**; it draws numbers that
  already exist.
- **Build-order step 1 is done.** The statistical core is importable, tested code
  (`src/eval_lab_methodology/`, version 0.2.0), with packaging (`pyproject.toml`
  plus the standard-library build backend) and CI that runs the unit tests and
  builds the wheel on every push and pull request.
- **Build-order step 2 is done.** The evidence-JSON schema is versioned
  (`evidence/schema.json`, schema version 1.1.0) and carries raw per-task
  outcomes; the Quarto report renders a full campaign from an evidence JSON; and
  a synthetic-data example ships with it (`evidence/sample-lab-report.json` and
  the synthetic campaign under `evidence/campaigns/`). The report and site are
  live at <https://jvjohnson.dev/eval-lab-methodology/>, auto-deployed from
  `main`.
- **A landed normative addition:** the identity-domain spec
  (`src/eval_lab_methodology/identity_domain.py`, documented in
  `identity-domain.qmd`) defines how a model identity domain is canonicalized so
  results are comparable across implementations. It ships with a **frozen
  conformance vector** — `CONFORMANCE_IDENTITY_DOMAIN` and its published hash
  `CONFORMANCE_IDENTITY_DOMAIN_SHA256` — that cross-implementation parity tests
  pin. See `AGENTS.md` for the rule: the vector is never edited in place; a spec
  change is a new schema version with a new vector.

Still to build (the remaining roadmap):

- A runnable `example/` a reviewer can clone and run against an open model or a
  public API (build-order step 3).
- Contributed sanitized real-run results and rendered reports (build-order
  step 4).
- One open packaging question: whether to publish a dev-extra lockfile so the
  development environment is pinned, not only the runtime dependencies.

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
