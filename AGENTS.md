# AGENTS.md — eval-lab-methodology (PUBLIC)

Read this before doing any work in this repo. The estimator/report build order —
what to build here and in what order — lives in `PLAN.md`; this file is the
boundary and the honesty/sanitization rules that gate every commit.

## What this repo is

The **public face** of the Agentic-Coding Evaluation Lab: the methodology write-up,
sanitized worked examples, reproducible figures, and the **infra-agnostic
statistical + reporting core** (including the Quarto reports/dashboard). It is the
citable work sample for the job search — it must stay clean, honest, and runnable
by anyone with no access to private infrastructure.

Anything here is world-readable. Treat every commit as a public release.

## The ecosystem and the boundary (roles)

| Component | Visibility | Role | May it appear here? |
|---|---|---|---|
| This repo (the methodology + core) | PUBLIC | Methodology + stats/report core + Quarto reports + sanitized results | — |
| The evaluation lab | PRIVATE | The working lab: real task suite, wiring to the gateway/state/editing harness, real campaigns | Only functionally as "the evaluation lab"; never by repo name |
| An OpenAI-compatible LLM gateway | PRIVATE | Transport/router; holds provider secrets | Only as "an OpenAI-compatible LLM gateway"; never by name |
| A state service | PRIVATE | Durable run/evidence state | Only as "a state service"; never by name |
| The editing harness (third-party OSS) | third-party OSS | The editing harness under evaluation | Cite as a dependency; do not fork/vendor |

Do **not** pull code, config, task fixtures, or identifiers from the private repos
into this one. Describe private couplings **functionally**, never by name.

## Where the work lives (dependency direction)

Public core ← private deployment:

- The **infra-agnostic statistical + reporting core** — the estimators (Wilson,
  two-stage bootstrap, Wilcoxon, GLMM wrapper), the superiority-by-margin decision
  rule, the power simulation, and the Quarto report templates — is developed and
  tested **here**, runnable on **synthetic or sanitized data**.
- The **private deployment (the evaluation lab)** imports/mirrors that core, wires it
  to the real gateway/state/editing harness and the real (private) task suite, runs
  real campaigns, and **publishes back sanitized results + rendered reports** here.

So: statistics, decision logic, power analysis, and reporting are public and
first-class; the plumbing, secrets, and the real task fixtures stay private.

## Quarto reports/dashboard (they belong here)

- The Quarto project lives in this repo and renders from an evidence JSON (the same
  pattern as `figures/generate.py` regenerating the SVGs from `evidence/data.json`).
- **Synthetic-data example reports:** fully public, no scrub needed.
- **Real-run reports:** run the sanitization pass below **before** committing. The
  report shows the statistics, the decision, the curves, and a reproducibility
  manifest (seeds, task-set hash, model versions) — **not** the plumbing.
- The site **auto-deploys from `main`** via `.github/workflows/deploy-pages.yml`
  to <https://jvjohnson.dev/eval-lab-methodology/>. Every merge to `main` is an
  immediate public publication — there is no separate publish step at which to
  catch a leak — so the sanitization contract below binds **at merge time**.

## The identity-domain spec is normative

`src/eval_lab_methodology/identity_domain.py` is a **normative
cross-implementation spec**, not just library code: independent implementations
canonicalize identity domains to byte-for-byte parity with it.
`CONFORMANCE_IDENTITY_DOMAIN` and `CONFORMANCE_IDENTITY_DOMAIN_SHA256` are frozen
published values that downstream parity tests pin — **never edit them in place**.
A change to the spec's semantics is a **new `schema_version` (v2) with a new
conformance vector**, published alongside the old one, never a mutation of v1.

## Sanitization contract (hard requirement — the redaction list)

Before anything is committed, confirm NONE of these appear (files, filenames, and
git history):

- Secrets, tokens, API keys, or secret file paths.
- Real hostnames, domains, IPs, endpoints, or internal infra identifiers
  (`localhost:8811` is acceptable as an illustrative default; real hosts are not).
- Provider account names/IDs; name providers only as generic "an OpenAI-compatible
  gateway / provider."
- GPU-cloud pod IDs, endpoints, object keys, bucket names, or billing/cost IDs.
- The private task-suite fixtures themselves — **publishing them risks benchmark
  contamination** and exposes harness internals. Publish task-*class* descriptions
  and synthetic/representative examples, not the private fixtures.
- The private governance organization name or private repo names.

Vendor/method common nouns are fine (Python, Redis, Ollama, Wilson interval,
bootstrap, GLMM, Quarto). The public alias "Agentic-Coding Evaluation Lab" is fine.

## Honesty rules

- Every published number traces to a produced artifact (a report/figure), and to
  the claim-evidence ledger discipline. No number appears that a run didn't produce.
- Label enforcing vs advisory vs planned; state limitations (sample size, confounds)
  plainly. The honesty is the point of the artifact.
- Seeded runs make intervals reproducible; keep it that way and say so.

## Gates before commit

Run all three from the repo root; every one must pass before a commit:

- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `make validate-report EVIDENCE=evidence/sample-lab-report.json` — and repeat
  for each `evidence/campaigns/**/evidence.json` file
- `python -m pip wheel . --no-deps -w dist/`

## What agents may / may not do here

May: develop and unit-test the stats + reporting core on synthetic data; render
example reports; sanitize and publish real results/figures; improve the write-up.

May not: import private-repo code/config/secrets; name private repos or providers;
commit raw real-run artifacts or the private task suite; publish an unverified
number.
