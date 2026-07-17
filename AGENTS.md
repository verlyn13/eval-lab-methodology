---
title: "AGENTS.md — eval-lab-methodology (PUBLIC)"
category: charter
component: eval-lab-methodology
status: active
version: 0.2.0
last_updated: 2026-07-17
tags: [methodology, statistics, evidence-contract, identity-domain, public, quarto]
priority: high
---

# AGENTS.md — eval-lab-methodology (PUBLIC)

Read this before doing any work in this repo. The estimator/report build order —
what to build here and in what order — lives in `PLAN.md`; this file is the
boundary and the honesty/sanitization rules that gate every commit.

**This is a PUBLIC repository.** Anything here is world-readable, and the site
**auto-publishes from `main`** — so treat every change as a public release from the
moment it lands. There is no separate publish step at which to catch a leak.

## What this repo is

The **public face** of the Agentic-Coding Evaluation Lab: the methodology write-up,
sanitized worked examples, reproducible figures, and the **infra-agnostic
statistical + reporting core** (including the Quarto reports/dashboard). It is the
citable work sample for the job search — it must stay clean, honest, and runnable
by anyone with no access to private infrastructure.

Anything here is world-readable. Treat every commit as a public release.

## Boundaries

**This repo owns:**

- The **infra-agnostic statistical + reporting core** — the estimators (Wilson,
  two-stage bootstrap, Wilcoxon, GLMM wrapper), the superiority-by-margin decision
  rule, the power simulation, and the Quarto report templates — developed and tested
  here, runnable on synthetic or sanitized data.
- The **normative identity-domain spec** (`src/eval_lab_methodology/identity_domain.py`)
  and its frozen conformance vector.
- The versioned **public evidence contract**, independent recomputation, and the
  published methodology write-up + figures + dashboard.
- The public site, which **auto-deploys from `main`** to
  <https://jvjohnson.dev/eval-lab-methodology/>.

**This repo does NOT own (must not become):**

- A router, transport, or provider registry — it holds no secrets and routes nothing.
- The working evaluation lab, its real task suite, or any real-campaign plumbing —
  those live in private infrastructure and are referred to here only functionally.
- A fork or vendored copy of the editing harness under evaluation — cite it as a
  dependency only.
- A store of raw real-run artifacts, private fixtures, or unverified numbers.

## The ecosystem and the boundary (roles)

| Component | Visibility | Role | May it appear here? |
|---|---|---|---|
| This repo (the methodology + core) | PUBLIC | Methodology + stats/report core + Quarto reports + sanitized results | — |
| The evaluation lab | PRIVATE | The working lab: real task suite, wiring to the gateway/state/editing harness, real campaigns | Only functionally as "the evaluation lab"; never by repo name |
| An OpenAI-compatible LLM gateway | PRIVATE | Transport/router; holds provider secrets | Only as "an OpenAI-compatible LLM gateway"; never by name |
| A state service | PRIVATE | Operational trace/context state, bounded retention; not the evidence authority | Only as "a state service"; never by name |
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
- Report validation independently scans every evidence key and scalar before
  rendering. Generic leak patterns remain reviewable in cleartext; private-name
  matches use only normalized SHA-256 fingerprints. Producer `public-safe`
  booleans remain required, but they are not treated as proof by themselves.
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

## Frozen / do-not-edit-in-place

- `src/eval_lab_methodology/identity_domain.py` — the normative identity-domain spec.
  Its `CONFORMANCE_IDENTITY_DOMAIN` and `CONFORMANCE_IDENTITY_DOMAIN_SHA256` are
  frozen, published values pinned by downstream parity tests. **Never edit them in
  place.** A semantic change is a new `schema_version` with a new conformance vector,
  published alongside the old one — never a mutation of the existing vector.

## Hard rules

1. **Public firewall.** Never reference private repos or private infrastructure by
   name, and never introduce private absolute paths. Describe private couplings
   **functionally** only. Merge to `main` auto-publishes, so **treat every change as
   public** and assume anything committed is world-readable immediately.
2. **No private imports.** Do not pull code, config, task fixtures, secrets, or
   identifiers from private repos into this one.
3. **Sanitization contract binds at merge time** — see the redaction list below.
   Confirm none of it appears before anything is committed.
4. **Honesty contract** — every published number traces to a produced artifact; no
   number appears that a run didn't produce. See Honesty rules below.
5. **Identity-domain freeze** — never edit the frozen conformance values in place;
   semantic changes are a new versioned conformance vector.
6. **Gate parity** — the exact merge gate below must pass locally before commit; the
   local command equals CI.

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

## Gate parity (local == CI)

The canonical merge gate — run from the repo root; CI invokes the same script and every stage must
pass before merge. Install the Python extras and the exact Quarto release named in
`.quarto-version`, then run:

```
python -m pip install '.[dev,report]' && bash scripts/run-merge-gate.sh
```

The script first refuses a missing or mismatched Quarto version, then enforces Ruff lint/format
with the version pinned in `pyproject.toml`, unit tests, both
exact-result checks, wheel containment, sample and campaign evidence validation, the full Quarto
site render, and sample/campaign report rendering. Adding a CI stage requires adding it to this
script so local and CI stay identical.

## Safe vs held commands

**Safe (run freely):** the gate and validation commands above, `unittest` discovery,
`make validate-report`, `python -m analysis.run_method_tranche --check`,
`python -m analysis.run_contract_v2 --check`, `pip wheel`, figure regeneration
(`figures/generate.py`), and local Quarto renders of synthetic-data example reports.

**Held (stop and confirm first):**

- Committing any real-run report, evidence, or figure — run the sanitization pass and
  get a human confirmation first.
- Editing the frozen identity-domain conformance values.
- Any change that could reference private repos/infra or add a private path.
- Anything that reaches private infrastructure, secrets, or the private task suite.

## What agents may / may not do here

May: develop and unit-test the stats + reporting core on synthetic data; render
example reports; sanitize and publish real results/figures; improve the write-up.

May not: import private-repo code/config/secrets; name private repos or providers;
commit raw real-run artifacts or the private task suite; publish an unverified
number.

## Truth lanes

- `PLAN.md` — the roadmap and estimator/report build order (authoritative for what to
  build here and in what sequence).
- `README.md` — the public methodology write-up and project status.

## STOP and escalate

Stop and escalate to a human maintainer before proceeding when:

- A change would (or might) leak any item on the sanitization redaction list.
- You are about to commit a real-run report/evidence/figure and cannot fully verify
  the sanitization pass.
- A change would require editing the frozen identity-domain conformance values in
  place, or otherwise mutating a published v1 conformance vector.
- The gate parity command cannot be made to pass, or CI and local disagree.
- A change would introduce a private repo name, provider account, or private absolute
  path — since merge to `main` auto-publishes, this is unrecoverable once merged.
