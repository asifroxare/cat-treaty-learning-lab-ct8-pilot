# CT8 child serialization evidence — owner Windows, 27 September 2026

The owner ran `deployment/measure_pickle_gate.py` with the existing CT7
Windows virtual environment. Each separate local process computed the unchanged
CT6 catalogue result for one occurrence per trial and full response detail.
The measured byte length is `pickle.dumps(("ok", result), protocol=5)`, the
shape and protocol used by the optional CT8 child pipe. All fixed samples
completed before the candidate 30-second deadline and below the probe's
observed 800 MiB process-tree stop. The safety sampler measures summed sampled
working sets; shared pages can be double counted and short peaks missed.

| Trials | Request bytes | Pickled result bytes | Wall seconds | Observed process-tree peak MiB |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 947,020 | 4,399,466 | 3.3001 | 100.04 |
| 2,500 | 2,372,020 | 10,989,110 | 4.9597 | 147.04 |
| 5,000 | 4,747,020 | 21,972,222 | 9.0436 | 255.04 |

The 5,000-trial sample is below the 128 MiB default child-result cap. It does
not establish a bound at 10,000 trials, 100,000 occurrences, 25 MiB input,
25,000 full-detail rows, four layers or hours-clause candidate expansion.
These dimensions cannot be extrapolated safely from a one-occurrence,
one-layer sample. The measurement is direct Python orchestration and pickle
serialization, not an API response or a staging deployment. It gives no
approval of the public result cap, deadline or host resources. The previous
probe-only validation error and interrupted sampling provided no measurement.
