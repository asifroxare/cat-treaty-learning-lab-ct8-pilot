# Catastrophe Treaty Learning Lab — CT2 Implementation Specification

**Milestone:** CT2 — Ultimate Net Loss and Ordered Inuring  
**Version:** 1.1
**Status:** Frozen following independent validation
**Date:** 14 September 2026  
**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority and dependency

This specification implements the revised CT2 scope under:

1. *Catastrophe Treaty Learning Lab Master Architecture — CT0 Frozen
   Specification v1.0*;
2. *CT0 Implementation Integration Addendum v1.3*;
3. `docs/CT1_IMPLEMENTATION_SPEC.md` v1.1;
4. `docs/CT1_ACCEPTANCE_REPORT.md`; and
5. `docs/CT2_SOURCE_REUSE_AUDIT.md`.

The integration addendum's revised roadmap governs milestone boundaries. CT2
therefore covers named Ultimate Net Loss stages and explicitly ordered inuring
reinsurance. Multi-layer towers belong to CT3.

## 2. Purpose

CT2 answers two questions transparently:

1. What contract-defined loss exists before other reinsurance?
2. What loss reaches the Cat XL program after each configured inuring cover?

Every movement must reconcile. The engine must never overwrite a generic
`loss` variable or silently treat pricing-lab `gross_event_loss` as post-inuring
Ultimate Net Loss.

## 3. Included scope

- one catalogue-defined occurrence at a time;
- named loss-basis stages from initial insured loss to Ultimate Net Loss;
- explicit inclusion/exclusion controls for LAE and other adjustments;
- ordered inuring cover application;
- calculated proportional recovery where the required aggregate subject basis
  is explicitly supplied;
- supplied recovery mode for covers whose own exposure-level calculation is
  outside CT2;
- scope, occurrence-limit and remaining-aggregate constraints;
- double-counting and incomplete-stage controls;
- immutable waterfall, explanation facts, warnings and trace references;
- deterministic serialization and CT2 metadata; and
- CT1 regression preservation.

## 4. Explicit exclusions

CT2 does not implement:

- Cat XL attachment, layer recovery, tower geometry, gaps or overlaps;
- hours-clause occurrence construction or election;
- policy-level surplus-share, facultative or per-risk XL calculations;
- reinstatement calculations or annual treaty processing;
- OEP/AEP simulation, technical pricing or capital analytics;
- API endpoints, frontend screens or deployment; or
- contract/legal interpretation inferred from cover labels.

## 5. Canonical loss stages

The result must expose these distinct fields:

1. `initial_insured_loss` — the occurrence loss received from a declared
   source after any upstream policy terms represented by that source;
2. `ultimate_net_loss_before_inuring` — the contract-defined result of the
   selected UNL adjustments;
3. `loss_after_inuring_cover` — one value after every ordered cover;
4. `cat_xl_subject_loss` — the final completed post-inuring loss passed to CT3.

`ground_up_loss` may be carried as optional provenance, but the engine must not
derive insured loss from it without policy terms. `cat_xl_subject_loss` must not
exist as a valid output when the configured waterfall is incomplete.

## 6. Ultimate Net Loss contract

All monetary input components are non-negative finite amounts. Direction is
represented by the field, not by a signed number.

### F03 — Ultimate Net Loss before inuring

\[
\mathrm{UNL} = I + L + C - S - U - O - E
\]

where:

- \(I\) = `initial_insured_loss`;
- \(L\) = included loss-adjustment expense;
- \(C\) = other included contract costs;
- \(S\) = salvage credit;
- \(U\) = subrogation credit;
- \(O\) = other non-inuring recoveries/credits; and
- \(E\) = contract exclusions.

The formula is contract configuration, not a universal definition. Each
component carries `included`, `label`, `amount`, `source_reference` and
`rule_reference`. Excluded components remain visible with zero applied effect.

If deductions exceed the sum of the insured loss and included additions, the
request fails explicitly. The engine must not silently floor a negative result
to zero.

### F04 — Loss-basis reconciliation

\[
I + \text{included additions}
= \mathrm{UNL} + \text{applied deductions}
\]

## 7. Inuring cover contract

### 7.1 Required cover fields

Every configured cover contains:

- `cover_id` — unique immutable identifier;
- `cover_type` — `quota_share`, `surplus_share`, `facultative`,
  `per_risk_xl` or `other`;
- `order` — unique contiguous positive integer beginning at 1;
- `valuation_mode` — `calculated_proportional` or `supplied_recovery`;
- `scope_fraction` — portion of incoming loss within the declared cover scope;
- `cession_rate` — required only for calculated proportional mode;
- optional `occurrence_limit`;
- optional `aggregate_remaining_before`;
- `supplied_recovery` — required only for supplied recovery mode;
- `recovery_source_id` — required and unique for supplied recovery mode;
- `currency`; and
- description/source/rule references.

