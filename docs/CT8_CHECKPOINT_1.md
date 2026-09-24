# CT8 checkpoint 1 — operational instrumentation

Baseline CT7 SHA-256: `76D6B877A27B009ED81CE6102BE0E635BF75F3B8CD720AE3FB4F4808A25884D5`.
Baseline commit: `2a45727b9621a860ee074d6b14172b65fd836ad3`.

This checkpoint adds standard-library, read-only deployment and controlled local
load probes. No changes to CT0–CT7 engine, CT6 transport or CT7 frontend. The
package is **not deployment-ready**. The review specification remains
`CT8_DEPLOYMENT_READINESS_SPEC_REVISED.md`, delivered separately.

Reviewer: confirm the single allowed response normalization path is a transport
field in both API workflows; independently select fixture digests; inspect
load probe's bounds and server resource limits; review deployment gating gaps in
`deployment/README.md` before any further implementation.
