# CT8 owner-only, no-card Render Free measurement

**Prepared 27 September 2026. Separate review candidate. No live calculation, UI invitation or public release is approved here.**

The original CT8 invited pilot remains disabled (`CT8_PILOT_ENABLED=false`). The new
`cat_treaty.ct8_measure_api:create_measure_app` entrypoint serves only:

- `GET /health/ready` (no sensitive detail)
- `GET /api/ct8-measure/v1/challenge` (at most 6 challenges/minute/process)
- `POST /api/ct8-measure/v1/runs/catalogue`
- `POST /api/ct8-measure/v1/runs/hours-clause`

No CT6 `/api/v1/*`, pilot `/api/pilot/v1/*`, docs or OpenAPI route is mounted.
One-use 20-second random challenges are kept in the only Uvicorn worker's
memory. HMAC SHA-256 signs challenge, route and the exact frozen CT7 fixture
SHA-256. Authentication and an exact Host check happen before bounded body
streaming. Only the two approved 2,378/2,934-byte fixture bytes can run;
anything else is rejected before the disposable calculation process. The
response uses the unchanged Python CT6 projection. The 30-second deadline,
one-slot semaphore, 4,096-byte body maximum and isolated process tree remain
mandatory. Restart clears pending challenges. Keep precisely one Render instance
and one Uvicorn worker; disable Auto-Deploy and previews. This is **capacity
measurement**, not an invited browser authentication system.

## Exact controls for a separately approved measurement deploy

| Render setting | Required value |
| --- | --- |
| Plan | Free, one instance, no autoscaling |
| Source | private `asifroxare/cat-treaty-learning-lab-ct8-pilot` at the exact independently reviewed new commit |
| Build | `pip install -r requirements-pilot.txt` |
| Start | `python -m uvicorn cat_treaty.ct8_measure_api:create_measure_app --factory --host 0.0.0.0 --port $PORT --workers 1` |
| `CT8_PILOT_ENABLED` | `false` (never turn on alongside measurement) |
| `CT8_MEASURE_ENABLED` | `true` only while the owner is actually measuring |
| `CT8_MEASURE_HOST` | actual exact assigned Render hostname, without `https://` |
| `CT8_MEASURE_SECRET` | newly generated 256-bit or stronger, high-entropy printable secret; provider-held and entered locally via hidden prompt; never paste into chat, URLs, GitHub or ZIP |

Before changing the currently disabled Render service, an independent reviewer
must inspect this new entrypoint and its new tests. The owner must explicitly
approve the reviewed release and these exact settings. Changing the start
command or env variables triggers another deploy; do not claim the previous
intentional failed deploy is capacity evidence. Restrict owner testing to the
synthetic fixtures; the owner's local `deployment/measure_free_host.py` prompts
for the secret without echoing it, checks the two full CT7 digests and reports
warm durations and response byte counts.

## Fail-closed staging gates and shutdown

Check full-response CT7 identities (remove only `api.request_id`), Render
structured cgroup peak/current/limit, Render CPU/memory charts and absence of
restart/OOM. A missing cgroup peak, peak over 384 MiB, warm response over
30 seconds, incomplete result, wrong digest, extra live Uvicorn instance,
replay success, unknown route success, unexpected billing or security bypass
stops measurement. Review direct-origin bad-signature/body/host attempts and
two concurrent requests. Cloudflare Access and physical-browser testing are
**not part of this owner-only gate** and remain open launch blockers.

After the measurement, immediately set `CT8_MEASURE_ENABLED=false`, restore the
invited-pilot (disabled) start command in Render and rotate/remove the staging
secret. Verify the public address has no active calculation endpoint. Record
the exact commit, build/deploy events and cgroup observations. No tester URL or
invite is authorized.