All covers in one waterfall use the same reporting currency. Currency
conversion remains outside CT2 and must occur before the request.

CT2 treats `aggregate_remaining_before` as a state snapshot supplied for this
occurrence; it does not persist or infer aggregate state across occurrences.
When that field is present, the cover row returns
`aggregate_remaining_after = aggregate_remaining_before - payable_recovery`.
When it is omitted, both aggregate fields are `null` and the aggregate
constraint is unbounded. CT3/CT5 owns chronological carryover of this returned
state into later occurrences.

### 7.2 Permitted valuation modes

`calculated_proportional` is permitted only where the contract owner declares
that an aggregate percentage may validly apply to the scoped incoming loss.
It is the normal CT2 teaching mode for quota share. It must not be presented as
a policy-level surplus, facultative or per-risk XL calculation.

`supplied_recovery` accepts a recovery calculated by an authoritative upstream
cover engine or supplied scenario. CT2 validates and applies it but does not
reconstruct missing policy/risk detail.

### F05 — Cover subject loss

\[
S_k = L_{k-1} \times q_k
\]

where \(L_{k-1}\) is incoming loss and \(q_k\) is `scope_fraction` in
\([0,1]\).

### F06 — Recovery before limits

For calculated proportional mode:

\[
B_k = S_k \times c_k
\]

For supplied recovery mode:

\[
B_k = \text{supplied recovery}_k
\]

Supplied recovery must not exceed \(S_k\). CT2 never increases a supplied
recovery to a formula-derived amount.

### F07 — Payable inuring recovery

\[
R_k = \min(B_k,\ O_k,\ A_k,\ L_{k-1})
\]

where omitted occurrence or aggregate limits \(O_k\) and \(A_k\) are treated
as unbounded for that constraint. The response separately shows every binding
constraint.

### F08 — Sequential outgoing loss

\[
L_k = L_{k-1} - R_k
\]

The next cover consumes only \(L_k\). Covers are never applied independently
to the original UNL unless a later reviewed coordination specification says so.

### F09 — Inuring reconciliation

For each cover and for the complete waterfall:

\[
L_{k-1} = R_k + L_k
\]

\[
\mathrm{UNL} = \sum_k R_k + \mathrm{Cat\ XL\ subject\ loss}
\]

## 8. Order, scope and double-counting controls

- cover order must be explicit, unique and gap-free;
- the engine does not select or optimize order;
- changing order creates a different disclosed scenario and may change results;
- a `cover_id` cannot occur twice;
- a supplied `recovery_source_id` cannot occur twice;
- every recovery is capped by the current incoming loss and declared scope;
- the result records `incoming_loss`, `cover_subject_loss`,
  `recovery_before_limits`, `payable_recovery`, `outgoing_loss`, limits and
  binding constraints for each row;
- no hidden recovery may be deducted outside a named row; and
- incomplete, ambiguous or invalid covers block completion rather than being
  silently skipped.

These controls prevent mechanical double deduction. They do not assert that
the selected legal inuring order is correct; that remains an explicit contract
assumption disclosed to the learner.

## 9. Completion gate for CT3

The waterfall returns one of:

- `complete` — every configured cover was applied and all reconciliations pass;
- `complete_no_inuring_covers` — no covers were configured and UNL passes
  unchanged; or
- failure — no valid `cat_xl_subject_loss` is emitted.

CT3 may accept only either complete status. It must reject an initial pricing
`gross_event_loss` presented directly as post-inuring loss when a configured
CT2 waterfall is required.

## 10. Immutable response model

The CT2 response contains:

- occurrence identity and source-stage declaration;
- `reporting_currency` for the occurrence and every monetary result;
- optional ground-up provenance;
- initial insured loss;
- all UNL components and applied effects;
- Ultimate Net Loss before inuring;
- ordered cover results;
- total inuring recovery;
- Cat XL subject loss;
- completion status;
- reconciliation checks;
- warnings and assumption disclosures;
- formula/rule trace references; and
- CT2 schema, engine and normalized-input hash metadata.

Every material row supports the learning contract: value, plain-language
meaning, driver fact and trace reference. Explanations are deterministic facts,
not free-form actuarial conclusions.

## 11. Validation rules

- all amounts and rates are finite real numbers; booleans are not numbers;
- monetary amounts are non-negative;
- fractions and cession rates lie in `[0, 1]`;
- IDs and references are nonblank;
- calculated mode requires a cession rate and forbids supplied recovery;
- supplied mode requires supplied recovery and unique source ID, and forbids a
  cession rate;
- supplied recovery cannot exceed declared cover subject loss;
- limits, when present, are strictly positive except aggregate remaining may be
  zero; an included or excluded component with a negative supplied amount is
  invalid because exclusion changes applied effect, not input validity;
