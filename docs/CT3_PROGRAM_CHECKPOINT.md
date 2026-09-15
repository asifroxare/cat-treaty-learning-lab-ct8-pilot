# CT3 F11–F16 Program Recovery Checkpoint

**Specification:** CT3 Implementation Specification v1.1

**Status:** Implemented and verified

**Date:** 15 September 2026

## Implemented scope

- F11 independent covered loss for every layer;
- F12 allocate-once priority coordination across two- and multi-layer overlaps;
- F13 separate ceded-share and placement-share recovery;
- F14 retained participation inside each allocated layer band;
- F15 total gross contractual recovery and insurer net loss;
- F16 base-retention, gap, in-layer-retention and above-tower buckets;
- deterministic geometry-order layer results and disclosed priority positions;
- authoritative eligible-or-blocked assessment envelope;
- blocked-recovery exception carrying the complete diagnostic geometry;
- deterministic explanation facts, warnings and assumptions; and
- three independent reconciliation records for F15 and F16.

The engine evaluates one completed CT2 occurrence. It applies no annual
capacity, reinstatement premium or cash-settlement adjustment. Those remain
outside CT3 under the frozen milestone boundary.

## Verification

- G26 continuous USD 45m tower recovery independently reproduced;
- loss below, exactly at and above attachment/exhaustion boundaries covered;
- acknowledged ventilation and gap-loss retention covered;
- different layer shares and zero-share boundaries covered;
- G30 priority overlap shows pre- and post-coordination values;
- priority-order sensitivity and three-way union allocation covered;
- blocked geometry returns no recovery result;
- mismatched supplied geometry is rejected;
- 19 program-recovery tests added;
- 545 earlier tests preserved; and
- 564 tests passing in total.

## Next checkpoint

Implement CT3 deterministic metadata, normalized-input hashing, complete golden
case acceptance and final CT3 distribution verification.
