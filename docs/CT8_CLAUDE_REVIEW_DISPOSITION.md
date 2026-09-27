# Independent CT8 execution review — disposition

Review received 25 September 2026. Public isolation remains OFF and public
deployment is not authorized.

| Finding | Disposition |
| --- | --- |
| Near-max legal response, 128 MiB IPC cap and 30-second deadline unmeasured | **OPEN — launch blocker.** Owner's 10,000-trial/one-occurrence direct sample completed in 18.52s; the legal 10,000-trial/25,000-occurrence full-detail sample stopped at 30s, then at the sampled 800 MiB guard with a 90s allowance. See `CT8_TRIAL_LIMIT_EVIDENCE.md` and `CT8_ROW_LIMIT_EVIDENCE.md`. The 30s candidate deadline is unsuitable; pickle size and actual completion resource needs remain unknown. |
| Semaphore is per API worker | **OPEN — launch blocker.** Require a single-worker/one-instance launch gate or cross-process/global cap and verify actual hosting configuration. |
| No HTTP busy/deadline evidence | Targeted HTTP tests show busy returns sanitized `CT6_INTERNAL_ERROR` without partial result, accepted response equals baseline, and synthetic deadline returns sanitized 500. These are mapping tests, not real child HTTP stress tests. Owner confirmed 7 targeted tests and 1010 backend tests passing on Windows, 25 September. |
| Abrupt parent death can orphan a child | Child watchdog uses the multiprocessing parent sentinel, fails closed when unavailable, and on Windows attempts to terminate its own process tree. New tests check actual PID termination and a spawned Windows descendant. New tests require Windows validation. **OPEN.** |
| Generic 500 for busy/timeout/crash conflates causes | **OPEN contract decision.** Independent reviewer found the shape defensible but did not accept it as a final transport amendment. Operator-side cause metrics/logging still required. |
| Windows virtualenv child termination unproven | Owner ran 7 targeted tests and 1010 backend tests on Windows, 25 September, including the previous abrupt-worker test. New direct PID and descendant checks remain pending. |
| Large partial pipe write not tested | **OPEN.** The deadline loop is independent of the reader thread, but a partial-write test is still required. |
| CORS, ingress rate/global caps, proxy trust absent | **OPEN — launch blocker.** The local code must not be described as public abuse protection. |

CT7 calculations and React remain unchanged. The isolation path remains opt-in
only and is not part of the validated public release.
