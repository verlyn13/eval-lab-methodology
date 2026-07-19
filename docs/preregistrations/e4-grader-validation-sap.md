# E4 grader-validation statistical analysis plan

## Metadata and claim boundary

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 0.2.0-candidate.3
- **Status:** Candidate protocol — offline design freeze implemented; not preregistered; no observations authorized.
- **Study type:** Authored-fixture instrument validation; no model or provider execution.

Counts and thresholds below are design inputs. They are not produced results, and this SAP cannot
admit the grader without a separately registered and accepted E4 result.

## Objective

E4 tests construct validity of the deterministic editing grader against independently adjudicated
human gold labels. It does not test whether a deterministic function agrees with itself.

The primary question is whether machine success/failure agrees sufficiently with the adjudicated
human interpretation of the task contract to admit the instrument for calibration studies. Because
the grader executes deterministically, disagreement principally diagnoses contract-to-test-system
fidelity, including ambiguous contracts, incomplete test oracles, and grader/harness
mis-specification. It is not described as random grader noise.

## Corpus construction

- Use four effective strata in each of four opaque registered task classes:
  `positive_clear`, `positive_boundary`, `negative_clear`, and `negative_near_miss`.
- Require at least 10 effective post-adjudication records in every class × stratum cell. This gives
  a minimum final corpus of 160 records and at least 80 adjudicated-positive and 80
  adjudicated-negative records.
- In each class, `positive_boundary` and `negative_near_miss` each contain at least two effective
  records from every registered edge category: `functional_edge`, `scope_edge`,
  `regression_edge`, and `artifact_edge`.
- A positive boundary record is intended to satisfy the contract while exercising exactly one
  registered edge. A negative near miss violates exactly one registered material contract
  dimension while intending to satisfy all others. A negative clear record plainly violates at
  least two independent material clauses.
- Authors record intended labels, strata, and edge categories. Only the adjudicated label and
  effective stratum count toward construction minima or analysis.
- A top-up appends a new retained record under the predeclared rule; it never replaces or suppresses
  a reviewed record. The final registered corpus may therefore exceed 160 records.
- After each complete adjudication wave, compute cell and edge-category deficits jointly in the
  registered class, stratum, and category order. Fill edge-category deficits first, counting each
  appended record toward its enclosing cell, then fill residual cell deficits in category
  round-robin order. Clear-cell residuals use the same canonical ordinal rule without an edge
  category. Top-up authors remain blinded to machine grades, reviewer rationales, and aggregates.
- Corpus records, task contracts, author-intended labels, failure/boundary strata, and the machine
  grader are frozen by exact digest before reviewer assignment.
- Construction cannot use outputs from E1 or a powered campaign.

The corpus is a versioned, extensible validation instrument. Suite growth requires a new corpus
version and revalidation rather than silently carrying forward the prior admission.

The generic metadata schema, construction constants, and top-up checks are repository-versioned in
[`analysis/calibration-freeze.v1.json`](../../analysis/calibration-freeze.v1.json). That synthetic
design artifact contains no authored corpus records and is not a registration or validation
result. Registration remains blocked on the actual corpus, task-contract and grader bindings,
reviewer assignments and receipts, and evidence/report schemas.

## Independent labels and adjudication

Two qualified reviewers independently label every record without seeing the machine grade, the
other reviewer's label, or the author-intended target. Reviewer order is randomized. Reviewers
record a binary label, rationale code, and ambiguity flag.

Agreement becomes the provisional gold label. A disagreement or any ambiguity flag goes to a third
adjudicator, who sees the task contract and both rationales but remains blinded to the machine
grade. The adjudicated label is the analysis gold label. The author-intent-versus-adjudicated-gold
disagreement rate and ambiguity rate are reported as contract-ambiguity diagnostics.

Two primary reviewers and one adjudicator are required. None may assess a record, task contract,
or grader behavior they authored or implemented. Each must pass a separate, non-overlapping,
frozen 16-record qualification packet with at least 15/16 agreement to its independently
established key and 8/8 on failure/near-miss cases. Qualification records do not enter E4. Keys are
frozen before assignment, and each reviewer remains blinded to their key until their response is
terminal.

## Analysis and certification granularity

Using adjudicated human label as truth and machine success as the prediction, report `TP`, `TN`,
`FP`, and `FN`, then compute:

\[
\mathrm{sensitivity}=\frac{TP}{TP+FN},\qquad
\mathrm{specificity}=\frac{TN}{TN+FP}.
\]

Certification applies to the overall adjudicated-positive population and the overall
adjudicated-negative population. Class- and stratum-specific confusion matrices are diagnostics;
their smaller denominators do not independently carry the overall Wilson-bound admission rule.

Also report positive and negative predictive values, class/stratum confusion matrices, raw reviewer
agreement, Cohen's kappa, author/adjudicator disagreement, and ambiguity. Sensitivity and
specificity receive two-sided 95% Wilson intervals.

The ambiguity numerator is the record-level union of either primary reviewer's flag, retained even
after adjudication resolves the label. Compare exact fractions without rounding. Admission
requires no unresolved ambiguity, an overall ambiguity fraction at most 0.10, and an ambiguity
fraction at most 0.20 in every class × effective-stratum cell. Author-intent disagreement remains
a reported diagnostic rather than an admission threshold.

## Admission rule

The instrument is eligible for explicit calibration admission only when all of these criteria hold:

- point sensitivity is at least 0.90;
- point specificity is at least 0.95;
- the two-sided 95% Wilson lower bound is at least 0.80 for both overall sensitivity and overall
  specificity;
- the frozen minimum effective adjudicated counts and every corpus-stratum requirement are met;
- every record has complete independent labels and any required adjudication; and
- no corpus, grader, task-contract, blinding, or byte-binding violation occurred.

The higher specificity threshold deliberately prioritizes false-pass avoidance: crediting a failure
as success can inflate a later candidate score, while a false fail is conservative. Passing this
rule does not establish validity outside the frozen suite and grader version.

## Missingness and hard stops

Any missing label, lost rationale, failed blinding check, post-assignment mutation, absent digest,
unregistered top-up, unresolved ambiguity, exceeded ambiguity limit, or exhausted construction
budget makes E4 `NOT_EVALUABLE`. E4 stops immediately on unblinding or evidence-integrity failure.
The registered ceiling is 48 person-hours across qualification, two independent reviews,
adjudication, and top-up review. It is a prospective stop rule, not measured labor evidence, and
cannot be enlarged after machine agreement is seen. Before registration, reviewers must freeze
reviewer identities, conflicts, assignments and receipt digests, actual corpus and grader bytes,
evidence schema, and exact public report schema.
