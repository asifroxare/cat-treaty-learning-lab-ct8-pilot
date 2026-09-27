# CT8 independent capacity review — disposition

**Review received:** 27 September 2026. **Decision:** public launch blocked;
no deployment, spending, or CT6 contract change authorized.

The reviewer checked the memo's Windows measurements against the evidence and
confirmed its numbers and code descriptions. Their central finding agrees
with the gate: a legal local 25,000-row request did not complete inside the
candidate 30-second deadline or below the sampled 800 MiB process-tree stop.
The later bounded Linux direct-engine results for one-layer and four-layer
fixtures are recorded in `CT8_LINUX_CAPACITY_EVIDENCE.md`; they are worker
observations, not full API or target-host sizing measurements.

| Reviewer point | Disposition |
| --- | --- |
| Reproduce full legal workload on Linux under an OS-enforced memory limit | **PARTIAL.** A direct one-layer CT6 engine run of the 25,000-row legal input completed under 2 GiB `RLIMIT_AS`; 91,939,829 pickled bytes, 835,600 KiB worker RSS, 27.529s. This Work container lacks Docker and the FastAPI/uvicorn API dependencies. Full bounded API/staging and other legal maxima remain OPEN. See `CT8_LINUX_CAPACITY_EVIDENCE.md`. |
| Directional exclusion of 512 MB Render Free | **Free not approved for this case; final sizing OPEN.** The direct Linux worker alone reached 835,600 KiB peak RSS in this environment, above Free's documented 512 MB. Host CPU, API parent and other fixtures remain unmeasured; do not select a paid plan from this single run. |
| 100,000 occurrences, four layers, and hours candidate expansion | **PARTIAL.** A legal four-layer/25,000-row full-detail direct-engine variant completed in 36.497s, 120,092,827 pickle bytes, 1,150,288 KiB worker RSS under 2 GiB `RLIMIT_AS`. The 25,000 full-detail-row limit means 100,000 occurrences cannot simultaneously demand 100,000 full-detail rows. Other loss mixes, high-occurrence summary and hours candidates remain OPEN. |
| Global admission if one worker/one instance | **OPEN.** Verify fixed instance count, worker command, autoscaling settings and direct-origin bypass in staging; the current semaphore is per-process. |
| Busy and crash both reported as generic HTTP 500 | **OPEN transport decision.** Add operator-side reason categories and metrics before changing any public CT6 code. A distinct busy response requires a versioned contract/error-precedence review and frontend handling. |
| Linux descendant cleanup | **OPEN pending full API and independent review.** Windows `taskkill /T /F` does not provide Linux process-tree guarantees. A POSIX process-group helper is wired into the opt-in executor; both the helper prototype and actual `_run_process` passed Linux deadline and abrupt-parent tests with a descendant. Full FastAPI/backend Linux integration and independent review remain pending. |
| `202 Accepted` asynchronous jobs as a fallback | **OPTION, not an approved small patch.** A versioned job protocol needs durable bounded storage, identity/expiry, concurrency, authentication or abuse controls, cancellations, status/result retrieval, retry and rollback semantics, new OpenAPI and frontend UX, and independent acceptance. Preserve all CT0–CT7 calculations and hashes. Do not silently retrofit CT6. |

## Next work in this workspace

Test the integrated executor on Linux with full dependencies under a host
resource ceiling, including response projection, high-occurrence summary,
hours candidates, and actual process-tree cleanup before deployment. Keep
production `CT8_ISOLATED_RUNS` OFF. Do not ask the owner for more unbounded
Windows probes.
