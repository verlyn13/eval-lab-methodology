# Roadmap — public methodology and independent verification

This repository is the public methodology authority for an evidence-gated
model-and-harness evaluation system. It owns statistical specifications,
versioned public evidence contracts, independent recomputation, and sanitized
human-readable reports. It does not own model routing, editing, deployment,
private campaign custody, or operational trace storage. Read `AGENTS.md` first:
every commit is world-readable and every merge to `main` is a publication act.

## Current status

### Repository-versioned and historical

- The dependency-free `eval_lab_methodology` core is versioned **0.2.0** in the
  repository and builds as a wheel. It has no Git tag, GitHub release, or
  package-registry publication. Its content hash and frozen identity-domain
  conformance vector are public compatibility contracts.
- Evidence Contract 1.1.0, the parameterized Quarto report, and synthetic
  example reports are live at <https://jvjohnson.dev/eval-lab-methodology/>.
- The repository package preserves the estimators and superiority component
  used by the historical report path: Wilson intervals, a seeded percentile
  bootstrap, a reported-only paired sign test, and a `CI lower bound > margin`
  rule. The broader historical deployment decision is not implemented as one
  public-core function.
- Those methods are **historical implementation truth**, not authorization for
  a new powered scientific claim.

### Experimental and not selected

- `reports/experimental-inference-note.qmd` is a synthetic, executable review
  of candidate finite-suite constructions. It is decision input, not a ruling.
- Its implementation lives under `analysis/_method_tranche/`, outside the
  installable package and outside the 0.2.0 content hash.
- The committed results artifact is regenerated and compared byte-for-byte in
  CI. Exact computation is therefore reproducible; inferential validity still
  depends on the stated design and assumptions.
- No enforcing test, replicate policy, or minimum practically important
  benefit has been selected for the next contract. Powered promotion remains
  unavailable until that coupled decision is made from a complete package.
- Contract B `2.0.0-draft.1` is an immutable, repository-only normative draft
  beside v1. It binds synthetic registration, reveal, schedule, attempts,
  attrition, copied observation provenance, analysis, decision, and report
  records and independently recomputes `NOT_EVALUABLE`. Its verifier, report
  renderer, and publication-safety scanner are bound by an ordered file
  manifest and aggregate digest. It is unreleased, outside repository package 0.2.0,
  operationally non-authoritative, and selects no method.
- Its canonical delivery manifest freezes the exact repository layout and bytes
  needed for hash-checked downstream mirroring, plus the source commit/tree,
  unchanged core identity, runtime dependency, and synthetic conformance pair.
  This is a repository delivery contract, not a package release or operational
  adoption; the wheel-buildable 0.2.0 package contents remain unchanged.
- Its synthetic observation cardinality is one Aider-owner descriptor-validation
  receipt and one lab-owned completion receipt per attempt; one distinct gateway
  open receipt, zero or more gateway call receipts, and one distinct gateway
  closure receipt per invocation. Zero calls are admissible only for a retained
  pre-dispatch failure; fallback is forbidden. The closure binds the open
  receipt, count, ordered request IDs, and ordered owner call receipts. Actual
  request-attempt counts and vectors remain gateway-owned. All owner receipt
  schemas and provenance classes are explicitly unratified fixtures pending
  frozen owner contracts.
- Its registry binding uses the actual `eval-registry.registration-receipt.v1`
  exact-byte and domain-separation contracts. Because the registry is at D2
  scaffolding only, the copied verification result is non-authoritative and the
  synthetic packet refuses signer, signature, or TSA authority.

## Scientific decision package still required

The experimental note narrows the problem but deliberately leaves these items
open:

1. **Estimand and design.** State whether the target is a fixed finite suite or
   a task superpopulation; define the four-class weighting; define arm-order
   assignment; and state the unit and source of replication.
2. **Applicable validity argument.** Establish a theorem or calibrated design
   for the actual class-balanced, paired, potentially non-identically
   distributed task setting. Results for randomized treatment assignment do not
   automatically validate arm-order randomization.
3. **Nuisance-boundary control.** Replace the current finite `0.01` grid
   judgment with a justified continuous-boundary argument or an explicitly
   conservative bound.
