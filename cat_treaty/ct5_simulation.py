"""CT5 catalogue orchestration, annual ledgers, utilization, and F32--F37."""

import math

from cat_treaty.annual_capacity import apply_annual_capacity, initialize_annual_capacity
from cat_treaty.ct4_models import CT4CatalogueResult, HoursClauseResult, HoursElectionStatus
from cat_treaty.ct5_models import (
    CT5AnnualLedgerRow,
    CT5CatalogueResult,
    CT5EventLedgerRow,
    CT5HoursClauseEntry,
    CT5LayerAnnualSummary,
    CT5LayerEventLedgerRow,
    CT5TreatyTerms,
    CT5UtilizationStatus,
)
from cat_treaty.ct5_settlement import calculate_ct5_settlement
from cat_treaty.reinstatement import calculate_reinstatement_premium


def apply_ct5_catalogue(
    *,
    ct4_result: CT4CatalogueResult,
    treaty_terms: CT5TreatyTerms,
) -> CT5CatalogueResult:
    """Apply CT5 statefully to every frozen CT4 catalogue occurrence."""

    if not isinstance(ct4_result, CT4CatalogueResult):
        raise ValueError("ct4_result must be a completed CT4CatalogueResult")
    if not isinstance(treaty_terms, CT5TreatyTerms):
        raise ValueError("treaty_terms must be CT5TreatyTerms")
    event_inputs = {
        event.event_id: event
        for trial in ct4_result.simulation_input.trials
        for event in trial.occurrences
    }
    if set(event_inputs) != {item.event_id for item in ct4_result.occurrence_rows}:
        raise ValueError("CT4 input events and completed occurrence rows do not match")
    if not event_inputs:
        raise ValueError("CT5 requires at least one CT4 occurrence to establish layer terms")

    first_event = next(iter(event_inputs.values()))
    reference_layers = {
        item.layer_id: item for item in first_event.program_input.layers
    }
    term_by_layer = {item.layer_id: item for item in treaty_terms.layer_terms}
    if set(reference_layers) != set(term_by_layer):
        raise ValueError("every CT3 layer requires exactly one CT5 term record")
    if first_event.program_input.program_id != treaty_terms.program_id:
        raise ValueError("CT3 program_id must match CT5 treaty terms")

    annual_rows: list[CT5AnnualLedgerRow] = []
    occurrence_rows: list[CT5EventLedgerRow] = []
    for ct4_annual in ct4_result.annual_rows:
        states = {
            layer_id: initialize_annual_capacity(
                layer,
                term_by_layer[layer_id],
                annual_trial_id=ct4_annual.annual_trial_id,
            )
            for layer_id, layer in reference_layers.items()
        }
        event_rows: list[CT5EventLedgerRow] = []
        for ct4_row in ct4_annual.occurrence_rows:
            event_input = event_inputs[ct4_row.event_id]
            result = ct4_row.assessment.program_result
            if result is None:
                raise ValueError("CT5 requires a completed CT3 program result")
            layer_result_by_id = {
                item.layer_input.layer_id: item for item in result.layer_results
            }
            if set(layer_result_by_id) != set(reference_layers):
                raise ValueError("occurrence layer results do not match frozen CT5 terms")
            layer_rows: list[CT5LayerEventLedgerRow] = []
            for layer_id in tuple(item.layer_input.layer_id for item in result.layer_results):
                layer_result = layer_result_by_id[layer_id]
                transition = apply_annual_capacity(
                    state=states[layer_id],
                    layer=reference_layers[layer_id],
                    terms=term_by_layer[layer_id],
                    pre_annual_capacity_recovery=(
                        layer_result.gross_contractual_recovery
                    ),
                )
                premium = calculate_reinstatement_premium(
                    transition=transition,
                    terms=term_by_layer[layer_id],
                    event_time=event_input.event_time,
                )
                layer_rows.append(
                    CT5LayerEventLedgerRow(
                        annual_trial_id=ct4_row.annual_trial_id,
                        occurrence_sequence=ct4_row.occurrence_sequence,
                        event_id=ct4_row.event_id,
                        layer_id=layer_id,
                        pre_annual_capacity_recovery=transition.pre_annual_capacity_recovery,
                        active_capacity_before=transition.state_before.active_capacity,
                        reinstatement_reserve_before=transition.state_before.remaining_reinstatement_reserve,
                        gross_contractual_recovery=transition.gross_contractual_recovery,
                        capacity_constrained_recovery_shortfall=transition.capacity_constrained_recovery_shortfall,
                        active_capacity_after_recovery=transition.active_capacity_after_recovery,
                        amount_reinstated=transition.amount_reinstated,
                        active_capacity_for_next_event=transition.state_after.active_capacity,
                        reinstatement_reserve_after=transition.state_after.remaining_reinstatement_reserve,
                        tranche_allocations=premium.tranche_allocations,
                        reinstatement_premium_payable=premium.reinstatement_premium_payable,
                        trace_references=ct4_row.trace_references + ("F25", "F26", "F27", "F28", "F29", "F30"),
                    )
                )
                states[layer_id] = transition.state_after

            frozen_layer_rows = tuple(layer_rows)
            gross = math.fsum(item.gross_contractual_recovery for item in frozen_layer_rows)
            premium_total = math.fsum(
                item.reinstatement_premium_payable for item in frozen_layer_rows
            )
            settlement_mode = treaty_terms.layer_terms[0].settlement_mode
            settlement = calculate_ct5_settlement(
                gross_contractual_recovery=gross,
                reinstatement_premium_payable=premium_total,
                settlement_mode=settlement_mode,
            )
            event_rows.append(
                CT5EventLedgerRow(
                    annual_trial_id=ct4_row.annual_trial_id,
                    occurrence_sequence=ct4_row.occurrence_sequence,
                    event_id=ct4_row.event_id,
                    subject_loss=ct4_row.subject_loss,
                    gross_contractual_recovery_pre_annual_capacity=(
                        ct4_row.gross_contractual_recovery_pre_annual_capacity
                    ),
                    gross_contractual_recovery=gross,
                    capacity_constrained_recovery_shortfall=(
                        ct4_row.gross_contractual_recovery_pre_annual_capacity - gross
                    ),
                    insurer_net_subject_loss=ct4_row.subject_loss - gross,
                    reinstatement_premium_payable=premium_total,
                    net_cash_settlement=settlement.net_cash_settlement,
                    settlement_mode=settlement_mode,
                    layer_rows=frozen_layer_rows,
                    reconciliation_passed=True,
                    trace_references=ct4_row.trace_references + ("F31", "F32", "F37"),
                )
            )

        frozen_events = tuple(event_rows)
        summaries = tuple(
            _annual_layer_summary(states[layer_id])
            for layer_id in reference_layers
        )
        annual = CT5AnnualLedgerRow(
            annual_trial_id=ct4_annual.annual_trial_id,
            event_rows=frozen_events,
            layer_summaries=summaries,
            subject_loss=math.fsum(item.subject_loss for item in frozen_events),
            gross_contractual_recovery=math.fsum(
                item.gross_contractual_recovery for item in frozen_events
            ),
            capacity_constrained_recovery_shortfall=math.fsum(
                item.capacity_constrained_recovery_shortfall for item in frozen_events
            ),
            insurer_net_subject_loss=math.fsum(
                item.insurer_net_subject_loss for item in frozen_events
            ),
            reinstatement_premium_payable=math.fsum(
                item.reinstatement_premium_payable for item in frozen_events
            ),
            net_cash_settlement=math.fsum(
                item.net_cash_settlement for item in frozen_events
            ),
            maximum_occurrence_recovery=max(
                (item.gross_contractual_recovery for item in frozen_events),
                default=0.0,
            ),
            reconciliation_passed=True,
        )
        annual_rows.append(annual)
        occurrence_rows.extend(frozen_events)

    return CT5CatalogueResult(
        ct4_result=ct4_result,
        treaty_terms=treaty_terms,
        occurrence_rows=tuple(occurrence_rows),
        annual_rows=tuple(annual_rows),
        completed=True,
    )


