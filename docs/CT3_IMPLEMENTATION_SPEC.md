# Catastrophe Treaty Learning Lab — CT3 Implementation Specification

**Milestone:** CT3 — Multi-Layer Cat XL Program and Geometry Controls
**Version:** 1.1
**Status:** Frozen following independent validation
**Date:** 15 September 2026
**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority and dependency

This specification implements the revised CT3 scope under:

1. *Catastrophe Treaty Learning Lab Master Architecture — CT0 Frozen
   Specification v1.0*;
2. *CT0 Implementation Integration Addendum v1.3*;
3. `docs/CT1_IMPLEMENTATION_SPEC.md` v1.1;
4. `docs/CT2_IMPLEMENTATION_SPEC.md` v1.1; and
5. `docs/CT2_ACCEPTANCE_REPORT.md`.

The integration addendum governs milestone order. CT3 covers the one-occurrence
multi-layer Cat XL program engine, continuous and ventilated towers, overlap
coordination and geometry controls. Treaty-year capacity and reinstatement
across a tower remain CT5 work.

## 2. Purpose

CT3 answers four questions transparently:

1. Is the proposed Cat XL program geometrically continuous, ventilated,
   overlapping or mixed?
2. Which loss band is allocated to each layer under the disclosed contract
   structure?
3. What does each layer recover after separate ceded and placement shares?
4. How does the complete program reconcile to the CT2 Cat XL subject loss?

The engine is a learning and experimentation component, not merely a recovery
calculator. Every gap, overlap, retained participation and loss above the tower
must remain visible.

## 3. Included scope

- exactly one completed CT2 occurrence waterfall per calculation;
- one to four occurrence Cat XL layers;
- layer attachment, occurrence limit, ceded share and placement share;
- layer exhaustion and deterministic geometric ordering;
- continuous, ventilated, overlapping and mixed geometry classification;
- explicit internal gap segments and affected loss;
- ambiguous-overlap rejection;
- priority-based overlap coordination when expressly selected;
- per-layer pre-coordination coverage, allocated coverage, recovery and
  retained participation;
- program recovery, retained loss and full loss-band reconciliation;
- deterministic explanations, warnings, trace references and metadata;
- single-layer backward-compatibility gates; and
- CT1 and CT2 regression preservation.

## 4. Explicit exclusions

CT3 does not implement:

- hours-clause occurrence construction or election;
- annual aggregate limits, reinstatements or chronological capacity carryover;
- cascading, drop-down, franchise or aggregate XL layers;
- pro-rata or custom overlap-sharing mathematics;
- policy-level loss generation or inuring calculations;
- OEP/AEP simulation, technical pricing or capital analytics;
- API endpoints, frontend screens or deployment; or
- inferred legal interpretation of a gap or overlap.

## 5. CT2 entry gate

The program engine accepts a `CT3ProgramInput` containing both:

- an `InuringWaterfallResult` accepted by
  `require_ct3_eligible_waterfall()`; and
- its immutable `CT2RunMetadata`.

The entry gate reads:

- occurrence identity;
- reporting currency;
- `cat_xl_subject_loss`;
- CT2 completion status; and
- CT2 trace and metadata references.

A raw scalar, pricing-lab `gross_event_loss`, unreconciled loss basis or partial
inuring result is invalid. CT3 never recalculates Ultimate Net Loss or inuring
recoveries.

The occurrence ID and reporting currency in the CT2 metadata must match the
completed waterfall. CT3 reconstructs the retained `InuringWaterfallInput`
from the completed loss basis and ordered cover inputs, recalculates the CT2
hash using the disclosed CT2 source/engine/schema versions, and requires an
exact match to `CT2RunMetadata.input_hash`. A completed waterfall and metadata
from different runs cannot be paired.

The remaining `CT3ProgramInput` fields are:

- unique nonblank `program_id`;
- one to four immutable layer inputs;
- `intentional_gap_acknowledged`;
- `overlap_coordination`;
- optional `priority_order`;
- description, source and rule references; and
- no user-supplied Cat XL subject-loss scalar.

