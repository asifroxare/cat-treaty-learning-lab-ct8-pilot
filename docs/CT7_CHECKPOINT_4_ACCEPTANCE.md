# CT7 Checkpoint 4 Acceptance

**Checkpoint:** Authoritative catalogue results, visualizations and audit trail

**Frozen authority:** CT7 v1.3

**Status:** Accepted after consolidated verification

## Delivered

- ordered catalogue result hierarchy sourced only from the CT6 success body;
- completion/scope summary and cumulative warning presentation;
- separate pre-annual-capacity entitlement and post-capacity settlement views;
- frozen three-way settlement names for contractual recovery, reinstatement
  premium payable and net cash settlement;
- negative net-cash preservation without flooring;
- annual capacity and reinstatement-reserve summaries with null/status handling;
- full-detail occurrence ledger and explicit summary-mode omission notice;
- structured CT6 learning facts with returned trace references;
- reconciliation table, engine/schema versions, request ID and all CT4/CT5
  deterministic hashes;
- proportional recovery visualization using the checked presentation-geometry
  boundary, with exact authoritative values retained in adjacent text; and
- dedicated Audit Trail route backed by shared catalogue run state.

## Calculation boundary

All displayed business values are branded CT6 authoritative numbers and pass
unchanged into `Intl.NumberFormat`. The only arithmetic introduced is isolated
inside `src/visualization/geometry/` and returns branded CSS coordinates used
solely for bar width. Geometry output is not displayed, serialized, logged or
used as a business result.

## Deliberately deferred

- detailed tail-series charts because the current CT6 OpenAPI contract exposes
  its analytics dictionaries as `unknown` rather than named numeric schemas;
- hours-clause workflow and election evidence (checkpoint 5);
- guided experiments and comparison (checkpoint 6); and
- complete type-aware G102 lint fixtures and accessibility hardening
  (checkpoints 7–8).

## Acceptance evidence

- CT6 OpenAPI snapshot equality: **PASS**;
- source and presentation-geometry boundaries: **PASS**;
- frontend suite: **39 tests passed in 8 files**;
- strict TypeScript and production build: **PASS**;
- production bundle: **44 transformed modules**, largest JavaScript artifact
  **294.18 kB** before gzip and **91.27 kB** after gzip;
- dependency audit: **0 vulnerabilities**; and
- complete CT1–CT6 regression: **1003 passed**, with the same two dependency
  deprecation warnings.
