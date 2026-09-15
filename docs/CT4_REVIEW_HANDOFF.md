# CT4 Independent Review Handoff

Review `docs/CT4_IMPLEMENTATION_SPEC.md` v1.0 against the frozen CT0–CT3
architecture. This is a specification review; no CT4 implementation is present.

## Required review scope

1. Verify F17–F24 algebra and denominator conventions.
2. Recompute at least one hand-worked OEP/AEP/TVaR example.
3. Test empty-year, zero-mean and return-period boundary behavior.
4. Review the distinction between exact reproducibility and statistical
   stability.
5. Review the frozen reference generator, draw order, seeds, sample sizes and
   tolerances before any CT4 code is written.
6. Confirm every recovery is clearly pre-annual-capacity and does not anticipate
   CT5.
7. Review hours-window validity separately from election and confirm invalid
   higher-recovery alternatives cannot win.
8. Answer all 15 questions in section 26 explicitly.

## Requested finding format

For each finding provide:

- stable ID such as `CT4-A`;
- section/formula affected;
- severity (`blocker`, `major`, `minor`, `cosmetic`);
- numerical or contractual reasoning;
- exact revision required; and
- golden case or regression test required.

State separately whether the formula set, empirical-tail conventions, stability
gate, hours-clause controls and milestone boundary are ready to freeze.
