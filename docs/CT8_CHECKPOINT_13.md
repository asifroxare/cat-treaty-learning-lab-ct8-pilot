# CT8 checkpoint 13 — guarded exact trial limit

Owner's 5,000-trial full-detail direct serialization was 21,972,222 bytes in
9.0436 seconds at an observed 255.04 MiB process-tree peak. This checkpoint
adds a **separate** local 10,000-trial full-detail sample with one occurrence
and one layer per trial. The synthetic request cap is 12 MiB; the shared
process-tree sampler stops the child at an observed 800 MiB or after 30
seconds and prints progress. The worker is terminated in `finally`. The
fixed 1,000/2,500/5,000-trial probe remains unchanged in its run sequence.

Even if this new sample passes, it does not address CT6's 100,000-occurrence,
25 MiB-body, four-layer or hours-clause maxima, nor the 25,000 full-detail
row combination. The observed peak is sampled and may miss a short spike.
No public resource/deadline decision is authorized. Frozen actuarial modules
and frontend components are unchanged.
