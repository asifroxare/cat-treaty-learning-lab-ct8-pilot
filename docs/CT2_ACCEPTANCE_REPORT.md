# CT2 Acceptance Report

**Status:** PASS — CT2 implementation complete

## Implemented scope

CT2 now provides the complete pure-Python path from a declared initial insured
loss to a validated Cat XL subject loss:

1. immutable loss-basis and inuring contracts;
2. F03 Ultimate Net Loss construction;
3. independent F04 loss-basis reconciliation;
4. F05 scoped cover subject loss;
5. F06 calculated proportional or supplied recovery;
6. F07 occurrence and aggregate constraints;
7. F08 explicitly ordered sequential consumption;
8. F09 per-row and total-waterfall reconciliation;
9. deterministic explanations, warnings and assumption disclosures;
10. CT2 canonical serialization, versioned SHA-256 input hashing; and
11. an explicit completion gate for future CT3 consumers.

## Acceptance gates

| Gate | Evidence | Result |
|---|---|---|
| CT1 regression | Complete pre-CT2 suite remains included and passing | PASS |
| Source boundary | AST audit rejects imports from pricing, API or frontend engines | PASS |
| Named stages | Models retain initial insured loss, UNL, every incoming/outgoing cover loss and Cat XL subject loss | PASS |
| UNL reconciliation | F03/F04 component, boundary, exclusion and overflow tests | PASS |
| Inuring reconciliation | Every cover row and total waterfall carry passed F09 checks | PASS |
| Ordering | Immutable input rejects implicit, duplicate or noncontiguous order | PASS |
| Double counting | Duplicate cover/source IDs and recovery above scoped current loss fail | PASS |
| Valuation modes | Calculated quota-share and supplied modes have mutually exclusive inputs | PASS |
| Aggregate lifecycle | Before/after state reconciles; cross-occurrence persistence remains outside CT2 | PASS |
| Completion gate | Raw gross/subject losses cannot substitute for a completed CT2 result | PASS |
| Metadata | Equivalent inputs serialize and hash identically; actuarial/version changes alter hash | PASS |
| Golden cases | G06 and G17–G25 execute with permanent trace IDs | PASS |
| Product separation | Product identity remains distinct from the Cat XOL Pricing Lab | PASS |

## Golden-case disposition

| Cases | Disposition at CT2 close |
|---|---|
| G01–G05 | Preserved CT1 occurrence compatibility cases |
| G06 | Executed in CT2: quota share inures before Cat XL |
| G07–G13 | Preserved for later treaty-year, tower, simulation and hours-clause milestones |
| G14–G16 | Preserved CT1 fixed/zero-share cases |
| G17–G25 | Executed in CT2 |

## Explicit boundary carried into CT3

CT2 does not calculate Cat XL attachment, recovery or tower geometry. CT3 may
consume only an `InuringWaterfallResult` accepted by
`require_ct3_eligible_waterfall()`. It may not substitute a raw pricing-lab
`gross_event_loss` or an unverified scalar.

No API, frontend, simulation, pricing, capital or deployment work is included
in CT2.

## Verification summary

- Full repository suite: 485 tests passed.
- Dependency integrity: no broken requirements.
- Python compilation: passed.
- Import and absolute-path boundaries: passed.
- Package extraction, isolated source import and independent rerun: passed
  before delivery.
