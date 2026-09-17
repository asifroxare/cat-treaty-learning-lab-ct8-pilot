# CT6 Checkpoint 1 Acceptance — Strict Models and Adapters

**Specification:** CT6 v1.0  
**Checkpoint:** Strict request/response wire models and conversion-only adapters  
**Status:** Accepted

Implemented:

- frozen strict Pydantic models with unknown-field rejection and no numeric-string coercion;
- catalogue provenance and generated/supplied seed rules;
- raw CT2 loss-basis and ordered inuring-cover source models;
- common CT3 program and exact CT5 layer-term mapping;
- bounded hours-clause input with mandatory disclosed program source;
- frozen tolerance, tail, settlement and reinstatement enum contracts;
- exact pre-/post-capacity and three-way settlement response field models;
- deterministic identity and Problem Details response foundations; and
- immutable conversion-only adapters into CT2, CT3, CT4 and CT5 input objects.

The adapter module imports no calculation, simulation, analytics, pricing,
capacity or identity engine. It constructs immutable inputs only. Endpoint and
orchestration implementation remains outside this checkpoint.

Acceptance evidence:

- strict type, extra-field, finite-number, provenance and mapping tests pass;
- hours source disclosure survives adaptation exactly;
- negative net cash settlement remains valid and unfloored;
- architecture tests prohibit engine imports in the adapter; and
- the complete CT1–CT6 regression suite passes.
