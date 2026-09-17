# Catastrophe Treaty Learning Lab — CT6 FastAPI Contract and Backend Orchestration Specification

**Milestone:** CT6 — FastAPI Contract and Backend Orchestration  
**Version:** 0.9-review  
**Status:** Draft for independent validation; implementation is not authorized  
**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority and dependency chain

CT6 exposes, but does not reinterpret, the accepted CT0–CT5 engine. Its
authoritative installed baseline is CT5 commit `a589d4a`, engine `ct5.0.0`,
schema `ct5.0`, with 932 passing tests.

The following remain authoritative:

- CT2 for Ultimate Net Loss and ordered inuring-reinsurance calculations;
- CT3 for program geometry and pre-annual-capacity occurrence recovery;
- CT4 for catalogue application, hours-clause election, ordering and
  pre-capacity tail analytics;
- CT5 for annual capacity, reinstatements, settlement, post-capacity analytics
  and deterministic identity; and
- every frozen tolerance, warning, reconciliation and golden-case convention
  in those milestones.

FastAPI, Pydantic and JSON are transport/adaptation layers. No actuarial formula may be implemented in an endpoint, response model, serializer or frontend-facing helper.

## 2. Purpose

CT6 provides a versioned, deterministic, auditable interface through which the
future learning frontend can:

1. submit one complete catalogue-defined or hours-clause teaching run;
2. invoke CT2 through CT5 in the mandatory sequence;
3. receive both pre-capacity and post-capacity results without conflation;
4. see warnings, exclusions, reconciliations and explanations;
5. reproduce run identities and canonical hashes; and
6. distinguish invalid input, contract blockage and server failure.

CT6 is not a database, job queue, authentication system, catastrophe model,
pricing engine or production deployment milestone.

## 3. Frozen architectural boundaries

### 3.1 Included

- FastAPI application factory and versioned routes;
- strict Pydantic request and response DTOs;
- explicit DTO-to-domain adapters;
- synchronous orchestration of the accepted CT2–CT5 functions;
- catalogue-defined and bounded hours-clause teaching modes;
- health, readiness and capability discovery;
- structured errors and stable machine-readable error codes;
- request correlation IDs;
- OpenAPI generation and contract tests;
- response-detail controls that never change authoritative calculations; and
- deterministic identity exposure.

### 3.2 Excluded

- actuarial calculations inside the API layer;
- persistence, user accounts, authentication and authorization;
- asynchronous jobs, queues, polling and web sockets;
- file upload, spreadsheet import/export and report generation;
- caching authoritative results;
- multiple currencies or FX conversion;
- user-supplied Python, formulas or executable expressions;
- API-driven mutation of frozen engine/schema versions;
- frontend implementation; and
- hosting, rate limiting, observability infrastructure and production secrets.

## 4. API identity and media type

- API title: `EdInsured Catastrophe Treaty Learning Lab API`
- API version: `ct6.0.0`
- API schema version: `ct6.0`
- Base path: `/api/v1`
- Product ID: `cat_treaty_learning_lab`
- Product route: `/cat-treaty`
- Request and response media type: `application/json`
- Character encoding: UTF-8
- OpenAPI document: `/openapi.json`
- Interactive documentation may be enabled outside production and disabled by
  deployment configuration without changing the contract.

Every successful run response declares the CT2, CT3, CT4, CT5 and CT6 engine
and schema versions used. A client may not choose or override an engine
version in v1.

## 5. Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Human-readable service identity; no engine execution |
| GET | `/health/live` | Process liveness only |
| GET | `/health/ready` | Import/configuration readiness; no simulation |
| GET | `/api/v1/capabilities` | Frozen versions, modes, enums and limits |
| POST | `/api/v1/runs/catalogue` | Complete catalogue-defined CT2–CT5 run |
| POST | `/api/v1/runs/hours-clause` | Complete bounded CT4 election followed by CT5 entry |

There is no generic route that infers run mode from whichever fields happen to
be present. Separate POST routes prevent ambiguous union parsing.

## 6. Common wire rules

1. Models use strict validation: booleans are not numbers, numeric strings are
   not coerced and unknown fields are rejected.
2. Enum values use their frozen lowercase wire strings.
3. All monetary values are JSON numbers in the declared reporting currency.
4. NaN, positive infinity and negative infinity are forbidden on input and
   output.
