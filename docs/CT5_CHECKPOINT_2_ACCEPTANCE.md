# CT5 Checkpoint 2 Acceptance — F25–F29 Annual Capacity

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

- F25 payable-placed initial, reinstatement-reserve and maximum capacity;
- independent annual reset by layer and trial;
- F26 recovery capped by active capacity before restoration;
- F27 post-recovery active capacity;
- F28 automatic post-event reinstatement, including after the last event;
- F29 allocation to the earliest non-exhausted tranche;
- partial and cross-tranche reinstatement usage evidence; and
- immutable, reconciled capacity transitions.

## Proven boundaries

- CT3 ceded and placement shares are applied exactly once.
- Reinstatement cannot increase recovery for its triggering occurrence.
- Layers do not borrow capacity from one another.
- Purchased reserve cannot be exceeded.
- Premium is not calculated in this checkpoint; F29 emits unpriced capacity
  usage for the later F30 engine.

## Verification

- CT5 model and capacity tests: 79 passed.
- Complete regression suite: 838 passed.
- G47–G50 and the capacity portion of G63/G67 are covered.
- No CT1–CT4 behavior or formula was modified.
