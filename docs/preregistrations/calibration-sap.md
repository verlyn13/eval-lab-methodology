# Lane A calibration protocol family

## Metadata

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 1.2.0-candidate.2
- **Status:** Candidate protocol — design decisions incorporated; not preregistered; no observations authorized.

## Purpose

This document is the index and common public claim boundary for three separate statistical
analysis plans:

1. [E4 grader validation](e4-grader-validation-sap.md)
2. [E1 Lane A A/A session-position study](e1-lane-a-aa-sap.md)
3. [E2 operating-characteristics simulation](e2-operating-characteristics-sap.md)

Lane A uses `m = 1` by construction: one task pair per fresh session. E1 is therefore an
exact-identity falsification study, not a correlation-estimation study. E4 validates the grader
against independently adjudicated human labels. E2 evaluates candidate decision rules and later
inherits accepted E4 and E1 inputs for sensitivity analysis.

## Common public rules

- E4, E1, and E2 require separate reviewed registrations and separate result artifacts.
- Values in these documents are frozen design inputs only after their remaining named fields are
  completed and registered. They are not produced observations.
- Every initiated attempt is retained as exactly one terminal attempt row. Failure, timeout,
  resource exhaustion, provenance failure, and harness failure are outcomes; none is silently
  dropped.
- No whole-attempt automatic retry is allowed. A separately authorized rerun uses a new attempt
  ordinal under a new registration rather than replacing the original record.
- No unregistered schedule, rule, corpus, or serving-profile substitution is allowed.
- A missing registration, byte binding, assignment row, required provenance record, terminal row,
  or analysis artifact makes the affected study `NOT_EVALUABLE`.
- Every study binds one versioned serving-profile digest. Public analysis treats that profile as an
  opaque registered input; deployment-specific values, credentials, and authority remain outside
  this public methodology.
- Calibration results cannot promote a system, select a powered method, or settle a minimum
  practically important benefit. Those require a later coupled ruling and a new protocol.

## Dependency order and phasing

E4 and E1 may proceed independently after their own registrations. E2 has two phases:

1. the base operating-characteristics grid uses frozen synthetic distributions and may execute
   without E4 or E1 observations; and
2. grader-error and apparatus-sensitivity cells execute only after accepted E4 and E1 result
   packets exist.

The sensitivity transformation and input schema must be frozen before the E4/E1 results are
observed. This prevents later results from tuning the sensitivity analysis.

## Current readiness

The statistical decisions from the 2026-07-17 review are incorporated below, but the family is not
registered. Registration remains blocked on the incomplete E4 corpus-stratum fields, exact
machine-readable artifacts and implementations, reviewed evidence/report schemas, and separately
established operational authority. Nothing in this public family authorizes execution.
