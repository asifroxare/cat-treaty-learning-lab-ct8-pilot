# CT8 exact trial limit — owner Windows, 27 September 2026

The guarded direct Python computation for 10,000 full-detail catalogue trials
and exactly one occurrence/one layer per trial completed in 18.5238 seconds.
The request was 9,497,025 bytes and the `pickle.dumps(("ok", result),
protocol=5)` child-result shape was 43,940,239 bytes. The sampled process-tree
peak was 424.97 MiB across recorded PIDs 12092 and 28832. This is a local
synthetic scenario and is not a staging-host resource guarantee. The sample
remained within the 30-second/800 MiB local guard and 128 MiB child-result cap.

This tests CT6's **trial count** limit, not the 100,000-occurrence or
25,000-full-row combinations, four layers, 25 MiB body, or hours candidates.
It does not approve those public limits or the chosen deadline/cap. See
`CT8_SERIALIZED_SIZE_EVIDENCE.md` for smaller full-detail measurements.