## 6. Layer contract

Every `CatLayerInput` contains:

- `layer_id` — unique nonblank identifier;
- `attachment` — non-negative finite amount;
- `occurrence_limit` — strictly positive finite amount;
- `ceded_share` — finite fraction in `[0, 1]`;
- `placement_share` — finite fraction in `[0, 1]`;
- `currency` — equal to the CT2 reporting currency;
- `description`, `source_reference` and `rule_reference`; and
- no annual-capacity or reinstatement fields in CT3.

Layer terms remain separate. Ceded share must not be collapsed into placement
share, and neither is inferred from the other.

### F10 — Layer exhaustion

\[
E_i = A_i + M_i
\]

where \(A_i\) is attachment and \(M_i\) is occurrence limit. Derived
exhaustion must be finite and strictly greater than attachment.

### F11 — Covered loss before overlap coordination

\[
C_i = \min(\max(S-A_i,0),M_i)
\]

where \(S\) is the completed CT2 Cat XL subject loss. F11 is the CT3 naming of
the frozen single-layer covered-loss formula. It is calculated independently
for every layer before overlap coordination.

## 7. Geometry model

Layers are placed in deterministic geometry order by:

1. ascending attachment;
2. ascending exhaustion; and
3. ascending `layer_id` as the stable tie-breaker.

User input order is not a hidden priority rule and cannot alter a non-overlap
result.

The geometry engine constructs finite internal segments from every attachment
and exhaustion boundary. A segment between the lowest attachment and highest
exhaustion is classified as:

- `covered` when exactly one layer spans it;
- `gap` when no layer spans it; or
- `overlap` when two or more layers span it.

The loss below the lowest attachment is `base_retention`, not a gap. Loss above
the highest exhaustion is `above_tower_loss`, not a gap. Geometry is classified
from contract terms even if the current occurrence does not reach a segment.

### 7.1 Program geometry classification

| Classification | Required condition |
|---|---|
| `single_layer` | Exactly one valid layer |
| `continuous` | Multiple layers, no internal gaps and no overlaps |
| `ventilated` | One or more internal gaps and no overlaps |
| `overlapping` | One or more overlaps and no gaps |
| `mixed` | At least one gap and at least one overlap |

The response separately carries `has_gaps` and `has_overlaps`; classification
must not hide either condition. Classification describes topology only and is
always populated after the layer terms pass validation. It does not assert that
the program is eligible for recovery.

### 7.2 Program eligibility

The geometry response separately carries `program_eligibility_status` as
`eligible` or `blocked` and a deterministic collection of structured
`blocking_issues`. A blocking issue includes a stable code, affected segment,
affected layer IDs, message and rule reference. Frozen CT3 codes include:

- `unacknowledged_gap`;
- `uncoordinated_overlap`;
- `invalid_priority_order`; and
- `unnecessary_priority_coordination`.

An overlapping or mixed topology under `overlap_coordination = none` is
therefore classified normally but is `blocked` by
`uncoordinated_overlap`. Topology and contractual eligibility must never be
collapsed into one field.

## 8. Gap control

A gap is permissible only when `intentional_gap_acknowledged = true` on the
program request. An acknowledged gap:

- is not described as a drafting error;
- returns its lower and upper boundaries;
- reports the amount of current subject loss falling inside it;
- is included in insurer retained loss; and
- produces a deterministic ventilation warning and learning explanation.

If any internal gap exists and acknowledgement is false, eligibility is
`blocked` and no recovery is emitted. The diagnostic geometry response remains
available. Acknowledgement does not endorse the commercial suitability of the
gap.

Supplying `intentional_gap_acknowledged = true` when no gap exists is permitted
but returns a notice that the acknowledgement was not required. It has no
effect on recovery.

## 9. Overlap control

`overlap_coordination` supports:

