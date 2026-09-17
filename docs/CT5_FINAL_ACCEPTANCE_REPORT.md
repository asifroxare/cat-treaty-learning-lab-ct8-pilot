# CT5 Final Acceptance Report

**Milestone:** CT5 — annual capacity, reinstatements, reinstatement premium and net cash settlement  
**Specification:** `docs/CT5_IMPLEMENTATION_SPEC.md` v1.0  
**Engine/schema:** `ct5.0.0` / `ct5.0`  
**Disposition:** Accepted for the complete backend installation package

## Acceptance result

The consolidated CT5 implementation satisfies F25–F37 and the frozen G47–G68
acceptance set. The complete regression suite passed with **932 tests**. CT1–CT4
behavior remains covered by the same run; CT5 does not replace or mutate the
frozen upstream results.

The final boundary is deliberate: this acceptance closes the CT5 backend
engine and installable source package. API, frontend and production deployment
remain later architectural milestones.

## Formula and control disposition

| Area | Result |
|---|---|
| F25–F29 annual capacity and ordered tranche allocation | Pass |
| F30 free/paid reinstatement premium and amount/time proration | Pass |
| F31 three-way settlement presentation | Pass |
| F32–F37 event, annual, utilization and shortfall reconciliation | Pass |
| Six post-capacity OEP/AEP perspectives and operational metrics | Pass |
| CT4 identity validation, canonical serialization and SHA-256 hashes | Pass |
| Fixed tolerance profile and fail-loudly validation | Pass |
| Hours-clause entry boundary | Pass — only CT4's valid elected occurrence rows enter CT5 |

## Consolidated golden-case evidence

The permanent machine-readable trace register is
`cat_treaty/golden_cases.py`. Each trace resolves to a collected behavioral
test, and the complete suite executes those tests.

| ID | Scenario | Evidence |
|---|---|---|
| G47 | No reinstatements | `test_g47_no_reinstatement_recovery_stops_at_initial_capacity` |
| G48 | One full reinstatement | `test_g48_one_full_reinstatement_benefits_only_later_event` |
| G49 | Third event after exhaustion | `test_g49_third_full_event_receives_zero_with_one_reinstatement` |
| G50 | Partial final reinstatement | `test_partial_recovery_restores_only_amount_consumed` |
| G51 | Ordered paid tranches | `test_f29_single_event_crosses_two_tranches_in_sequence` |
| G52 | Multi-layer independence | `test_layer_ledgers_preserve_independent_capacity` |
| G53 | Free reinstatement | `test_free_reinstatement_restores_capacity_with_zero_premium` |
| G54 | Pro rata remaining term | `test_pro_rata_remaining_term_uses_exact_fraction` |
| G55 | Fixed non-default shares | `test_f25_capacity_uses_payable_placed_share_once` |
| G56 | Settlement presentation | `test_g56_modes_do_not_change_capacity_tranches_or_f30_premium` |
| G57 | Zero payable capacity | `test_zero_capacity_utilization_is_null_not_zero` |
| G58 | Empty annual trial | `test_empty_annual_trial_is_retained_with_reset_layer_summaries` |
| G59 | Post-capacity reconciliation | `test_subject_recovery_and_net_aep_samples_reconcile` |
| G60 | Input permutation | `test_non_contractual_layer_term_order_canonicalizes_identically` |
| G61 | Hours-clause entry | `test_g61_hours_clause_entry_uses_only_elected_occurrences` |
| G62 | Invalid event time | `test_invalid_event_time_is_rejected_before_pricing` |
| G63 | One event crosses two tranches | `test_g63_one_event_crossing_two_tranches_uses_each_own_terms` |
| G64 | Equal event timestamps | `test_ct4_deterministic_tied_timestamp_order_is_preserved` |
| G65 | Negative cash settlement | `test_g65_negative_cash_settlement_is_valid_and_unfloored` |
| G66 | Partial amount plus time proration | `test_g66_amount_and_time_proration_are_multiplicative` |
| G67 | No same-event reinstatement benefit | `test_capacity_transition_contract_rejects_same_event_overrecovery` |
| G68 | Capacity-shortfall tails | `test_f37_shortfall_has_own_oep_and_aep_samples` |

## Final verification procedure

The distribution gate requires all of the following on the committed source:

1. `python -m pip check` reports no broken requirements.
2. `python -c "import cat_treaty; print(cat_treaty.CT5_ENGINE_VERSION)"` reports
   `ct5.0.0`.
3. `python -m pytest -q` passes the complete regression suite.
4. `git status --short` is empty before packaging.
5. The archive is built from a fresh clone of the final commit.
6. The archive is extracted independently and its complete test suite passes.

The archive SHA-256 is recorded outside the archive after final byte creation,
because embedding the archive's own digest would change that digest.
