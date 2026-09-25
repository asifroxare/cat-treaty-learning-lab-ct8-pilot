# CT8 opt-in isolation scaling evidence — owner Windows

Owner executed `deployment/measure_isolation.py` on 25 September 2026.
The command launched one local API worker on loopback with
`CT8_ISOLATED_RUNS=true`, one local slot and a 30-second candidate deadline.
All requests were synthetic catalogue fixtures with one occurrence per trial
and one layer. Each completed with HTTP 200 and an authoritative completion
status. Reported process-tree peaks sum peak working sets from sampled PIDs;
these may double-count shared memory and are approximate.

| Trials | Detail | Request bytes | Response bytes | Wall seconds | Observed process-tree peak MiB |
| ---: | --- | ---: | ---: | ---: | ---: |
| 100 | summary | 95,618 | 554,202 | 1.3892 | 134.08 |
| 500 | summary | 474,018 | 2,532,844 | 2.1651 | 161.31 |
| 1,000 | summary | 947,023 | 5,024,076 | 3.2442 | 201.30 |
| 1,000 | full | 947,020 | 7,409,041 | 3.3565 | 231.46 |

The default result IPC cap is 128 MiB of pickled child output, whereas the
reported bytes above measure HTTP JSON responses. The two sizes are not
interchangeable. The sample did not approach 10,000 trials, 100,000 total
occurrences, 25 MiB input, 25,000 full-detail rows, four layers, or the
largest legal hours candidate workload. Do not extrapolate these samples to
those bounds. Neither the 30-second deadline nor the 128 MiB cap is approved
for public execution. Cross-worker concurrency, ingress policy, staging and
production browser acceptance are also open.
