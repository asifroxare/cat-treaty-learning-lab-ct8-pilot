# CT8 checkpoint 11 — bounded isolation scaling probe

Owner confirmed the checkpoint 10 Windows targeted isolation suite (9 passed)
and full backend suite (1012 passed) on 25 September 2026.

`deployment/measure_isolation.py` launches the API on `127.0.0.1` with exactly
one worker, opt-in spawned computation, one execution slot and the candidate
30-second deadline. It runs 100, 500 and 1000 synthetic trials in summary
mode, then 1000 trials in full mode. Each request is limited to 2 MiB, the
trial generator is capped at 1000, and response byte count, request byte count,
elapsed time and sampled process-tree peak are reported. The local API process
tree is terminated on exit. A dependency-free test checks the generator's
limits, identities and full-detail selection.

This probe does **not** reach CT6's maxima (10,000 trials, 100,000 occurrences,
25 MiB input and up to 25,000 full rows), does not establish memory or deadline
requirements for a public host, and does not authorize deployment. The
reviewer's outstanding capacity, global concurrency and ingress blockers stay
open. There is no actuarial or frontend change.
