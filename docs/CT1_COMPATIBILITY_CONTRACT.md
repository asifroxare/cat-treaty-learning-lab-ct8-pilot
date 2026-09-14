# CT1 Compatibility and Migration Contract

**Status:** Frozen implementation contract  
**Treaty schema:** `ct1.0`  
**Supported pricing API baseline:** `1.0.0`

## Purpose

This contract permits the Catastrophe Treaty Learning Lab to reuse validated
Cat XOL Pricing Lab results without silently changing their meaning. It does
not create an HTTP API; it freezes the rules that a later API must apply.

## Legacy request rule

An existing pricing request that supplies none of the new CT1 fields remains
valid. The compatibility boundary resolves it as:

- `ceded_share = 1.0`
- `placement_share = 1.0`
- `settlement_mode = paid_separately`
- effective `schema_version = ct1.0`
- migration notice `legacy_request_defaults_applied`

These defaults preserve existing numerical recovery and pricing behavior.

## Canonical CT1 rule

A request using `ceded_share`, `placement_share`, or `settlement_mode` must
explicitly supply `schema_version = ct1.0`. This prevents a new field from
being accepted under an unidentified or legacy schema.

Canonical fields omitted from an explicit CT1 request receive the documented
100% shares and paid-separately defaults without a legacy migration notice.

## Supported literals

- Capacity basis: `payable_placed_share`
- Settlement modes: `paid_separately`, `deducted_from_settlement`
- Product ID: `cat_treaty_learning_lab`
- Reserved product route: `/cat-treaty`

Unknown schema versions, pricing API versions, capacity bases, or settlement
modes fail explicitly. Values are never guessed, coerced by spelling, or
silently reinterpreted.

## Product boundary

The Cat XOL Pricing Learning Lab and Cat Treaty Learning Lab remain separate
user experiences. Compatibility defaults do not redirect a pricing user into
the treaty product and do not change the deployed pricing interface.

## Deprecation rule

CT1 does not remove any existing pricing field. A later removal or semantic
change requires all of the following:

1. a new reviewed specification version;
2. a new schema version;
3. a documented replacement field;
4. a stated migration period; and
5. regression tests for both products.
