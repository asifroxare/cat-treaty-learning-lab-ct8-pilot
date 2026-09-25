# CT8 bounded resource evidence — 25 September 2026

Owner Windows local sample on the corrected CT8 candidate:

| Synthetic catalogue request | Body bytes | Response seconds | Observed process-tree peak MiB |
| --- | ---: | ---: | ---: |
| 1 trial, one request | 2,386 | 0.0391 | 62.79 |
| 10 trials, one request | 10,833 | 0.0688 | 63.21 |
| 100 trials, one request | 95,618 | 0.2863 | 67.80 |
| 10 trials, two concurrent requests | 10,833 each | 0.1218 / 0.1239 | 67.80 |

The probe sampled the virtual-environment launcher and child interpreter
(PIDs 1736 and 29804). The previous flat 4.08 MiB launcher-only reading is
invalid and excluded. Peak working sets summed across processes may double
count shared pages and are only approximate. This is a single short local run,
with one layer, one occurrence per trial and summary detail. Do not extrapolate
to CT6's 10,000-trial/100,000-occurrence/25 MiB bounds or use these figures to
select a public plan, deadline or concurrency limit.

`deployment/isolated_execution.py` is an **unconnected prototype** that
spawns a child process and terminates it after a deadline. Three local
outcomes were exercised: complete result, deadline termination, abrupt child
exit. It is not wired into FastAPI. In particular, its result transport and
error mapping need further review for large CT6 responses and frozen problem
precedence before an application-level control can be approved.
