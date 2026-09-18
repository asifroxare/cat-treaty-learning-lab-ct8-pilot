# CT6 Final Acceptance and Audit Report

**Milestone:** CT6 FastAPI Contract and Backend Orchestration  
**Frozen specification:** `docs/CT6_IMPLEMENTATION_SPEC.md` v1.0  
**Starting checkpoint:** `e3d959d` — Implement CT6 FastAPI transport contract  
**Decision:** Accepted for installation-package verification

## 1. Scope accepted

CT6 exposes the frozen CT2–CT5 catastrophe treaty engines through separate
catalogue and hours-clause FastAPI routes. The API layer performs strict wire
validation, conversion-only adaptation, orchestration and authoritative
projection. It does not duplicate actuarial formulas.

Accepted public routes:

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Product and API identity |
| GET | `/health/live` | Process liveness without simulation |
| GET | `/health/ready` | Engine/version readiness without simulation |
| GET | `/api/v1/capabilities` | Versions, modes, tolerances and limits |
| POST | `/api/v1/runs/catalogue` | Catalogue-defined CT2 → CT3 → CT4 → CT5 run |
| POST | `/api/v1/runs/hours-clause` | Bounded hours-clause election and CT5 run |

## 2. Independent-review disposition

CT6-A through CT6-J remain closed in `docs/CT6_AUDIT_DISPOSITION.md`. CT6-K
records the only issue found during consolidated acceptance: annual layer
utilization/status evidence existed in CT5 but was not projected publicly.
The response now contains typed post-capacity `layer_summaries`; G79 verifies
the zero-capacity convention through the HTTP interface.

## 3. Permanent golden-case register

Every case has a permanent pytest node ID in
`cat_treaty.golden_cases.CT6_GOLDEN_CASE_EVIDENCE`.

| Case | Acceptance evidence |
|---|---|
| G69 | Liveness/readiness return stable 200 contracts and execute no simulation |
| G70 | Catalogue request completes CT2–CT5 and returns pre-/post-capacity views |
| G71 | Hours request sends only valid elected occurrences into CT5 and preserves election evidence |
| G72 | Malformed JSON returns sanitized 400 with request ID |
| G73 | Numeric strings and unknown fields return path-based strict-schema errors |
| G74 | Invalid contractual election returns 422 without downstream payload |
| G75 | Repeated canonical input preserves results and all hashes |
| G76 | Permitted component permutation preserves identities |
| G77 | Full/summary modes preserve hashes, warnings and election evidence |
| G78 | Finite negative net cash settlement survives JSON and annual aggregation unchanged |
| G79 | Zero capacity returns null utilization with explicit not-applicable status |
| G80 | All cumulative credibility warnings remain under HTTP 200 |
| G81 | Full-detail overflow returns 413 without truncation or downgrade |
| G82 | Unexpected failure returns sanitized 500 without partial actuarial payload |
| G83 | Unsupported string version returns 409; missing/wrong-typed version returns 422 |

Although the requested range was G69–G82, G83 is included because the frozen
CT6 completion gate explicitly makes version-conflict precedence mandatory.

## 4. Regression evidence

The complete CT1–CT6 suite was executed after all acceptance and runtime
changes:

```text
1003 passed, 2 warnings in 7.29s
No broken requirements found.
```

The two warnings are upstream FastAPI/Starlette TestClient deprecation notices.
They do not represent application failures, skipped tests or weakened gates.
No test is skipped, xfailed or substituted for an upstream CT1–CT5 test.

## 5. Runtime and security configuration

- `python -m cat_treaty` and the `cat-treaty-api` console entry start Uvicorn.
- Host, port, log level and CORS are environment configuration only.
- CORS uses an explicit allowlist; wildcard origins are rejected.
- Public problem text comes from a static reviewed catalogue.
- Stack traces, exception text, client values, paths and secrets are not
  included in public errors.
- Request size, synchronous catalogue counts and full-detail response limits
  are enforced without changing actuarial hashes.
- `.env.example` contains safe examples only; `.env` remains ignored.

## 6. Formula and identity controls

- The API imports frozen engines and contains no F03–F37 reimplementation.
- Gross contractual recovery, reinstatement premium payable and net cash
  settlement remain separate fields.
- Pre-annual-capacity and post-capacity recoveries remain separately named.
- CT4 and CT5 canonical hashes are preserved across request IDs, JSON key
  ordering and response-detail modes.
- Warnings, exclusions, election evidence and reconciliations remain
  structured and non-authoritative explanatory output.

## 7. Installation-package gate

The distribution must be created from the final clean commit, exclude virtual
environments/caches/secrets, pass archive-integrity testing, and be installed
into a fresh virtual environment. The accompanying distribution manifest
records the final commit, archive SHA-256, dependency check, import check and
fresh-package pytest result.

## 8. Final decision

The CT6 source and API contract are accepted. Deployment itself remains a
separate later milestone; this acceptance authorizes creation and independent
installation testing of the CT6 package, not public deployment.
