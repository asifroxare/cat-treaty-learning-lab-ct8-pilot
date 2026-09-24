# CT8 deployment tooling — predeployment checkpoint

This directory adds operational probes only. It does not alter CT0–CT7 models,
formulas, FastAPI handlers, or frontend presentation. It is not a public
hosting configuration or a completed deployment-readiness sign-off.

`probe.py` checks health, readiness and capabilities, optionally runs a real
catalogue or hours-clause fixture and prints a response hash without printing
input or result. The hash excludes only `api.request_id`, which is a transport
correlation field. Approve expected fixture digests independently before using
them as gates. Use only non-sensitive fixture input.

`load_probe.py` is bounded to loopback, 8 concurrent and 32 total requests. It
is a measurement instrument, not a benchmark result. It cannot prove a timeout
cancels server work. Obtain explicit staging load authorization before adapting
its loopback restriction.

`verify_release.py` checks a clean Git tree, OpenAPI digest and the compiled
API origin against actual built JS. It will fail until a reviewed CT8 commit is
made and production assets are built with the final approved API host. It does
not decide an infrastructure provider or claim a release is safe.

Pending implementation before any public deployment: measured worst-case loads,
process-isolated computation/cancellation, ingress sizing and concurrency/rate
limits, trusted-host/proxy enforcement, error precedence matrix, reviewed golden
fixtures, actual CSP/cache/TLS behavior, physical browsers, staging E2E,
monitoring, rollback drill and independent audit. Each needs separate evidence.

`staging_acceptance.py` verifies HTTPS edge behavior, SPA fallback, CORS and
independently approved full-response fixture digests. It fails closed when
manifest origins or digests disagree. It does not test physical browsers or
worker cancellation. Its explicit topology is split-origin; a same-origin
provider design needs a separately reviewed variant. The fixture manifest
example contains placeholders only and cannot pass as release evidence.

`ACCEPTANCE_MATRIX.md` lists the remaining gates with every status OPEN.
