# CT8 no-domain pilot: reviewed staging candidate

**27 September 2026. No deployment, invitation, DNS change, paid plan or public release.**

Cloudflare documents one-click Access on `workers.dev` and a Worker rate-limit
binding. This supersedes the earlier assumption that a Cloudflare-managed
custom domain was necessary for invited staging. **The same new Worker** serves
the separately built pilot UI from its `ASSETS` binding and forwards only three
pilot API routes to a separate Render Free pilot origin. Its single hostname
avoids cross-site browser cookie requirements. Protect the entire Worker
hostname, including preview URLs, with the new owner-only Access application.
The Render default
`onrender.com` name must stay addressable because Render allows disabling it
only after a custom domain is added. Direct-origin access must fail both the
origin-proof and independently signed JWT tests before the request body is
read. If that changed exposure is unacceptable, do not stage on this route.

The edge now fails closed on missing, rejected or failing `PILOT_RATE_LIMITER`
for computation POSTs; OPTIONS preflight and read-only capabilities do not
consume binding tokens. The example Wrangler binding permits six requests per
minute **per Cloudflare location only**, as a temporary staging ceiling, not
an approved pilot envelope or global concurrency limit. The Python pilot's
one process/one calculation slot and individual per-email rate control are
still required. Cloudflare notes binding counters are eventually consistent.

The existing `CT8_FREE_PILOT_STAGING_GATE.md` still applies except that its
custom-domain / disabled-Render-subdomain topology is replaced for this
*no-domain staging candidate* by the explicit publicly addressable origin
above. Do not claim the former disabled-subdomain negative test has passed.
Test the actual origin with spoofed Host, signed JWT but no secret, and
invalid JWT; no computation may start. Also test one-click Access audience,
preflight and credentials in physical browsers, edge rate limiting, Python
busy rejection, memory and reconciliation on the real Free host. Missing
cgroup numbers or OOM are stop conditions. Review a rollback drill before
inviting anyone.

The example binding is not a deployable configuration: choose a namespace
unique to the owner's Cloudflare account, verify the proposed single Worker
hostname is available, obtain its real owner-only Access audience and secure
provider-held secrets,
and a measured small Python limit JSON. Do not put credentials or invitations
into the ZIP. Keep frozen CT0–CT7 calculations and Cat XOL Pricing Lab
separate. External references: https://developers.cloudflare.com/changelog/post/2025-10-03-one-click-access-for-workers/ ; https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/ ; https://render.com/docs/custom-domains .
