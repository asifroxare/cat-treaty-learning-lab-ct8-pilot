# CT4 Immutable Domain Models Checkpoint

**Specification:** CT4 Implementation Specification v1.1

**Status:** Implemented and verified

**Date:** 15 September 2026

## Implemented scope

- immutable event-level occurrence and explicit annual-trial inputs;
- declared trial population with contiguous IDs and empty-trial support;
- simulation-wide occurrence-definition mode;
- one fixed CT3 program-term fingerprint across catalogue occurrences;
- tail-probability, TVaR, return-period and numerical-tolerance configuration;
- timestamped hours-clause components and contract terms;
- bounded one-trial hours-clause teaching scenarios;
- contractual election authorization and manual-selection controls;
- valid/excluded candidate-window and candidate-set evidence records;
- cumulative tail-warning records;
- immutable perspective analytics with mean, population-standard-deviation and
  coefficient-of-variation reconciliation;
- exact `gross_contractual_recovery_pre_annual_capacity` occurrence ledger;
- annual F17 OEP, F18 AEP and F20 reconciliation validation;
- common OEP-driver identity and tie-break validation; and
- SHA-256 run-identity contract.

The models validate completed records but do not calculate simulation ledgers,
tail statistics or hours-window elections. Those algorithms remain in later
CT4 checkpoints.

## Verification

- 50 CT4 model and validation tests added;
- all 616 installed CT1–CT3 tests preserved;
- 666 tests passing in total;
- Python compilation and import boundaries passing; and
- no CT4 simulation, tail or election engine included.

## Next checkpoint

Implement catalogue-defined occurrence application, deterministic ordering,
preflight validation and F17–F20 annual ledgers.
