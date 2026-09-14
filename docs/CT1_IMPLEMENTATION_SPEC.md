# Catastrophe Treaty Learning Lab — CT1 Implementation Specification

**Milestone:** CT1 — Compatibility and Shared Engine Freeze  
**Version:** 1.0  
**Status:** Approved implementation specification  
**Date:** 14 September 2026  
**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority

This specification implements CT1 under:

1. *Catastrophe Treaty Learning Lab Master Architecture — CT0 Frozen Specification v1.0*.
2. *CT0 Implementation Integration Addendum v1.3*.
3. The independently reproduced Cat XOL Pricing Simulator baseline at commit `a47eb24605f56e1c85701e04ee12101171a9c881`.
4. `docs/CT0_REPRODUCTION_GATE.md`, which records the successful Windows reproduction gate.

If this document conflicts with CT0 or the accepted addendum, CT0 and the addendum prevail. Any actuarial change requires a new reviewed specification version before code is changed.

## 2. Product and repository boundary

The products remain separate:

- The existing Cat XOL Pricing Learning Lab remains in `C:\Aasif\Learning projects\cat-xol-pricing-lab` and is not modified by CT1.
- The extracted copy under `C:\Aasif\Cat XOL\cat-xol-pricing-source\cat-xol-pricing-lab` is audit/reference material only.
- All new Cat Treaty Learning Lab work occurs in `C:\Aasif\Cat XOL\cat-treaty-learning-lab`.

Separate products may share validated actuarial foundations, but they must retain different routes, introductions, navigation, scenarios, learning objectives, outputs and acceptance tests.

The treaty project must not depend at runtime on either user-specific absolute Windows path. CT1 establishes a versioned adapter contract around the validated engine. It does not silently fork or rewrite the existing formulas.

## 3. CT1 purpose

CT1 creates a stable compatibility and extension seam around the proven Cat XOL engine before Ultimate Net Loss stages, inuring, programme towers, hours clauses or capital modelling are introduced.

CT1 must:

- preserve existing numerical behavior under default compatibility settings;
- translate existing objects into canonical CT0 names without numerical transformation;
- introduce separate functional `ceded_share` and `placement_share` fields;
- expose settlement as three separate values;
- declare capacity on the `payable_placed_share` basis;
- add reproducibility and product-identity metadata; and
- provide regression evidence for all of the above.

## 4. Scope

### 4.1 Deliverables

| ID | Deliverable | Required evidence |
|---|---|---|
| CT1.1 | Baseline snapshot | Commit, specifications, manifests and reproduction results recorded |
| CT1.2 | Canonical adapter | Existing catalogue, annual-trial, event, recovery and pricing values mapped without numerical change |
| CT1.3 | Functional shares | Separate fixed annual-trial shares applied under F02 |
| CT1.4 | Settlement fields | Gross recovery, reinstatement premium and net cash settlement returned separately |
| CT1.5 | Version metadata | Catalogue, engine and schema versions plus normalized input hash |
| CT1.6 | Product boundary | Distinct product identifier and reserved route; no combined frontend |
| CT1.7 | Regression suite | Compatibility, shares, capacity, settlement and metadata gates pass |
| CT1.8 | Compatibility freeze | Request, response, migration and deprecation rules documented before CT2 |

### 4.2 Files

| File | Responsibility |
|---|---|
| `cat_treaty/models.py` | Immutable canonical CT0 records, enums and validation |
| `cat_treaty/adapter.py` | Numerical-identity mapping from validated engine outputs |
| `cat_treaty/shares.py` | Functional share application and payable-capacity scaling |
| `cat_treaty/settlement.py` | Settlement presentation only |
| `cat_treaty/metadata.py` | Version fields and deterministic normalized input hash |
| `tests/test_ct1_compatibility.py` | Existing-behavior identity checks |
| `tests/test_ct1_shares.py` | Share, capacity and zero-capacity checks |
| `tests/test_ct1_settlement.py` | Settlement invariants |
| `tests/test_ct1_metadata.py` | Version and hash checks |
| `tests/test_ct1_golden_cases.py` | G01–G15 traceability |

## 5. Explicit exclusions

CT1 does not implement:

- Ultimate Net Loss stages or inuring reinsurance;
- multi-layer programmes, continuous or ventilated towers;
- hours-clause regrouping or occurrence elections;
- aggregate XL;
- capital or solvency analytics;
- new Monte Carlo tail modelling;
- a FastAPI application or finished React interface;
- per-event or mid-year share changes; or
- changes to the existing Cat XOL Pricing Simulator.

