# CT3 Deterministic Geometry Checkpoint

**Specification:** CT3 Implementation Specification v1.1

**Status:** Implemented and verified

**Date:** 15 September 2026

## Implemented scope

- deterministic layer ordering by attachment, exhaustion and layer ID;
- finite segment construction from every attachment and exhaustion boundary;
- covered, gap and overlap segment membership;
- topology-only `single_layer`, `continuous`, `ventilated`, `overlapping` and
  `mixed` classification;
- explicit intentional-gap acknowledgement controls;
- uncoordinated-overlap blocking;
- complete priority-order eligibility checks;
- rejection of unnecessary priority coordination on non-overlapping programs;
- deterministic structured blocking issues, notices and ventilation warnings;
  and
- geometry that remains visible when contractual eligibility is blocked.

Base retention and above-tower loss remain outside internal geometry segments,
as required by the frozen CT3 convention. Geometry is constructed solely from
contract terms and is unchanged by the current occurrence loss.

## Verification

- G26 continuous-tower geometry covered;
- G27 acknowledged ventilation covered;
- G28 unacknowledged-gap diagnostic blocking covered;
- G29 uncoordinated-overlap diagnostic blocking covered;
- overlapping priority, invalid priority, mixed topology, permutation and
  zero-subject-loss boundaries covered;
- 16 geometry tests added;
- 529 earlier tests preserved; and
- 545 tests passing in total.

## Next checkpoint

Implement F11–F16 occurrence recovery, priority allocation, retained-loss
buckets and program reconciliation using only eligible geometry.
