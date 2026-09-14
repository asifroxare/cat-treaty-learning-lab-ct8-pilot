# CT2 Independent-Audit Disposition

**Status:** All findings incorporated
**Specification:** `docs/CT2_IMPLEMENTATION_SPEC.md` v1.1
**Date:** 14 September 2026

## Formula verification

The independent audit confirmed that F03/F04 reconcile and that the F05–F09
sequence telescopes correctly from Ultimate Net Loss to Cat XL subject loss.
No formula change was required.

## Findings closed

| Finding | Disposition |
|---|---|
| Aggregate lifecycle underspecified | CT2 now declares aggregate input as a single-occurrence state snapshot, returns `aggregate_remaining_after`, and assigns chronological carryover to CT3/CT5 |
| Occurrence currency had no named home | `reporting_currency` is now a required occurrence/result field |
| Supplied recovery with zero scope lacked explicit coverage | G23 and the inuring test scope now require rejection of nonzero supplied recovery when scope is zero |
| Excluded-component validation could be misread | The validation contract now states that excluded negative amounts remain invalid |

## Accepted validation decisions

- F03 is contract-neutral and auditable.
- Calculated proportional recovery remains limited to a declared aggregate
  percentage basis.
- Supplied recovery is the CT2 treatment for surplus, facultative and per-risk
  XL when authoritative risk-level calculations are unavailable.
- Sequential order and unique IDs prevent mechanical double deduction without
  claiming to determine legal inuring order.
- Negative Ultimate Net Loss attempts are rejected rather than floored.
- CT3 may consume only a completed CT2 waterfall result.

With these clarifications, CT2 v1.1 is frozen for implementation. Formulas
F03–F09 and golden-case IDs G17–G25 are unchanged.
