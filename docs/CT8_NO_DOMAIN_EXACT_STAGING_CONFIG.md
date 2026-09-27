# CT8 no-domain staging: exact candidate settings for owner review

**Prepared 27 September 2026. No service or Worker created; no secret or tester identity stored here.** The owner's Cloudflare dashboard shows `Enable Access` beside an existing `asif-rox.workers.dev` Worker. Leave that existing Worker and all existing Render labs untouched.

## One Worker, one separate backend

| Setting | Candidate value or binding | Gate |
| --- | --- | --- |
| New Worker name | `edinsured-ct8-cat-pilot` | Must be available in owner's account; do not edit `edinsured-live` |
| Pilot UI and API hostname | `edinsured-ct8-cat-pilot.asif-rox.workers.dev` | Protect **production and preview addresses** with owner-only Access before enabling any invitation |
| Worker static assets | `frontend/dist` built with `VITE_CT8_PILOT_MODE=true` and `VITE_CT6_API_BASE_URL=https://edinsured-ct8-cat-pilot.asif-rox.workers.dev`; `[assets]` Worker-first, SPA fallback | Browser navigation and `/assets/*` work; unknown `/api/*` returns 404; no secrets in build |
| Worker API | `deployment/pilot_edge_worker.mjs` allows only three CT8 pilot routes; `PILOT_PUBLIC_HOST=edinsured-ct8-cat-pilot.asif-rox.workers.dev`, `PILOT_UI_ORIGIN=https://edinsured-ct8-cat-pilot.asif-rox.workers.dev` | Signed Access JWT checked by Python; do not treat presence of JWT header as signature verification |
| Worker rate binding | `PILOT_RATE_LIMITER` provisional six calculation POSTs per 60 seconds **per Cloudflare location**; choose account-unique namespace ID | Missing/failed binding returns 503; 429 does not forward; not a global cap |
| New Render service | Free plan; candidate name `edinsured-ct8-cat-pilot`; one instance, one Uvicorn worker; build `pip install -r requirements-pilot.txt`; start `python -m uvicorn cat_treaty.pilot_api:create_pilot_app --factory --host 0.0.0.0 --port $PORT --workers 1` | Check actual service hostname after reservation; no autoscale or automatic paid upgrade |
| Render hostname | Candidate `edinsured-ct8-cat-pilot.onrender.com`; `CT8_PILOT_API_HOST` must equal the actual Render hostname; Worker `PILOT_ORIGIN_HOST` must match | Default Render hostname remains reachable; direct request without origin proof cannot start calculation |
| Temporary small-run limits | `CT8_PILOT_LIMITS_JSON={"max_body_bytes":4096,"max_trials":1,"max_occurrences":1,"max_layers":1,"max_hours_components":2,"max_requests_per_minute":2,"allow_full_detail":true}`; `CT8_PILOT_DEADLINE_SECONDS=30` | These admit the two supplied CT7 golden fixture shapes (2378/2934 bytes). **Staging measurement only**, not a public pilot envelope; reject every larger input |
| Other Render variables | `CT8_PILOT_ENABLED=true`; `CT8_PILOT_UI_ORIGIN=https://edinsured-ct8-cat-pilot.asif-rox.workers.dev`; `CT8_PILOT_ACCESS_TEAM` = actual Access team slug; `CT8_PILOT_ACCESS_AUDIENCE` = actual *new pilot application* AUD; `CT8_PILOT_EMAIL_ALLOWLIST` = owner's exact email; `CT8_PILOT_ORIGIN_SECRET` = new random secret of at least 32 printable characters | Provider-held variables only; never copy any secret into frontend/ZIP/chat/logs |
| Other Worker bindings | `PILOT_ORIGIN_HOST` = actual Render hostname; `PILOT_ORIGIN_SECRET` = same provider-held secret; `ASSETS` = built frontend | Worker ignores user-supplied proof, adds provider secret to Render request |

## Required order after separate staging approval

1. Privately select and record actual account-unique rate namespace, Render hostname, Access team/AUD, owner-only email policy and provider secrets. Do not proceed if Zero Trust onboarding requires unexpected billing or cannot provide a matching audience.
2. Create new Render Free pilot with reviewed ZIP only; initially keep `CT8_PILOT_ENABLED` disabled so no public calculation. Verify one instance/worker and startup refusal without all required variables. Then apply temporary limits and Access config; verify no original CT6 route or OpenAPI is exposed.
3. Build and inspect immutable pilot UI for the single Worker host. Create only the new Worker with Access on production **and preview**. Confirm direct-origin secret/JWT bypass attempts fail before accepting any real request; verify Worker binding, preflight and browser sign-in. Disable previews if they cannot be protected.
4. Run catalogue and hours CT7 synthetic fixture probes only; compare full-response digests with approved manifest; record cgroup peak, response bytes and warm latency. Stop on memory >384 MiB, missing memory reading, warm duration >30 s, restart/OOM, wrong identities, unexpected cost or bypass.
5. Test simultaneous requests, denied large bodies, cold start, physical browser routes, mobile and keyboard, logout and rollback. Independent review of the record and explicit final owner authorization precede invitations.

## Release boundary

One-click Access availability was confirmed visually on an **existing** Worker; Access has not been enabled for CT8, the separate Worker and Render service have not been created, and provider rate binding/live JWT/cgroup evidence remains unverified. Render's public default address is a deliberate change from the earlier custom-domain staging design; the owner must accept it explicitly as part of a controlled test. Treat `CT8_FREE_PILOT_STAGING_GATE.md` and `CT8_NO_DOMAIN_STAGING_DISPOSITION.md` as applicable stop rules; the earlier disabled-Render-subdomain criterion does not hold for this design.
