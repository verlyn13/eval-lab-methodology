# Agentic-Coding Evaluation Lab — Methodology

Public statistical methods, evidence contracts, and report tooling for comparing coding-agent
configurations. This repository is a methodology and verification project; it is not an operational
benchmark, model leaderboard, or deployment service.

## Current status

| Surface | Status | Claim boundary |
|---|---|---|
| Statistical core `0.2.0` | Repository-versioned; wheel builds locally; not tagged or published to a package registry | Preserves historical estimators and a superiority component; not authorized for a new powered claim |
| Experimental inference note | Published synthetic decision input | No successor method is selected |
| Evidence Contract B `2.0.0-draft.1` | Immutable repository-only draft with a frozen delivery manifest | Synthetic conformance only; recomputes `NOT_EVALUABLE`; no operational authority |
| Identity domain v1 | Frozen structural specification and conformance vector | Matching hashes are necessary, not sufficient, for numerical comparability |
| Real campaign evidence | One historical four-task smoke summary with a transport confound; raw attempt records are not published | Not independently recomputable, not a benchmark, and not a scientifically admissible powered comparison |

There is currently no defensible powered real-model result and no promotion recommendation. See
[STATUS.md](STATUS.md) for the readiness boundary and remaining work.

## What is implemented

- A dependency-free Python core with Wilson intervals, a seeded percentile bootstrap, a two-sided
  paired sign test, and a superiority-by-margin helper.
- Evidence Contract `1.1.0` and a parameterized Quarto report for historical and synthetic examples.
- A frozen identity-domain v1 field set, canonicalization rule, and cross-implementation vector.
- An executable experimental methods note with committed, byte-checked synthetic results.
- Contract B `2.0.0-draft.1`, which validates a synthetic registration-to-report join, independently
  recomputes the result, and refuses mismatched or incomplete evidence.
- Recursive evidence-input scanning in the parameterized report path and a separately bound
  Contract B publication-safety scanner.

The public core's historical superiority helper returns true only when the bootstrap confidence
interval lower bound is strictly greater than the supplied margin. That implementation is preserved
for reproducibility; it is not the selected rule for future powered campaigns.

## What is not implemented or claimed

- No accepted successor estimand, enforcing test, replicate policy, or minimum practically
  important benefit.
- No validated operating characteristics for the intended class-balanced design.
- No operational registration signer, trusted timestamp path, or production owner-receipt join.
- No validated grader study, governed 40-task suite, A/A calibration, or powered campaign.
- No evidence that a candidate model or harness improves real task performance.

## Public artifacts

- [Methodology site](https://jvjohnson.dev/eval-lab-methodology/)
- [Experimental inference note](reports/experimental-inference-note.qmd)
- [Contract B v2 refusal example](reports/contract-v2-not-evaluable.qmd)
- [Identity-domain specification](identity-domain.qmd)
- [Delivery manifest](evidence/contract-v2/delivery-manifest.v1.json)
- [Roadmap](PLAN.md)

The Contract B verifier and report renderer are under `analysis/contract_v2/`. They are deliberately
outside the installable `0.2.0` wheel. The delivery manifest pins their source commit and tree,
relative layout, dependencies, file digests, aggregate digests, conformance fixture, and golden
report. Downstream consumers must verify those exact bytes and preserve the layout.

## Evidence and provenance rules

- Published numbers must trace to committed evidence bytes, with the retained raw-versus-summary
  boundary stated.
- Synthetic, representative, smoke, and measured evidence remain distinct.
- A copied fact retains its originating observer and receipt; copying never upgrades provenance.
- Missing or contradictory inputs produce refusal, not a best-effort decision.
- The parameterized evidence-report path recursively re-scans evidence inputs; Contract B checks
  its bound public payload separately. Neither control is a whole-repository scanner.

The repository contains two historical worked examples:

- a representative, stubbed-harness refusal example that demonstrates plumbing only; and
- a four-task, two-replicate live smoke run with a known transport confound.

Neither is a current statistical result. The smoke artifact retains summary values rather than the
raw per-attempt outcomes needed for independent interval recomputation. Their recorded values are
historical artifacts, not evidence for model selection.

## Identity-domain scope

Identity-domain equality prevents known stack changes from being silently read as model effects. The
v1 preimage includes runtime, image, hardware, model-artifact, and launch fields. It does not prove
that all residual serving state is controlled. Prefix-cache state, batch context, session position,
decoding parameters, harness version, and other unrecorded state can still affect numerics. A
matching v1 hash is therefore a necessary admission check, not a complete reproducibility guarantee.
The frozen source's broader historical wording is corrected in [ERRATA.md](ERRATA.md); v1 bytes and
the conformance vector remain unchanged.

Frozen v1 constants and the conformance vector are never changed in place. A wider field set requires
a new schema version.

## Repository boundary

This public repository owns infra-agnostic methods, schemas, independent recomputation, sanitized
reports, and public specifications. Private systems own task fixtures, execution, model transport,
editing, deployment lifecycle, operational traces, and evidence custody. Private identifiers,
endpoints, credentials, raw model responses, and task fixtures do not belong here.

## Verify locally

```bash
python -m pip install '.[dev]'
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m analysis.run_method_tranche --check
PYTHONPATH=src python -m analysis.run_contract_v2 --check
make validate-report EVIDENCE=evidence/sample-lab-report.json
python -m pip wheel . --no-deps -w dist/
```

Quarto is also required to render the site and HTML reports. CI runs tests, exact-result checks,
wheel containment, report validation, and site rendering before publication.

## Next milestones

1. Select and justify the successor scientific design, including its assumptions and operating
   characteristics.
2. Complete operational owner contracts and registration verification outside this repository.
3. Validate the grader, task suite, dependence assumptions, and apparatus noise floor.
4. Run a registered, powered local campaign and publish a sanitized independently recomputable
   report.

## License

Apache-2.0. See [LICENSE](LICENSE).
