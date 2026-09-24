# CT8 staging candidate: Cloudflare Pages + Render API

This is a configuration candidate, not a deployment instruction or hosting
purchase. It follows the user's existing Cloudflare and Render experience.
The split-origin choice requires explicit API origin at Vite build time and
exact production CORS origin at backend runtime. Keep Treaty Lab in dedicated
projects separate from Cat XOL Pricing Lab.

Frontend: build Vite with `VITE_CT6_API_BASE_URL` set to the exact HTTPS API
origin; then run `prepare_pages.py` on `frontend/dist` before upload to
Cloudflare Pages. The generated `_headers` uses a script policy without inline
JavaScript and allows inline CSS for reviewed geometry widths. The generated
`_redirects` rewrites only known React routes and does not rewrite missing
`/assets/*` paths. Verify every header, cache and rewrite at the actual edge.
Retain old fingerprinted assets across releases for open tabs; test CDN
invalidation on rollback.

Backend: the CT6 FastAPI service would run on an isolated Render web service
with explicit `CT6_CORS_ORIGINS`, TLS ingress, health `/health/ready` and a
separate instance from the existing quota-share service. No Render Blueprint,
start command, billing choice, request limits, rate controls or alert thresholds
are approved in this checkpoint. The free plan's idle spin-down and resource
limits need measured suitability before selection. In particular, do not
assume that a process manager's worker timeout bounds an asynchronous request:
Gunicorn documents timeout as worker silence, and an ASGI worker can remain
responsive while computation occupies a separate thread. Demonstrate actual
cancellation/termination rather than relying on a setting name.

Official references consulted 24 September 2026:
- https://developers.cloudflare.com/pages/configuration/headers/
- https://developers.cloudflare.com/pages/configuration/redirects/
- https://render.com/docs/free
- https://render.com/docs/health-checks
- https://gunicorn.org/reference/settings/

Open provider decision: retain this split-origin staging candidate or select
another provider after workload measurement. No public launch is authorized.
