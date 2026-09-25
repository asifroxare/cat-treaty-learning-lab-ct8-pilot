# CT8 optional isolated execution — review candidate

**Status:** implementation candidate, off by default; not authorized for public
hosting. Frozen CT0–CT7 engine modules and React components remain unchanged.

`CT8_ISOLATED_RUNS=true` makes catalogue and hours-clause runs use a disposable
spawned child process. `CT8_ISOLATION_DEADLINE_SECONDS` defaults to 30 (1–300)
and `CT8_ISOLATION_MAX_CONCURRENCY` defaults to one (1–4) **per API worker**.
Accepted child responses are projected through the existing CT6 response
builder in the parent; any timeout, broken child or busy local slot follows
the existing static `CT6_INTERNAL_ERROR` 500 path, with no partial result.
The isolated child maps CT4 preflight and hours-contract blockage back to
their existing 422 paths, and domain errors back to 422. No new OpenAPI route,
model or public error code has been added.

This changes the outcome of some otherwise valid over-time or concurrent
requests when enabled. Treat it as an explicit CT6 transport-behavior
amendment, requiring independent review and acceptance. It does not promise
that the 10,000-trial/100,000-occurrence maximum completes under 30 seconds.
The 128 MiB inter-process result cap can also turn a large valid request into
a 500; measure the maximum before choosing or enabling this value. Rate
limits, maximum body streaming and global caps across multiple API workers
still require hosting-level enforcement. One API worker is assumed for the
per-process semaphore to act as a global local cap.

Current tests exercise default behavior (existing CT6 suite), opt-in full
catalogue and hours response equality, blocked hours classification, settings
validation, and a generic disposable-process timeout/crash demonstration.
Full Windows tests, busy/deadline HTTP behavior, worst legal workload,
combined precedence and staging remain OPEN.

Independent reviewer questions:

1. Does the spawned result transport preserve all CT6 values and blocked
   classifications across Windows and Linux, including large legal responses?
2. Is mapping deadline, child failure and busy slot to `CT6_INTERNAL_ERROR`
   acceptable, or does the frozen problem contract need a new explicit error?
3. Does the reader thread plus pipe enforce the total deadline even if a child
   partially writes a large result? What test demonstrates it?
4. Are process creation/termination and error handling safe when the HTTP
   client disconnects, the API worker exits or Uvicorn runs multiple workers?
5. What measured upper bounds justify the deadline, result cap and per-worker
   concurrency? Can one deployment instance safely honor frozen CT6 maxima?
6. Are request size, ingress rate/global caps and proxy trust enforced outside
   this module without changing error precedence silently?

Do not set `CT8_ISOLATED_RUNS=true` in a public service until these questions
are resolved with reproducible evidence and reviewed configuration.

Windows implementation detail: on forced termination, the parent invokes
`taskkill /T /F` for the spawned PID to include any virtual-environment
launcher descendant. This still requires a Windows test that records the
child PID and confirms no interpreter descendant remains after an expired
request; merely receiving a 500 is insufficient proof of termination.

The next checkpoint adds a direct `_run_process` test with a child that writes
an early start marker and would write a completion marker after two seconds.
The parent enforces a 1.5-second deadline, then waits beyond the child's
scheduled completion and requires the completion marker to remain absent. This
tests the Windows process-tree termination path, not merely the HTTP 500.