- all currencies match the occurrence reporting currency;
- output losses and recoveries are finite and non-negative; and
- reconciliation uses the project's declared floating-point tolerance and
  never hides a material imbalance.

## 12. Golden cases

Existing G01–G16 retain their frozen meanings and IDs.

| ID | Scenario | Expected CT2 check |
|---|---|---|
| G06 | Quota share inures before Cat XL | Post-inuring subject loss uses the ordered proportional recovery; no Cat XL calculation occurs in CT2 |
| G17 | UNL additions and deductions | F03 and F04 reconcile with every applied/excluded component visible |
| G18 | No inuring covers | Cat XL subject loss equals UNL with `complete_no_inuring_covers` status |
| G19 | 40% quota share | Recovery equals scoped incoming loss × 40%; outgoing loss reconciles |
| G20 | Order sensitivity | Reversing two valid covers creates a disclosed alternative result; engine never chooses the better order |
| G21 | Binding limit | Recovery is capped and the exact occurrence or aggregate constraint is named |
| G22 | Supplied recovery | Authoritative supplied amount is preserved subject to scope/current-loss caps |
| G23 | Out-of-scope cover | Zero subject, zero recovery and unchanged outgoing loss remain visible; supplied mode with zero scope and nonzero recovery fails validation |
| G24 | Duplicate recovery source | Request fails before any completed subject loss is emitted |
| G25 | Negative UNL attempt | Excess deductions fail explicitly; result is not silently floored |

## 13. Regression and acceptance gates

| Gate | Pass condition |
|---|---|
| CT1 regression | All 338 CT1 tests remain passing |
| Source boundary | No CT2 domain module imports pricing recovery, analytics or pricing engines |
| Named stages | No intermediate amount is represented only by an overloaded `loss` field |
| UNL reconciliation | F03/F04 pass independently across boundary and mixed-component cases |
| Inuring reconciliation | Every cover row and total waterfall satisfy F09 |
| Ordering | Noncontiguous, duplicate and implicit orders fail; valid reorderings are deterministic |
| Double counting | Duplicate IDs/source IDs and recovery above current scoped loss fail |
| Valuation modes | Calculated and supplied modes enforce mutually exclusive inputs |
| Completion gate | Invalid/incomplete waterfalls never emit valid CT3 subject loss |
| Metadata | Equivalent normalized inputs produce stable hashes and disclose CT2 versions |
| Golden cases | G06 and G17–G25 pass with trace IDs |
| Repository | Full suite passes and working tree is clean after CT2 commit |

## 14. Planned implementation units

| Unit | Responsibility |
|---|---|
| `cat_treaty/loss_basis.py` | Validate and reconcile UNL components |
| `cat_treaty/inuring.py` | Apply covers sequentially and build waterfall rows |
| `cat_treaty/ct2_models.py` | Immutable CT2 enums, inputs, rows and result types |
| `cat_treaty/ct2_metadata.py` | CT2 schema/engine identity and normalized hash |
| `tests/test_ct2_loss_basis.py` | F03/F04 and validation |
| `tests/test_ct2_inuring.py` | F05–F09, ordering, limits, modes, aggregate-before/after state, and supplied-mode zero-scope rejection |
| `tests/test_ct2_golden_cases.py` | G06 and G17–G25 traceability |
| `tests/test_ct2_boundaries.py` | Import, completion and CT1 regression boundaries |

Actuarial calculations remain in pure Python backend modules. Future API and
frontend layers may only serialize or display these authoritative results.

## 15. Implementation order

1. Independently validate and freeze this specification.
2. Add immutable CT2 models and validation tests.
3. Implement UNL construction and reconciliation.
4. Implement ordered inuring and cover constraints.
5. Implement completion gate, deterministic metadata and explanations.
6. Add G06 and G17–G25 acceptance tests.
7. Run the full CT1+CT2 suite and audit import boundaries.
8. Record acceptance evidence, commit and package CT2.

No CT3 tower work begins until every CT2 gate passes.

## 16. Validation decisions requested

The independent reviewer should answer explicitly:

1. Is the F03 component treatment sufficiently contract-neutral and auditable?
2. Is calculated proportional recovery appropriately limited to a declared
   aggregate-percentage basis?
3. Is supplied recovery the correct CT2 treatment for surplus, facultative and
   per-risk XL when risk-level data are absent?
4. Do the sequential order and source-ID controls prevent mechanical double
   counting without pretending to determine legal inuring order?
5. Is rejecting, rather than flooring, deductions that exceed additions the
   safest learning-lab behavior?
6. Is the CT3 completion gate sufficiently explicit?

Approval freezes formulas F03–F09, milestone boundaries, golden-case IDs and
validation behavior. Any later actuarial change requires a versioned review.
