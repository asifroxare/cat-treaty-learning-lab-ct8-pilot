# CT2 Immutable Models Checkpoint

**Status:** PASS

Implemented in `cat_treaty/ct2_models.py`:

- frozen contract enums for loss components, cover types, valuation modes,
  completion states and binding constraints;
- immutable loss-component, loss-basis input and reconciled result models;
- immutable inuring-cover input and collection-level waterfall input models;
- immutable cover-result and completed-waterfall response models;
- aggregate-before/after state validation;
- deterministic reconciliation and explanation records;
- strict mode exclusivity, non-negative finite values, share/rate bounds,
  explicit order, unique cover/source IDs and reporting-currency consistency;
- completed-result gating for CT3; and
- complete cover-input retention in each result row for auditability.

No F03–F09 calculation engine was added in this checkpoint. Constructors
validate completed records but do not originate actuarial amounts.

## Verification

- CT1 baseline entering CT2: 338 tests.
- Full suite after this checkpoint: 401 tests.
- Python bytecode compilation: required before commit.
- Working tree: required clean after commit.
