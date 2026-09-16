# Catastrophe Treaty Learning Lab — CT5 Implementation Specification

**Milestone:** CT5 — Annual Capacity, Reinstatements and Settlement  
**Version:** 1.0-draft  
**Status:** Independent review required; not frozen; no implementation authorized  
**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority and dependency chain

CT5 extends, and does not reinterpret:

- CT0 Frozen Specification v1.0;
- CT1 Implementation Specification and acceptance report;
- CT2 Ultimate Net Loss and inuring-reinsurance contract;
- CT3 Cat XL program geometry and occurrence recovery;
- CT4 Implementation Specification v1.1 and final acceptance report; and
- the installed CT4 identity `6b69697`, with 759 passing tests.

CT4 remains authoritative for occurrence definition, deterministic ordering,
pre-annual-capacity layer recoveries and empirical tail conventions. CT5 may
constrain those recoveries through annual capacity; it may not recreate CT2,
CT3 or CT4 occurrence logic.

This draft must be independently reviewed and revised as necessary. CT5 coding
is prohibited until the document is explicitly frozen.

## 2. Purpose

CT5 turns each completed CT4 annual trial into a stateful treaty-year ledger.
It teaches and calculates:

1. how occurrence capacity is consumed across chronologically ordered events;
2. how contractual reinstatement tranches restore capacity for later events;
3. how reinstatement premium is calculated by amount and declared time basis;
4. why gross recovery, premium payable and cash settlement are different
   quantities;
5. how capacity exhaustion reshapes OEP, AEP and insurer-net tails; and
6. how every result reconciles to the CT4 pre-capacity entitlement.

CT5 is a treaty-operation simulator, not a pricing model or claims-adjudication
system.

## 3. Scope

### 3.1 Included

- one completed CT4 catalogue or elected hours-clause result;
- one to four CT3 Cat XL layers;
- independent annual-capacity state by layer;
- zero or more ordered reinstatement tranches per layer;
- free and paid reinstatements;
- full premium and pro-rata-as-to-time premium bases;
- pro rata as to amount for every partial reinstatement;
- fixed ceded and placement shares inherited from CT3;
- payable-placed-share capacity and premium amounts;
- partial final reinstatements;
- deterministic event and layer ledgers;
- paid-separately and deducted-from-settlement presentation modes;
- post-capacity OEP/AEP, AAL, volatility, quantiles and tail means; and
- deterministic metadata, input/result hashes and explanations.

### 3.2 Excluded

- aggregate deductibles, franchise deductibles and annual aggregate XL;
- drop-down, clash, sideways, cascading or interlocking reinstatements;
- one layer borrowing capacity from another;
- reinstatement of capacity within the same occurrence;
- hours-clause regrouping beyond the already-elected CT4 result;
- mid-year changes to layers, shares, reinstatement wording or premium terms;
- multi-currency conversion or foreign-exchange effects;
- brokerage, taxes, levies, profit commission and premium-payment timing;
- minimum/deposit premium true-ups;
- reinstatement premium calculated on another reinstatement premium;
- credit risk, collateral, payment default or claims-payment delay;
- deriving original layer premium from CT4 loss output; and
- commercial rate adequacy or catastrophe-model validation.

## 4. Required CT4 entry contract

CT5 accepts only a completed, hashed CT4 result whose:

- result identity is valid under `CT4_ENGINE_VERSION = "ct4.0.0"` and
  `CT4_SCHEMA_VERSION = "ct4.0"`;
- occurrence and annual ledgers reconcile;
- occurrence ordering is frozen;
- hours-clause election, if applicable, is complete and valid;
- every occurrence exposes CT3 layer results; and
- recovery field is
  `gross_contractual_recovery_pre_annual_capacity`.

A raw event loss, raw annual loss, unverified CT3 result or un-hashed CT4
ledger is rejected. CT5 never accepts an annual aggregate as a substitute for
ordered occurrence rows.

## 5. Contractual term model

Each CT3 layer receives one immutable CT5 term record:

- `layer_id`, matching exactly one CT3 layer;
- `original_layer_premium`, on the payable-placed-share basis;
- `premium_basis_declaration`;
- ordered `reinstatement_tranches`;
- treaty-term start and end in the same units as CT4 event time;
- settlement mode;
- source and rule references.

