# CT8 owner-only capacity probe: independent review request

**Review candidate, 27 September 2026.** Render Free currently has a deliberately
disabled pilot entrypoint and Auto-Deploy Off. No card was entered for
Cloudflare Zero Trust and no live CT8 calculation is available.

Changed code: `cat_treaty/ct8_measure_api.py`,
`deployment/measure_free_host.py`, `tests/test_ct8_measure_api.py` and
`docs/CT8_NO_CARD_MEASUREMENT_GATE.md`. The frozen CT0–CT7 engine and response
projection were not changed.

Evidence for the final review candidate: backend full suite **1,028 passed,
1 Windows-only skipped**; focused new suite **6 passed**; frontend standard
**73 passed, one real-API-only skipped** plus build audit; Edge Worker
**3 passed**. The full backend suite should be rerun for the final commit.
Both synthetic fixtures returned the exact approved CT7 normalized
full-response digests under the new transport (only `api.request_id` removed).
No Windows or live Render Free run yet.

Ask independent reviewer to inspect, in this order:

1. Does the new entrypoint fail closed unless measurement is explicitly enabled,
   the invited pilot disabled, the exact Render host matched, and a high-entropy
   secret configured? Can any CT6 unrestricted or pilot route run here?
2. Does signing a one-use 20-second challenge, exact mode and immutable CT7
   request SHA-256 prevent replay across process restarts, cross-route requests
   and request-body substitutions? Is any untrusted input parsed or executed
   before signature verification and 4,096-byte streaming cap?
3. Can a bad request or disconnected client create a second isolated child or
   release the one-slot guard early? Can logging reveal the secret, inputs or
   responses? Are errors generic?
4. Does the owner's local probe verify the frozen response digests without
   leaking the secret into process arguments, URLs, console or artifacts?
5. Identify any new launch blocker or test gap. Distinguish owner-only capacity
   measurement from an invited browser release. A publicly reachable Render
   origin remains a load/DoS exposure even when its calculation auth is sound.

**Do not enable the Render service based on passing tests alone.** A reviewer
disposition and owner confirmation of the exact release commit/environment
precede measurement. The cgroup/CPU and physical-browser launch gates remain
open until observed on the actual hosts.
