"""CT5 F32--F37 catalogue orchestration and ledger tests."""

from dataclasses import replace

import pytest

from cat_treaty.ct4_models import CT4AnnualTrialInput
from cat_treaty.ct5_models import (
    CT5CatalogueResult,
    CT5TreatyTerms,
    CT5UtilizationStatus,
    ReinstatementChargeType,
)
from cat_treaty.ct5_simulation import apply_ct5_catalogue
from cat_treaty.models import SettlementMode
from cat_treaty.simulation import apply_catalogue_simulation
from tests.test_ct4_simulation import catalogue, event
from tests.test_ct5_models import layer_terms, tranche


def terms(
    *,
    reinstatements: int = 0,
    settlement_mode: SettlementMode = SettlementMode.PAID_SEPARATELY,
) -> CT5TreatyTerms:
    layer_terms_rows = []
    for layer_id, premium in (("L1", 2_000_000.0), ("L2", 3_000_000.0)):
        rows = tuple(
            tranche(
                sequence=index,
                premium_rate=1.0,
                charge_type=ReinstatementChargeType.PAID,
            )
            for index in range(1, reinstatements + 1)
        )
        layer_terms_rows.append(
            layer_terms(
                layer_id=layer_id,
                original_layer_premium=premium,
                reinstatement_tranches=rows,
                settlement_mode=settlement_mode,
            )
        )
    return CT5TreatyTerms(
        program_id="PROGRAM-1",
        layer_terms=tuple(layer_terms_rows),
        source_reference="contract:program",
        rule_reference="CT5-v1",
    )


def ct4_result(*trial_events):
    trials = tuple(
        CT4AnnualTrialInput(index, f"trial-{index}", events)
        for index, events in enumerate(trial_events, start=1)
    )
    return apply_catalogue_simulation(catalogue(*trials))


def test_no_reinstatement_orchestration_constrains_second_full_event() -> None:
    source = ct4_result(
        (
            event("E1", 60_000_000.0, event_time=1.0),
            event("E2", 60_000_000.0, event_time=2.0),
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    assert isinstance(result, CT5CatalogueResult)
    assert tuple(item.gross_contractual_recovery for item in result.occurrence_rows) == (50_000_000.0, 0.0)
    assert tuple(item.capacity_constrained_recovery_shortfall for item in result.occurrence_rows) == (0.0, 50_000_000.0)
    annual = result.annual_rows[0]
    assert annual.subject_loss == 120_000_000.0
    assert annual.gross_contractual_recovery == 50_000_000.0
    assert annual.insurer_net_subject_loss == 70_000_000.0
    assert annual.capacity_constrained_recovery_shortfall == 50_000_000.0


def test_one_reinstatement_supports_two_events_not_three() -> None:
    source = ct4_result(
        tuple(
            event(f"E{index}", 60_000_000.0, event_time=float(index))
            for index in range(1, 4)
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms(reinstatements=1))
    assert tuple(item.gross_contractual_recovery for item in result.occurrence_rows) == (50_000_000.0, 50_000_000.0, 0.0)
    assert result.annual_rows[0].gross_contractual_recovery == 100_000_000.0


def test_f32_event_reconciles_exact_ct4_subject_loss() -> None:
    source = ct4_result((event("E1", 45_000_000.0, event_time=100.0),))
    row = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms()).occurrence_rows[0]
    assert row.subject_loss == source.occurrence_rows[0].subject_loss == 45_000_000.0
    assert row.gross_contractual_recovery == 35_000_000.0
    assert row.insurer_net_subject_loss == 10_000_000.0
    assert row.subject_loss == row.gross_contractual_recovery + row.insurer_net_subject_loss


def test_layer_ledgers_preserve_independent_capacity() -> None:
    source = ct4_result((event("E1", 60_000_000.0),))
    row = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms()).occurrence_rows[0]
    assert tuple(item.layer_id for item in row.layer_rows) == ("L1", "L2")
    assert tuple(item.gross_contractual_recovery for item in row.layer_rows) == (20_000_000.0, 30_000_000.0)
    assert tuple(item.active_capacity_for_next_event for item in row.layer_rows) == (0.0, 0.0)


def test_annual_reset_prevents_capacity_carryover_between_trials() -> None:
    source = ct4_result(
        (event("Y1", 60_000_000.0, trial_id=1),),
        (event("Y2", 60_000_000.0, trial_id=2),),
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    assert tuple(item.gross_contractual_recovery for item in result.occurrence_rows) == (50_000_000.0, 50_000_000.0)
    assert tuple(item.gross_contractual_recovery for item in result.annual_rows) == (50_000_000.0, 50_000_000.0)


def test_empty_annual_trial_is_retained_with_reset_layer_summaries() -> None:
    source = ct4_result(
        (event("Y1", 45_000_000.0, trial_id=1),),
        (),
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms(reinstatements=1))
    empty = result.annual_rows[1]
    assert empty.event_rows == ()
    assert empty.subject_loss == empty.gross_contractual_recovery == 0.0
    assert len(empty.layer_summaries) == 2
    assert all(item.total_recovery == item.total_reinstated == 0.0 for item in empty.layer_summaries)


def test_utilization_uses_realized_and_nominal_denominators() -> None:
    source = ct4_result((event("E1", 60_000_000.0),))
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms(reinstatements=2))
    summaries = {item.layer_id: item for item in result.annual_rows[0].layer_summaries}
    assert summaries["L1"].realized_capacity_utilization == 0.5
    assert summaries["L1"].reinstatement_reserve_utilization == 0.5
    assert summaries["L2"].realized_capacity_utilization == 0.5
    assert summaries["L2"].reinstatement_reserve_utilization == 0.5


def test_no_reinstatement_reserve_has_explicit_na_status() -> None:
    source = ct4_result((event("E1", 45_000_000.0),))
    summary = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms()).annual_rows[0].layer_summaries[0]
    assert summary.reinstatement_reserve_utilization is None
    assert summary.reinstatement_reserve_utilization_status is CT5UtilizationStatus.NOT_APPLICABLE_NO_REINSTATEMENT_CAPACITY


