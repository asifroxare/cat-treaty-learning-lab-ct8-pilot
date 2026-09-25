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

`export_ct7_goldens.py` can be run with the exact clean CT7 repository path and
an empty output directory outside that tree. It refuses any other Git HEAD or
unclean tree and creates candidate request/response digests from CT7's existing
fixture constructors. An independent reviewer must approve fixture coverage,
values, exclusions and hashes before putting them in a staging manifest. The
script is stored in CT8, not copied into the frozen CT7 repository.

`python -m unittest -v test_tools.py` verifies that request-ID normalization
does not hide changes to all three settlement components or exclusion reasons,
and that a staging manifest with the wrong origins is rejected before network
access. These tests require only the Python standard library; they do not
replace CT7's 1003-test suite.

`prepare_pages.py` builds an explicit `_headers` and known-route `_redirects`
policy for a Cloudflare Pages staging candidate. It rejects localhost or a
missing API origin in the compiled JavaScript. Physical browser and CDN-edge
verification remain mandatory; see `PLATFORM_CANDIDATE.md`.

`reproduce_ct8.py` is the single Windows checkpoint driver. It uses the
existing installed CT7 virtual environment without moving or replacing it,
then runs backend pytest, fresh `npm ci`, the complete frontend `check`, and
real CT6 API acceptance against the CT8 candidate. It does not deploy or
write to the CT7 repository. Only use it after extracting a CT8 candidate in a
separate folder. Its successful result is local reproduction evidence, not
physical-browser or production-readiness evidence.

`verify_goldens.py` compares the two owner-supplied synthetic CT7 fixture
responses against the CT8 candidate in-process. It checks exact provenance and
input digests, then hashes the entire successful response excluding only
`api.request_id`. Its bundled candidate manifest is in `fixtures/ct7` with a
coverage assessment. These cases do not replace broader CT0–CT7 tests or
independent actuarial review.

`measure_local.py` begins resource measurement with bounded synthetic loads on
loopback. It starts and stops its own CT8 API process and samples peak Windows
working set. The measured 1/10/100-trial cases are far below frozen maximums;
no public concurrency or timeout threshold follows from this first sample.

Windows memory note: the first successful timing run produced a flat 4.08 MiB
for the Python virtual-environment launcher's PID. This is not a valid API
memory measurement. The revised local probe samples the launcher and its
interpreter descendants, lists sampled PIDs, and rejects an implausibly low
aggregate. It also terminates the whole process tree when finished.

`isolated_execution.py` is a prototype only. Its small-function tests prove
process termination after a deadline, but it is not connected to the public
API. It does not yet preserve CT6 error precedence or bound large result
transport. Do not describe it as a deployed production guard.