def prepare_ct5_hours_clause_entry(result: HoursClauseResult) -> CT5HoursClauseEntry:
    """Freeze only the valid elected CT4 occurrences for later CT5 processing."""

    if not isinstance(result, HoursClauseResult):
        raise ValueError("result must be HoursClauseResult")
    if result.election_status is not HoursElectionStatus.SELECTED or result.annual_row is None:
        raise ValueError("blocked hours-clause result cannot enter CT5")
    windows = {item.candidate_id: item for item in result.candidate_windows}
    event_times = []
    for row in result.selected_occurrence_rows:
        candidate_id = row.event_id.rsplit(":", 1)[-1]
        window = windows.get(candidate_id)
        if window is None:
            raise ValueError("elected occurrence has no matching CT4 candidate window")
        event_times.append(float(window.start))
    return CT5HoursClauseEntry(
        ct4_result=result,
        occurrence_rows=result.selected_occurrence_rows,
        event_times=tuple(event_times),
    )


def _annual_layer_summary(state) -> CT5LayerAnnualSummary:
    realized_denominator = state.initial_capacity + state.cumulative_reinstated
    if realized_denominator == 0:
        realized_value = None
        realized_status = CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
    else:
        realized_value = state.cumulative_recovery / realized_denominator
        realized_status = CT5UtilizationStatus.APPLICABLE

    if state.initial_reinstatement_reserve == 0:
        reserve_value = None
        reserve_status = (
            CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
            if state.initial_capacity == 0
            else CT5UtilizationStatus.NOT_APPLICABLE_NO_REINSTATEMENT_CAPACITY
        )
    else:
        reserve_value = (
            state.cumulative_reinstated / state.initial_reinstatement_reserve
        )
        reserve_status = CT5UtilizationStatus.APPLICABLE
    return CT5LayerAnnualSummary(
        annual_trial_id=state.annual_trial_id,
        layer_id=state.layer_id,
        initial_capacity=state.initial_capacity,
        initial_reinstatement_reserve=state.initial_reinstatement_reserve,
        total_recovery=state.cumulative_recovery,
        total_reinstated=state.cumulative_reinstated,
        final_active_capacity=state.active_capacity,
        final_reinstatement_reserve=state.remaining_reinstatement_reserve,
        realized_capacity_utilization=realized_value,
        realized_capacity_utilization_status=realized_status,
        reinstatement_reserve_utilization=reserve_value,
        reinstatement_reserve_utilization_status=reserve_status,
    )
