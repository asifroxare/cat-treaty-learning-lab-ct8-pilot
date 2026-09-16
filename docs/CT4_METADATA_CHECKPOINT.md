# CT4 Deterministic Metadata and Hashing Checkpoint

## Scope completed

- Frozen engine version `ct4.0.0` and schema version `ct4.0`.
- Canonical JSON serialization with stable keys, numeric normalization and no rounding.
- Version-bound SHA-256 normalized-input hashes.
- Canonical result hashes bound to the input hash, engine and schema versions.
- Catalogue occurrences normalize by time, sequence and event ID.
- Hours components normalize by timestamp and component ID.
- Empty annual trials remain present in normalized inputs and completed results.
- Seed, catalogue/source identity, treaty terms, loss inputs and contractual election settings affect identity.
- Descriptions, explanation wording, display references, formatting and UI state are excluded.
- Completed hashes require matching F19-F24 analytics; blocked hours elections cannot masquerade as completed results.
- Catalogue and hours-clause results share the same immutable CT4 run-identity contract.

## Response compatibility

The immutable `CT4RunIdentity` remains the public identity envelope and carries simulation ID, normalized-input hash, result hash, engine version and schema version. Full catalogue/source/seed disclosure remains available through the immutable simulation input bound by that hash.

## Deferred by design

- Frozen synthetic reference generator and multi-seed/sample stability gate.
- Consolidated G11, G13 and G35-G46 final acceptance report and distribution.

## Verification

Verified result: `733 passed`. The full suite must pass with a clean working tree before distribution.