Each reinstatement tranche declares:

- positive integer sequence beginning at one;
- `premium_rate`, where `1.0` means 100% of original layer premium;
- `time_basis`, either `full_time` or `pro_rata_remaining_term`; and
- whether the wording labels the tranche free or paid.

A free tranche has `premium_rate = 0`. A paid tranche may use a rate above
100%. The free/paid label must agree with the numerical rate. Tranche sequence
and rate are contractual inputs and therefore hash-significant.

The number of full reinstatements equals the number of declared tranches.
Fractional *usage* of the final tranche is permitted; fractional undeclared
tranches are not.

## 6. Capacity basis and share boundary

CT5 preserves CT1's frozen capacity basis:

`capacity_basis = payable_placed_share`

For layer (i):

- occurrence limit (L_i) is the 100% CT3 layer limit;
- ceded share is (q_i);
- placement share is (p_i); and
- fixed share factor is (s_i=q_i p_i).

### F25 — Initial and maximum annual capacity

\[
I_i=L_i s_i
\]

\[
P_{i,0}=I_i n_i
\]

\[
M_i=I_i+P_{i,0}=I_i(1+n_i)
\]

where:

- (I_i) is active capacity at the start of every annual trial;
- (n_i) is the integer number of reinstatement tranches;
- (P_{i,0}) is the initial reinstatement reserve; and
- (M_i) is the maximum recovery capacity available during the year.

CT4 layer recovery already reflects ceded and placement shares. CT5 must not
apply either share a second time.

For constant shares, the payable ledger equals the corresponding 100%-layer
ledger multiplied by (s_i). Per-event or mid-year share variation remains out
of scope.

## 7. Annual reset and deterministic ordering

At the start of every annual trial and for every layer:

\[
A_{i,0}=I_i,\qquad P_{i,0}=I_i n_i
\]

where (A) is active capacity and (P) is unused reinstatement reserve.

No capacity, premium or tranche usage carries between annual trials.

Within a trial, CT5 consumes events in the exact CT4 occurrence sequence.
When two events share a timestamp, CT4's sequence and stable ID remain
authoritative. Reinstatement following the earlier ordered event is available
to the later ordered event, even when their timestamps are equal. This is a
declared deterministic teaching convention, not inferred contract wording.

## 8. Per-event layer capacity engine

Let (U_{yji}) be CT4's pre-annual-capacity contractual recovery for annual
trial (y), occurrence (j), layer (i). Let (A^-_{yji}) and (P^-_{yji}) be active
capacity and reinstatement reserve immediately before the event.

### F26 — Actual layer recovery after annual capacity

\[
R_{yji}=\min(U_{yji},A^-_{yji})
\]

No reinstated amount may increase (R_{yji}) for the triggering occurrence.

### F27 — Active capacity after recovery, before reinstatement

\[
D_{yji}=A^-_{yji}-R_{yji}
\]

### F28 — Automatic reinstatement after the occurrence

\[
H_{yji}=I_i-D_{yji}
\]

\[
J_{yji}=\min(H_{yji},P^-_{yji})
\]

\[
A^+_{yji}=D_{yji}+J_{yji}
\]

\[
P^+_{yji}=P^-_{yji}-J_{yji}
\]

where:

- (H) is the amount required to restore the active occurrence limit;
- (J) is the amount actually reinstated;
- (A^+) is capacity available to the next ordered event; and
- (P^+) is unused reinstatement reserve.

Automatic reinstatement applies after every covered event, including the last
observed event of a simulated year. Premium is payable for that restoration
even if no later event occurs. This reflects contractual restoration triggered
by loss, not hindsight about whether restored capacity is subsequently used.

If no reserve remains, active capacity declines and later recovery may be
partially constrained or zero.

## 9. Ordered tranche allocation

Each tranche contains exactly (I_i) of payable reinstatement capacity. Let
(Z^-_{yjik}) be capacity already used in tranche (k) before the event.

### F29 — Sequential tranche use

The engine allocates (J_{yji}) to the lowest-numbered non-exhausted tranche.
For each tranche:

\[
\Delta J_{yjik}=\min\left(J^{remaining}_{yji}, I_i-Z^-_{yjik}\right)
\]

and continues until the event's reinstatement amount is fully allocated or no
tranche remains.

No later tranche may be used before every earlier tranche is exhausted. Each
allocation records tranche sequence, amount before, amount used, amount after,
rate and time basis.

Fractional reinstatements used are reported as:

\[
N^{used}_{yi}=\frac{\sum_j J_{yji}}{I_i}
\]

when (I_i>0). This value may be non-integer. For zero payable capacity it is
zero with a separate not-applicable utilization status.

## 10. Reinstatement premium

Original layer premium is an explicit contractual input. CT5 does not infer it
from AAL, technical premium, rate-on-line or any pricing-lab output.

For tranche (k), let:

- (B_i) be original layer premium on the payable-placed-share basis;
- (\rho_{ik}) be the tranche premium rate; and
- (\tau_{yjik}) be the time factor.

### F30 — Tranche and event premium

\[
RP_{yjik}=B_i\rho_{ik}\frac{\Delta J_{yjik}}{I_i}\tau_{yjik}
\]

\[
RP_{yj}=\sum_i\sum_k RP_{yjik}
\]

For `full_time`:

\[
\tau_{yjik}=1
\]

For `pro_rata_remaining_term`:

\[
\tau_{yjik}=\frac{term\_end-t_{yj}}{term\_end-term\_start}
\]

The event time must lie in the inclusive-start/exclusive-end treaty term.
Invalid timestamps are rejected rather than clamped. No rounding occurs inside
the engine.

Every premium is pro rata as to amount. Time proration occurs only when the
tranche explicitly declares it. A free tranche produces zero premium while
still restoring and consuming capacity.

If (I_i=0), recovery, reserve, reinstatement and premium are all zero; no
division is performed.

## 11. Three-way settlement

CT5 preserves three separately named fields:

1. `gross_contractual_recovery`;
2. `reinstatement_premium_payable`; and
3. `net_cash_settlement`.

The default is `paid_separately`.

### F31 — Settlement presentation

For `paid_separately`:

\[
net\_cash\_settlement_{yj}=gross\_contractual\_recovery_{yj}
\]

For the advanced `deducted_from_settlement` presentation:

\[
net\_cash\_settlement_{yj}=gross\_contractual\_recovery_{yj}
-reinstatement\_premium\_payable_{yj}
\]

Net cash settlement may be negative when a contractually valid premium exceeds
recovery. The engine does not floor or silently offset it.

Changing settlement mode must not change pre-capacity recovery, actual gross
recovery, capacity consumed, reinstatement amount, tranche usage, premium
payable or insurer net subject loss. It changes only the settlement
presentation.

## 12. Event and annual reconciliation

### F32 — Event program recovery and insurer net loss

\[
R_{yj}=\sum_i R_{yji}
\]

\[
N_{yj}=S_{yj}-R_{yj}
\]

where (S_{yj}) is the unchanged CT4 Cat XL subject loss. Settlement mode does
not enter insurer net subject loss.

### F33 — Annual totals

\[
R_y=\sum_jR_{yj},\quad RP_y=\sum_jRP_{yj},\quad
C_y=\sum_j net\_cash\_settlement_{yj}
\]

\[
N_y=\sum_jN_{yj},\qquad S_y=R_y+N_y
\]

All sums use `math.fsum` in frozen event/layer/tranche order.

### F34 — Layer active-capacity reconciliation

\[
I_i+\sum_jJ_{yji}-\sum_jR_{yji}=A^{final}_{yi}
\]

### F35 — Reinstatement-reserve reconciliation

\[
I_in_i-\sum_jJ_{yji}=P^{final}_{yi}
\]

### F36 — Contractual maximum

\[
\sum_jR_{yji}\le I_i(1+n_i)
\]

Every layer, event and annual reconciliation must pass before CT5 analytics or
hashes are emitted.

## 13. Capacity utilization

CT5 reports, by layer and annual trial:

\[
available\_capacity\_utilization=
\frac{\sum_jR_{yji}}{I_i+\sum_jJ_{yji}}
\]

and:

