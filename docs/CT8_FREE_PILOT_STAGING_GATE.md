# CT8 free pilot — controlled staging gate

**No-domain candidate amendment:** `CT8_NO_DOMAIN_STAGING_DISPOSITION.md`
documents a separate `workers.dev` Access route that temporarily leaves the
Render default hostname addressable, subject to direct-origin negative tests
and independent acceptance. The custom-domain/disabled-Render-subdomain row
below describes the original topology; it is not evidence that the no-domain
candidate meets that row.
`CT8_NO_DOMAIN_EXACT_STAGING_CONFIG.md` gives the one-Worker UI/API candidate;
it supersedes the split-origin UI and API rows below for that candidate.

**Prepared 27 September 2026. No service, DNS, spending or public URL has
been created.** This is an execution checklist for a separately authorized
staging exercise, not a deployment instruction or approval. The pilot stays
disabled without explicit settings and measured limits. The owner does not
need Docker or another Windows workload probe.

## Exact service topology to review before any staging action

| Component | Required configuration | Negative proof |
| --- | --- | --- |
| React build | Separate `VITE_CT8_PILOT_MODE=true` build, exact HTTPS `VITE_CT6_API_BASE_URL`; compiled-route/origin audit; Access on pilot UI | No secret or localhost origin; production CT6 build and reference app remain separate |
| Edge proxy | `deployment/pilot_edge_worker.mjs` on a dedicated Access-protected pilot API hostname; three allowed pilot routes, explicit CORS OPTIONS policy and origin-proof secret binding | Frozen `/api/v1/runs/*`, unknown routes, unapproved origin, unsigned identities and supplied forged proof do not reach computation |
| Render origin | New, separate Free web service; **one instance and one Uvicorn worker**; `requirements-pilot.txt`; start `python -m uvicorn cat_treaty.pilot_api:create_pilot_app --factory --host 0.0.0.0 --port $PORT --workers 1`; exact custom origin hostname; disable default `onrender.com` hostname | A direct custom-Host/SNI request without valid proof/JWT is rejected; full CT6 `/api/v1/runs/*`, docs and OpenAPI return 404 |
| Configuration | Provider-held `CT8_PILOT_ENABLED`, exact `CT8_PILOT_API_HOST`, `CT8_PILOT_UI_ORIGIN`, origin secret, Access team/audience, named-email allowlist, measured `CT8_PILOT_LIMITS_JSON`, reviewed deadline | Missing/malformed config stops startup; secrets never appear in frontend, ZIP, URLs or logs |
| Capacity | Backend single calculation slot, early body/shape gate, per-identity minute limit; Cloudflare rate policy and protected origin; no autoscaling | A second run returns busy and cannot start a child; timed-out/disconnected runs keep their slot until stopped |

**Before opening staging:** enumerate the exact hostnames, allowed UI origin,
Access application audience and session duration, invited emails, provider
usage budget, incident owner, and exact immutable ZIP/commit. Review these
values privately; do not put secrets or invitation lists in a report or ZIP.
Cloudflare Access may block CORS preflight before it reaches the Worker;
configure and test a narrow OPTIONS behavior without granting calculation
access. HTTP security headers, TLS, host handling and origin proof must be
verified on the actual network path. Disable automatic deployment or
unreviewed scale-up.

## Bounded capacity acceptance

1. Begin with only **preapproved small CT7 catalogue and hours fixtures**,
   one request at a time; do not submit the 10,000-trial legal maximum on
   Free. Use an explicit, independently reviewed *temporary staging* limits
   JSON sufficient for those fixtures. An upper code limit is not a measured
   launch limit. First visit after idle can include about a minute of wake
   time; separate that from the calculation duration.
2. For each allowed mode, record Python dependency versions, service plan
   (512 MB / 0.1 CPU), one-worker command, response size/time, deterministic
   full-response digest excluding only request ID, complete reconciliation,
   backend event category, and `cgroup_peak_bytes/current/limit` from the
   structured Render logs. Cross-check Render memory/CPU charts. A missing
   cgroup peak or an effectively unlimited cgroup means **no host-sizing
   evidence**. Cgroup peak can include previous runs and is conservative.
3. Exercise at least two concurrent authenticated requests, invalid/large
   streams, valid-token direct-origin replay without the Worker proof, bad
   Access signatures and CORS preflight. Monitor calculation child count,
   readiness while work runs, memory/restarts, and recovery after deadline.
4. Provisional **stop conditions** for staging, not approved public limits:
   any service restart/OOM, missing process-tree or cgroup memory evidence,
   peak above **384 MiB** (75% of Free RAM), an accepted small request above
   **30 seconds of warm calculation/transfer**, an incomplete result, wrong
   CT7 identity, unexpected paid usage, or a direct-origin/auth bypass.
   These are intentionally strict triggers for redesign/review, not claims
   about Render performance. Never increase a timeout or selected trial
   limit in public merely to make a failing probe pass.
5. Only after small-mode evidence passes, agree the exact permitted catalogue
   and hours dimensions, detailed-output mode, browser teaching paths and
   response errors. Rebuild and retest against those immutable settings.
   Guided, Explore, comparison, keyboard/mobile/physical browsers, stale-tab
   and Cold/Ready UX must be tested separately. Do not advertise a path that
   its configured envelope rejects by default.

## Operate and roll back

Render Free provides no SSH/shell access and may restart a service at any
time. Use structured logs (outcome, elapsed, request/response byte counts,
cgroup peak/current/limit and API/child RSS) plus outside-in health checks;
do not log inputs, result bodies, tokens, IPs or emails. An OOM may kill the
service before an event can be logged: treat restart/no-completion as failure.
Record an incident owner, alert destination, tester-notice text, session
revocation process, provider-log retention and deletion practice. Watch the
shared workspace's **750 Free instance hours per calendar month** and
bandwidth/build usage. Stop new invitations if spend or provider suspension
risks arise; never upgrade automatically. Disable the edge Worker route and
Access invitations first if an issue occurs, then restore the last reviewed
pair and verify that no frozen CT6 route became public.

**Release gate remains OPEN.** After independent review of the whole staging
record and a rollback drill, present the exact release ZIP SHA-256, hostnames,
tester audience, terms and any costs to Aasif for final approval. No test URL
is authorized by this document.
