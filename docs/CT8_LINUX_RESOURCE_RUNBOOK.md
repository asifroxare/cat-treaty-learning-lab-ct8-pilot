# CT8 Linux resource acceptance — proposed runbook

**Status:** reviewed procedure candidate, not executed. Do not deploy from
this document. The Work container does not have Docker or the backend
dependencies. Its 8 GiB cgroup is not the proposed target host.

1. Build a reproducible Linux image from the exact review commit and pinned
   dependency lock, recording Python/OS/image digests. Use the dedicated
   Catastrophe Treaty Learning Lab repository only.
2. Run the legal fixtures in an isolated container with an OS-enforced
   memory and PID ceiling, no outbound network, one API worker, one accepted
   computation and a parent deadline below the tested edge read timeout.
   The first trial limit is a diagnostic ceiling, not a selected host size.
3. Record each request digest and acceptance status, cgroup `memory.peak`,
   CPU and wall time, actual response JSON and pickled bytes, exit reason,
   complete engine identity, and PID list before and after cleanup. Stop the
   sequence on any OOM, non-completion, orphan or mismatch. Re-run successful
   cases on the selected staging instance before choosing public limits.
4. Include 10,000 trials with one event/full detail; the legal 25,000 full
   rows under 25 MiB; high-occurrence **summary** requests where body/schema
   constraints permit; four-layer cases; and hours candidate expansion.
   Do not assume 100,000 full-detail rows are legal: CT6 caps full detail at
   25,000 rows. Check every case against the frozen schema and error
   precedence before calling it a legal maximum.
5. Verify deadline exit and abrupt API-worker death with a descendant child
   on the actual Linux image. Inspect cgroup processes, not only a response
   status or marker absence. A surviving child blocks promotion.
6. Compare maximum accepted wall time plus serialization/transfer margin
   with the real Cloudflare and hosting timeouts. Verify rate/global admission
   and direct-origin bypass controls at staging. Record independent review
   before selecting a plan or proposing any versioned transport change.

The first Linux run should use a conservative bounded fixture and a memory
limit chosen for that host; increasing limits requires explicit host and
cost review. Neither a 2 GiB instance nor any longer runtime is endorsed by
the partial Windows evidence. The owner has not authorized a paid service.