5. IDs are case-sensitive, trimmed non-empty strings. The server never silently
   rewrites an ID.
6. Ordered contractual arrays remain ordered. Unordered presentation arrays
   are canonicalized only where the upstream specification permits it.
7. `null` is semantically distinct from zero. In particular, zero-capacity and
   other not-applicable metrics retain their frozen null/status pairs.
8. Dates/times remain the finite numeric treaty-time coordinates frozen by
   CT4/CT5; CT6 does not introduce timezone conversion.
9. Request models and response models are different types. Clients cannot
   submit calculated response fields as authoritative inputs.
10. Descriptions and source/rule references remain visible but never replace
    machine-readable codes or calculated fields.

## 7. Common request envelope

Both run routes accept:

```json
{
  "api_schema_version": "ct6.0",
  "client_request_id": "optional-client-id",
  "response_detail": "full",
  "input": {}
}
```

Rules:

- `api_schema_version` is mandatory and must equal `ct6.0`;
- `client_request_id` is optional, non-empty when supplied, and is echoed but
  excluded from all actuarial hashes;
- `response_detail` is `full` or `summary` and defaults to `full`; and
- `input` contains the route-specific authoritative input.

The server generates a UUID request correlation ID for every request. It is
returned as `X-Request-ID` and in the body. A syntactically valid incoming
`X-Request-ID` may be propagated; it is never included in deterministic hashes.

## 8. Catalogue request contract

`POST /api/v1/runs/catalogue` accepts one end-to-end source request rather than
asking the client to manufacture calculated CT2–CT5 results.

### 8.1 Simulation header

- `simulation_id`;
- `trial_count`;
- `catalogue_version` and `source_version`;
- `simulation_seed`, nullable when the supplied catalogue is not generated;
- CT4 tail configuration; and
- the frozen numerical-tolerance profile, which must equal the supported
  profile rather than being user-adjustable.

### 8.2 Annual trials and occurrences

Trials are contiguous from 1 through `trial_count`; empty trials are required
and preserved. Each occurrence supplies:

- annual-trial ID, event ID, event time and declared event sequence;
- peril, region and source/trace references;
- raw CT2 `LossBasisInput` fields and visible included/excluded components; and
- ordered raw `InuringCoverInput` fields.

The client does not supply `LossBasisResult`, `InuringWaterfallResult`, CT3
recovery, CT4 ledger, CT5 ledger, analytics or hashes. CT6 constructs those by
calling the accepted engines.

### 8.3 Program and annual-capacity terms

The request supplies one simulation-wide:

- CT3 program ID, one to four layers, intentional-gap acknowledgement,
  overlap coordination and complete priority order when required; and
- CT5 term record for every CT3 layer, including original layer premium,
  treaty bounds, ordered reinstatement tranches and settlement mode.

CT6 applies the fixed program terms to every occurrence. Per-event or mid-year
term/share variation is rejected before execution.

## 9. Hours-clause request contract

`POST /api/v1/runs/hours-clause` is restricted to CT4's bounded teaching mode:

- one scenario and one annual trial;
- one to twelve timestamped components;
- treaty hours, peril, region and causal admissibility rules;
- all contractually authorized election methods;
- one selected election method and a manual candidate-set ID only for manual
  election;
- one validated CT3 program-terms source contract; and
- matching CT5 terms for every layer.

The route first generates candidate windows/sets and exclusion evidence, then
elects only from valid sets. A higher-recovery invalid split is never eligible.
Only the elected CT4 occurrence rows and their elected-window times enter CT5.
Blocked election returns a structured non-success response and no CT5 ledger
or analytics.

The hours request may use the frozen domain-shaped program-terms source in v1.
CT6 must validate its CT2/CT3 identity; it may not fabricate an unreported loss
basis or silently assume that inuring recovery is zero.

## 10. Mandatory orchestration sequence

For catalogue mode the orchestrator performs exactly:

1. parse the strict wire DTO;
2. construct and validate CT2 loss-basis inputs;
3. call F03/F04 loss-basis construction;
4. construct and call F05–F09 inuring waterfalls;
5. build CT2 metadata;
6. construct CT3 program inputs from the common terms;
7. evaluate geometry eligibility and F11–F16 occurrence recovery;
8. construct the complete CT4 simulation input;
9. run catalogue preflight and deterministic occurrence ordering;
10. apply the CT4 catalogue and calculate tail/frequency analytics;
11. build and reproduce the CT4 identity;
12. apply CT5 annual capacity and F25–F37 orchestration;
13. calculate CT5 analytics;
14. reproduce CT4 identity inside CT5 and build CT5 identity;
15. build explanations exclusively from structured domain facts; and
16. serialize the response.

Hours-clause mode replaces steps 2–10 with the frozen CT4 hours-clause
generation, admissibility and election flow, while retaining identity checks
and the rule that only elected rows enter CT5.

Any failed step terminates the run. The API never returns a partial success
containing authoritative downstream figures.

## 11. Success response contract

Both run routes return HTTP 200 with:

```json
{
  "api": {},
  "request": {},
  "versions": {},
  "identity": {},
  "pre_capacity": {},
  "post_capacity": {},
  "learning": {},
  "warnings": []
}
```

### 11.1 `api`

- request correlation ID;
- echoed client request ID, nullable;
- API/schema versions;
- completion status `complete`; and
- run mode.

### 11.2 `request`

- simulation/scenario ID;
- reporting currency;
- trial and occurrence counts;
- program ID and layer IDs; and
- response-detail mode.

This is an input summary, not a second authoritative input representation.

### 11.3 `versions` and `identity`

- CT2–CT6 engine/schema versions;
- CT4 input/result hashes;
- CT5 input/result hashes; and
- simulation identity.

Hashes are lowercase SHA-256 strings and are identical for identical canonical
inputs/results regardless of request ID, description wording, response-detail
mode or JSON object-key order.

### 11.4 `pre_capacity`

Clearly labelled CT4 results:

- occurrence and annual ledgers when `response_detail=full`;
- CT4 tail and frequency analytics;
- geometry, candidate/exclusion and election evidence when applicable;
- pre-annual-capacity gross contractual recovery; and
- pre-capacity insurer net loss.

No field in this section may be labelled simply `annual_treaty_recovery`.

### 11.5 `post_capacity`

Clearly labelled CT5 results:

- layer/event/annual ledgers when `response_detail=full`;
- the three-way settlement fields: gross contractual recovery,
  reinstatement premium payable and net cash settlement;
- insurer-net and capacity-shortfall fields;
- six-perspective post-capacity analytics;
- utilization and exhaustion metrics with status fields; and
- every reconciliation flag.

### 11.6 `learning`

Structured facts and concise explanations must identify:

- loss-stage transformations and inuring order;
- geometry classification, gaps and overlap controls;
- why each layer attached, exhausted or paid zero;
- pre-capacity entitlement versus post-capacity recovery;
- capacity consumed/restored and tranche attribution;
- reinstatement premium amount/time factors;
- settlement-mode effect; and
- warning and exclusion reasons.

The explanation layer may translate structured facts into prose but may not
calculate or alter a monetary result.

### 11.7 `summary` response detail

`summary` omits occurrence-, layer-event- and curve-point arrays only. It
retains annual summaries, all headline analytics, warnings, reconciliations,
exclusion/election evidence and identities. Full internal results are still
calculated before hashing. Therefore `full` and `summary` produce identical
CT4/CT5 hashes.

## 12. Error contract

All non-success bodies use a Problem Details-style object:

```json
{
  "type": "https://edinsured.example/problems/domain-validation",
  "title": "Domain validation failed",
  "status": 422,
  "code": "CT6_DOMAIN_VALIDATION",
  "detail": "The request violates the treaty contract.",
  "instance": "/api/v1/runs/catalogue",
  "request_id": "...",
  "errors": [
    {
      "path": "input.trials[0].occurrences[0].loss_basis",
      "code": "CT2_NEGATIVE_UNL",
      "message": "Applied deductions exceed insured loss and additions.",
      "rule_reference": "CT2-F03-F04"
    }
  ]
}
```