- `none` — default; every geometrical overlap blocks recovery; and
- `priority` — allocate each overlapping loss band once according to an
  explicit complete `priority_order`.

If overlap exists under `none`, eligibility is `blocked`; the geometry response
identifies every affected segment and layer ID, and no recovery is emitted. The
engine must not silently sum overlapping entitlements.

`priority_order` must contain every program layer ID exactly once. It is used
only for band allocation, never inferred from input or geometry order. Supplying
priority coordination when no overlap exists is rejected as misleading.

Pro-rata sharing and custom coordination remain deferred. A free-text
coordination description is audit metadata and cannot substitute for a frozen
calculation rule.

### F12 — Priority-coordinated covered loss

For priority position \(i\), define the independently covered interval reached
by the occurrence as:

\[
I_i = [A_i,\ \min(E_i,S))
\]

Then:

\[
C_i^* = \operatorname{measure}\left(
I_i \setminus \bigcup_{j<i} I_j
\right)
\]

If \(S\leq A_i\), \(I_i\) is the empty interval and both covered-loss
measures are zero.

For a program without overlap, \(C_i^*=C_i\). Under priority coordination, a
dollar of the overlapping band is allocated only to the first-priority layer
that spans it. If that layer is less than fully ceded or placed, its unpaid
share remains with the insurer; a lower-priority layer does not silently fill
that share.

Every layer response carries both `covered_loss_before_coordination` and
`allocated_covered_loss`. The difference is
`covered_loss_removed_by_coordination`.

## 10. Layer and program recovery

### F13 — Layer gross contractual recovery

\[
U_i = C_i \times c_i \times p_i
\]

\[
R_i = C_i^* \times c_i \times p_i
\]

where \(c_i\) is ceded share and \(p_i\) is placement share. Both shares are
displayed and hashed separately. \(U_i\) is
`recovery_before_coordination`; \(R_i\) is
`gross_contractual_recovery` after the selected geometry rule. No annual
capacity or settlement deduction exists in CT3.

### F14 — Layer retained participation

\[
Q_i = C_i^* - R_i
\]

### F15 — Total gross contractual recovery and insurer net

\[
R = \sum_i R_i
\]

\[
N = S - R
\]

Gross contractual recovery may not be negative or exceed Cat XL subject loss.
CT3 applies no annual-capacity, reinstatement-premium or cash-settlement
adjustment.

### F16 — Loss-band reconciliation

\[
S = B + G + \sum_i C_i^* + T
\]

\[
N = B + G + \sum_i Q_i + T
\]

where:

- \(B\) is subject loss below the lowest attachment;
- \(G\) is subject loss in acknowledged internal gaps;
- \(T\) is subject loss above the highest exhaustion; and
- coordinated allocated intervals are disjoint.

For the program attachment and exhaustion extremes
\(A_{\min}=\min_i A_i\) and \(E_{\max}=\max_i E_i\), and for each internal gap
\(g=[g_l,g_u)\), the retained-band definitions are:

\[
B=\min(S,A_{\min})
\]

\[
G=\sum_{g\in\text{gaps}}\max(\min(S,g_u)-g_l,0)
\]

\[
T=\max(S-E_{\max},0)
\]

Both F15 and F16 must pass. The result exposes all four retained-loss drivers:
base retention, gap loss, in-layer retained participation and above-tower loss.

## 11. Immutable response contract

### 11.1 Geometry response

- deterministic sorted layer IDs;
- attachment and exhaustion boundaries;
- topology-only geometry classification;
- `has_gaps` and `has_overlaps`;
- every finite geometry segment with start, end, classification and layer IDs;
- program eligibility status and structured blocking issues;
- gap acknowledgement status;
- overlap coordination mode and priority order; and
- validation notices, warnings and trace references.

### 11.2 Layer response

- complete immutable layer input;
- geometry position and priority position when applicable;
- covered loss before coordination;
- allocated covered loss;
- covered loss removed by coordination;
- ceded share and placement share;
- recovery before coordination;
- gross contractual recovery after coordination;
- retained participation inside the allocated band;
- attachment/exhaustion indicators; and
- formula and explanation trace references.