4. **Dependence.** Bound cross-task correlation induced by shared serving state,
   session-by-arm interactions, batch composition, and prefix caching. Retain
   session and task-pair identifiers so the assumption is auditable.
5. **Level-matched comparison.** Compare candidate procedures at the same
   demonstrated Type I level; do not attribute unmatched power gaps to one
   mechanism.
6. **Replicate operating characteristics.** Extend the one-replicate synthetic
   calculations to the registered two- and three-replicate lattices, with a
   deployment-grounded replicate interpretation.
7. **Bounded-mean alternative.** Complete the authorized bounded-mean/betting
   interval frontier and compare its assumptions and operating characteristics.
8. **Outcome and missingness.** Fix the grader definition, measurement-error
   study, retry/error/timeout policy, attrition table, and protected-task rule.
9. **Practical benefit.** Justify any nonzero margin from calibration,
   feasibility, and cost/benefit evidence; a preregistered arbitrary constant is
   not a scientific justification.
10. **Independent recomputation.** Define Contract v2 so the public core derives
    the result and decision from raw records, refusing any producer claim that
    does not match exactly.

Until these are resolved, the scientifically correct outcome is
`NOT_EVALUABLE`, not promotion.

## Delivery roadmap

### Step 1 — publish the experimental inference note

- Keep candidate code repository-only and keep package version 0.2.0 unchanged.
- Render the note on the public site with a plain-language result card.
- Verify the committed synthetic result bytes in tests and CI.
- Record limitations and disagreements without selecting a method.

Acceptance: full unit suite, byte-for-byte result check, evidence-report
validation, wheel inspection, Quarto render, and public-boundary review are all
green. A merge is a separate reviewed publication act.

### Step 2 — Contract v2 and independent verifier

Add a new immutable contract beside v1. It must represent the analysis plan,
registration binding, assignment schedule, raw attempts and attrition,
provenance-preserving observations, analysis result, and decision receipt. The
public implementation recomputes the enforcing result from raw records and
refuses on any mismatch, stale version, missing receipt, or provenance upgrade.

Acceptance: a fully synthetic v2 campaign renders a human report, exact
recomputation agrees bit-for-bit, and mutation tests demonstrate refusal. This
step records the selected method only after the coupled scientific ruling; it
must not choose that method itself.

Draft checkpoint: `2.0.0-draft.1` exercises the complete structural join and
the fail-closed outcome while method authority is held. Adoption and any
non-`NOT_EVALUABLE` decision semantics require a new reviewed contract version;
the draft is never edited in place after publication.

### Step 3 — calibrated scientific design

Complete grader validation, the frozen 40-task balanced suite and selection
record, the independence/noise-floor study, and operating-characteristic
simulation for the actual rule. Publish sanitized method artifacts only after
their originating evidence and registration receipts are independently
verifiable.

Acceptance: measured Type I error, power, dependence sensitivity, feasibility,
grader agreement, and residual threats are reported for the exact planned
design. Simulation is not a substitute for the empirical calibration inputs it
claims to use.

### Step 4 — reproducible public example

Provide a clone-and-run, zero-cost example using an open model or public-safe
synthetic fixture. It must exercise registration, observation joins,
recomputation, refusal, and report rendering without private infrastructure.

### Step 5 — sanitized real campaign

Accept a real campaign only after the producing systems satisfy their own
charters and the public boundary is independently scanned. The report must name
the finite target, assumptions, operating characteristics, attrition, prior
attempt count, identity domain, and residual validity threats. A no-go or
not-evaluable result is a first-class publishable outcome.

## Stable public contract

The versioned evidence contract is the interface between private producers and
this public verifier. Copies preserve the originating receipt and provenance;
no plane may upgrade an attested value to measured. Frozen v1 constants are
never edited in place. Any incompatible semantics require a new schema version,
new conformance fixtures, and a versioned package release.

## Historical invariants

The worked examples must remain described exactly as they were computed:

- the paired sign test is two-sided and reported only;
- the historical gate uses the seeded single-stage bootstrap lower bound;
- the live worked example's latency criterion is `n/a`, not an overrun; and
- representative or synthetic values are never relabeled as measured results.

New methods apply prospectively. They do not rewrite old evidence or strengthen
old claims.