\[
reinstatement\_reserve\_utilization=
\frac{\sum_jJ_{yji}}{I_in_i}
\]

when the respective denominator is positive.

For zero initial payable capacity, utilization is null with
`not_applicable_zero_capacity`. When initial capacity is positive but there are
zero reinstatement tranches, reinstatement-reserve utilization is null with
`not_applicable_no_reinstatement_capacity`. It is never reported as NaN,
infinity or a fabricated 0%.

## 14. Immutable ledger contract

### 14.1 Layer-event row

Each layer/event row returns:

- annual trial, occurrence sequence, event ID and layer ID;
- CT4 pre-capacity layer recovery;
- active capacity and reserve before the event;
- actual layer recovery and constrained amount;
- active capacity after recovery, before reinstatement;
- amount reinstated;
- active capacity and reserve available to the next event;
- ordered tranche-allocation rows;
- reinstatement premium payable;
- capacity basis and formula references.

### 14.2 Event row

Each event row returns:

- subject loss;
- CT4 gross contractual recovery before annual capacity;
- CT5 gross contractual recovery after annual capacity;
- capacity-constrained recovery;
- insurer net subject loss after capacity;
- reinstatement premium payable;
- net cash settlement and settlement mode;
- layer rows and reconciliation status; and
- deterministic explanation facts.

### 14.3 Annual row

Every annual trial, including an empty trial, returns:

- ordered event rows;
- subject loss, gross recovery, premium, cash settlement and insurer-net totals;
- maximum occurrence recovery after capacity;
- layer capacity and tranche summaries;
- utilization values with explicit statuses;
- attachment, exhaustion and capacity-shortfall indicators; and
- F33–F36 reconciliation results.

## 15. Post-capacity analytics

CT5 reuses CT4's frozen nearest-rank, `r/Y`, TVaR, volatility and credibility
conventions. It does not redefine F21–F24.

Annual samples include exactly `trial_count` observations for:

- subject loss;
- gross contractual recovery after annual capacity;
- insurer net subject loss after annual capacity;
- reinstatement premium payable; and
- net cash settlement.

Recovery and insurer-net OEP are recomputed from CT5 event rows. Premium and
cash-settlement OEP/AEP are separately labelled. Negative net cash settlement
is permitted, so analytics models for that perspective must accept finite
negative observations without applying non-negative-loss validation.

CT5 also reports:

- probability annual capacity constrains at least one event;
- average recovery constrained by capacity;
- probability each layer exhausts maximum annual capacity;
- average and maximum reinstatements used; and
- average reinstatement premium, conditional and unconditional.

CT4 analytics remain visible as the pre-capacity benchmark; CT5 never overwrites
them.

## 16. Metadata and deterministic hashing

Frozen defaults proposed for review:

- `CT5_ENGINE_VERSION = "ct5.0.0"`;
- `CT5_SCHEMA_VERSION = "ct5.0"`;
- existing treaty product ID and route; and
- SHA-256 canonical input and result hashes.

Input identity includes:

- complete CT4 input and result hashes;
- layer-to-term mapping;
- original layer premium and basis declaration;
- every ordered tranche rate and time basis;
- treaty-term boundaries;
- settlement mode;
- numerical tolerances; and
- CT5 engine/schema versions.

Result identity includes canonical layer/event/annual ledgers, post-capacity
analytics, utilization statuses, warnings, CT5 versions and input hash.

Descriptions, explanation wording, number formatting and UI state are
excluded. Non-contractual input order is canonicalized; tranche order is never
canonicalized away because it changes premium.

## 17. Validation and fail-loudly rules

- every CT4 layer has exactly one CT5 term record and no unknown layer exists;
- original layer premium is finite and non-negative;
- rates are finite and non-negative;
- tranche sequences are contiguous and unique from one;
- free/paid labels agree with rates;
- treaty end exceeds treaty start;
- every event time lies inside the treaty term;
- layer terms and shares remain fixed for the annual trial and simulation;
- all monetary and capacity values are finite;
- capacity and reserve balances are non-negative;
- actual recovery cannot exceed CT4 pre-capacity recovery or active capacity;
- reinstated capacity cannot exceed reserve or restore active capacity above
  the initial occurrence limit;