### 11.3 Program response

- complete eligible CT2 input identity;
- verified CT2 metadata and input hash;
- Cat XL subject loss;
- geometry and layer results;
- total gross contractual recovery and insurer net loss;
- base-retention, gap, in-layer-retention and above-tower buckets;
- passed F15/F16 reconciliation checks;
- deterministic explanations, warnings and assumptions; and
- CT3 schema, engine and normalized-input hash metadata.

After valid layer terms are received, a blocked program still returns the
complete diagnostic geometry response. Its program recovery result is null and
it emits no layer or program recovery amounts. Invalid layer terms fail before
geometry construction. No blocked or invalid geometry returns a valid program
recovery result.

## 12. Numerical and validation rules

- booleans are not numeric inputs;
- all amounts and shares are finite;
- attachments are non-negative;
- occurrence limits are strictly positive;
- shares lie in the closed interval `[0, 1]`;
- layer IDs are unique and nonblank;
- one to four layers are required;
- currencies match the completed CT2 result;
- attachment plus limit must remain finite;
- geometry segments have strictly increasing finite boundaries;
- a gap requires explicit acknowledgement;
- an overlap requires the frozen priority rule and complete priority order;
- duplicate, missing or unknown priority IDs fail;
- all recoveries and retained-loss buckets are non-negative;
- program recovery cannot exceed subject loss;
- F11–F16 use `math.fsum` and the project tolerance of relative `1e-12` and
  absolute USD `1e-6` for reconciliation only; and
- tolerances never turn an invalid negative input into a valid one.

## 13. Deterministic metadata

Frozen defaults:

- `CT3_ENGINE_VERSION = "ct3.0.0"`;
- `CT3_SCHEMA_VERSION = "ct3.0"`;
- existing treaty `PRODUCT_ID` and `PRODUCT_ROUTE`; and
- the CT2 input hash and CT3 program input hash are both disclosed.

The CT3 normalized-input hash includes:

- eligible CT2 result identity and CT2 input hash;
- Cat XL subject loss;
- every actuarially relevant layer term;
- intentional-gap acknowledgement;
- overlap coordination mode and priority order; and
- CT3 engine/schema versions.

It excludes descriptions, display labels, formatting, explanation text and UI
state. Layer request order is canonicalized because it is not contractual;
explicit `priority_order` is preserved because it is contractual.

## 14. Golden cases

Existing G01–G25 retain their frozen meanings and IDs.

| ID | Scenario | Expected CT3 check |
|---|---|---|
| G01 | Loss below attachment | Zero program recovery |
| G02 | Loss exactly at attachment | Zero recovery under excess-of-loss convention |
| G03 | Partial layer loss with 90% share | Recovery equals 90% of covered loss |
| G04 | Loss exactly at exhaustion | Full payable occurrence limit |
| G05 | Loss above tower | Excess remains in above-tower insurer loss |
| G10 | Ventilated program | Gap loss remains with insurer and is separately visible |
| G26 | Continuous USD 45m example | USD 20m xs 10m plus USD 30m xs 30m recovers USD 35m; insurer retains USD 10m |
| G27 | Intentional ventilation | Acknowledged USD 30m–50m gap is classified and reconciled |
| G28 | Unacknowledged gap | Ventilated or mixed topology remains visible; status is blocked with `unacknowledged_gap`, and no recovery is emitted |
| G29 | Ambiguous overlap | Overlapping or mixed topology remains visible; coordination `none` produces `uncoordinated_overlap` with segment and layer reasons and no recovery |
| G30 | Priority overlap | Overlapping band is allocated once to the first-priority layer and both pre/post coordination amounts are shown |
| G31 | Different layer shares | Each layer separately applies ceded share × placement share |
| G32 | Request-order permutation | Non-overlap geometry, recovery, serialization and hash remain identical |
| G33 | Zero subject loss | Every layer recovery and retained bucket is zero while contract geometry remains visible |
| G34 | CT2 entry gate | Raw scalar and pricing gross loss cannot enter the CT3 program engine |

