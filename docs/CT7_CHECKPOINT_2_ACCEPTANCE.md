# CT7 Checkpoint 2 Acceptance

**Checkpoint:** Frontend foundation, design tokens, routing and CT6 client contract

**Frozen authority:** CT7 v1.3, commit `8043ea4`

**Status:** Accepted after consolidated verification

## Delivered

- React/Vite/TypeScript application foundation;
- semantic product shell and educational disclaimer;
- responsive design-token system with visible focus and reduced-motion rules;
- all six frozen destinations and fallback routing;
- committed CT6 OpenAPI snapshot and generated TypeScript schema;
- OpenAPI drift check against the live FastAPI application;
- request types for catalogue and hours-clause routes;
- deep branded `AuthoritativeNumber` response boundary;
- exact CT6 problem-code to execution-state mapping;
- orthogonal `ResultFreshness` contract;
- dedicated catalogue/hours HTTP client with request-ID propagation;
- fail-closed handling for offline, malformed and incomplete responses; and
- source import/raw-HTML boundary check.

## Deliberately deferred

- treaty request forms and builders (checkpoint 3);
- catalogue result visualizations (checkpoint 4);
- hours-clause interaction (checkpoint 5);
- guided experiments and comparison (checkpoint 6);
- complete G84–G105/static-geometry/accessibility gates (checkpoints 7–8); and
- public deployment.

## Authority controls

No actuarial formula was added. Generated CT6 transport types are confined to
`src/api`; features receive only public request contracts or branded
authoritative responses. The frontend performs no recovery, capacity,
reinstatement, settlement or tail calculation.

## Acceptance gates

- CT6 OpenAPI snapshot equality: **PASS**;
- generated types and application compile under strict TypeScript: **PASS**;
- source-boundary check: **PASS**;
- frontend test suite: **26 passed in 5 files**;
- production build without source maps: **PASS**;
- dependency audit: **0 vulnerabilities**;
- complete CT1–CT6 regression: **1003 passed**; and
- backend warnings: **2 existing dependency deprecation warnings**.

## Verification record

Verified on 20 September 2026 with Node 24 and the isolated Python test
environment. The production bundle contained 31 transformed modules. Its
largest JavaScript artifact was 265.16 kB before gzip and 84.31 kB after gzip.
The checkpoint does not alter any CT1–CT6 Python source or frozen actuarial
formula.
