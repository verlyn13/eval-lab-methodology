# Lane A calibration protocol family

## Metadata

- **Date:** 2026-07-17
- **Version:** 1.1.0-candidate.1
- **Status:** Candidate protocol — not preregistered; no observations authorized.

## Purpose

This document is the index and common claim boundary for three separate candidate statistical
analysis plans:

1. [E4 grader validation](e4-grader-validation-sap.md)
2. [E1 Lane A A/A session-position study](e1-lane-a-aa-sap.md)
3. [E2 operating-characteristics simulation](e2-operating-characteristics-sap.md)

The former umbrella draft combined three different studies and incorrectly described the E1
objective as estimation of within-session correlation. The replacement family uses Lane A `m = 1`
by construction: one task pair per fresh session. E1 is therefore a determinism/falsification study,
not a correlation-estimation study.

## Common rules

- E4, E1, and E2 require separate reviewed registrations and separate result artifacts.
- Planned values in these documents are design candidates, not produced observations.
- Every initiated E1 attempt is retained as exactly one terminal attempt row. Failure, timeout,
  resource exhaustion, receipt failure, and harness failure are outcomes; none is silently dropped.
- No whole-attempt automatic retry is allowed. A separately authorized rerun must use a new attempt
  ordinal and a new registration rather than replacing the original record.
- Each gateway call has a planned provider retry limit of zero. A client invocation may contain
  multiple disclosed calls; all calls must be included in its closure record.
- No fallback model, direct provider path, or unregistered schedule substitution is allowed.
- A missing registration, byte binding, assignment row, owner receipt, invocation closure, terminal
  attempt row, or required analysis artifact makes the affected study `NOT_EVALUABLE`.
- Calibration results cannot promote a system, select a powered method, or settle a minimum
  practically important benefit. Those require a later coupled ruling and a new protocol.

## Current readiness

These documents are reviewable design inputs only. Before any study can be registered, reviewers
must resolve the candidate decisions called out in each SAP, freeze the machine-readable inputs and
implementations by digest, approve the evidence/report contracts, and establish operational
registration and observation authority.
