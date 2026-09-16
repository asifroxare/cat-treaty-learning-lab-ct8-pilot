# CT5 Independent Audit Disposition

**Specification:** CT5 Implementation Specification — Frozen v1.0  
**Audit outcome:** Accepted after revision  
**Implementation status:** Authorized; no CT5 production code exists at freeze

## Disposition

| Finding | Decision | Frozen resolution |
|---|---|---|
| CT5-A — CT4 subject-loss provenance | Accepted | Section 4 now requires the exact occurrence-level `subject_loss` field, common to all layer rows, and rejects missing or renamed inputs. |
| CT5-B — utilization denominators | Accepted | The realized metric is named `realized_capacity_utilization`; its realized denominator is expressly distinguished from nominal reinstatement reserve. A numeric illustration is mandatory. |
| CT5-C — one event spanning tranches | Accepted | F30 expressly applies each tranche's own rate/time basis. G63 and a two-tranche worked example freeze the behavior. |
| CT5-D — tied timestamps | Accepted | G64 proves CT4 stable sequence/ID controls attribution of initial and restored capacity. |
| CT5-E — negative cash | Accepted | G65 requires a finite negative settlement without flooring. |
| CT5-F — combined amount/time proration | Accepted | G66 freezes multiplicative amount and remaining-term proration. |
| CT5-G — shortfall perspective | Accepted | F37 adds `capacity_constrained_recovery_shortfall` as a sixth OEP/AEP perspective; G68 freezes reconciliation and denominators. |
| CT5-I — no same-event benefit | Accepted | G67 proves reinstatement occurs only after the triggering occurrence's recovery is fixed. |
| CT5-J — tolerance definition | Accepted | Relative `1e-12` and absolute currency `1e-6` are fixed, version-bound and non-configurable in CT5 v1, with inside/outside boundary tests required. |
| CT5-M — changing shares | Accepted | Mid-year and per-event ceded/placement-share changes are expressly excluded. |

## Formula conclusion

F25–F36 were independently judged structurally sound. F37 is an additive
analytics identity and does not alter recovery, capacity, premium or settlement
calculations. No existing frozen CT0–CT4 formula is reopened.

## Authorization boundary

This disposition closes the review findings and authorizes staged CT5
implementation against the frozen specification. Each implementation checkpoint
must preserve all 759 inherited CT1–CT4 tests, add its specified CT5 tests and
leave the repository clean before moving to the next checkpoint.