These exclusions prevent later treaty features from being introduced before the compatibility boundary is proven.

## 6. Existing behavior frozen by CT1

The following remain authoritative:

1. A fixed configuration and seed generate identical catalogue values.
2. Events are processed in event-time and event-ID order.
3. For the existing 100% layer, occurrence recovery is:

   `covered_loss = min(max(subject_loss - attachment, 0), occurrence_limit)`

4. Reinstated capacity becomes available only to later events.
5. Layer AAL is the mean annual recovery including zero-loss years.
6. OEP uses the largest applicable occurrence in each annual trial.
7. AEP uses annual aggregate loss.
8. Reinstatement pricing does not change contractual recovery or Layer AAL.
9. Technical pricing, ROL, payback and expected reinstatement premium remain unchanged under compatibility defaults.
10. The frontend remains a consumer of backend results.

## 7. Canonical compatibility mappings

| Existing value | Canonical CT0 value | Rule |
|---|---|---|
| `CatalogueConfig.random_seed` | simulation seed | Preserve exactly and disclose in metadata |
| `EventRecord.year` | `annual_trial_id` | Alias only; it is not a calendar treaty year |
| `EventRecord.event_id` | `event_id` | Preserve stable identifier |
| `EventRecord.event_time` | `event_time` | Preserve elapsed-day meaning |
| `EventRecord.event_sequence` | `event_sequence` | Preserve chronological order |
| `gross_event_loss` | initial Cat subject loss | Do not describe as post-inuring Ultimate Net Loss |
| `actual_treaty_recovery` | gross recovery for the existing 100% layer | Identity mapping only at 100% ceded and placement shares with no inuring |
| `reinstatement_premium` | `reinstatement_premium_payable` | Preserve pricing value; settlement treatment is separate |
| `net_event_loss` | legacy loss after current layer recovery | Preserve for compatibility; do not overload for future loss stages |

The adapter must not round, rescale, reinterpret or recalculate an existing value merely to rename it.

## 8. Functional share contract

### 8.1 Stored inputs

`ceded_share` and `placement_share` are separate values in the domain model and future API schema.

- Each is finite and lies in the closed interval `[0, 1]`.
- Each defaults to `1.0`.
- They are fixed for the entire annual trial.
- Every event and reinstatement in that trial uses the same values.
- Their product may be used during calculation but must not replace either stored input.

### 8.2 Formula F02

For each occurrence:

`gross_contractual_recovery = covered_loss × ceded_share × placement_share`

where `covered_loss` is the existing authoritative occurrence-layer result before shares.

Expected proportional cases:

| Ceded | Placement | Payable proportion of covered loss |
|---:|---:|---:|
| 100% | 100% | 100% |
| 90% | 100% | 90% |
| 100% | 75% | 75% |
| 90% | 75% | 67.5% |
| 0% | 100% | 0% |
| 100% | 0% | 0% |

## 9. Capacity contract

The CT1 capacity basis is the literal value:

`payable_placed_share`

The future response schema must disclose that basis.

- Initial payable capacity = `occurrence_limit × ceded_share × placement_share`.
- Capacity consumed = `gross_contractual_recovery`.
- Reinstated payable capacity uses the same fixed share factor.
- Remaining payable capacity may never be negative.
- Recovery may never exceed payable contractual entitlement or available capacity.

For constant annual-trial shares, recovery, capacity consumed, capacity reinstated and capacity remaining must equal the corresponding 100%-basis values multiplied by `ceded_share × placement_share`. The nonzero capacity-utilization fraction must therefore be identical on both bases.

## 10. Zero payable capacity

If either share is zero:

- initial payable capacity is zero;
- gross contractual recovery is zero;
- capacity consumed is zero;
- capacity reinstated is zero;
- remaining payable capacity is zero;
- `capacity_utilization` is `null`; and
- `capacity_utilization_status` is `not_applicable_zero_capacity`.

A future interface must display `N/A – no payable capacity`. It must never substitute `0%`, `NaN`, infinity or an error.

For positive capacity, `capacity_utilization_status` is `applicable` and utilization must be finite and bounded by the definition inherited from the validated capacity engine.

## 11. Settlement contract

Every applicable result exposes three separate fields:

1. `gross_contractual_recovery`
2. `reinstatement_premium_payable`
3. `net_cash_settlement`

The presentation mode is explicit:

- `paid_separately` is the default:  
  `net_cash_settlement = gross_contractual_recovery`
- `deducted_from_settlement` is advanced:  
  `net_cash_settlement = gross_contractual_recovery - reinstatement_premium_payable`

