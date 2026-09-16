# CT5 Checkpoint 4 Acceptance — F31 Settlement

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

- three separately named settlement fields;
- default `paid_separately` presentation;
- advanced `deducted_from_settlement` presentation;
- finite negative net cash settlement without flooring; and
- immutable F31 reconciliation validation.

## Proven invariants

Changing settlement mode changes only `net_cash_settlement`. It does not alter:

- pre-capacity or post-capacity recovery;
- reinstatement premium payable;
- capacity consumed or restored;
- tranche usage or pricing evidence; or
- insurer net subject loss.

The settlement module imports neither the capacity engine nor the premium
engine and therefore cannot recalculate their authoritative outputs.

## Verification

- Complete regression suite: 881 passed.
- G56 and G65 settlement behavior is covered.
- No CT1–CT4 behavior or formula was modified.