## 15. Acceptance gates

| Gate | Pass condition |
|---|---|
| CT1/CT2 regression | All 485 existing tests remain passing |
| CT2 entry | Only a completed CT2 waterfall result is accepted |
| Single-layer identity | G01–G05 match frozen occurrence results at equivalent terms |
| Geometry | Segment boundaries, topology classification and layer membership recompute independently of eligibility |
| Continuous tower | Adjacent boundaries produce no gap or overlap |
| Ventilated tower | Every gap and current gap loss are visible and acknowledged |
| Ambiguous overlap | Topology is returned and recovery is blocked with structured reasons |
| Priority overlap | Each reached band is allocated once in explicit priority order |
| Shares | Ceded and placement shares remain separate and functional per layer |
| Program reconciliation | F15 and F16 pass independently |
| Numerical safety | Boundary, zero, very large and non-finite cases behave explicitly |
| Metadata | Equivalent canonical inputs hash identically; contractual changes alter hash |
| Source boundary | CT3 domain modules do not import pricing, API or frontend engines |
| Golden cases | G01–G05, G10 and G26–G34 pass with trace IDs |
| Repository | Full suite passes and working tree is clean after CT3 commit |

## 16. Planned implementation units

| Unit | Responsibility |
|---|---|
| `cat_treaty/ct3_models.py` | Immutable layer, program, geometry and result contracts |
| `cat_treaty/geometry.py` | Sort layers and construct/classify finite geometry segments |
| `cat_treaty/program.py` | F11–F16 priority allocation and program recovery |
| `cat_treaty/ct3_metadata.py` | CT3 canonical serialization, versions and hashes |
| `tests/test_ct3_models.py` | Field, collection and immutability validation |
| `tests/test_ct3_geometry.py` | Continuous, gap, overlap, mixed and deterministic geometry |
| `tests/test_ct3_program.py` | Recovery, shares, priority allocation and reconciliation |
| `tests/test_ct3_metadata.py` | Canonical serialization and hashing |
| `tests/test_ct3_golden_cases.py` | G01–G05, G10 and G26–G34 |
| `tests/test_ct3_boundaries.py` | CT2 gate, import and product boundaries |

All actuarial calculations remain in pure Python backend modules. Future API
and frontend layers may only serialize or display authoritative CT3 results.

## 17. Implementation order

1. Independently validate and freeze this specification.
2. Add immutable CT3 models and validation tests.
3. Implement deterministic geometry analysis and controls.
4. Implement F11–F16 recovery and priority coordination.
5. Add CT3 metadata, hashing and explanation facts.
6. Add golden-case and boundary acceptance tests.
7. Run the complete CT1–CT3 regression and source-boundary audit.
8. Record acceptance, commit and package the final CT3 archive.

No CT4 hours-clause work begins until every CT3 gate passes.

## 18. Independent-validation questions

The reviewer should answer explicitly:

1. Is defining internal gaps only between the lowest attachment and highest
   exhaustion correct, with base retention and above-tower loss separate?
2. Is blocking all uncoordinated overlap the safest default?
3. Under priority coordination, is allocating the overlapping band once and
   applying the winning layer's shares afterward contractually cautious?
4. Should a complete priority order include all layers, rather than only
   overlapping layers, to keep execution deterministic?
5. Is rejecting unnecessary priority coordination on a non-overlap program
   preferable to silently ignoring it?
6. Are one to four layers appropriate for version one?
7. Is annual capacity/reinstatement correctly excluded until CT5?
8. Do F15/F16 expose enough retained-loss drivers for the learning lab?

Approval freezes F10–F16, geometry classifications, overlap behavior,
golden-case IDs G26–G34 and CT3 milestone boundaries. Any actuarial change
requires a versioned review before coding.
