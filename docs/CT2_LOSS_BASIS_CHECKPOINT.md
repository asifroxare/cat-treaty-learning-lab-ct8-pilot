# CT2 F03/F04 Loss-Basis Checkpoint

**Status:** PASS

Implemented in `cat_treaty/loss_basis.py`:

- `build_loss_basis()` as the authoritative pure F03 calculation;
- category-controlled addition and deduction treatment;
- preservation of included and excluded component records;
- explicit rejection when deductions create negative Ultimate Net Loss;
- explicit rejection of derived non-finite totals;
- constructor-enforced F03 result integrity; and
- `verify_loss_basis_reconciliation()` as an independent F04 check.

Covered by `tests/test_ct2_loss_basis.py`:

- no-component identity;
- G17 across every F03 component category;
- included/excluded behavior;
- each addition and deduction category independently;
- zero-UNL boundary;
- G25 excess-deduction rejection;
- overflow and invalid-type rejection;
- immutability and non-mutation; and
- component-order stability.

No inuring recovery calculation, Cat XL calculation, API or frontend logic was
added in this checkpoint.

## Verification

- Prior CT1 plus CT2-model suite: 401 tests.
- Full suite after F03/F04 implementation: 417 tests.
