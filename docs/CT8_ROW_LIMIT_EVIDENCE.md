# CT8 legal row-limit result — owner Windows, 27 September 2026

The guarded local direct-serialization probe generated 10,000 trials with
25,000 unique occurrences, one layer and full detail. Its 22,705,383-byte
request body is below CT6's frozen 25 MiB input limit. The run printed
progress at 5, 10, 16, 21 and 26 seconds, then the parent guard stopped the
calculation at the **30-second local deadline**. No result byte count or final
peak working set was reported. There is no evidence of an authoritative
response for this sample. The process-tree cleanup is in the probe's `finally`
path; the supplied output does not independently prove every process exited.

This is concrete evidence that the candidate 30-second CT8 isolation deadline
is insufficient for at least one legal local full-detail workload on the
owner's Windows hardware. Do not enable `CT8_ISOLATED_RUNS=true` publicly with
the default 30-second deadline. This does not establish the elapsed time,
memory or pickled size needed to complete the sample, nor the suitability of
any hosting plan. Review a longer bounded deadline with a process-tree memory
guard and compare it against actual ingress/request timeouts before choosing
public settings. Frozen CT6 maxima must not be silently lowered.

Cloudflare currently documents a default 125-second proxy read timeout for a
proxied origin response (Error 524 on expiry), with a higher setting limited
to Enterprise. This ingress constraint needs staging verification; it does
not by itself justify a longer CT8 application deadline without complete
workload, transfer and host-resource evidence.

Reference checked 27 September 2026:
https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/

The owner next ran the 90-second/observed 800 MiB version. It printed progress
at 5, 10, 16, 21 and 26 seconds and then reported **STOPPED at the 800 MiB
local process-tree limit**. This is a sampled sum of peak working sets across
the process tree, not a measured unique resident set or a hard OS quota. The
output supplied no final elapsed time, result size or complete memory peak.
Do not infer the exact instance size required from this stop. The 30-second
deadline and 800 MiB local ceiling are independently inadequate as evidence
for serving this legal workload; further blind increases in either threshold
are not a substitute for a reviewed host capacity and contract decision.
