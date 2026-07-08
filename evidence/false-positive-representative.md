# Worked example one: the gate caught a false positive (representative data)

**Provenance:** produced with a stubbed editing harness on representative data.
This demonstrates the design behavior of the gate. It is not a live model A/B.

## The capability layer's ranking

| target                  | fix_failing_test | multifile_refactor | repo_reasoning | small_edit | overall |
|-------------------------|------------------|--------------------|----------------|------------|---------|
| local incumbent default | 80%              | 50%                | 60%            | 90%        | 70%     |
| qwen2.5-coder-32b (32B) | 90%              | 80%                | 70%            | 90%        | 82%     |

Role recommendation: switch the local coding role to the 32B candidate, margin
**+0.12**, confidence **"confident."** A capability-only decision flips the
default here.

## The promotion gate's decision

```
Decision: NO-GO — failing: beats_incumbent_beyond_band
paired delta +0.250 (band 0.10); bootstrap CI [0.0, 0.5]; sign test 2W/0L/2T (p=0.5)

| criterion                       | result |
| beats_incumbent_beyond_band     | FAIL   |  # mean clears band but CI low = 0 (not significant)
| reliability_class_ge_incumbent  | pass   |
| latency_slo                     | pass   |
| no_regression_must_not_break    | pass   |
| replicates_ge_2                 | pass   |
```

The mean paired delta clears the 0.10 tolerance band. The bootstrap CI lower
bound sits at 0. The `beats_incumbent_beyond_band` criterion requires **both**
`paired_delta > band` **and** `ci_low > 0`, so a gain that clears the band but
whose interval touches zero is refused. The sign test is reported as a companion
diagnostic and is not part of the decision.

The result is a defensible no-go: the bigger, newer, higher-scoring candidate was
declined because the gain was not statistically distinguishable from zero. No
performance improvement is claimed. The value is the refusal.
