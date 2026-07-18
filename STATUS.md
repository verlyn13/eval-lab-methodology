# Status

- **Status:** Prototype — public methodology and verification code; repository-versioned, with no distributed release
- **Evidence:** Synthetic and representative examples, plus one confounded historical smoke summary — no admissible real-model comparison
- **Decision:** No promotion recommendation — the draft evidence contract recomputes `NOT_EVALUABLE`, meaning no scientific conclusion can be drawn from its evidence
- **Demonstrates:** Independent, fail-closed evaluation reporting on synthetic evidence
- **Does not demonstrate:** Performance of any real model
- **Relevant to:** Model testing, challenger evaluation, and model-risk review

## Readiness verdict

The audited baseline passes its current CI and exact-result checks. The evaluation system is not
ready for a powered scientific promotion decision or production use.

## Verified now

| Item | Evidence | Status |
|---|---|---|
| Public site | Render run `29657510137` and Pages run `29657510147` passed for current published baseline `5423caa` | published |
| Core version | `pyproject.toml` and frozen core identify `0.2.0`; wheel containment is tested | repository-versioned, not distributed — the version names code in this repository, not a release anyone can install from a registry |
| Experimental calculations | Committed synthetic results regenerate byte-for-byte | decision input only — the numbers inform, but do not make, the pending method decision |
| Calibration SAP family | Separate E4, E1, and E2 candidate protocols incorporate the 2026-07-17 statistical decisions and retain explicit freeze blockers | not preregistered; no observations authorized; exact corpus strata, implementations, schemas, and operational bindings remain incomplete |
| Contract B v2 draft | Exact schema, verifier, renderer, safety scanner, fixture, report, and delivery manifest are digest-bound (every implementation byte is hash-pinned) | synthetic conformance only — the draft evidence contract is validated against invented data, not real campaigns |
| Independent refusal | The public verifier derives `NOT_EVALUABLE` from the synthetic fixture and rejects mutations — it recomputes the result from frozen evidence bytes and refuses any altered copy | verified for the fixture |
| Publication scanning | Evidence inputs are recursively scanned in the parameterized report path; Contract B checks its bound public payload separately | path-scoped; no whole-repository scan — leak scanning covers the report inputs, not every file in the repository |

There is no Git tag, GitHub release, or package-registry publication for version `0.2.0`. “Version”
therefore identifies repository and wheel metadata, not a distributed release.

## Not ready

| Requirement | Current gap |
|---|---|
| Scientific design | Estimand, enforcing test, replicate policy, and practical-benefit rule remain undecided — what is measured, the test that determines whether evidence supports a decision, how many repeated trials are required, and the minimum improvement worth changing models for are all still awaiting an explicit decision |
| Operating characteristics | Type I error (how often the rule would be wrong), power (how often it would detect a real difference), dependence sensitivity, and feasibility are not established for the intended design |
| Measurement validity | Grader validation, protected-task policy, and governed task selection are incomplete — the scoring instrument itself is not yet validated |
| Operational provenance | Registration signing/timestamp verification and runtime owner receipts are not operational — runtime evidence is not yet signed and independently verified in production |
| Calibration | No accepted grader study, A/A session-position invariance study, or rule-calibration study exists — nothing yet shows the measurement apparatus is quiet and consistent enough to trust |
| Real result | No powered, registered, scientifically admissible model comparison has been published |
| Historical smoke reproducibility | Only summary statistics are public; raw per-attempt outcomes required to recompute the interval are absent — outside readers cannot independently re-derive it |
| Publication enforcement | Active no-bypass ruleset `18954954` requires pull requests, signed commits, linear history, resolved review threads, and the strict `Render public evidence reports` check; approval count is zero under the disclosed solo-maintainer model | protected, but not independent review |

## Claim policy

Current public artifacts support claims about software structure, exact-byte verification, synthetic
recomputation, and explicit refusal behavior. They do not support claims that:

- one model or harness is better than another;
- the historical bootstrap rule has validated error control for the intended design;
- identity-domain equality alone establishes reproducibility;
- Contract B v2 is an accepted or operational evidence contract; or
- the end-to-end private system is production-ready.

## Path to a first admissible result

1. Accept a scientific analysis plan and publish the corresponding versioned method contract.
2. Complete owner-issued runtime observations and operational registration verification.
3. Freeze the grader, task-selection record, task suite, assignment, retry, and attrition policies.
4. Run and review grader validation, A/A session-position invariance calibration, and operating-
   characteristic analysis.
5. Register and execute the first powered local comparison.
6. Independently recompute, sanitize, review, and publish the result, including a no-go or
   `NOT_EVALUABLE` outcome if that is what the evidence supports.

Remote GPU evaluation is a separate later baseline. It must not inherit local-lane validity by
convention.

## Known errata

The frozen identity-domain v1 module docstring overstates what hash equality establishes. The
versioned interpretation correction is recorded in [ERRATA.md](ERRATA.md); frozen v1 bytes and the
conformance vector are unchanged.

## Provenance

- Status date: 2026-07-18
- Baseline reviewed for this candidate update: `5423caa370664f1e34101e8e812397f6a9608e1a`
