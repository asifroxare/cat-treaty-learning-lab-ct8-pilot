import { acceptAuthoritativeResponse, type AuthoritativeSuccessResponse } from "../../api/authoritative";
import type { components } from "../../api/generated/ct6";

type RawSuccess = components["schemas"]["CT6SuccessResponse"];

export function ct6SuccessFixture(options: { summary?: boolean; zeroCapacity?: boolean; negativeCash?: boolean } = {}): AuthoritativeSuccessResponse {
  const raw: RawSuccess = {
    api: { api_schema_version: "ct6.0", api_version: "ct6.0.0", client_request_id: null, completion_status: "complete", request_id: "request-ct7", run_mode: "catalogue" },
    request: { simulation_id: "S1", program_id: "P1", trial_count: 1, occurrence_count: 1, layer_ids: ["L1"], reporting_currency: "USD", response_detail: options.summary ? "summary" : "full" },
    identity: { simulation_id: "S1", ct4_input_hash: "a".repeat(64), ct4_result_hash: "b".repeat(64), ct5_input_hash: "c".repeat(64), ct5_result_hash: "d".repeat(64) },
    versions: { ct2_engine_version: "ct2.0.0", ct2_schema_version: "ct2.0", ct3_engine_version: "ct3.0.0", ct3_schema_version: "ct3.0", ct4_engine_version: "ct4.0.0", ct4_schema_version: "ct4.0", ct5_engine_version: "ct5.0.0", ct5_schema_version: "ct5.0", ct6_api_version: "ct6.0.0", ct6_schema_version: "ct6.0" },
    warnings: [{ code: "CT4_TAIL_CREDIBILITY", message: "The selected return period has limited empirical support.", return_period: 100, source: "CT4" }],
    pre_capacity: {
      annual_rows: [{ annual_trial_id: 1, subject_loss: 40_500_000, gross_contractual_recovery_pre_annual_capacity: 20_000_000, insurer_net_loss_pre_annual_capacity: 20_500_000, maximum_occurrence_recovery_pre_annual_capacity: 20_000_000, reconciliation_passed: true }],
      occurrence_rows: options.summary ? null : [{ annual_trial_id: 1, occurrence_sequence: 1, event_id: "E1", subject_loss: 40_500_000, gross_contractual_recovery_pre_annual_capacity: 20_000_000, insurer_net_loss_pre_annual_capacity: 20_500_000, reconciliation_passed: true }],
      candidate_sets: [], candidate_windows: [], valid_candidate_set_ids: [], selected_candidate_set_id: null, selected_election_method: null, frequency_analytics: {}, tail_analytics: {},
    },
    post_capacity: {
      annual_rows: [{
        annual_trial_id: 1, subject_loss: 40_500_000, gross_contractual_recovery: options.zeroCapacity ? 0 : 20_000_000,
        capacity_constrained_recovery_shortfall: options.zeroCapacity ? 20_000_000 : 0, insurer_net_subject_loss: options.zeroCapacity ? 40_500_000 : 20_500_000,
        reinstatement_premium_payable: options.negativeCash ? 21_000_000 : 1_000_000, net_cash_settlement: options.negativeCash ? -1_000_000 : 19_000_000,
        maximum_occurrence_recovery: options.zeroCapacity ? 0 : 20_000_000, reconciliation_passed: true,
        layer_summaries: [{
          annual_trial_id: 1, layer_id: "L1", initial_capacity: options.zeroCapacity ? 0 : 20_000_000, final_active_capacity: 20_000_000,
          initial_reinstatement_reserve: 20_000_000, final_reinstatement_reserve: 0, total_recovery: options.zeroCapacity ? 0 : 20_000_000, total_reinstated: 20_000_000,
          realized_capacity_utilization: options.zeroCapacity ? null : 1, realized_capacity_utilization_status: options.zeroCapacity ? "not_applicable_zero_capacity" : "applicable",
          reinstatement_reserve_utilization: 1, reinstatement_reserve_utilization_status: "applicable",
        }],
      }],
      occurrence_rows: options.summary ? null : [{
        annual_trial_id: 1, occurrence_sequence: 1, event_id: "E1", subject_loss: 40_500_000,
        gross_contractual_recovery_pre_annual_capacity: 20_000_000, gross_contractual_recovery: options.zeroCapacity ? 0 : 20_000_000,
        capacity_constrained_recovery_shortfall: options.zeroCapacity ? 20_000_000 : 0, insurer_net_subject_loss: options.zeroCapacity ? 40_500_000 : 20_500_000,
        reinstatement_premium_payable: options.negativeCash ? 21_000_000 : 1_000_000, net_cash_settlement: options.negativeCash ? -1_000_000 : 19_000_000,
        reconciliation_passed: true, layer_event_rows: [],
      }],
      analytics: {},
    },
    learning: {
      facts: [{ category: "capacity", metric_name: "gross_contractual_recovery", value: 20_000_000, driver_statement: "Annual capacity was available.", meaning: "The contractual entitlement was payable.", trace_references: ["E1", "L1"] }],
      reconciliations: [{ scope: "annual", identifier: "1", passed: true, formula_references: ["F37"] }],
    },
  };
  return acceptAuthoritativeResponse(raw);
}
