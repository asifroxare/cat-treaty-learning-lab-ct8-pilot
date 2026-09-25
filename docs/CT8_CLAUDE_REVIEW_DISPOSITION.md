# Independent CT8 execution review — disposition

Review received 25 September 2026. Public isolation remains OFF and public
deployment is not authorized.

| Finding | Disposition |
| --- | --- |
| Near-max legal response, 128 MiB IPC cap and 30-second deadline unmeasured | **OPEN — launch blocker.** No parameter justified from 1–100 trial samples. |
| Semaphore is per API worker | **OPEN — launch blocker.** Require a single-worker/one-instance launch gate or cross-process/global cap and verify actual hosting configuration. |
| No HTTP busy/deadline evidence | Added targeted HTTP tests: busy returns sanitized `CT6_INTERNAL_ERROR` without a partial result; admitted response equals ordinary baseline; synthetic deadline returns sanitized 500 without partial result. Windows result pending. |
| Abrupt parent death can orphan a child | Added child watchdog waiting on the parent's multiprocessing sentinel and an abrupt-worker-death test. Windows test and platform review pending. **OPEN.** |
| Generic 500 for busy/timeout/crash conflates causes | **OPEN contract decision.** Independent reviewer found the shape defensible but did not accept it as a final transport amendment. Operator-side cause metrics/logging still required. |
| Windows virtualenv child termination unproven | Updated evidence: owner ran the 4-test targeted suite on Windows on 25 September; the started-child deadline marker test passed. Full backend suite then passed 1007. Further abrupt-worker tests still needed. |
| Large partial pipe write not tested | **OPEN.** The deadline loop is independent of the reader thread, but a partial-write test is still required. |
| CORS, ingress rate/global caps, proxy trust absent | **OPEN — launch blocker.** The local code must not be described as public abuse protection. |

CT7 calculations and React remain unchanged. The isolation path remains opt-in
only and is not part of the validated public release.
