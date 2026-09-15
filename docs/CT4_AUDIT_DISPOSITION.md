# CT4 Independent Audit Disposition

**Specification:** `docs/CT4_IMPLEMENTATION_SPEC.md` v1.1

**Disposition:** Accepted and frozen

**Date:** 15 September 2026

## 1. Dependency provenance

The review's blocking question concerned CT4's reference to CT3 v1.1 after the
reviewer had previously seen CT3 v1.0. CT3 v1.0 was the review draft. The
reviewed geometry-classification gap was resolved in CT3 v1.1 at commit
`5c61fb3`:

- topology classification became independent of contractual eligibility;
- `overlapping` became the exhaustive topology value for overlap without gaps;
- G29 returns classified geometry and structured `uncoordinated_overlap`
  reasons; and
- blocked geometry emits no program or layer recovery.

CT3 was subsequently implemented and accepted at commit `d58dccb` with 616
tests passing. The dependency is therefore resolved rather than deferred.

## 2. Formula disposition

The independent review accepted F17–F24. F20 preserves the occurrence identity
through annual totals and AAL. F21 and F23 use the same nearest-rank index.

The review also identified a useful consequence of frozen program terms:
recovery and insurer net loss are non-decreasing in subject loss. CT4 v1.1 now
requires the greatest-subject-loss occurrence to attain all three F17 maxima
and freezes a common deterministic driver tie-break. A regression gate will
test this invariant, including recovery plateaus.

## 3. Clarifications incorporated

| Finding | Disposition |
|---|---|
| Credibility warnings might be interpreted as mutually exclusive | All applicable warning codes now attach cumulatively. |
| Occurrence mode appeared simulation-wide only by inference | It is explicitly simulation-wide; hours-clause teaching mode requires exactly one trial and cannot mix with catalogue mode. |
| G11/G13 provenance was not local to CT4 | CT4 now points to the frozen CT1/CT0 reservations and CT3 preservation of those IDs. |
| `r/Y` versus `r/(Y+1)` remained open | `r/Y` is frozen as observed empirical trial frequency; its 100% endpoint is intentional. |
| Pre-annual-capacity terminology might remain prose-only | The exact backend and future API field name is mandatory. |
| One bad record can waste a large run | A preflight stage is required, but any later invalid occurrence still blocks the run and partial analytics remain prohibited. |

## 4. Stability governance

The reviewer accepted the separation of exact reproducibility from statistical
stability and the advance freeze of the reference generator, RNG draw order,
seeds, sample sizes, metrics and tolerances. These values may not be adjusted
after implementation results are observed without a reviewed specification
amendment.

## 5. Freeze decision

CT4 Implementation Specification v1.1 is frozen for implementation. This
checkpoint contains no CT4 production code. The next authorized checkpoint is
the immutable CT4 catalogue, trial, occurrence and analytics domain models with
validation tests.