| HTTP | Stable code | Use |
|---|---|---|
| 400 | `CT6_MALFORMED_JSON` | Invalid JSON or media type |
| 409 | `CT6_VERSION_CONFLICT` | Unsupported API/domain schema version |
| 413 | `CT6_REQUEST_TOO_LARGE` | Byte/count limit exceeded |
| 422 | `CT6_SCHEMA_VALIDATION` | DTO shape/type/unknown-field failure |
| 422 | `CT6_DOMAIN_VALIDATION` | Frozen domain rule failure |
| 422 | `CT6_CONTRACT_BLOCKED` | Geometry, preflight or election blockage |
| 500 | `CT6_INTERNAL_ERROR` | Unexpected server failure |
| 503 | `CT6_NOT_READY` | Required engine/configuration unavailable |

Warnings and credibility cautions never turn a valid run into an error. They
remain structured entries in an HTTP 200 response. Stack traces, local paths,
environment values and raw exception representations are never returned.

Validation errors are deterministically ordered first by request path and then
by stable code. One request may disclose multiple independently detectable
input errors, but no engine calculation proceeds after validation failure.

## 13. Limits and execution policy

Proposed CT6 v1 API limits:

- request body: 25 MiB;
- catalogue trials: 1–50,000;
- total catalogue occurrences: 0–250,000;
- layers: 1–4;
- hours-clause components: 1–12;
- full-detail occurrence rows: at most 25,000; and
- processing: synchronous, one response per request.

If a valid request exceeds the full-detail row limit, the server returns 413
with guidance to request `summary`; it does not silently downgrade. Requests
within engine limits but unsuitable for synchronous deployment are a future
asynchronous milestone, not partially implemented in CT6.

These are API/deployment protection limits, not actuarial assumptions and not
inputs to deterministic hashes.

## 14. Health and capability contracts

`GET /health/live` returns HTTP 200 when the process event loop can answer. It
does not import every engine or execute a sample run.

`GET /health/ready` checks that required modules and supported version
constants are available. It performs no stochastic simulation and exposes no
secrets. It returns 200 `ready` or 503 `not_ready` with stable check names.

`GET /api/v1/capabilities` returns:

- API and CT2–CT5 supported versions;
- supported run modes, enums, settlement modes and election methods;
- numerical tolerance profile;
- route limits and response-detail modes; and
- product identity.

Capabilities are descriptive and cannot override the engine.

## 15. Determinism and idempotence

- Identical canonical contractual inputs produce identical CT4/CT5 hashes and
  numerical results.
- Request IDs, timing, host, response detail, descriptions and explanation
  wording do not enter actuarial hashes.
- CT6 introduces no random draw. A supplied seed is passed through only to the
  frozen catalogue identity that already owns it.
- JSON object-key order is irrelevant; contractual array order remains
  significant where frozen upstream.
- Repeating a request is computationally idempotent but creates a new HTTP
  transaction; CT6 stores no run and promises no exactly-once execution.
- Serialization uses finite JSON numbers and preserves the upstream canonical
  SHA-256 implementations rather than hashing the presentation response.

## 16. Security and deployment-neutral controls

- CORS origins are configuration, never `*` with credentials in production.
- Request size is checked before expensive parsing where the server permits.
- Error handling redacts stack traces and local implementation details.
- The API never reads arbitrary client paths or URLs.
- Source/reference strings are data, never templates or executable code.
- Secrets are supplied only by deployment configuration and are never included
  in capabilities, responses or hashes.
- Production rate limiting, authentication and network policy are deferred but
  the application factory must allow them to be added without changing the
  actuarial contract.

## 17. OpenAPI and compatibility rules

The generated OpenAPI document is contract-tested. Every documented success
and error model must be referenced by the relevant route. Examples are valid
against their schema.

Within `ct6.0`, fields may be added only when optional and non-authoritative.
Renaming/removing a field, changing a default, changing enum meaning, changing
an HTTP/error code, or changing the orchestration sequence requires a new API
schema version. A CT2–CT5 engine/schema change also requires explicit CT6
compatibility review even if the HTTP shape appears unchanged.

## 18. Performance and observability tests

CT6 freezes correctness before performance. Tests must measure, not promise, a
reference runtime for small, medium and declared-limit fixtures. No hard
wall-clock pass threshold is portable across machines in v1.

Structured server logs may contain request ID, route, status, duration,
counts, versions and the first 12 characters of result hashes. Logs must not
contain the full input, full loss ledger, secrets or stack traces for expected
4xx failures. Logging must not change the response or deterministic identity.

## 19. Golden API cases

