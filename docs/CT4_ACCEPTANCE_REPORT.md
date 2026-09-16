# CT4 Final Acceptance Report

## Decision

CT4 is accepted for installation. The stochastic multi-year catalogue engine, hours-clause teaching engine, empirical tail analytics, frequency metrics, deterministic metadata, exact reproducibility and frozen stability gates are complete.

## Completed scope

- Catalogue-defined occurrences with complete preflight and deterministic ordering.
- Explicit empty annual trials and fixed `trial_count` denominators.
- F17 OEP maxima and F18 AEP aggregates for subject, recovery and insurer net.
- F19 AAL and F20 annual/AAL reconciliation.
- F21 nearest-rank quantiles and return-period estimates.
- F22 empirical curves using the frozen `r/Y` plotting position.
- F23 quantile-inclusive TVaR and F24 population volatility/CV.
- Cumulative limited, severe and beyond-sample credibility warnings.
- Separate occurrence and annual attachment/exhaustion frequencies.
- Bounded hours-clause candidates, admissibility-before-election and rejection evidence.
- Catalogue and hours result identities with canonical input/result SHA-256 hashes.
- G11, G13 and G35-G46 consolidated acceptance coverage.

## Frozen stability evidence

- Generator: `ct4_discrete_reference_v1`.
- RNG: Python `random.Random` MT19937 with frozen draw order.
- Baseline: 500,000 trials, seed 20260915.
- Candidates: 25,000 and 100,000 trials for seeds 11, 29, 47, 71 and 101.
- Comparisons: 70 of 70 passed without changing any tolerance.

Baseline metrics:

| Metric | Baseline |
|---|---:|
| Recovery AAL | 9,838,120 |
| Annual attachment frequency | 0.551268 |
| Recovery OEP 10-year | 25,000,000 |
| Recovery OEP 20-year | 25,000,000 |
| Recovery AEP 10-year | 30,000,000 |
| Recovery AEP 20-year | 50,000,000 |
| Recovery AEP TVaR 99% | 81,106,778.64427115 |

Worst tolerance utilization:

| Sample | Metric | Seed | Difference | Tolerance | Result |
|---:|---|---:|---:|---:|---|
| 25,000 | Recovery AAL | 47 | 2.295967% | 3.0% relative | Pass |
| 100,000 | Recovery AAL | 29 | 1.344972% | 1.5% relative | Pass |

## Frozen boundary

Every CT4 recovery remains `gross_contractual_recovery_pre_annual_capacity`. CT4 does not consume annual capacity, calculate reinstatements or present net cash settlement; those belong to CT5.

The reference stability experiment validates deterministic implementation behavior. It does not certify catastrophe-model calibration or commercial pricing suitability.

## Distribution gate

The final package must be extracted into a clean temporary directory, reproduce the full test count, preserve the recorded Git commit and show no uncommitted files before its checksum is published.

Pre-distribution repository verification: `759 passed`.
