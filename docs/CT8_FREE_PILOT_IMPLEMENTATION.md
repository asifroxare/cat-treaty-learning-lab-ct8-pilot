# CT8 invited free pilot — implementation review candidate

**27 September 2026 · No deployment, no measured production limits, no
approved host.** This package implements a separate *disabled by default*
Python pilot API and opt-in React presentation. The CT6 API, actuarial
engines, frozen identities and reference OpenAPI remain unchanged. The pilot
implementation is a candidate for independent review and owner reproduction;
it is **not** an approved final free-tier release.

## Separate paths

- Run the pilot only with the Uvicorn factory
  `cat_treaty.pilot_api:create_pilot_app` and `--factory`. It will refuse to
  start until all required `CT8_PILOT_*` settings are provided. No `app`
  variable is exported from the pilot module. The CT6 `cat_treaty.api:app`
  must never be started on the Free instance.
- The pilot app exposes only `/api/pilot/v1/runs/catalogue`,
  `/api/pilot/v1/runs/hours-clause`, `/api/pilot/v1/capabilities` and a
  minimal `/health/ready`. CT6 `/api/v1/runs/*`, OpenAPI and debug/docs
  endpoints are absent. The frontend's default build still calls CT6;
  an explicitly separate `VITE_CT8_PILOT_MODE=true` build calls pilot routes
  and labels its smaller test scope. Its build audit also requires an exact
  HTTPS `VITE_CT6_API_BASE_URL`, checks the compiled pilot route/origin and
  refuses a localhost origin. The variable name is inherited from CT7's
  presentation boundary; it never authorizes the CT6 route on the pilot host.
- `deployment/pilot_edge_worker.mjs` is a candidate proxy for a
  Cloudflare-protected pilot hostname. It only forwards named pilot paths
  to the dedicated Render custom-domain origin, **replaces** any incoming
  `X-CT8-Pilot-Origin` header with its secret, and does not proxy CT6 paths.
  The Python API verifies both this independent secret and a signed,
  unexpired, audience-bound Cloudflare Access JWT for an individually allowed
  email. Trusted Host must match the origin custom hostname. Disable the
  Render default `onrender.com` hostname after configuring the custom domain;
  reject direct custom-host requests without the proof or JWT. The two
  secrets/configurations must be provisioned only in provider settings.

## Required settings and conservative stops

`CT8_PILOT_ENABLED=true`, exact `CT8_PILOT_API_HOST`, exact HTTPS
`CT8_PILOT_UI_ORIGIN`, high-entropy `CT8_PILOT_ORIGIN_SECRET`,
`CT8_PILOT_ACCESS_TEAM`, `CT8_PILOT_ACCESS_AUDIENCE`, explicit
`CT8_PILOT_EMAIL_ALLOWLIST`, `CT8_PILOT_DEADLINE_SECONDS`, and a complete
`CT8_PILOT_LIMITS_JSON` are required. The limits JSON has exactly seven
fields: `max_body_bytes`, `max_trials`, `max_occurrences`, `max_layers`,
`max_hours_components`, `max_requests_per_minute`, and `allow_full_detail`.
Code-level ceilings (1 MiB body, 1,000 trials, 2,000 occurrences, 4 layers,
12 hours components, 10 requests/minute) are **upper stops for invalid
configuration**, never validated launch limits. Choose substantially lower
operational values only from full API tests under a free-sized resource
ceiling, including candidate hours and error precedence. No approved JSON
or access credentials are included in this package.

The pilot installs `requirements-pilot.txt` for JWT verification;
`requirements.txt` for the frozen CT6 app is unchanged.

The API authenticates before reading a request body, caps streamed bytes,
checks dimensions before model validation and slot acquisition, and accepts
one calculation at a time. Excess or out-of-scope work gets an explicit
pilot response; no silent downgrade or partial result. Successful responses
are projected by frozen CT6 Python code. The edge proxy and backend limits
both protect against valid testers going directly to the Render origin.

`cat_treaty/pilot_observability.py` emits category-only JSON events via the
Uvicorn error logger. Where Linux permits, it reads the whole cgroup's memory
peak/current/limit and API/reaped-child peak RSS; missing metrics stay `null`.
Operator events omit input, result, email, IP, token and request ID. A process
killed by OOM may not log a final event: service restart is a failure signal.
`CT8_FREE_PILOT_STAGING_GATE.md` specifies the stop conditions and the
information required before choosing numerical pilot limits.

## Evidence and remaining acceptance

The JWT signature/policy checks and edge route rejection have local tests.
In this Work Linux environment, the full backend suite passed with one
Windows-only skip, the standard frontend suite/build/audit passed, and the
existing real CT6 API workflow passed. A separately configured pilot
origin with real Cloudflare Access and a free-sized host has **not** run.
The owner and an independent reviewer must inspect the JWT validation,
origin proxy, CORS/preflight configuration, valid-token direct-origin
replay, slot release after timeout, and error precedence before any invite.

Before hosting or a test URL is approved, obtain whole API memory/CPU/time
measurements on an actually bounded 512 MB/0.1 CPU Linux instance for each
enabled route, verify exact approved operational limits and real-browser
flows, set session expiry/revocation, protect both hostnames with Access,
check direct-origin bypass, observe cold starts and monitoring without shell
access, and drill rollback. Render Free instance hours, bandwidth and
build minutes are shared with other services in the owner's workspace.

**Deployment status: BLOCKED.** Owner approval of exact artifact/digest,
pilot limits, invited audience, DNS and spending is a separate final gate.

## Exact independent implementation-review questions

1. Can any direct-origin, spoofed-Host or replayed-valid-JWT request reach a
   calculation without both the server-side proof and per-identity limits?
   Does the Worker safely overwrite the inbound proof and preserve JWT claims?
2. Are JWT issuer, audience, signature, key rotation, lifetime, explicit
   email allowlist, HTTPS key retrieval and network-failure behavior fail
   closed without blocking the event loop or exposing private details?
3. Can a client stream oversized, deeply nested or malformed JSON, declare a
   false Content-Length, flood rejection paths or disconnect mid-run in a
   way that launches multiple children, leaks a slot or consumes unexpected
   512 MB-class resources? Which bounded tests are still necessary?
4. Is any frozen CT6 route, OpenAPI or source-only debug endpoint reachable
   through the pilot app, Worker or frontend build, including OPTIONS?
   Does each pilot success preserve CT6 actuarial numbers, identities and
   reconciliation exactly apart from transport request IDs?
5. Does Cloudflare Access deliver authenticated fetches and CORS preflights
   through the proposed UI/Worker/origin topology on the actual domains?
   Which exact provider settings must be recorded before launch?
6. Are the Work Linux test results and scoped skip represented accurately?
   Which physical-browser, free-instance measurement, monitoring, rollback
   and tester-data gates still block the invited URL?
