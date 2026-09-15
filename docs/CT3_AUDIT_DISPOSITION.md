# CT3 Independent Audit Disposition

**Specification:** `docs/CT3_IMPLEMENTATION_SPEC.md` v1.1

**Disposition:** Accepted and frozen

**Date:** 15 September 2026

## 1. Formula review

The independent review confirmed F10–F16 are internally consistent. Golden
case G26 was independently recomputed: USD 20m from the first layer plus USD
15m from the second gives USD 35m gross contractual recovery, USD 10m retained
loss and full reconciliation to USD 45m subject loss.

The non-negativity and upper-bound properties of F13–F16 follow from the frozen
share bounds and allocate-once construction. Runtime reconciliation remains an
audit control and numerical-stability check; it is not a substitute for the
formula design.

## 2. Finding dispositions

| Finding | Disposition |
|---|---|
| Overlap with no coordination had no exhaustive geometry classification | Resolved by separating topology from eligibility. Valid layer terms always produce `single_layer`, `continuous`, `ventilated`, `overlapping` or `mixed`; contractual defects separately set eligibility to `blocked`. |
| B, G and T were described but not formally defined | Resolved with explicit retained-band definitions under F16. |
| Diagnostic geometry on blocked programs was implicit | Resolved: complete geometry and structured blocking issues are returned, while the program recovery result is null and no recovery amounts are emitted. |

The correction does not change F10–F16. It makes G28 and G29 deterministic and
prevents classification from being mistaken for contractual recoverability.

## 3. Decision record

The reviewer accepted all eight requested design decisions: base retention and
above-tower loss remain distinct from gaps; uncoordinated overlap blocks by
default; overlapping bands are allocated once before shares; priority order is
complete; unnecessary priority coordination is rejected; CT3 retains the
one-to-four-layer limit; annual capacity remains deferred to CT5; and the four
retained-loss buckets form a complete partition of subject loss.

## 4. Freeze decision

CT3 Implementation Specification v1.1 is frozen for implementation. The next
authorized checkpoint is immutable CT3 domain models and their validation
tests. No CT3 production code is included in this specification checkpoint.
