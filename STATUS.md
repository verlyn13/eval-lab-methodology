# Status

Status date: 2026-07-14
Audited public baseline: `3ceffb1474146c8b462af11112faf4c50b547ce8`

## Readiness verdict

The audited baseline passes its current CI and exact-result checks. The evaluation system is not
ready for a powered scientific promotion decision or production use.

## Verified now

| Item | Evidence | Status |
|---|---|---|
| Public site | Render and Pages workflows passed for publication commit `3ceffb1` | published |
| Core version | `pyproject.toml` and frozen core identify `0.2.0`; wheel containment is tested | repository-versioned, not distributed |
| Experimental calculations | Committed synthetic results regenerate byte-for-byte | decision input only |
| Contract B v2 draft | Exact schema, verifier, renderer, safety scanner, fixture, report, and delivery manifest are digest-bound | synthetic conformance only |
| Independent refusal | The public verifier derives `NOT_EVALUABLE` from the synthetic fixture and rejects mutations | verified for the fixture |
| Publication scanning | Evidence inputs are recursively scanned in the parameterized report path; Contract B checks its bound public payload separately | path-scoped; no whole-repository scan |

There is no Git tag, GitHub release, or package-registry publication for version `0.2.0`. “Version”
therefore identifies repository and wheel metadata, not a distributed release.

## Not ready

| Requirement | Current gap |
|---|---|
| Scientific design | Estimand, enforcing test, replicate policy, and practical-benefit rule remain undecided |
| Operating characteristics | Type I error, power, dependence sensitivity, and feasibility are not established for the intended design |
| Measurement validity | Grader validation, protected-task policy, and governed task selection are incomplete |
| Operational provenance | Registration signing/timestamp verification and runtime owner receipts are not operational |
| Calibration | No accepted grader study, A/A independence/noise-floor study, or rule-calibration study exists |
| Real result | No powered, registered, scientifically admissible model comparison has been published |
| Historical smoke reproducibility | Only summary statistics are public; raw per-attempt outcomes required to recompute the interval are absent |
| Publication enforcement | CI passes on current `main`, but no GitHub ruleset or branch protection currently requires those checks |

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
4. Run and review grader validation, A/A independence/noise-floor calibration, and operating-
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
