# E1 Lane A A/A session-position statistical analysis plan

## Metadata and claim boundary

- **Date:** 2026-07-17
- **Version:** 0.1.0-candidate.1
- **Status:** Candidate protocol — not preregistered; no observations authorized.
- **Study type:** Local-lane calibration; structurally non-promotable.

All counts, seeds, and rules below are **planned candidate values**. They are not observations and
do not establish a powered-study replicate policy.

## Objective

E1 attempts to falsify exact outcome invariance when two blinded arms resolve to the same content
digest and task pairs are isolated by fresh sessions. Lane A uses **`m = 1`**: one task pair per
fresh session. The design removes within-session clustering from the later task-level comparison by
construction; E1 does not estimate an intra-session correlation and does not test a null hypothesis
that such a correlation is zero.

E1 reports whether task success and exact outcome digests remain identical across A/A arms and
registered session positions. Latency and resource measures are diagnostics only and never turn a
divergent outcome into an invariant one.

## Planned design and counts

- 40 registered task pairs, with 10 in each of four fixed task classes.
- 3 rounds, each containing one fresh session for every task pair.
- 120 sessions total: `40 task pairs x 3 rounds`.
- 2 blinded arm attempts per session, yielding 240 terminal arm attempts total.
- Each arm attempt has a separate editing-client descriptor and a separate gateway invocation with
  open, zero-or-more call, and closure receipts.
- Both arms must bind the same resolved content digest, decoding configuration, task bytes, harness,
  grader, prompt, identity-domain preimage, and resource policy.

The number of model calls is not fixed at 240. A client invocation may make multiple gateway calls,
all of which must appear in invocation closure. Zero calls are valid only for a retained terminal
pre-dispatch failure.

## Planned assignment schedule

The candidate schedule seed is the UTF-8 string `lane-a-aa-schedule-v1`. Sort registered opaque task
identifiers by `SHA-256(seed || NUL || task_id)`. Use that base order in round 1 and rotate it by 13
and 27 positions in rounds 2 and 3. The machine-readable schedule must bind the resulting task,
round, planned-position, and arm-order rows before registration.

Within each round, arm order is determined by the parity of `round_index + planned_position`, where
round indices are 0, 1, and 2 and positions are 1 through 40. This yields exactly 20 sessions in each
arm order per round and 60 in each arm order overall.

The execution record must also store the **actual chronological session position**. Analysis uses
actual position and reports any deviation from the registered order; a synthetic early/middle/late
label is not a substitute.

## Session isolation and execution

Before each task-pair session, create isolated workspaces and fresh client processes for both arms.
Each arm gets its own invocation and workspace; neither arm may read the other's artifacts. Close
both invocations and emit both terminal attempt rows before beginning the next session. Record
machine-load, model-residency, cache, process, harness, and verification-subprocess diagnostics that
the registered observation contract can actually support. Do not claim an engine restart unless it
is observed and receipt-bound.

The provider retry limit is zero for every gateway call. There is no automatic whole-attempt retry.
Client-generated additional calls are disclosed within the same invocation and do not create a new
scientific attempt. Every failure remains in the attempt ledger.

## Analysis and falsification rule

For each task and round, compare the two arms' `task_success` and exact `outcome_digest`. For each
task across its three actual positions, compare the same fingerprint. Report:

- cross-arm and cross-position divergence counts and exact task/round locations;
- terminal status and failure-mode counts by arm order, round, class, and actual position;
- latency and resource summaries by the same strata, labeled diagnostic; and
- all schedule deviations, receipt failures, and incomplete joins.

The candidate E1 result has four states, applied in the following precedence order:

- `INVARIANCE_NOT_REFUTED` when all 120 sessions and 240 arm attempts have complete terminal
  accounting, every required owner join and digest binding validates, no unplanned terminal
  apparatus failure occurs, and there is zero cross-arm and zero cross-position divergence;
- `INVARIANCE_REFUTED` when the evidence is complete and valid but at least one fingerprint
  diverges;
- `APPARATUS_NOT_ADMISSIBLE` when fingerprints do not diverge but complete, valid evidence contains
  an unplanned timeout, resource, harness, or client failure; or
- `NOT_EVALUABLE` when missing or invalid registration, schedule, binding, receipt, closure, or
  terminal accounting prevents the falsification analysis from being trusted.

Thus a valid negative observation is reported as an invariance falsification or an apparatus
admission failure, not discarded as missingness.
This exact-invariance rule is a candidate requiring formal review; a clean result does not prove
invariance outside the registered apparatus and makes no population-level claim about a correlation
parameter.

## Hard stops and consequences

Stop dispatch on a content-digest mismatch, fallback, direct unregistered transport, broken receipt
chain, schedule mutation, evidence-integrity failure, or loss of session isolation. Already initiated
attempts remain reportable terminal rows. A validly observed timeout, resource exhaustion, harness
error, or client error is not dropped or replaced and blocks apparatus admission; absent fingerprint
divergence it yields `APPARATUS_NOT_ADMISSIBLE`. A broken evidence chain yields `NOT_EVALUABLE`.

An evaluable E1 result is evidence only about the frozen local apparatus and schedule. It cannot
validate a remote lane, select an enforcing test, define the powered replicate unit, or authorize
promotion.
Before registration, reviewers must freeze the executable schedule, wall-time bound, zero-dollar
resource budget, stop implementation, evidence schema, and report schema by exact digest.
