# CT3 Acceptance Report

**Status:** PASS — CT3 implementation complete

**Specification:** CT3 Implementation Specification v1.1

## Implemented scope

CT3 now provides the complete pure-Python path from a verified CT2 Cat XL
subject loss to an auditable one-occurrence, multi-layer Cat XL program result:

1. immutable one-to-four-layer program contracts;
2. verified CT2 occurrence, reporting currency and input-hash entry;
3. deterministic layer ordering and geometry segmentation;
4. continuous, ventilated, overlapping and mixed topology classification;
5. separate topology classification and contractual eligibility;
6. acknowledged-gap and explicit priority-overlap controls;
7. F11 independent layer covered loss;
8. F12 allocate-once priority coordination;
9. F13 separate ceded-share and placement-share recovery;
10. F14 layer retained participation;
11. F15 program recovery and insurer net loss;
12. F16 loss-band and retained-bucket reconciliation;
13. deterministic explanations, warnings and assumptions; and
14. versioned canonical serialization and SHA-256 input hashing.

## Acceptance gates

| Gate | Evidence | Result |
|---|---|---|
| CT1/CT2 regression | All 545 pre-final-checkpoint tests remain included and passing | PASS |
| CT2 entry | Program model verifies occurrence, currency and reconstructed CT2 input hash | PASS |
| Models | Immutable terms, results, issue records and response envelope validations | PASS |
| Geometry | Boundaries, segments, topology and deterministic order recompute independently | PASS |
| Gap control | Acknowledged gaps reconcile; unacknowledged gaps return geometry and block recovery | PASS |
| Overlap control | Uncoordinated overlap blocks; complete priority allocates each band once | PASS |
| Shares | Ceded and placement shares remain separate and functional per layer | PASS |
| Program reconciliation | F15 and both F16 checks pass independently | PASS |
| Metadata | Canonical order is stable; contractual and version changes alter the hash | PASS |
| Source boundary | CT3 domain modules do not import pricing, API or frontend engines | PASS |
| Product separation | Product identity remains distinct from the Cat XOL Pricing Lab | PASS |
| Golden cases | G01–G05, G10 and G26–G34 execute with permanent IDs | PASS |

## Golden-case disposition

| Cases | CT3 disposition |
|---|---|
| G01–G05 | Single-layer compatibility independently executed through CT3 |
| G06 | Preserved CT2 inuring-before-Cat-XL case |
| G07–G09 | Reserved for later treaty-year and simulation milestones |
| G10 | Ventilated program executed through CT3 |
| G11–G13 | Reserved for later simulation and hours-clause milestones |
| G14–G16 | Preserved CT1 fixed/zero-share cases |
| G17–G25 | Preserved CT2 loss-basis and inuring cases |
| G26–G34 | Executed through CT3 |

## Explicit boundary carried forward

CT3 evaluates one completed occurrence. It does not implement annual aggregate
capacity, reinstatements, chronological event processing, hours-clause
occurrence election, OEP/AEP simulation, technical pricing, capital analytics,
API endpoints, frontend screens or deployment. Annual tower capacity remains a
CT5 responsibility under the frozen architecture.

## Distribution gate

Before delivery, the complete repository archive must be extracted to a new
directory and independently checked for:

- successful package import and Python compilation;
- the full test-suite pass count;
- expected CT3 Git commit identity;
- no uncommitted files in the extracted Git worktree; and
- a disclosed SHA-256 archive digest.
