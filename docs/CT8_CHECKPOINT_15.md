# CT8 checkpoint 15 — independent Linux cleanup review candidate

The independent capacity reviewer confirmed the evidence memo and identified
Linux descendant cleanup and generic busy/timeout/crash 500 responses as
unresolved launch gates. `CT8_CLAUDE_CAPACITY_REVIEW_DISPOSITION.md` records
all seven findings and `CT8_LINUX_RESOURCE_RUNBOOK.md` sets out a proposed
host acceptance procedure. No public capacity, paid plan or versioned
transport change is approved.

The optional CT8 executor now starts a POSIX child in its own process group.
On Linux, a parent deadline kills that group; if the API worker exits abruptly,
the child watchdog detects the parent sentinel closing and kills its own
group. Windows continues to use the prior `taskkill /T /F` path. Both an
unconnected process-tree experiment and the **actual CT8 `_run_process`**
passed deadline and abrupt-parent Linux tests with a spawned descendant in
the Work container. Thirteen dependency-free deployment-tool tests passed.

The Work container has no FastAPI/pytest/uvicorn dependencies and no Docker.
The full API/backend Linux suite and Windows regression for this candidate
have **not** run. `CT8_ISOLATED_RUNS` remains OFF by default. Frozen CT0–CT7
calculations, hashes and React components remain unchanged. The 30-second
deadline and 128 MiB IPC cap are still unapproved for public use. Require
independent source review and platform reproduction before treating this
candidate as a deployment control.
