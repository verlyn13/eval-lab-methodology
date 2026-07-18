# E4 grader-validation statistical analysis plan

## Metadata and claim boundary

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 0.2.0-candidate.2
- **Status:** Candidate protocol — design decisions incorporated; not preregistered; no observations authorized.
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

- Begin with at least 160 authored output records across four registered task classes.
- The construction target is at least 80 adjudicated-positive and 80 adjudicated-negative records.
- Each class includes satisfying, clearly non-satisfying, boundary, and near-miss records.
- Boundary categories, minimum effective adjudicated counts per stratum, deterministic top-up
  rules, and the ambiguity threshold must be fixed before authoring starts.
- A top-up appends a new retained record under the predeclared rule; it never replaces or suppresses
  a reviewed record. The final registered corpus may therefore exceed 160 records.
- Corpus records, task contracts, author-intended labels, failure/boundary strata, and the machine
  grader are frozen by exact digest before reviewer assignment.
- Construction cannot use outputs from E1 or a powered campaign.

The corpus is a versioned, extensible validation instrument. Suite growth requires a new corpus
version and revalidation rather than silently carrying forward the prior admission.

Registration remains blocked until the boundary taxonomy, per-stratum minimums, top-up rule, and
ambiguity threshold are populated with exact values and reviewed.

## Independent labels and adjudication

Two qualified reviewers independently label every record without seeing the machine grade, the
other reviewer's label, or the author-intended target. Reviewer order is randomized. Reviewers
record a binary label, rationale code, and ambiguity flag.

Agreement becomes the provisional gold label. A disagreement or any ambiguity flag goes to a third
adjudicator, who sees the task contract and both rationales but remains blinded to the machine
grade. The adjudicated label is the analysis gold label. The author-intent-versus-adjudicated-gold
disagreement rate and ambiguity rate are reported as contract-ambiguity diagnostics.

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
or unregistered top-up makes E4 `NOT_EVALUABLE`. E4 stops immediately on unblinding or
evidence-integrity failure. Before registration, reviewers must freeze reviewer qualifications,
conflict rules, assignments, hour budget, corpus-stratum values, evidence schema, and exact public
report schema.
