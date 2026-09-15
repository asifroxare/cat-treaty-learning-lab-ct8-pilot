# CT3 Immutable Domain Models Checkpoint

**Specification:** CT3 Implementation Specification v1.1

**Status:** Implemented and verified

**Date:** 15 September 2026

## Implemented scope

- immutable Cat XL layer terms with F10 exhaustion;
- CT3 program input containing a completed CT2 waterfall and metadata;
- CT2 occurrence, currency and normalized-input-hash verification;
- one-to-four-layer, unique-ID and currency controls;
- separate ceded share and placement share fields;
- explicit gap acknowledgement, overlap mode and priority-order inputs;
- topology, segment, eligibility and structured blocking-issue contracts;
- per-layer F13/F14 result reconciliation;
- program-level F15/F16 result reconciliation; and
- eligible and blocked assessment envelopes.

Priority-order completeness and legal applicability are deliberately evaluated
after geometry is known. The input model validates only the request shape, so
the geometry stage can return the frozen `invalid_priority_order` or
`unnecessary_priority_coordination` structured issue rather than failing
silently before diagnostic geometry exists.

## Verification

- 44 CT3 model validation tests added;
- 485 CT1/CT2 regression tests preserved;
- 529 tests passing in total; and
- no geometry-construction or recovery-engine implementation included in this
  checkpoint.

## Next checkpoint

Implement deterministic geometry analysis, topology classification, gap and
overlap eligibility controls, and their golden-case tests.
