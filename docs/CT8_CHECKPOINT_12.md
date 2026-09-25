# CT8 checkpoint 12 — guarded serialized-result measurement

Owner's 100–1,000-trial opt-in HTTP measurements appear in
`CT8_ISOLATION_SCALING_EVIDENCE.md`; they do not measure the pickled result
sent over the CT8 child pipe. `deployment/measure_pickle_gate.py` runs separate
local workers at fixed 1,000, 2,500 and 5,000 full-detail trial counts, with
one occurrence per trial. Each worker computes the unchanged CT6 catalogue
result and measures `pickle.dumps(("ok", result), protocol=5)`, the same result
shape and protocol as the optional isolation executor. It prints only size
metadata, never a treaty result. A Windows process-tree sampler aborts a run
at 800 MiB of summed observed working sets or 30 seconds, and always
terminates the spawned process tree. `STOPPED` is a valid safety outcome,
not evidence that a public threshold was achieved.

This measurement intentionally stops short of 10,000 trials, 100,000
occurrences, 25 MiB input, 25,000 full-detail rows and multi-layer cases.
The probe's sampling can miss very short memory spikes; it is not a hard OS
memory limit. The 128 MiB cap and 30-second deadline stay unapproved, as do
all public ingress, multiworker and staging controls. Frozen actuarial code
and React remain unchanged.

First owner Windows attempt stopped at 1,000 trials before computation:
the probe directly validated raw JSON against strict tuple types. The API's
`_normalize_json_value()` is required first. This probe-only defect is fixed
in the next ZIP; the failed attempt supplies no size or capacity evidence.
