# CT5 Checkpoint 6 Acceptance — Post-Capacity Analytics

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

Six separately labelled annual perspectives:

1. subject loss;
2. gross recovery after annual capacity;
3. insurer net subject loss after annual capacity;
4. reinstatement premium payable;
5. net cash settlement; and
6. capacity-constrained recovery shortfall.

Each perspective provides complete OEP and AEP samples, AAL, population
standard deviation, coefficient-of-variation status, empirical exceedance
curves, nearest-rank quantiles, TVaR and return-period estimates with cumulative
CT4 credibility warnings.

Operational metrics include annual constraint probability, average constrained
recovery, layer maximum-capacity exhaustion probability, average and maximum
reinstatements used, and conditional/unconditional reinstatement premium.

## Frozen conventions preserved

- Every annual trial remains in every sample, including empty trials.
- Plotting position remains `r/Y` with duplicates retained.
- Nearest-rank estimates do not interpolate.
- TVaR includes the quantile observation and every larger observation.
- Credibility warnings accumulate; none suppress another.
- Finite negative net cash settlement is retained in samples, curves and tail
  estimates without flooring.
- Coefficient of variation is N/A for zero or negative annual mean.
- Average/maximum reinstatements used are measured across applicable
  positive-capacity layer-years.

## Verification

- Focused CT5 analytics tests: 18 passed.
- Complete regression suite: 916 passed.
- Fresh Checkpoint 6 work was rebuilt from clean commit `c0839ee` after the
  interrupted attempt was discarded.
- No CT1–CT4 behavior or formula was modified.
