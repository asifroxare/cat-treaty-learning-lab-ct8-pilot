# CT8 independent capacity review — disposition

**Review received:** 27 September 2026. **Decision:** public launch blocked;
no deployment, spending, or CT6 contract change authorized.

The reviewer checked the memo's Windows measurements against the evidence and
confirmed its numbers and code descriptions. Their central finding agrees
with the gate: a legal local 25,000-row request did not complete inside the
candidate 30-second deadline or below the sampled 800 MiB process-tree stop.
No final resource peak, pickled result size or host performance is known.

| Reviewer point | Disposition |
| --- | --- |
| Reproduce full legal workload on Linux under an OS-enforced memory limit | **OPEN — launch blocker.** This Work container has an 8 GiB cgroup but no Docker and no FastAPI/pytest/uvicorn dependencies. It cannot reproduce the actual API/engine here. Provide a separate, controlled Linux staging benchmark with cgroup peak evidence and cleanup verification; do not claim this has run. |
| Directional exclusion of 512 MB Render Free | **OPEN for final sizing.** Render documents 512 MB; the sampled Windows process-tree stop is directional, not authoritative Linux RSS. Do not select a paid plan from partial Windows results. |
| 100,000 occurrences, four layers, and hours candidate expansion | **OPEN.** The 25,000 full-detail-row limit means a 100,000-occurrence request cannot simultaneously demand 100,000 full-detail rows. Test each *legal* response-detail/body/row combination and inspect actual schema limits. |
| Global admission if one worker/one instance | **OPEN.** Verify fixed instance count, worker command, autoscaling settings and direct-origin bypass in staging; the current semaphore is per-process. |
| Busy and crash both reported as generic HTTP 500 | **OPEN transport decision.** Add operator-side reason categories and metrics before changing any public CT6 code. A distinct busy response requires a versioned contract/error-precedence review and frontend handling. |
| Linux descendant cleanup | **OPEN pending full API and independent review.** Windows `taskkill /T /F` does not provide Linux process-tree guarantees. A POSIX process-group helper is wired into the opt-in executor; both the helper prototype and actual `_run_process` passed Linux deadline and abrupt-parent tests with a descendant. Full FastAPI/backend Linux integration and independent review remain pending. |
| `202 Accepted` asynchronous jobs as a fallback | **OPTION, not an approved small patch.** A versioned job protocol needs durable bounded storage, identity/expiry, concurrency, authentication or abuse controls, cancellations, status/result retrieval, retry and rollback semantics, new OpenAPI and frontend UX, and independent acceptance. Preserve all CT0–CT7 calculations and hashes. Do not silently retrofit CT6. |

## Next work in this workspace

Prepare a reviewed Linux resource-limit runbook and test the integrated
executor on Linux with full dependencies before deployment. Keep production
`CT8_ISOLATED_RUNS` OFF. Consolidate implementation and evidence into one
reviewed ZIP before asking the owner for a checkpoint. The owner should not
be asked for more unbounded Windows probes.
