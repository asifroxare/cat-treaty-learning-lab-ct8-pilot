# CT8 bounded full-API Linux gate — prepared, not run

**Status 27 September 2026: OPEN.** The Work environment does not have
FastAPI, Uvicorn, pytest or HTTPX installed and cannot fetch the pinned
dependencies. The owner does not have Docker. No full-API Linux pass is
claimed; no public deployment, paid service or contract change is authorized.

`deployment/linux_api_capacity_gate.py` is a self-contained local probe for a
reviewer with project Python dependencies installed in a **dedicated Linux
cgroup-v2 container limited to 1.5–2 GiB**. It refuses an unbounded or
oversized cgroup. It binds one Uvicorn worker to loopback only, enables opt-in
CT8 isolation with one slot and a *probe-only* 90-second deadline, then shuts
down the worker in a `finally` block. It reads at most 150 MiB of HTTP response
and stops requests after 105 seconds. The container runtime must enforce the
cgroup limit if the probe itself is killed. Do not run this inside a shared
production cgroup or directly on the owner's Windows machine.

Suggested execution **inside that container**, from the extracted repository
root, after installing exact project requirements:

```sh
python deployment/linux_api_capacity_gate.py
python deployment/linux_api_capacity_gate.py --full
```

The first case uses 1,000 trials, 1,000 occurrences and four layers. The
second is an **explicit** 10,000-trial, 25,000-occurrence full-detail legal
fixture with four layers. Each must return HTTP 200, an authoritative
`complete` response, a response byte count and SHA-256 excluding only the
request ID, elapsed time, and the whole cgroup's `memory.peak`. The gate fails
if `memory.events` records a new memory ceiling event or if the request,
readiness, response or server lifecycle fails. Record the cgroup CPU limit,
Python/dependency versions, commit, container image digest and outputs.

**Verification already done here:** generated requests are byte-for-byte
equal in size to the previously validated four-layer direct-engine fixtures
(948,994 and 22,707,357 bytes); the script compiles; and it refused this
Work environment's 8 GiB memory cgroup. The live API path has **not** been
executed here. This probe covers only catalogue; high-occurrence summary,
hours candidates, cross-route error precedence, frontend, edge, monitoring,
rollback and independent review remain separate gates. A pass on 2 GiB would
be evidence for these fixtures only, not a blanket plan-size approval.

If the full case times out, exceeds memory, or fails the 128 MiB result cap,
record the stop and preserve the frozen CT6 contract. Decide host sizing or a
separately versioned transport amendment in independent review; do not simply
turn up a public deadline or change response limits.
