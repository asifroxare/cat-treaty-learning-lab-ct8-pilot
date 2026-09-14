# CT1 Acceptance Report

Status: **PASS — CT1 implementation complete**

## Scope accepted

CT1 establishes the compatibility foundation between the completed Cat XOL
Pricing Lab and the separate Catastrophe Treaty Learning Lab. It does not copy
the pricing simulator or introduce a second pricing engine.

Implemented and tested:

- immutable canonical event, processed-event, annual and pricing models;
- deterministic product, engine and schema metadata plus normalized hashes;
- structural adapters for validated pricing-lab event, recovery, year and
  pricing records;
- independent `ceded_share` and `placement_share` treatment;
- payable-placed-share capacity scaling with fixed shares per annual trial;
- the three-way settlement ledger and presentation invariant;
- versioned legacy/canonical request resolution and migration notices; and
- CT1 golden-case execution and CT0 milestone traceability.

## Golden-case disposition

| Cases | CT1 disposition |
|---|---|
| G01–G06 | Executed in CT1 against authoritative occurrence results |
| G07–G10 | Preserved for CT2/CT3; G08 settlement invariant is already unit-tested |
| G11 | Preserved for CT4 catalogue/simulation testing |
| G12 | Preserved for CT6 capital testing |
| G13 | CT0 hours-clause occurrence-election case; requires the later occurrence engine |
| G14 | Executed in CT1 for two-event fixed-share capacity equivalence |
| G15–G16 | Executed in CT1 with explicit zero-capacity N/A status |

This disposition does not claim later-milestone scenarios as CT1 passes.

## Required regression evidence

| Gate | Evidence | Result |
|---|---|---|
| Reproduced pricing baseline | `docs/CT0_REPRODUCTION_GATE.md`: 154 backend and 8 frontend tests | PASS |
| Recovery identity | Default-share processed-event adapter tests | PASS |
| Functional shares | Six F02 share combinations and boundaries | PASS |
| Capacity basis | Payable-placed scaling and G14 fixed-share equivalence | PASS |
| Zero capacity | G15/G16 return `null` utilization and explicit N/A status | PASS |
| Pricing identity | Components, metrics, targets and reinstatement premium preserved | PASS |
| Settlement invariant | Gross recovery and capacity unchanged between presentations | PASS |
| Metadata | Stable versions and normalized SHA-256 hashes | PASS |
| Compatibility | Legacy defaults and explicit `ct1.0` negotiation | PASS |
| Product separation | Treaty product ID/route remain distinct from pricing product | PASS |

## Boundary carried into CT2

CT1 consumes already validated occurrence and recovery records. It deliberately
does not implement tower geometry, hours-clause election, inuring calculations,
event simulation, pricing calculations, UI, API endpoints or deployment. Those
remain governed by their later frozen milestones.
