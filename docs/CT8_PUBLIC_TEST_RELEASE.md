# CT8 public test release (small, GitHub sign-in required)

## Gate and scope

This update builds on the GitHub OAuth issuer fix (`c24b755`). Set both independent switches only after deploying this reviewed source and Worker:

- Render: `CT8_NOCARD_PUBLIC_TEST_ENABLED=true`.
- Cloudflare CT8 Worker: `PILOT_PUBLIC_TEST_ENABLED=true`.

The two switches default to `false`. Setting either to `false` restores the original numeric-ID allowlist at that boundary. `PILOT_NOCARD_ENABLED=false` still closes the entire Worker immediately; do that for incident rollback. The existing shared signing key, exact host checks, one Uvicorn worker, one Render instance, isolated child, 30-second deadline, 16-MiB result cap, 4,096-byte body, one catalogue trial/occurrence/layer or two hours-clause components and the frozen engine remain unchanged.

All GitHub accounts with positive safe numeric IDs can sign in when both public switches are enabled. The Worker still enforces the login/callback IP limit and per-GitHub-ID API rate binding. The Python process admits at most **two** signed calculation requests per rolling 60 seconds across all accounts, before body read and parsing; it rejects excess with `CT8_PILOT_BUSY` (HTTP 429). Per-ID and single-active-calculation guards remain. This is a small feedback pilot; expect busy replies when multiple visitors try calculations at once. Do not imply that full CT6 limits or high availability are available on Render Free.

The Worker accepts the exact `iss=https://github.com/login/oauth` parameter GitHub returned during first live sign-in. The browser now shows “Signed in with GitHub” after an authenticated capabilities reply.

## Evidence and acceptance

Local Linux: backend 1,037 passed / 1 Windows-only skipped; Worker 8 passed; frontend 73 passed / 1 real-API test skipped in standard suite, build and audit passed. Focused Python test verifies a new signed account and global two-per-minute refusal with no third calculation, plus private-mode restoration. Worker test verifies newly signed-in GitHub ID is rejected in private mode and accepted in public mode. Frozen CT7 full-response golden tests remain in the backend suite.

Live owner-only private evidence before this update: catalogue 200 in 4,231 ms with cgroup peak 126,681,088 / 536,870,912 bytes; hours-clause 200 in 3,785 ms with cgroup peak 127,315,968 / 536,870,912 bytes; both returned CT4/CT5 identities. Direct origin and unsigned Worker capabilities both returned 401. These two examples do **not** prove public traffic capacity.

After upload, check: deployed Render commit and readiness; Worker preview still private while switches off; new GitHub account login and valid limited run, rejected unauthenticated direct-origin and Worker calls, shared 429 on third signed run within a minute, resource logs below 384 MiB stop threshold, and a disable/re-enable rollback drill. Keep the post on hold until a second GitHub account has actually completed a calculation and the rollback drill passed. Never include OAuth callback URLs, keys, GitHub IDs or request bodies in public posts or logs.