G01–G68 retain their frozen meanings. CT6 adds:

| ID | Scenario | Expected check |
|---|---|---|
| G69 | Liveness/readiness | Stable 200 contracts and no simulation execution |
| G70 | Catalogue end to end | One request runs CT2–CT5 and returns both capacity views |
| G71 | Hours-clause end to end | Only the valid elected CT4 occurrences enter CT5 |
| G72 | Malformed JSON | 400 problem body with request ID and no traceback |
| G73 | Strict schema failure | Numeric string/unknown field is rejected with path evidence |
| G74 | Contract blockage | Invalid gap/overlap/election returns 422 and no downstream result |
| G75 | Deterministic repeat | Repeated canonical input has identical results and hashes |
| G76 | Permitted input permutation | Non-contractual ordering changes neither result nor hashes |
| G77 | Response detail | Full and summary responses retain identical authoritative hashes |
| G78 | Negative cash settlement | Finite negative value survives JSON and analytics unchanged |
| G79 | Zero capacity | Value remains null with explicit not-applicable status |
| G80 | Credibility warnings | Valid run returns 200 with all cumulative warnings |
| G81 | API limit | Oversized full request fails explicitly; no silent truncation/downgrade |
| G82 | Internal failure containment | Sanitized 500 response and no partial actuarial payload |

## 20. Required test modules

- `tests/test_ct6_models.py` — strict DTO shape, enums and null semantics;
- `tests/test_ct6_adapters.py` — exact DTO/domain mapping and no calculations;
- `tests/test_ct6_orchestration.py` — mandatory CT2–CT5 call sequence;
- `tests/test_ct6_api.py` — routes, status codes and response schemas;
- `tests/test_ct6_errors.py` — stable problem bodies and sanitization;
- `tests/test_ct6_openapi.py` — schema snapshot and example validation;
- `tests/test_ct6_determinism.py` — hashes, repeats and detail modes;
- `tests/test_ct6_limits.py` — byte/count boundaries; and
- `tests/test_ct6_golden_cases.py` — G69–G82 consolidated acceptance.

All existing CT1–CT5 tests remain mandatory. CT6 acceptance cannot weaken,
skip, xfail or replace an upstream test.

## 21. Implementation checkpoints

1. Freeze this specification after independent review.
2. Implement strict API DTOs and conversion-only adapters.
3. Implement catalogue orchestration and identities.
4. Implement hours-clause orchestration and CT5 entry.
5. Implement success projections, summary/full detail and learning facts.
6. Implement structured errors, health, capabilities and OpenAPI tests.
7. Complete G69–G82, full regression and distribution verification.

Each checkpoint requires a clean commit and the entire regression suite before
the next begins.

## 22. Completion gate

CT6 is complete only when:

- independent review findings are resolved in a disposition document;
- the API contains no actuarial formula duplication;
- G69–G82 pass with permanent trace IDs;
- all CT1–CT5 tests continue to pass;
- OpenAPI matches the frozen contract;
- malformed, invalid and blocked requests never return partial success;
- identical canonical runs reproduce CT4/CT5 hashes;
- a fresh environment passes dependency, import and complete test gates; and
- the installation package is built and retested from the final clean commit.

## 23. Questions for independent validation

1. Is accepting raw CT2 loss-basis/inuring inputs for catalogue mode the right
   boundary, rather than accepting client-manufactured CT2/CT3 results?
2. Is the frozen domain-shaped program source acceptable for the bounded
   hours-clause route, given the prohibition on fabricated loss basis?
3. Are separate catalogue and hours routes preferable to one discriminated
   union route?
4. Does `summary` omit the right presentation arrays while preserving enough
   audit evidence and identical authoritative hashes?
5. Should contract blockage remain HTTP 422, distinct by stable code, or use
   HTTP 409?
6. Are the proposed synchronous limits suitable for a learning lab, and should
   exceeding the full-detail row limit be 413 rather than 422?
7. Is returning cumulative credibility warnings under HTTP 200 correct?
8. Does the error schema provide enough deterministic path/rule evidence
   without leaking implementation detail?
9. Are G69–G82 sufficient to freeze the API and orchestration contract?
10. Is any response field capable of confusing pre-capacity entitlement with
    post-capacity annual recovery or gross recovery with net cash settlement?