- later tranches cannot precede earlier tranches;
- no event, layer or annual reconciliation may fail; and
- one invalid occurrence or term record blocks the entire CT5 run without
  partial analytics.

## 18. Learning and experimentation requirements

Every completed run explains:

- why CT4 recovery is an entitlement before annual capacity;
- why CT5 recovery can be lower for later events;
- why reinstatement does not increase recovery for the triggering event;
- which layer and event consumed each tranche;
- why premium may be due after the final observed event;
- how amount and time proration change premium;
- why a free reinstatement still consumes contractual capacity;
- why paid-separately and deducted modes leave gross recovery unchanged;
- why a layer can attach yet produce constrained or zero recovery; and
- why annual capacity affects AEP more directly than occurrence attachment.

Scenario comparison may vary one declared contractual term at a time, including
reinstatement count, rates, time basis, original premium or settlement mode.
Scenarios remain separate simulations and are never pooled.

## 19. Golden cases

G01–G46 retain their frozen meanings. CT5 adds:

| ID | Scenario | Expected check |
|---|---|---|
| G47 | No reinstatements | Recovery stops when initial annual layer capacity is exhausted |
| G48 | One full reinstatement | First exhaustion restores one full limit for a later event |
| G49 | Third event after exhaustion | With one reinstatement, a third full-limit event receives zero recovery |
| G50 | Partial final reinstatement | Partial loss consumes and prices the exact fraction restored |
| G51 | Ordered paid tranches | Earlier tranche exhausts before a differently priced later tranche |
| G52 | Multi-layer independence | One layer exhausts without borrowing from another layer |
| G53 | Free reinstatement | Capacity restores while premium remains zero |
| G54 | Pro rata remaining term | Premium uses the declared remaining-term fraction exactly |
| G55 | Fixed non-default shares | Payable recovery/capacity/premium reconcile without double application |
| G56 | Settlement presentation | Both modes have identical gross recovery, premium and capacity; only net cash settlement changes |
| G57 | Zero payable capacity | All capacity/recovery/premium values are zero and utilization is null/N/A |
| G58 | Empty annual trial | Zero ledger remains in every annual denominator and capacity resets normally |
| G59 | Post-capacity reconciliation | Subject equals gross recovery plus insurer net at event, annual and AAL levels |
| G60 | Input permutation | Non-contractual term input order does not change ledgers or hashes |
| G61 | Hours-clause entry | CT5 consumes only the valid CT4 elected occurrences |
| G62 | Invalid event time | Out-of-term event blocks the complete run before capacity calculation |

### Hand-worked core example

One layer has payable initial capacity USD 20m, one 100% full-time paid
reinstatement and original layer premium USD 2m.

- Event 1 pre-capacity recovery: USD 20m.
- Actual recovery: USD 20m.
- Reinstated amount: USD 20m.
- Premium: USD 2m.
- Capacity for Event 2: USD 20m.
- Event 2 pre-capacity recovery: USD 20m.
- Actual recovery: USD 20m.
- Reinstated amount and premium: zero because reserve is exhausted.
- Event 3 pre-capacity recovery: USD 20m.
- Actual recovery: zero.
- Annual gross recovery: USD 40m.
- Annual premium payable: USD 2m.
- Paid-separately cash settlement: USD 40m.
- Deducted cash settlement: USD 38m.

## 20. Acceptance gates

| Gate | Pass condition |
|---|---|
| CT1–CT4 regression | All 759 installed tests remain passing |
| Entry identity | Only completed, matching CT4 identities are accepted |
| Layer mapping | Exactly one CT5 term record exists for every CT3 layer |
| Capacity | F25–F29 reproduce hand-worked full and partial cases |
| Premium | F30 reproduces free, full-time and remaining-term cases |
| Settlement | F31 changes only net cash settlement presentation |
| Reconciliation | F32–F36 pass for every event, layer, year and portfolio mean |
| Zero capacity | Null/N/A conventions produce no NaN, infinity or false 0% |
| Ordering | Event and tranche order are deterministic and hash-stable |
| Analytics | Post-capacity samples retain all declared annual trials |
| Credibility | CT4 empirical-tail warnings remain unchanged in meaning |
| Metadata | Contractual/version changes alter hashes; display changes do not |
| Product boundary | No CT5 module imports pricing, API or frontend engines |
| Golden cases | G47–G62 pass with permanent trace IDs |
| Distribution | Fresh extraction installs, passes the full suite and is Git-clean |

