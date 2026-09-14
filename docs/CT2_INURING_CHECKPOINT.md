# CT2 F05–F09 Ordered-Inuring Checkpoint

**Status:** PASS

Implemented in `cat_treaty/inuring.py`:

- F05 cover subject loss from sequential incoming loss and declared scope;
- F06 calculated quota-share or authoritative supplied recovery;
- F07 occurrence-limit and aggregate-remaining constraints;
- F08 sequential outgoing loss without order selection or optimization;
- F09 per-cover and total-waterfall reconciliation;
- explicit binding-constraint records, including simultaneous constraints;
- aggregate remaining after the occurrence;
- deterministic explanation facts, warnings and assumption disclosures; and
- completed/no-cover states that provide validated Cat XL subject loss to CT3.

Covered by `tests/test_ct2_inuring.py`:

- G06 and G19 quota share before Cat XL;
- G18 no-cover identity;
- G20 order-sensitive scenarios;
- G21 occurrence and aggregate limits;
- G22 supplied recovery;
- G23 zero-scope behavior and strict supplied-recovery rejection;
- G24 duplicate source prevention at the immutable input boundary;
- partial scope, zero aggregate, nonbinding limits and two-cover sequencing;
- deterministic explanations and passed reconciliation records; and
- immutability, non-mutation and invalid engine types.

No Cat XL layer/tower, annual carryover, simulation, pricing, API or frontend
logic was introduced.

## Verification

- Prior suite: 417 tests.
- Full suite after F05–F09 implementation: 441 tests.
