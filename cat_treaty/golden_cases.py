"""Permanent CT5 G47--G68 acceptance traceability."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CT5GoldenCaseEvidence:
    case_id: str
    scenario: str
    test_node_id: str


CT5_GOLDEN_CASE_EVIDENCE = (
    CT5GoldenCaseEvidence("G47", "No reinstatements", "tests/test_ct5_capacity.py::test_g47_no_reinstatement_recovery_stops_at_initial_capacity"),
    CT5GoldenCaseEvidence("G48", "One full reinstatement", "tests/test_ct5_capacity.py::test_g48_one_full_reinstatement_benefits_only_later_event"),
    CT5GoldenCaseEvidence("G49", "Third event after exhaustion", "tests/test_ct5_capacity.py::test_g49_third_full_event_receives_zero_with_one_reinstatement"),
    CT5GoldenCaseEvidence("G50", "Partial final reinstatement", "tests/test_ct5_capacity.py::test_partial_recovery_restores_only_amount_consumed"),
    CT5GoldenCaseEvidence("G51", "Ordered paid tranches", "tests/test_ct5_capacity.py::test_f29_single_event_crosses_two_tranches_in_sequence"),
    CT5GoldenCaseEvidence("G52", "Multi-layer independence", "tests/test_ct5_simulation.py::test_layer_ledgers_preserve_independent_capacity"),
    CT5GoldenCaseEvidence("G53", "Free reinstatement", "tests/test_ct5_reinstatement.py::test_free_reinstatement_restores_capacity_with_zero_premium"),
    CT5GoldenCaseEvidence("G54", "Pro rata remaining term", "tests/test_ct5_reinstatement.py::test_pro_rata_remaining_term_uses_exact_fraction"),
    CT5GoldenCaseEvidence("G55", "Fixed non-default shares", "tests/test_ct5_capacity.py::test_f25_capacity_uses_payable_placed_share_once"),
    CT5GoldenCaseEvidence("G56", "Settlement presentation", "tests/test_ct5_settlement.py::test_g56_modes_do_not_change_capacity_tranches_or_f30_premium"),
    CT5GoldenCaseEvidence("G57", "Zero payable capacity", "tests/test_ct5_models.py::test_zero_capacity_utilization_is_null_not_zero"),
    CT5GoldenCaseEvidence("G58", "Empty annual trial", "tests/test_ct5_simulation.py::test_empty_annual_trial_is_retained_with_reset_layer_summaries"),
    CT5GoldenCaseEvidence("G59", "Post-capacity reconciliation", "tests/test_ct5_analytics.py::test_subject_recovery_and_net_aep_samples_reconcile"),
    CT5GoldenCaseEvidence("G60", "Input permutation", "tests/test_ct5_metadata.py::test_non_contractual_layer_term_order_canonicalizes_identically"),
    CT5GoldenCaseEvidence("G61", "Hours-clause entry", "tests/test_ct5_golden_cases.py::test_g61_hours_clause_entry_uses_only_elected_occurrences"),
    CT5GoldenCaseEvidence("G62", "Invalid event time", "tests/test_ct5_reinstatement.py::test_invalid_event_time_is_rejected_before_pricing"),
    CT5GoldenCaseEvidence("G63", "One event crosses two tranches", "tests/test_ct5_reinstatement.py::test_g63_one_event_crossing_two_tranches_uses_each_own_terms"),
    CT5GoldenCaseEvidence("G64", "Equal event timestamps", "tests/test_ct5_simulation.py::test_ct4_deterministic_tied_timestamp_order_is_preserved"),
    CT5GoldenCaseEvidence("G65", "Negative cash settlement", "tests/test_ct5_settlement.py::test_g65_negative_cash_settlement_is_valid_and_unfloored"),
    CT5GoldenCaseEvidence("G66", "Partial amount plus time proration", "tests/test_ct5_reinstatement.py::test_g66_amount_and_time_proration_are_multiplicative"),
    CT5GoldenCaseEvidence("G67", "No same-event reinstatement benefit", "tests/test_ct5_capacity.py::test_capacity_transition_contract_rejects_same_event_overrecovery"),
    CT5GoldenCaseEvidence("G68", "Capacity-shortfall tails", "tests/test_ct5_analytics.py::test_f37_shortfall_has_own_oep_and_aep_samples"),
)


@dataclass(frozen=True, slots=True)
class CT6GoldenCaseEvidence:
    case_id: str
    scenario: str
    test_node_id: str


CT6_GOLDEN_CASE_EVIDENCE = (
    CT6GoldenCaseEvidence("G69", "Liveness and readiness", "tests/test_ct6_golden_cases.py::test_g69_liveness_and_readiness_do_not_execute_simulation"),
    CT6GoldenCaseEvidence("G70", "Catalogue end to end", "tests/test_ct6_golden_cases.py::test_g70_catalogue_end_to_end_returns_both_capacity_views"),
    CT6GoldenCaseEvidence("G71", "Hours-clause end to end", "tests/test_ct6_golden_cases.py::test_g71_hours_clause_end_to_end_preserves_election_evidence"),
    CT6GoldenCaseEvidence("G72", "Malformed JSON", "tests/test_ct6_golden_cases.py::test_g72_malformed_json_is_sanitized_400"),
    CT6GoldenCaseEvidence("G73", "Strict schema failure", "tests/test_ct6_golden_cases.py::test_g73_numeric_string_and_unknown_field_are_rejected"),
    CT6GoldenCaseEvidence("G74", "Contract blockage", "tests/test_ct6_golden_cases.py::test_g74_invalid_election_blocks_without_downstream_payload"),
    CT6GoldenCaseEvidence("G75", "Deterministic repeat", "tests/test_ct6_golden_cases.py::test_g75_deterministic_repeat_preserves_results_and_hashes"),
    CT6GoldenCaseEvidence("G76", "Permitted input permutation", "tests/test_ct6_golden_cases.py::test_g76_permitted_component_permutation_preserves_hashes"),
    CT6GoldenCaseEvidence("G77", "Response detail", "tests/test_ct6_golden_cases.py::test_g77_full_and_summary_preserve_hashes_warnings_and_election"),
    CT6GoldenCaseEvidence("G78", "Negative cash settlement", "tests/test_ct6_golden_cases.py::test_g78_negative_cash_settlement_survives_json"),
    CT6GoldenCaseEvidence("G79", "Zero capacity", "tests/test_ct6_golden_cases.py::test_g79_zero_capacity_is_null_with_explicit_status"),
    CT6GoldenCaseEvidence("G80", "Credibility warnings", "tests/test_ct6_golden_cases.py::test_g80_cumulative_credibility_warnings_remain_http_200"),
    CT6GoldenCaseEvidence("G81", "API limit", "tests/test_ct6_golden_cases.py::test_g81_oversized_full_response_is_rejected_without_downgrade"),
    CT6GoldenCaseEvidence("G82", "Internal failure containment", "tests/test_ct6_golden_cases.py::test_g82_internal_failure_is_sanitized_without_partial_payload"),
    CT6GoldenCaseEvidence("G83", "API version conflict", "tests/test_ct6_golden_cases.py::test_g83_version_conflict_precedence_is_frozen"),
)
