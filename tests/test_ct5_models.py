"""Validation tests for immutable CT5 domain contracts."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct5_models import (
    CT5AnnualLedgerRow,
    CT5CapacityState,
    CT5EventLedgerRow,
    CT5LayerAnnualSummary,
    CT5LayerEventLedgerRow,
    CT5LayerTerms,
    CT5MetricPerspective,
    CT5Settlement,
    CT5TreatyTerms,
    CT5UtilizationStatus,
    ReinstatementChargeType,
    ReinstatementTimeBasis,
    ReinstatementTranche,
    TrancheAllocation,
)
from cat_treaty.models import CapacityBasis, SettlementMode


def tranche(**changes: object) -> ReinstatementTranche:
    values: dict[str, object] = {
        "sequence": 1,
        "premium_rate": 1.0,
        "time_basis": ReinstatementTimeBasis.FULL_TIME,
        "charge_type": ReinstatementChargeType.PAID,
        "source_reference": "wording:reinstatement-1",
        "rule_reference": "CT5-F30",
    }
    values.update(changes)
    return ReinstatementTranche(**values)


def layer_terms(**changes: object) -> CT5LayerTerms:
    values: dict[str, object] = {
        "layer_id": "L1",
        "original_layer_premium": 2_000_000.0,
        "premium_basis_declaration": "payable placed share",
        "reinstatement_tranches": (tranche(),),
        "treaty_term_start": 0.0,
        "treaty_term_end": 8_760.0,
        "settlement_mode": SettlementMode.PAID_SEPARATELY,
        "source_reference": "contract:L1",
        "rule_reference": "CT5-terms",
    }
    values.update(changes)
    return CT5LayerTerms(**values)


def allocation(**changes: object) -> TrancheAllocation:
    values: dict[str, object] = {
        "tranche_sequence": 1,
        "capacity_before": 20.0,
        "amount_used": 5.0,
        "capacity_after": 15.0,
        "premium_rate": 1.0,
        "time_basis": ReinstatementTimeBasis.FULL_TIME,
        "time_factor": 1.0,
        "reinstatement_premium_payable": 0.5,
        "rule_reference": "CT5-F30",
    }
    values.update(changes)
    return TrancheAllocation(**values)


def layer_row(**changes: object) -> CT5LayerEventLedgerRow:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "occurrence_sequence": 1,
        "event_id": "E1",
        "layer_id": "L1",
        "pre_annual_capacity_recovery": 12.0,
        "active_capacity_before": 10.0,
        "reinstatement_reserve_before": 20.0,
        "gross_contractual_recovery": 10.0,
        "capacity_constrained_recovery_shortfall": 2.0,
        "active_capacity_after_recovery": 0.0,
        "amount_reinstated": 5.0,
        "active_capacity_for_next_event": 5.0,
        "reinstatement_reserve_after": 15.0,
        "tranche_allocations": (allocation(),),
        "reinstatement_premium_payable": 0.5,
        "trace_references": ("event:E1", "layer:L1"),
    }
    values.update(changes)
    return CT5LayerEventLedgerRow(**values)


def event_row(**changes: object) -> CT5EventLedgerRow:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "occurrence_sequence": 1,
        "event_id": "E1",
        "subject_loss": 30.0,
        "gross_contractual_recovery_pre_annual_capacity": 12.0,
        "gross_contractual_recovery": 10.0,
        "capacity_constrained_recovery_shortfall": 2.0,
        "insurer_net_subject_loss": 20.0,
        "reinstatement_premium_payable": 0.5,
        "net_cash_settlement": 10.0,
        "settlement_mode": SettlementMode.PAID_SEPARATELY,
        "layer_rows": (layer_row(),),
        "reconciliation_passed": True,
        "trace_references": ("event:E1",),
    }
    values.update(changes)
    return CT5EventLedgerRow(**values)


def layer_summary(**changes: object) -> CT5LayerAnnualSummary:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "layer_id": "L1",
        "initial_capacity": 20.0,
        "initial_reinstatement_reserve": 20.0,
        "total_recovery": 10.0,
        "total_reinstated": 5.0,
        "final_active_capacity": 15.0,
        "final_reinstatement_reserve": 15.0,
        "realized_capacity_utilization": 0.4,
        "realized_capacity_utilization_status": CT5UtilizationStatus.APPLICABLE,
        "reinstatement_reserve_utilization": 0.25,
        "reinstatement_reserve_utilization_status": CT5UtilizationStatus.APPLICABLE,
    }
    values.update(changes)
    return CT5LayerAnnualSummary(**values)


def annual_row(**changes: object) -> CT5AnnualLedgerRow:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "event_rows": (event_row(),),
        "layer_summaries": (layer_summary(),),
        "subject_loss": 30.0,
        "gross_contractual_recovery": 10.0,
        "capacity_constrained_recovery_shortfall": 2.0,
        "insurer_net_subject_loss": 20.0,
        "reinstatement_premium_payable": 0.5,
        "net_cash_settlement": 10.0,
        "maximum_occurrence_recovery": 10.0,
        "reconciliation_passed": True,
    }
    values.update(changes)
    return CT5AnnualLedgerRow(**values)


def test_ct5_literals_are_frozen() -> None:
    assert ReinstatementTimeBasis.FULL_TIME.value == "full_time"
    assert ReinstatementChargeType.FREE.value == "free"
    assert CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY.value == "not_applicable_zero_capacity"
    assert len(CT5MetricPerspective) == 6
    assert CT5MetricPerspective.CAPACITY_CONSTRAINED_RECOVERY_SHORTFALL.value == "capacity_constrained_recovery_shortfall"


def test_models_are_immutable_and_slotted() -> None:
    value = tranche()
    with pytest.raises(FrozenInstanceError):
        value.premium_rate = 2.0  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        value.extra = True  # type: ignore[attr-defined]


def test_ct5_public_package_exports() -> None:
    import cat_treaty

    expected = {
        "CT5AnnualLedgerRow",
        "CT5CapacityState",
        "CT5EventLedgerRow",
        "CT5LayerAnnualSummary",
        "CT5LayerEventLedgerRow",
        "CT5LayerTerms",
        "CT5MetricPerspective",
        "CT5Settlement",
        "CT5TreatyTerms",
        "CT5UtilizationStatus",
        "ReinstatementChargeType",
        "ReinstatementTimeBasis",
        "ReinstatementTranche",
        "TrancheAllocation",
    }
    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, name) for name in expected)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"sequence": 0}, "positive integer"),
        ({"premium_rate": -1.0}, "non-negative"),
        ({"premium_rate": math.inf}, "finite"),
        ({"time_basis": "full_time"}, "ReinstatementTimeBasis"),
        ({"charge_type": "paid"}, "ReinstatementChargeType"),
        ({"source_reference": ""}, "non-empty"),
    ],
)
def test_tranche_rejects_invalid_fields(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        tranche(**changes)


def test_free_and_paid_labels_must_agree_with_rate() -> None:
    assert tranche(premium_rate=0.0, charge_type=ReinstatementChargeType.FREE).premium_rate == 0
    with pytest.raises(ValueError, match="free tranche"):
        tranche(charge_type=ReinstatementChargeType.FREE)
    with pytest.raises(ValueError, match="paid tranche"):
        tranche(premium_rate=0.0)
    assert tranche(premium_rate=2.5).premium_rate == 2.5


def test_layer_terms_accept_zero_or_contiguous_tranches() -> None:
    assert layer_terms(reinstatement_tranches=()).reinstatement_tranches == ()
    second = tranche(sequence=2, premium_rate=0.0, charge_type=ReinstatementChargeType.FREE)
    assert len(layer_terms(reinstatement_tranches=(tranche(), second)).reinstatement_tranches) == 2
    with pytest.raises(ValueError, match="contiguous"):
        layer_terms(reinstatement_tranches=(second,))
    with pytest.raises(ValueError, match="contiguous"):
        layer_terms(reinstatement_tranches=(second, tranche()))


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"layer_id": ""}, "non-empty"),
        ({"original_layer_premium": -1.0}, "non-negative"),
        ({"premium_basis_declaration": ""}, "non-empty"),
        ({"treaty_term_end": 0.0}, "must exceed"),
        ({"settlement_mode": "paid_separately"}, "SettlementMode"),
        ({"capacity_basis": "payable_placed_share"}, "capacity_basis"),
    ],
)
def test_layer_terms_reject_invalid_values(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        layer_terms(**changes)


def test_treaty_terms_require_one_to_four_unique_layers() -> None:
    terms = CT5TreatyTerms("P1", (layer_terms(),), "contract", "CT5")
    assert terms.layer_terms[0].layer_id == "L1"
    with pytest.raises(ValueError, match="one to four"):
        replace(terms, layer_terms=())
    with pytest.raises(ValueError, match="unique"):
        replace(terms, layer_terms=(layer_terms(), layer_terms()))
    with pytest.raises(ValueError, match="one to four"):
        replace(terms, layer_terms=tuple(layer_terms(layer_id=f"L{i}") for i in range(5)))


def test_initial_capacity_state_is_valid() -> None:
    state = CT5CapacityState("L1", 1, 0, 20.0, 20.0, 40.0, 40.0, 0.0, 0.0)
    assert state.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE


def test_progressed_capacity_state_reconciles_f34_and_f35() -> None:
    state = CT5CapacityState("L1", 1, 2, 20.0, 15.0, 40.0, 25.0, 20.0, 15.0)
    assert state.active_capacity == 15.0
    for changes in (
        {"active_capacity": 14.0},
        {"remaining_reinstatement_reserve": 24.0},
        {"active_capacity": 21.0},
        {"completed_event_count": -1},
    ):
        with pytest.raises(ValueError):
            replace(state, **changes)


def test_initial_state_forbids_activity() -> None:
    with pytest.raises(ValueError, match="initial state"):
        CT5CapacityState("L1", 1, 0, 20.0, 15.0, 40.0, 35.0, 10.0, 5.0)


def test_tranche_allocation_reconciles_and_full_time_is_one() -> None:
    assert allocation().capacity_after == 15.0
    with pytest.raises(ValueError, match="does not reconcile"):
        allocation(capacity_after=14.0)
    with pytest.raises(ValueError, match="cannot exceed"):
        allocation(amount_used=21.0, capacity_after=0.0)
    with pytest.raises(ValueError, match="time_factor 1"):
        allocation(time_factor=0.5)
    pro_rata = allocation(
        time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM,
        time_factor=0.25,
    )
    assert pro_rata.time_factor == 0.25


def test_settlement_supports_both_modes_and_negative_cash() -> None:
    separate = CT5Settlement(10.0, 2.0, 10.0, SettlementMode.PAID_SEPARATELY)
    deducted = CT5Settlement(10.0, 2.0, 8.0, SettlementMode.DEDUCTED_FROM_SETTLEMENT)
    negative = CT5Settlement(1.0, 1.5, -0.5, SettlementMode.DEDUCTED_FROM_SETTLEMENT)
    assert separate.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert negative.net_cash_settlement == -0.5
    with pytest.raises(ValueError, match="F31"):
        replace(deducted, net_cash_settlement=10.0)


@pytest.mark.parametrize(
    "changes",
    [
        {"capacity_constrained_recovery_shortfall": 1.0},
        {"active_capacity_after_recovery": 1.0},
        {"active_capacity_for_next_event": 4.0},
        {"reinstatement_reserve_after": 14.0},
        {"amount_reinstated": 4.0},
        {"reinstatement_premium_payable": 0.4},
        {"trace_references": ()},
    ],
)
def test_layer_event_row_rejects_broken_reconciliation(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        layer_row(**changes)


def test_layer_event_row_accepts_ordered_cross_tranche_allocation() -> None:
    first = allocation(capacity_before=5.0, amount_used=5.0, capacity_after=0.0, reinstatement_premium_payable=0.25)
    second = allocation(
        tranche_sequence=2,
        capacity_before=20.0,
        amount_used=5.0,
        capacity_after=15.0,
        premium_rate=1.0,
        time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM,
        time_factor=0.25,
        reinstatement_premium_payable=0.125,
    )
    row = layer_row(
        amount_reinstated=10.0,
        active_capacity_for_next_event=10.0,
        reinstatement_reserve_after=10.0,
        tranche_allocations=(first, second),
        reinstatement_premium_payable=0.375,
    )
    assert tuple(item.tranche_sequence for item in row.tranche_allocations) == (1, 2)
    with pytest.raises(ValueError, match="ordered"):
        replace(row, tranche_allocations=(second, first))


@pytest.mark.parametrize(
    "changes",
    [
        {"subject_loss": 29.0},
        {"gross_contractual_recovery_pre_annual_capacity": 11.0},
        {"gross_contractual_recovery": 9.0},
        {"capacity_constrained_recovery_shortfall": 1.0},
        {"insurer_net_subject_loss": 19.0},
        {"reinstatement_premium_payable": 0.4},
        {"net_cash_settlement": 9.0},
        {"reconciliation_passed": False},
        {"layer_rows": ()},
    ],
)
def test_event_row_rejects_broken_contract(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        event_row(**changes)


def test_event_identity_must_match_layer_identity() -> None:
    with pytest.raises(ValueError, match="identity"):
        event_row(layer_rows=(layer_row(event_id="OTHER"),))


def test_layer_annual_summary_uses_distinct_denominators() -> None:
    summary = layer_summary()
    assert summary.realized_capacity_utilization == 10 / 25
    assert summary.reinstatement_reserve_utilization == 5 / 20
    with pytest.raises(ValueError, match="frozen denominator"):
        replace(summary, realized_capacity_utilization=0.5)
    with pytest.raises(ValueError, match="frozen denominator"):
        replace(summary, reinstatement_reserve_utilization=0.4)


def test_zero_capacity_utilization_is_null_not_zero() -> None:
    summary = layer_summary(
        initial_capacity=0.0,
        initial_reinstatement_reserve=0.0,
        total_recovery=0.0,
        total_reinstated=0.0,
        final_active_capacity=0.0,
        final_reinstatement_reserve=0.0,
        realized_capacity_utilization=None,
        realized_capacity_utilization_status=CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY,
        reinstatement_reserve_utilization=None,
        reinstatement_reserve_utilization_status=CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY,
    )
    assert summary.realized_capacity_utilization is None
    with pytest.raises(ValueError):
        replace(summary, realized_capacity_utilization=0.0)


def test_no_reinstatement_capacity_has_distinct_status() -> None:
    summary = layer_summary(
        initial_capacity=20.0,
        initial_reinstatement_reserve=0.0,
        total_recovery=10.0,
        total_reinstated=0.0,
        final_active_capacity=10.0,
        final_reinstatement_reserve=0.0,
        realized_capacity_utilization=0.5,
        reinstatement_reserve_utilization=None,
        reinstatement_reserve_utilization_status=CT5UtilizationStatus.NOT_APPLICABLE_NO_REINSTATEMENT_CAPACITY,
    )
    assert summary.reinstatement_reserve_utilization is None


def test_annual_row_reconciles_complete_and_empty_trials() -> None:
    assert annual_row().maximum_occurrence_recovery == 10.0
    empty = CT5AnnualLedgerRow(1, (), (), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, True)
    assert empty.event_rows == ()


@pytest.mark.parametrize(
    "changes",
    [
        {"subject_loss": 29.0},
        {"gross_contractual_recovery": 9.0},
        {"capacity_constrained_recovery_shortfall": 1.0},
        {"insurer_net_subject_loss": 19.0},
        {"reinstatement_premium_payable": 0.4},
        {"net_cash_settlement": 9.0},
        {"maximum_occurrence_recovery": 9.0},
        {"reconciliation_passed": False},
    ],
)
def test_annual_row_rejects_broken_reconciliation(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        annual_row(**changes)


def test_annual_event_sequence_must_be_contiguous() -> None:
    later_layer = layer_row(occurrence_sequence=2, event_id="E2")
    later_event = event_row(
        occurrence_sequence=2,
        event_id="E2",
        layer_rows=(later_layer,),
    )
    row = annual_row(
        event_rows=(event_row(), later_event),
        subject_loss=60.0,
        gross_contractual_recovery=20.0,
        capacity_constrained_recovery_shortfall=4.0,
        insurer_net_subject_loss=40.0,
        reinstatement_premium_payable=1.0,
        net_cash_settlement=20.0,
    )
    assert len(row.event_rows) == 2
    with pytest.raises(ValueError, match="contiguous"):
        replace(row, event_rows=(later_event,))


def test_tolerance_accepts_boundary_scale_but_rejects_material_difference() -> None:
    assert replace(layer_summary(), final_active_capacity=15.0 + 1e-6)
    with pytest.raises(ValueError, match="F34"):
        replace(layer_summary(), final_active_capacity=15.0 + 2e-6)
