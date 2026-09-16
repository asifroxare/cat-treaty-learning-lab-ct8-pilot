# CT5 Checkpoint 1 Acceptance — Immutable Domain Models

**Specification:** CT5 Implementation Specification — Frozen v1.0

**Scope completed:** immutable term, reinstatement-tranche, capacity-state,
settlement and ledger domain models with validation tests.

## Implemented contracts

- frozen reinstatement time-basis and free/paid charge enums;
- ordered, contiguous reinstatement-tranche terms;
- one-to-four-layer treaty term container;
- payable-placed-share annual capacity state with F34/F35 validation;
- ordered tranche-allocation evidence;
- three-way F31 settlement, including valid negative net cash settlement;
- layer-event, event and annual ledger records;
- distinct realized-capacity and nominal-reserve utilization contracts;
- explicit zero-capacity and no-reinstatement-capacity statuses; and
- six frozen CT5 analytics-perspective identifiers.

## Boundary

This checkpoint defines and validates immutable data contracts only. It does
not implement F25–F37 calculation engines, simulation orchestration, analytics
or CT5 metadata/hashing.

## Verification

- CT5 model tests: 55 passed.
- Complete regression suite: 814 passed.
- No CT1–CT4 behavior or formula was modified.
