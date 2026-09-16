# CT5 Checkpoint 3 Acceptance — F30 Reinstatement Premium

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

- F30 premium pro rata as to reinstated amount;
- `full_time` and `pro_rata_remaining_term` bases;
- free and paid tranches, including rates above 100%;
- independent pricing when one event spans multiple tranches;
- premium after the final observed event;
- inclusive-start/exclusive-end treaty-time validation; and
- immutable tranche and event premium evidence.

## Proven boundaries

- F30 consumes validated F29 usage without changing recovery or capacity.
- Every tranche retains its own rate and time basis; blending is prohibited.
- Invalid timestamps fail before any premium result is emitted.
- Zero payable capacity returns zero without division.
- No intermediate rounding is performed.

## Verification

- CT5 model, capacity and premium tests: 100 passed.
- Complete regression suite: 859 passed.
- G53, G54, G63 and G66 premium behavior is covered.
- No CT1–CT4 behavior or formula was modified.
