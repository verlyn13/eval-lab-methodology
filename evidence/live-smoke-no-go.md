# Worked example two: a live no-go, with its caveats

- **Status:** Historical worked example
- **Evidence:** Live, summary-only — executed end to end, but only sanitized summary values are
  public, and the run carried a transport confound
- **Decision:** Recorded historical `NO-GO` — the historical rule declined the candidate; because
  of the confound this is not a judgment of the model's quality
- **Demonstrates:** The historical decision path retaining a refusal on live inputs, and `n/a`
  handling when a criterion cannot be measured
- **Does not demonstrate:** Any valid model-effect estimate
- **Relevant to:** Reviewers inspecting how the historical decision plumbing handled a real,
  confounded run

**Provenance:** executed end to end over the real editing harness and the real
gateway. Small-n: candidate `qwen2.5-coder-32b` vs the local incumbent, 4 tasks x
2 replicates. This run carried a transport artifact (see caveat).

Only the sanitized summary values below are retained publicly. Raw per-attempt
outcomes needed to independently recompute the interval are not published, so
this artifact is historical documentation rather than independently
recomputable evidence.

## The promotion gate's decision

```
Decision: NO-GO — failing: beats_incumbent_beyond_band, latency_slo, no_regression_must_not_break
paired delta -0.500 (CI [-0.875, -0.125]); sign test 0W / 3L / 1T (p=0.25)
candidate task_success 0% / diff_apply 0% vs incumbent 50% / 75%; both transport_blocked

| criterion                      | result | detail                                                        |
| beats_incumbent_beyond_band    | FAIL   | historical rule: delta -0.500, CI low -0.875                  |
| reliability_class_ge_incumbent | pass   | both 'transport_blocked' (local adapter drops tools)          |
| latency_slo                    | n/a    | candidate had 0 successes -> no latency to measure            |
| no_regression_must_not_break   | FAIL   | regressions on the must-not-break subset                      |
| replicates_ge_2                | pass   | 2 replicates, 4 paired tasks                                  |
```

The paired sign test in the block above is two-sided and reported only; the
deciding mechanism in the historical rule is the bootstrap CI lower bound.

## Caveats that travel with this run

- **Small-n.** Four tasks by two replicates is a smoke-scale run, not a study.
- **Transport artifact.** The candidate's 0% task success was partly a transport
  limitation, not purely model quality. The local Ollama adapter was dropping
  tool calls, which the harness records as `transport_blocked` rather than a
  model failure. This artifact does not establish current transport behavior.
- **What it does show.** The historical software path retained a no-go when the
  interval was below zero, and the latency criterion resolved to `n/a` rather
  than pass because zero successes left no latency to measure — non-evaluable
  is never a pass. It does not establish a powered comparison or a valid
  model-effect estimate.
