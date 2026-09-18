# CT6 Checkpoint 4 Acceptance — Authoritative Success Responses

**Specification:** CT6 v1.0  
**Checkpoint:** Full/summary projection, audit evidence and learning facts  
**Status:** Accepted

The response projector now exposes:

- frozen API, request-summary, version and CT4/CT5 identity sections;
- exact pre-capacity occurrence and annual field names;
- exact post-capacity occurrence, layer-event and annual field names;
- separate gross contractual recovery, reinstatement premium payable and net
  cash settlement values;
- CT4 and CT5 analytics without recomputation;
- complete hours candidate, exclusion and election evidence;
- cumulative CT3/CT4/CT5 warnings;
- structured CT2–CT5 reconciliation evidence; and
- structured learning facts for loss stages, occurrence geometry/recovery,
  annual capacity, reinstatement and settlement.

`full` includes authoritative occurrence, layer-event, sample and curve arrays.
`summary` omits only those presentation-heavy arrays while retaining annual
summaries, analytics estimates, warnings, reconciliations, learning facts,
candidate evidence and identities. Response detail and request correlation IDs
do not change CT4 or CT5 hashes.

Acceptance tests prove:

- frozen field names contain no ambiguous `recovery` or `net` aliases;
- summary/full identities are identical;
- summary retains warnings and invalid hours-split evidence;
- cumulative credibility warnings are not suppressed;
- every exposed reconciliation passes; and
- responses serialize as finite JSON without NaN or infinity.

This checkpoint adds no FastAPI routes or HTTP exception handlers.
