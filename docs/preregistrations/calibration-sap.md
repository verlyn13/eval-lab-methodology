# Calibration Statistical Analysis Plan (SAP)

## 1. Metadata
- **Title**: Phase 12 Lane A Instrument Calibration Preregistration
- **Date**: 2026-07-16
- **Version**: 1.0.0
- **Status**: Preregistered Draft

---

## 2. E4 Grader Validation Protocol
The objective of E4 is to measure the agreement between the deterministic machine grader ($G_m$) and the independent human gold label ($G_h$).

### Metrics
We will compute the following metrics over a class-balanced validation corpus ($N \ge 40$ attempts representing all four classes and failure modes):

* **Sensitivity (True Positive Rate)**:
  $$\text{Sensitivity} = \frac{TP}{TP + FN}$$
  *Where $TP$ is the number of attempts graded as success by both human and machine, and $FN$ is the number of attempts graded as success by human but failure by machine.*

* **Specificity (True Negative Rate)**:
  $$\text{Specificity} = \frac{TN}{TN + FP}$$
  *Where $TN$ is graded as failure by both, and $FP$ is graded as failure by human but success by machine.*

* **Positive Predictive Value (PPV)**:
  $$\text{PPV} = \frac{TP}{TP + FP}$$

* **Negative Predictive Value (NPV)**:
  $$\text{NPV} = \frac{TN}{TN + FN}$$

### Validation Thresholds
The instrument is declared valid for calibration only if:
* $\text{Sensitivity} \ge 0.90$
* $\text{Specificity} \ge 0.95$

---

## 3. E1 A/A Independence Study
The objective of E1 is to estimate the within-session correlation coefficient ($\rho$) and verify that local hardware and cache conditions do not introduce systematic bias between experimental arms.

### Design
* **Arms**: Arm 1 (A) and Arm 2 (A') run identical model digests (`qwen3.5:9b`).
* **Sample Size**: 3 serial replicates of the frozen 40-task suite per arm (240 total attempts).
* **Null Hypothesis**: $H_0: \rho = 0$ (attempts are independent).
* **Test Statistic**: Pearson correlation coefficient and Ljung-Box test for serial autocorrelation on latency and success vectors.

---

## 4. E2 Operating Characteristics Simulation
E2 evaluates the provisional decision rule and estimates statistical power under varying effect sizes.

### Simulation Inputs
* Empirical success rates and transition matrices from E1.
* Measurement error rates from E4.
* Simulation runs ($B = 10,000$) to evaluate the Type I error rate ($\alpha$) and statistical power ($1-\beta$) under candidate sample sizes ($N$) and Minimum Practical Improvement Boundaries (MPIB).

---

## 5. Attrition & Missingness Handling
Every initiated attempt must be accounted for in the attrition table.
* **Timeout/OOM/Harness Error**: Evaluated as `NOT_EVALUABLE` and excluded from the capability pass-rate calculations, but documented in the attrition table.
* **Transient Network Error**: Subject to a maximum of 1 automatic retry; the retry carries its own unique attempt index and receipts.
