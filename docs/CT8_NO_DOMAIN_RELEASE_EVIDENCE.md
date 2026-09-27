# CT8 no-domain staging review package evidence

**Prepared 27 September 2026; no deployment.** The single new Cloudflare
Worker and new Render Free service remain candidate names only.

- Linux backend full suite: **1,022 passed, 1 Windows-only skipped**, one
  third-party Starlette deprecation warning.
- Frontend standard `npm run check`: API contract, boundaries, type-aware
  calculation gate, guided content, 73 tests (one real-API-only skipped),
  production build and audit passed.
- Pilot frontend build with `VITE_CT8_PILOT_MODE=true` and proposed same-origin
  `VITE_CT6_API_BASE_URL`: build and production audit passed (three assets,
  345,849 bytes, no source maps or local paths).
- Edge `node --test deployment/test_pilot_edge.mjs`: **3 passed** including
  fail-closed binding and same-origin UI/forbidden API route checks.
- No new actuarial formula; existing Python backend remains authoritative.
  The frozen CT7 golden suite and previous real CT6 API acceptance remain
  historical evidence, **not** proof of Render Free host capacity or live
  Cloudflare Access/browser behavior.

Open release gates: confirm actual worker name and audience, enable Access on
both production and previews for the **new** Worker, select private provider
values, verify direct Render bypass rejection, run memory-bounded actual Free
host fixture measurements, physical browser acceptance, rollback drill and
independent review. No external invitation or live URL is approved.