def test_paid_separately_annual_cash_equals_gross_recovery() -> None:
    source = ct4_result((event("E1", 60_000_000.0),))
    annual = apply_ct5_catalogue(
        ct4_result=source,
        treaty_terms=terms(reinstatements=1),
    ).annual_rows[0]
    assert annual.reinstatement_premium_payable == 5_000_000.0
    assert annual.net_cash_settlement == annual.gross_contractual_recovery == 50_000_000.0


def test_deducted_mode_changes_cash_not_gross_or_insurer_net() -> None:
    source = ct4_result((event("E1", 60_000_000.0),))
    separate = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms(reinstatements=1))
    deducted = apply_ct5_catalogue(
        ct4_result=source,
        treaty_terms=terms(
            reinstatements=1,
            settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
        ),
    )
    left, right = separate.annual_rows[0], deducted.annual_rows[0]
    assert left.gross_contractual_recovery == right.gross_contractual_recovery
    assert left.insurer_net_subject_loss == right.insurer_net_subject_loss
    assert left.reinstatement_premium_payable == right.reinstatement_premium_payable
    assert right.net_cash_settlement == right.gross_contractual_recovery - right.reinstatement_premium_payable


def test_f37_shortfall_equals_pre_capacity_less_post_capacity_at_every_level() -> None:
    source = ct4_result(
        (
            event("E1", 60_000_000.0, event_time=1.0),
            event("E2", 45_000_000.0, event_time=2.0),
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    for event_row in result.occurrence_rows:
        assert event_row.capacity_constrained_recovery_shortfall == pytest.approx(
            event_row.gross_contractual_recovery_pre_annual_capacity - event_row.gross_contractual_recovery
        )
        assert event_row.capacity_constrained_recovery_shortfall == pytest.approx(
            sum(item.capacity_constrained_recovery_shortfall for item in event_row.layer_rows)
        )
    assert result.annual_rows[0].capacity_constrained_recovery_shortfall == pytest.approx(
        sum(item.capacity_constrained_recovery_shortfall for item in result.occurrence_rows)
    )


def test_ct4_deterministic_tied_timestamp_order_is_preserved() -> None:
    source = ct4_result(
        (
            event("B", 60_000_000.0, event_time=10.0, event_sequence=1),
            event("A", 60_000_000.0, event_time=10.0, event_sequence=1),
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms(reinstatements=1))
    assert tuple(item.event_id for item in result.occurrence_rows) == ("A", "B")
    assert result.occurrence_rows[0].layer_rows[0].active_capacity_before == 20_000_000.0
    assert result.occurrence_rows[1].layer_rows[0].active_capacity_before == 20_000_000.0


def test_terms_must_map_every_layer_exactly_once() -> None:
    source = ct4_result((event("E1", 45_000_000.0),))
    incomplete = replace(terms(), layer_terms=(terms().layer_terms[0],))
    with pytest.raises(ValueError, match="exactly one"):
        apply_ct5_catalogue(ct4_result=source, treaty_terms=incomplete)
    with pytest.raises(ValueError, match="program_id"):
        apply_ct5_catalogue(
            ct4_result=source,
            treaty_terms=replace(terms(), program_id="OTHER"),
        )


def test_all_empty_catalogue_cannot_invent_layer_terms() -> None:
    source = ct4_result(())
    with pytest.raises(ValueError, match="at least one CT4 occurrence"):
        apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())


def test_mixed_layer_settlement_modes_are_rejected() -> None:
    rows = terms().layer_terms
    with pytest.raises(ValueError, match="simulation-wide"):
        CT5TreatyTerms(
            program_id="PROGRAM-1",
            layer_terms=(
                rows[0],
                replace(rows[1], settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT),
            ),
            source_reference="contract",
            rule_reference="CT5",
        )


def test_result_rejects_occurrence_reordering() -> None:
    source = ct4_result(
        (
            event("E1", 45_000_000.0, event_time=1.0),
            event("E2", 45_000_000.0, event_time=2.0),
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    with pytest.raises(ValueError):
        replace(result, occurrence_rows=tuple(reversed(result.occurrence_rows)))


def test_ct5_simulation_public_exports() -> None:
    import cat_treaty

    assert "CT5CatalogueResult" in cat_treaty.__all__
    assert "apply_ct5_catalogue" in cat_treaty.__all__
    assert cat_treaty.apply_ct5_catalogue is apply_ct5_catalogue
