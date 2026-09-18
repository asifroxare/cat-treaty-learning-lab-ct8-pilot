# CT7 Independent Review Disposition

**Reviewed draft:** `CT7_IMPLEMENTATION_SPEC.md` v1.0  
**Revised draft:** v1.1  
**Status:** All F01–F08 revisions incorporated; awaiting reviewer confirmation before freeze

| ID | Severity | Decision | Revision | Required evidence |
|---|---|---|---|---|
| F01 | Blocking | Accepted | Added result-specific evidence-path resolution, neutral-content rules and G104–G105. | Invented uncited Why fixture and “recommended election” fixture must fail. |
| F02 | Major | Accepted | Defined `resultFreshness = none/current/stale` as orthogonal to the single execution state. | G89 asserts `editing + stale` and allowed stale coexistence during submission/error. |
| F03 | Major | Accepted | Added frozen mapping for every CT6 problem code, network failure and unknown response. | Contract tests assert exactly one mapped state per code. |
| F04 | Major | Accepted | Defined branded `AuthoritativeNumber`, type-aware ESLint prohibitions, import boundaries and narrow formatting behavior. | G102 must reject `recovery = grossLoss - retention`. |
| F05 | Minor | Accepted | Named `docs/CT6_TEST_COUNT_ADDENDUM.md` and required independent-reviewer plus project-owner acceptance. | Missing/unaccepted addendum blocks any successor count. |
| F06 | Minor | Accepted | Forbade numeric deltas and all non-numeric output-difference/ranking badges in CT7 v1. | G96 asserts their absence. |
| F07 | Minor | Accepted | E01 and E02 now cite the governing CT2/CT3 specifications and sections. | Experiment contract tests retain citations. |
| F08 | Cosmetic | Accepted | Replaced the mixed input list with a destination-specific table. | Information-architecture review verifies route placement. |

## Reviewer-answer disposition

- Product separation remains frozen and G84 now checks cross-navigation state
  isolation.
- Side-by-side comparison remains the CT7 v1 decision.
- Pre/post-capacity, hours-clause evidence, full/summary semantics,
  accessibility, security and persistence decisions remain unchanged.
- Nothing has been deferred from CT7 to deployment readiness.
- F01–F04 were the freeze blockers; v1.1 resolves each with objective evidence.

## Freeze gate

This disposition does not self-approve the specification. The independent
reviewer must confirm that the revisions close F01–F08. Only then may the
document status change from **Revised Draft** to **Frozen**, and only then may
React scaffolding begin.
