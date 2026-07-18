# E1 Lane A A/A session-position statistical analysis plan

## Metadata and claim boundary

- **Decision date:** 2026-07-17
- **Last updated:** 2026-07-18
- **Version:** 0.2.0-candidate.2
- **Status:** Candidate protocol — design decisions incorporated; not preregistered; no observations authorized.
- **Study type:** Local-lane exact-identity falsification; structurally non-promotable.

The candidate design counts and rules below are protocol inputs, not observations. They establish
no powered-study replicate policy.

## Objective and estimand

E1 attempts to falsify exact cross-arm identity when two blinded arms receive byte-identical
registered scientific invocation payloads under the same versioned serving profile. Lane A uses
**`m = 1`**: one task pair per fresh session. E1 does not estimate an intra-session correlation and
does not claim general determinism outside the registered apparatus.

The primary estimand is the cross-arm divergence frequency among the 120 planned session pairs.
Cross-position comparisons of the same task across rounds are a separately reported diagnostic;
they are not pooled into the primary denominator. Latency, resource use, and warmup behavior are
diagnostics and never turn a divergence into identity.

## Design to register and counts

- 40 task pairs, with 10 in each of four fixed task classes.
- 3 rounds, each containing one fresh session for every task pair.
- 120 sessions total: `40 task pairs x 3 rounds`.
- 120 primary cross-arm comparisons.
- 2 blinded arm attempts per session, yielding 240 terminal arm attempts total.
- Each arm attempt has an isolated workspace, fresh client process, separate invocation record, and
  separate terminal row.
- Both arms bind the same task bytes, registered scientific invocation payload bytes, harness,
  grader, prompt, identity-domain preimage, resource policy, and serving-profile digest.

The exact scientific request-body bytes are hashed immediately before transmission and must match
between arms. Transport-envelope fields that must differ, such as unique record identifiers, must
remain outside that body, be enumerated before registration, and be bound separately. No
post-transmission canonicalization may erase a request-body difference. An unregistered byte
difference makes the comparison `NOT_EVALUABLE`.

## Assignment schedule

The schedule seed is the UTF-8 string `lane-a-aa-schedule-v1`. Sort registered opaque task
identifiers by `SHA-256(seed || NUL || task_id)`. Use that base order in round 1 and rotate it by 13
and 27 positions in rounds 2 and 3. The machine-readable schedule binds task, round,
planned-position, and arm-order rows before registration.

Within each round, arm order is determined by the parity of `round_index + planned_position`, where
round indices are 0, 1, and 2 and positions are 1 through 40. This yields exactly 20 sessions in
each arm order per round and 60 in each arm order overall.

The execution record also stores the **actual chronological session position**. Analysis uses
actual position and reports every deviation from registered order.

## Serving-profile and recomputation requirements

Every E1 record binds one registered serving-profile digest. That profile must structurally enforce
serialized execution, independent prompt computation, transmitted decoding parameters, adequate
context capacity, quiescence, and the registered resource bounds. Exact deployment values and
mechanisms are not part of this public document.

A scientific `INVARIANCE_NOT_REFUTED` requires authoritative, request-bound evidence that the
second arm independently recomputed its prompt. Timing is corroborative only. If the registered
apparatus cannot provide the authoritative recomputation record, E1 is `NOT_EVALUABLE`.

Each session begins with one standardized, non-task warmup invocation whose result is discarded and
recorded outside the 240 scientific attempts. The warmup must not provide reusable task-prefix
state. Cross-arm divergence is reported as a possible first-call/warm-state effect; cross-position
divergence is reported separately as a possible position or state-leakage effect.

## Stage localization

Every arm records this digest chain:

`fixture -> invocation -> transcript -> workspace_post -> diff -> outcome`

For every divergence, report the earliest differing stage. `outcome_digest` is the sensitive
end-check; `task_success` is the estimand-level check. A transcript-stage classification is allowed
only when fixture and registered invocation bytes match exactly and every required upstream digest
and recomputation record validates.

The non-causal localization label is
`ENGINE_STAGE_DIVERGENCE_UNDER_REGISTERED_APPARATUS`. It identifies the earliest observed stage
under one registered apparatus; it does not prove that an engine algorithm was the sole cause.
Missing or ambiguous upstream evidence yields `NOT_EVALUABLE`, never this label.

## Falsification rule and state precedence

The terminal state is assigned in this conservative precedence order:

1. `NOT_EVALUABLE` when missing or invalid registration, schedule, binding, provenance,
   recomputation, or terminal accounting prevents trusted analysis;
2. `APPARATUS_NOT_ADMISSIBLE` when otherwise complete evidence contains any unplanned timeout,
   resource, harness, or client failure, including a failure that co-occurs with divergence;
3. `INVARIANCE_REFUTED` when all evidence is complete, the apparatus is admissible, every upstream
   scientific byte and digest matches, and at least one of the 120 primary cross-arm comparisons
   cleanly diverges; the divergence carries the localization label above; or
4. `INVARIANCE_NOT_REFUTED` when all 120 sessions and 240 attempts are complete and admissible and
   all 120 primary cross-arm comparisons are identical.

Cross-position results are emitted as a separate diagnostic result and do not change the primary
cross-arm denominator or silently acquire a causal label.

With zero clean cross-arm divergences, the nominal rule-of-three upper detection bound is
approximately `3 / 120 = 2.5%`. This does not prove invariance, cannot exclude rarer divergence, and
is further limited by repeated-task dependence because the 120 pairs arise from 40 tasks across
three rounds.

## Hard stops and remaining freeze work

Stop dispatch on an unregistered byte difference, serving-profile mismatch, schedule mutation,
loss of isolation, evidence-integrity failure, or missing authoritative recomputation evidence.
Already initiated attempts remain terminal rows.

Before registration, reviewers must freeze the executable schedule, canonical scientific-payload
rule, serving-profile digest, recomputation-record schema, wall-time and resource bounds, stop
implementation, evidence schema, classifier implementation, and report schema by exact digest.
This public SAP does not establish operational authority or reveal deployment-specific apparatus
values.
