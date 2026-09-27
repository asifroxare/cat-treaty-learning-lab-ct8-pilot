# CT8 checkpoint 14 — full-detail row limit candidate

This checkpoint adds a distinct local fixture with exactly 10,000 trials and
25,000 occurrences (three occurrences in the first 5,000 trials and two in
the remaining 5,000). Event identities, CT2 loss-basis occurrence identities,
sequences and times are unique and aligned. The generated request is
22,705,383 bytes, below CT6's 25 MiB input cap. An offline test checks its
count, uniqueness and body limit. The new guarded worker uses the same
30-second and sampled 800 MiB process-tree safety stops as checkpoint 13.

`STOPPED` is an informative result and means the public 30-second candidate
deadline or memory threshold may be unsuitable. Even a PASS would not cover
100,000 occurrences, four layers, hours candidates or ingress behavior.
Frozen actuarial code and React have not changed. No deployment is authorized.

The owner ran the initial version on Windows and the legal 25,000-row request
hit the local 30-second safety stop. The revised measurement uses **90 seconds
only for the local row-limit probe** while retaining the observed 800 MiB stop.
The production `CT8_ISOLATION_DEADLINE_SECONDS` default remains 30 and must
not be enabled publicly on the evidence currently available.
