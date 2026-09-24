# CT8 checkpoint 7 — bounded local workload measurement

Windows CT8 candidate evidence: backend 1003 passed, frontend 72 passed,
production build/audit passed and real CT6 workflows passed. The owner also
ran `verify_goldens.py`: catalogue and hours-clause full-response digests
matched their frozen CT7 baselines. These are two synthetic scenarios and do
not establish worst-case safety or independent actuarial correctness.

Added `deployment/measure_local.py`: it launches an API bound to loopback,
sends summary-mode synthetic catalogue requests with 1, 10 and 100 trials,
then two simultaneous 10-trial requests. It samples the launched API process's
Windows peak working set, records duration/body size and terminates that
process in a `finally` block. It caps input count at 100 trials and has a
60-second client timeout. No public endpoint is accepted.

The local measurement is a first scaling observation only. It does not cover
10,000 trials, 100,000 occurrences, 25 MiB bodies, multiple layers, all
reinstatement patterns or public concurrency. The app has no proven
cancellation of a compute task when a client times out. No public resource
limits or rate thresholds should be chosen from these measurements alone.
