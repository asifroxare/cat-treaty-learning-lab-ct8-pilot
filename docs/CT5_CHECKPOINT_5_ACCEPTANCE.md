# CT5 Checkpoint 5 Acceptance — F32–F37 Annual Orchestration

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

- deterministic consumption of completed CT4 catalogue occurrences;
- exact CT4 `subject_loss` and pre-capacity layer-recovery provenance;
- independent state by layer with reset at each annual trial;
- complete layer-event, event and annual ledgers;
- F32 event recovery and insurer-net reconciliation;
- F33 annual totals;
- F34 active-capacity and F35 reinstatement-reserve reconciliation;
- F36 contractual maximum through non-negative final state;
- F37 occurrence and annual capacity-shortfall amounts; and
- realized-capacity and nominal-reserve utilization with explicit N/A states.

## Proven controls

- CT4 occurrence sequence, including stable tied timestamps, is preserved.
- Every CT3 layer maps to exactly one CT5 term record.
- One simulation-wide settlement mode is enforced across layers.
- Empty annual trials remain in the output and denominator.
- Capacity never carries between annual trials or across layers.
- CT5 cannot invent program terms for an entirely empty CT4 catalogue.

## Deferred by planned milestone boundary

- completed CT4 hash/identity verification and CT5 canonical hashes belong to
  the deterministic metadata checkpoint;
- selected hours-clause-result entry is finalized with that identity boundary;
- OEP/AEP sample construction and tail metrics belong to the analytics
  checkpoint.

## Verification

- Integrated CT5 tests: 139 passed.
- Complete regression suite: 898 passed.
- No CT1–CT4 behavior or formula was modified.
