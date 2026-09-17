# CT5 Checkpoint 7 Acceptance — Deterministic Metadata

**Specification:** CT5 Implementation Specification — Frozen v1.0

## Implemented

- `CT5_ENGINE_VERSION = "ct5.0.0"`;
- `CT5_SCHEMA_VERSION = "ct5.0"`;
- exact reproduction and validation of the authoritative CT4 identity;
- canonical CT5 contractual-input serialization;
- canonical CT5 ledger and analytics serialization;
- version-bound SHA-256 input and result hashes; and
- immutable CT5 identity carrying both upstream CT4 hashes.

## Hash boundaries

Hash-significant inputs include CT4 input/result identity, ordered tranche
terms, premiums, time bases, treaty boundaries, settlement mode, fixed
tolerances, product identity and CT5 versions. Non-contractual layer input
order is canonicalized while tranche order is preserved.

Descriptions, source/rule/trace references, warning prose and display wording
are excluded. Completed analytics must exactly reproduce from the completed
CT5 ledgers before a result hash is emitted.

## Verification

- Focused CT5 metadata tests: 13 passed.
- Complete regression suite: 929 passed.
- Altered and unsupported CT4 identities fail before CT5 identity issuance.
- No CT1–CT4 behavior or formula was modified.
