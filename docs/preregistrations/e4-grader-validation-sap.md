# E4 grader-validation statistical analysis plan

## Metadata and claim boundary

- **Date:** 2026-07-17
- **Version:** 0.1.0-candidate.1
- **Status:** Candidate protocol — not preregistered; no observations authorized.
- **Study type:** Authored-fixture instrument validation; no model or provider execution.

All counts and thresholds below are **planned candidate values**. They are neither accepted design
parameters nor produced results.

## Objective

E4 tests construct validity of the deterministic editing grader against an independently authored
gold label. It does not test whether a deterministic function agrees with itself. Re-executed
score-path repeatability belongs to E1's outcome-digest checks.

The primary question is whether machine success/failure agrees sufficiently with the adjudicated
human interpretation of the task contract to admit the instrument for calibration studies. Passing
E4 would not validate a powered comparison or establish general validity outside the frozen task
suite and grader version.

## Planned corpus

- 160 authored output records: 40 from each of four registered task classes.
- Within each class, 20 records are authored to satisfy the task contract and 20 are authored not to
  satisfy it, for a planned 80/80 gold-label balance.
- Non-success records cover registered failure strata, including incomplete edits, out-of-scope
  edits, verification failure, setup failure, timeout, and malformed output where applicable.
- Corpus records, task contracts, expected labels, failure strata, and the machine grader are frozen
  by exact digest before either reviewer receives an assignment.
- Corpus construction cannot use outputs from the later E1 study or any powered campaign.

The corpus size and strata are candidates that require methodology review before registration.

## Independent labels and adjudication

Two qualified reviewers independently label every record without seeing the machine grade, the
other reviewer's label, or a success/non-success target. Reviewer order is randomized. Reviewers
record a binary label, rationale code, and ambiguity flag.

Agreement between reviewers becomes the provisional gold label. A disagreement or any ambiguity
flag goes to a third adjudicator, who sees the task contract and both rationales but remains blinded
to the machine grade. The adjudicated label is the analysis gold label. Reviewer identities,
qualification criteria, conflicts, assignments, and adjudications must be retained in the private
study record; only a sanitized role-level report is public.

## Analysis

Using the adjudicated human label as truth and machine success as the prediction, report `TP`, `TN`,
`FP`, and `FN`, then compute:

\[
\mathrm{sensitivity}=\frac{TP}{TP+FN},\qquad
\mathrm{specificity}=\frac{TN}{TN+FP}.
\]

Also report positive predictive value, negative predictive value, class-stratified confusion
matrices, failure-stratum errors, raw reviewer agreement, and Cohen's kappa. Sensitivity and
specificity receive two-sided 95% Wilson intervals. Reviewer-agreement measures are disclosures,
not substitute admission criteria.

## Candidate admission rule

The instrument is only a **candidate for calibration admission** when all of these planned criteria
hold:

- point sensitivity is at least 0.90;
- point specificity is at least 0.95;
- the two-sided 95% Wilson lower bound is at least 0.80 for both sensitivity and specificity;
- all 160 records have complete independent labels and any required adjudication; and
- no corpus, grader, task-contract, blinding, or byte-binding violation occurred.

These numerical thresholds remain decisions for formal review. Even if achieved, the registered
E4 result must still be accepted explicitly; this draft cannot admit the instrument by itself.

## Missingness and hard stops

Any missing label, lost rationale, failed blinding check, post-assignment corpus change, or absent
digest makes E4 `NOT_EVALUABLE`. Records are not replaced after review begins. E4 stops immediately
on unblinding or evidence-integrity failure. The review schedule, reviewer-hour budget, conflict
rule, and exact public report schema must be frozen before registration.
