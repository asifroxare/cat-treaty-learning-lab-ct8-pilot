# CT7 Checkpoint 6 Acceptance

**Checkpoint:** Guided Lab experiments and independent comparison

**Frozen authority:** CT7 v1.3

**Status:** Accepted after consolidated verification

## Delivered

- versioned E01–E07 scenario catalogue with complete typed CT6 requests;
- one declared controlled input mechanism per experiment;
- prediction gate before baseline or scenario execution;
- independent baseline/scenario transport calls and identities;
- API-backed facts, warnings, trace references and audit hashes;
- typed result-specific takeaway content with mandatory evidence paths;
- fail-closed suppression when any evidence path is unresolved;
- production content-neutrality gate banning recommendation/ranking language;
- E07 routed through the CT6 hours-clause contract;
- side-by-side comparison using separate complete requests and responses;
- visible controlled input field without client-calculated result deltas; and
- currency/schema compatibility guard that preserves both independent results.

## Seven experiments

- E01 changes one disclosed inuring cession;
- E02 moves one Cat XL attachment;
- E03 changes placement share while ceded share remains fixed;
- E04 adds a later occurrence to the same annual trial;
- E05 switches a paid reinstatement tranche to free;
- E06 changes the annual-trial sample; and
- E07 changes the authorized hours-clause election method.

Production scenarios contain no expected numerical result. Tests use response
fixtures tied to the frozen CT6 schema.

## Comparison boundary

The UI displays baseline and scenario with identical labels, units and
precision. It does not calculate monetary/percentage deltas and does not attach
changed, higher/lower, improvement, ranking or recommendation badges to output
rows. Failed runs cannot overwrite their counterpart.

## Deliberately deferred

- full type-aware G102 static fixtures and comprehensive accessibility/security
  hardening (checkpoint 7);
- G84–G105 and real-API browser acceptance (checkpoint 8); and
- final installation/reproduction package (checkpoint 9).

## Acceptance evidence

- CT6 OpenAPI snapshot equality: **PASS**;
- source and presentation-geometry boundaries: **PASS**;
- guided-content neutrality gate: **PASS**;
- frontend suite: **52 tests passed in 13 files**;
- strict TypeScript and production build: **PASS**;
- production bundle: **53 transformed modules**, largest JavaScript artifact
  **324.25 kB** before gzip and **97.19 kB** after gzip;
- dependency audit: **0 vulnerabilities**; and
- complete CT1–CT6 regression: **1003 passed**, with the same two dependency
  deprecation warnings.
