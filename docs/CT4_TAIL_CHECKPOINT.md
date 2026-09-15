# CT4 F21-F24 Tail Analytics Checkpoint

## Scope completed

- F19 annual average loss over the complete declared trial population.
- F21 nearest-rank empirical quantiles without interpolation.
- Return-period conversion through `p = 1 - 1/T` for both OEP and AEP samples.
- F22 empirical exceedance curves using the frozen `r/Y` plotting position.
- Duplicate loss observations remain separate ranked curve points.
- F23 TVaR includes the nearest-rank quantile observation and every larger observation.
- F24 two-pass population standard deviation and coefficient of variation.
- Zero-mean CV is null with `not_applicable_zero_mean`, never zero, NaN or infinity.
- Limited, severe and sample-exceedance credibility warnings attach cumulatively.
- Subject, recovery and insurer-net AALs reconcile under F20.

## Response convention

The legacy-compatible `var_estimates`, `tvar_estimates` and `return_period_estimates` fields carry the AEP series. Explicit OEP and AEP fields remove ambiguity for new consumers.

## Deferred by design

- Occurrence and annual frequency metrics.
- Hours-clause candidate generation, admissibility and election.
- CT4 canonical metadata, hashing, frozen stability experiment and final acceptance packaging.

## Verification

Verified result: `694 passed`. The full suite must pass with a clean working tree before distribution.
