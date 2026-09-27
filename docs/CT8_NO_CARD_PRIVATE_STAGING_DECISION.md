# CT8 private staging without Cloudflare Zero Trust billing

**27 September 2026 — owner decision draft. No auth replacement, account payment, invitation or live calculation is authorized by this document.**

## Why the approved path paused

The owner selected Cloudflare Zero Trust Free, but the actual checkout demands a payment method and agreement to charge monthly usage beyond free limits. The owner's prior approval covered a $0 staging exercise, not authorization for an open-ended charge agreement. Stop that checkout. The new Render Free service currently refuses to start because `CT8_PILOT_ENABLED=false`; keep it disabled and Auto-Deploy Off.

## Two precise choices

| Path | Next action | Tradeoff |
| --- | --- | --- |
| A. Keep Cloudflare Access | Owner independently reviews the checkout agreement and decides whether to authorize a payment method and possible overage charges. If not, do nothing. | Minimal software change, but potential charges and new payment agreement. |
| B. No-card **owner-only capacity staging** | Create a separate, explicitly versioned CT8 *measurement entrypoint* accepting only small synthetic CT7 fixtures with a high-entropy provider-held secret and a short-lived, nonce-checked, HMAC-signed probe request. Restrict to the same one-worker/one-slot, early body cap and pilot dimensions; no browser invitation. | More implementation and independent security review. Lets us measure the actual Render Free host without Cloudflare Access; **does not approve an invited browser pilot or public launch**. |

**Recommendation: B for the immediate capacity question.** Do not silently weaken the current pilot app, reuse the origin-proof header as a browser credential, put a shared secret in React/URLs/ZIP/logs, or expose frozen `/api/v1/runs/*`. The measurement entrypoint is Python backend only, restricted to fixture digests and owner-invoked probes; React stays unchanged. After measuring, choose an identity solution separately before inviting testers. An alternative later is to use a domain/identity provider that the owner already has, subject to a new review.

## Required B implementation and acceptance before changing Render

1. Implement separate fail-closed measurement mode and fixed allowlist for **both supplied synthetic CT7 fixture bodies**. Confirm body digests first; reject other inputs, oversize bodies, missing/expired/replayed authentication, second concurrent work and unknown routes before calculation. Use a short-lived, one-use server challenge included in the HMAC so a process restart invalidates pending probes. Rotate the staging secret after the exercise.
2. Keep a private, newly generated 256-bit+ signing key in Render and the owner's local probe environment only. Never send it to chat or commit it. Provide a helper that prompts locally for the key, signs a bounded probe, reports status, response digest, time and host memory evidence without printing the key, input or result. Restrict access to the owner's selected IP at the edge if the provider offers it; this is additional protection, not the primary authentication.
3. Independent review verifies that the new path is separate from the invited pilot, uses constant-time signature comparison and replay protection within the one-worker process, and cannot run full CT6 legal maxima. Run the complete backend/frontend checks and deliver a distinct reviewed ZIP/commit; disable automatic deploys.
4. Only then set Render's new secret and explicit measurement flags, deploy the exact reviewed commit, and send one approved fixture at a time. Stop on missing cgroup peak, >384 MiB, >30s warm response, restart/OOM, wrong CT7 identity or an auth bypass. Reset `CT8_PILOT_ENABLED=false` / disable the measurement mode after evidence capture.

**Owner decision required:** approve the revised owner-only, no-card capacity measurement design before implementation or further Render deployment. The existing private-staging authorization did not approve replacing Cloudflare Access for invited users. No external tester access will be offered on path B.