## 21. Planned implementation units

| Unit | Responsibility |
|---|---|
| `cat_treaty/ct5_models.py` | Immutable terms, tranches, state, ledgers, analytics and statuses |
| `cat_treaty/annual_capacity.py` | F25–F29 per-layer state transitions |
| `cat_treaty/reinstatement.py` | Ordered tranche allocation and F30 premium |
| `cat_treaty/ct5_settlement.py` | F31 three-way presentation |
| `cat_treaty/ct5_simulation.py` | CT4 entry validation and F32–F36 annual orchestration |
| `cat_treaty/ct5_analytics.py` | Post-capacity distributions, frequencies and explanations |
| `cat_treaty/ct5_metadata.py` | Canonical serialization and version-bound hashes |
| `tests/test_ct5_models.py` | Validation, immutability and zero-capacity contracts |
| `tests/test_ct5_capacity.py` | F25–F29 hand-worked capacity cases |
| `tests/test_ct5_reinstatement.py` | F30 tranche and premium cases |
| `tests/test_ct5_settlement.py` | F31 invariants and negative cash presentation |
| `tests/test_ct5_simulation.py` | F32–F36 ordering and reconciliations |
| `tests/test_ct5_analytics.py` | Post-capacity OEP/AEP and annual denominators |
| `tests/test_ct5_metadata.py` | Hash, permutation and version gates |
| `tests/test_ct5_golden_cases.py` | G47–G62 consolidated acceptance |
| `tests/test_ct5_boundaries.py` | Source, product and milestone boundaries |

## 22. Proposed implementation order

1. Independently review this draft and resolve every structural or formula
   finding.
2. Freeze CT5 Specification v1.0 and record an audit-disposition document.
3. Implement immutable CT5 terms, state and ledger models.
4. Implement F25–F29 annual capacity and ordered tranche allocation.
5. Implement F30 reinstatement premium.
6. Implement F31 settlement presentation.
7. Implement F32–F36 annual orchestration and reconciliations.
8. Implement post-capacity analytics and learning explanations.
9. Implement CT5 canonical metadata and hashes.
10. Consolidate G47–G62 and run the full regression/distribution gate.

## 23. Reviewer decisions requested

The independent reviewer should answer explicitly:

1. Is payable-placed-share capacity the correct continuation of CT1 and CT4?
2. Does F26 correctly prevent reinstated capacity from benefiting the same
   occurrence?
3. Do F27–F29 handle partial final reinstatements without hidden over-restoration?
4. Should automatic reinstatement and premium apply after the final observed
   event, as specified?
5. Is sequential tranche allocation sufficiently explicit when rates differ?
6. Is original layer premium correctly required as an external contractual
   input rather than inferred from CT4?
7. Is the remaining-term factor in F30 contractually cautious and correctly
   bounded by fail-fast timestamp validation?
8. Should v1 support any other time basis, or is `full_time` plus
   `pro_rata_remaining_term` the correct boundary?
9. Is negative net cash settlement acceptable without flooring in the advanced
   deduction presentation?
10. Are F32–F36 sufficient to reconcile recovery, capacity, reserve and insurer
    net independently?
11. Are utilization denominators and zero/not-applicable statuses unambiguous?
12. Should post-capacity analytics include any perspective beyond the five
    declared annual samples?
13. Are G47–G62 sufficient to prevent double shares, same-event
    reinstatement, tranche-order and settlement defects?
14. Are the exclusions appropriate for CT5, particularly aggregate features,
    cross-layer capacity and premium taxes/brokerage?
15. Is the proposed metadata boundary sufficient to prove that a CT5 result is
    tied to one exact completed CT4 result?

## 24. Freeze rule

Independent approval of this draft does not itself authorize coding if the
review contains unresolved findings. After every accepted change is folded in,
the final document must be relabelled:

`CT5 Implementation Specification — Frozen v1.0`

Only that frozen commit authorizes CT5 implementation.
