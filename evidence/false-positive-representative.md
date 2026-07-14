# Worked example one: representative refusal under the historical rule

**Provenance:** produced with a stubbed editing harness on representative data.
This demonstrates historical decision plumbing. It is not a live model A/B,
does not establish that a real promotion would have been a false positive, and
does not validate the rule's error rate.

## The capability layer's ranking

| target                  | fix_failing_test | multifile_refactor | repo_reasoning | small_edit | overall |
|-------------------------|------------------|--------------------|----------------|------------|---------|
| local incumbent default | 80%              | 50%                | 60%            | 90%        | 70%     |
| qwen2.5-coder-32b (32B) | 90%              | 80%                | 70%            | 90%        | 82%     |

The representative capability summary has an overall candidate-minus-incumbent
delta of **+0.12**. It is descriptive input only and does not authorize a role
change.

## The promotion gate's decision

```
Decision: NO-GO — failing: beats_incumbent_beyond_band
paired delta +0.250 (band 0.10); bootstrap CI [0.0, 0.5]; sign test 2W/0L/2T (p=0.5)

| criterion                       | result |
| beats_incumbent_beyond_band     | FAIL   |  # CI low = 0 does not exceed the 0.10 margin
| reliability_class_ge_incumbent  | pass   |
| latency_slo                     | pass   |
| no_regression_must_not_break    | pass   |
| replicates_ge_2                 | pass   |
```

The mean paired delta clears the 0.10 tolerance band, but the bootstrap CI lower
bound is 0. The historical public helper requires `ci_low > margin`, so this
input is refused. The sign test is reported as a companion diagnostic and is
not part of the decision.

The historical rule returns no-go for these representative inputs. This is a
reproducible software example, not an inferential result or evidence about a
candidate model. No performance improvement or error-control claim is made.