Changing presentation mode must not alter covered loss, gross contractual recovery, capacity consumed, capacity reinstated, capacity remaining, Layer AAL or any pricing calculation. No hidden offsetting or clamping rule may be introduced in CT1.

## 12. Metadata and reproducibility

Every canonical run result must carry:

- `product_id = "cat_treaty_learning_lab"`
- reserved product route `/cat-treaty`
- `catalogue_version`
- `engine_version`
- `schema_version`
- simulation seed where applicable
- `input_hash`
- `capacity_basis = "payable_placed_share"`

The input hash must:

1. include all actuarially relevant normalized inputs and version metadata;
2. use stable key ordering and an explicitly defined serialization;
3. exclude display formatting and non-actuarial UI state;
4. use SHA-256; and
5. reproduce exactly for equivalent normalized inputs.

## 13. Compatibility and migration rules

- Existing requests with no share fields behave as `ceded_share = 1.0` and `placement_share = 1.0`.
- Existing field meanings are not silently changed.
- Canonical aliases may be added while legacy fields remain available during a documented migration period.
- A field may be removed or reinterpreted only through a later versioned specification and schema change.
- Unknown settlement modes, capacity bases or incompatible schema versions must fail explicitly.
- The adapter must not depend on a local absolute path to the pricing repository.

## 14. Golden-case register

### 14.1 Existing cases

G01–G12 remain authoritative exactly as defined in the CT0 Frozen Specification. CT1 tests must reference those IDs and must not redefine or renumber them.

### 14.2 CT1 traceability additions

**G13 — Two-event proportional equivalence**

- One annual trial contains two chronologically ordered events.
- Both events use one fixed non-default `ceded_share` and `placement_share`.
- The test first obtains the authoritative 100%-basis event and capacity ledger.
- The payable-basis recovery, consumption, reinstatement and remaining capacity must equal each corresponding 100%-basis value multiplied by the constant share product.
- The defined nonzero utilization fraction must be identical on both bases.

**G14 — Zero ceded share**

- `ceded_share = 0`, `placement_share = 1`.
- All payable recovery and capacity values are zero.
- Utilization is `null` with status `not_applicable_zero_capacity`.

**G15 — Zero placement share**

- `ceded_share = 1`, `placement_share = 0`.
- All payable recovery and capacity values are zero.
- Utilization is `null` with status `not_applicable_zero_capacity`.

## 15. Regression gates

| Gate | Pass condition |
|---|---|
| Baseline | The reproduced pricing baseline remains 154 passing backend tests and 8 passing frontend tests |
| Catalogue identity | Fixed configurations and seeds preserve existing values |
| Recovery identity | Default shares reproduce existing `actual_treaty_recovery` exactly |
| Share calculations | All six F02 combinations reconcile independently |
| Capacity basis | Capacity ledger reconciles on `payable_placed_share` |
| G13 | Two-event proportional equivalence passes |
| G14–G15 | Zero-capacity convention passes without NaN, infinity, error or false 0% |
| Pricing identity | Layer AAL, technical premium, ROL, payback and expected reinstatement premium remain unchanged under defaults |
| Settlement invariant | Presentation mode changes only `net_cash_settlement` |
| Metadata | Versions and normalized input hashes are stable and disclosed |
| Product separation | Product ID and route differ from the pricing product |
| Repository | Tests pass and the working tree is clean after the CT1 commit |

## 16. Required invariants

For every valid CT1 result:

- all input shares are finite and within `[0, 1]`;
- monetary values are finite;
- covered loss and gross contractual recovery are non-negative;
- recovery does not exceed contractual entitlement or available capacity;
- remaining capacity is non-negative;
- event ordering is deterministic;
- default compatibility results equal the validated source results;
- gross contractual recovery is independent of settlement presentation;
- zero capacity produces explicit not-applicable utilization; and
- no frontend or adapter performs actuarial calculations independently.

## 17. Implementation order

1. Freeze and commit this specification.
2. Define immutable canonical models and validation tests.
3. Implement deterministic version metadata and normalized input hashing.
4. Implement the numerical-identity compatibility adapter.
5. Implement functional shares and payable capacity scaling.
6. Implement settlement presentation.
7. Add G01–G15 traceability and regression tests.
8. Run the new treaty suite and the reproduced pricing regression suite.
9. Record results and commit CT1.

No CT2 work begins until every CT1 regression gate passes and the repository is clean.

## 18. Freeze decision

Once committed, this document is the coding authority for CT1. Implementation may clarify names or types, but it may not change formulas, boundaries, defaults, invariants or exclusions without review and a new specification version.
