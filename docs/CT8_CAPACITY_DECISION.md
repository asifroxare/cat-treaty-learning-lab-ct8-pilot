# CT8 capacity decision gate — 27 September 2026

**Status: blocked for public deployment; no plan or purchase selected.**

The frozen CT6 transport accepts up to 10,000 trials, 100,000 occurrences,
25 MiB input and 25,000 full-detail rows. The optional CT8 isolated path has
a candidate 30-second deadline and a 128 MiB pickled child-result cap.

Owner Windows measurements establish:

| Valid synthetic workload | Result |
| --- | --- |
| 10,000 trials, one occurrence and one layer per trial, full detail | Completed in 18.52s; 43.94 MB pickled result; observed 424.97 MiB process-tree peak. |
| 10,000 trials, 25,000 occurrences, one layer, full detail, 22.71 MB request | Stopped at the 30s local guard without a result. |
| Same 25,000-occurrence request with up to 90s allowed | Stopped at the observed 800 MiB process-tree guard without a result. |

These process-tree figures sum sampled peak working sets, may count shared
pages more than once, and do not establish the true peak or host capacity.
The 25,000-row response size and completion time remain unknown. Four-layer
and hours-clause maxima also remain unmeasured. The default CT8 isolation
deadline is demonstrably too short for the sampled legal row-limit workload.

Render documents 512 MB RAM for its Free web service and 2 GB and higher RAM
options in other plans. The 512 MB free instance is **not an approved
candidate** for the currently sampled legal row-limit workload. This is an
inference from the stop and plan sizes, not a benchmark on Render Linux.
Cloudflare documents a default 125-second origin proxy read timeout. A longer
application deadline must leave enough margin for response serialization and
transfer, and be tested on the actual route.

Two possible directions require separate review:

1. Preserve the frozen CT6 maximums. First measure a complete legal
   row-limit and other meaningful worst-case workloads under a reviewed
   host resource ceiling; choose and stage an adequately sized paid or other
   host, set a justified result cap/deadline, and verify global admission,
   ingress and browser behavior. Do not select plan size from these local
   partial probes alone.
2. Propose a formal versioned public contract revision with lower limits or
   an asynchronous job protocol. This requires explicit owner authorization,
   independent actuarial/transport review, revised OpenAPI and acceptance
   evidence. It cannot be applied silently to CT6 or CT0–CT7.

Current recommended direction is (1) because the owner asked to preserve
frozen decisions. Neither direction authorizes spending or deployment.

Official references checked 27 September 2026:
- https://render.com/docs/compute-plans
- https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/
