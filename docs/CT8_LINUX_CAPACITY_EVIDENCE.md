# CT8 bounded Linux direct-engine measurement — 27 September 2026

The Work Linux container used the unchanged CT6 catalogue orchestration and
the exact `_normalize_json_value` function compiled from `cat_treaty/api.py`
without importing the unavailable FastAPI package initializer. The worker
ran in a separate process with an OS-enforced 2 GiB `RLIMIT_AS` address-space
ceiling and a 100-second parent deadline. The Work container itself has an
8 GiB cgroup. This was **not** a Render host or a live CT6 API request.

| Synthetic full-detail case | Request bytes | Pickled result bytes | Worker peak RSS | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| 1,000 trials, one occurrence and layer per trial | 947,020 | 4,399,466 | 75,920 KiB | 1.109 |
| 10,000 trials, 25,000 occurrences, one layer | 22,705,383 | 91,939,829 | 835,600 KiB | 27.529 |
| 1,000 trials, 1,000 occurrences, four contiguous layers | 948,994 | 5,736,313 | 88,992 KiB | 1.653 |
| 10,000 trials, 25,000 occurrences, four contiguous layers | 22,707,357 | 120,092,827 | 1,150,288 KiB | 36.497 |

The small case's pickled byte count exactly matches the owner Windows
measurement (4,399,466), supporting the wire-normalization and serialization
method. The 25,000-row Linux case completes below the **candidate 128 MiB
pickle cap** and the 2 GiB OS address-space ceiling in this specific
environment. 835,600 KiB is about 816 MiB for the direct worker alone; API
worker memory, child launcher, response projection and concurrent ingress are
not included. Windows previously stopped the corresponding probe at 30s and
then at an observed 800 MiB *summed process-tree* guard, so it produced no
authoritative Windows result for this case.

The four-layer fixture duplicates treaty terms into contiguous 20m layers
at attachments 10m, 30m, 50m and 70m, with consistent layer IDs and one
settlement mode. It passed strict CT6 model validation and unchanged backend
orchestration. Its 120,092,827 pickled bytes leave 14,124,901 bytes under
the candidate 128 MiB cap, so another legal loss mix or extra evidence could
still exceed that cap. This Linux completion does not approve the 30-second
isolation deadline: the four-layer case required 36.497 seconds *without*
the full API, response projection or edge transfer, and the target host may
have fewer CPU resources. It does not prove a 2 GiB Render instance is
sufficient. High-occurrence summary mode and hours-clause candidates remain
unmeasured. The next gate is a measured full API run on a bounded Linux
staging instance with process-tree/cgroup peak, error precedence and complete
golden identities. No public deployment or purchase is authorized.
