"""CT0/CT1 golden-case execution and milestone traceability."""

from dataclasses import dataclass, replace

import pytest

from cat_treaty.adapter import adapt_processed_event_record
from cat_treaty.models import (
    CapacityUtilizationStatus,
    SettlementMode,
    TreatyShares,
)
from cat_treaty.shares import scale_payable_capacity


@dataclass(frozen=True, slots=True)
class SourceEvent:
    year: int = 1
    event_id: str = "GOLDEN-EVENT"
    event_time: float = 1.0
    event_sequence: int = 1
    peril: str = "hurricane"
    region: str = "gulf_coast"
    risks_affected: int = 10
    gross_event_loss: float = 2_500_000.0
    qualifies_under_two_risk_warranty: bool = True
    occurrence_recovery_before_capacity_constraint: float = 1_500_000.0
    capacity_before_event: float = 5_000_000.0
    actual_treaty_recovery: float = 1_500_000.0
    capacity_consumed: float = 1_500_000.0
    remaining_capacity_before_reinstatement: float = 3_500_000.0
    amount_reinstated: float = 0.0
    reinstatement_premium: float | None = 30_000.0
    capacity_available_for_next_event: float = 3_500_000.0
    reinstatements_remaining: float = 1.0
    net_event_loss: float = 1_000_000.0


BASE_EVENT = SourceEvent()


@pytest.mark.parametrize(
    ("case_id", "source", "shares", "expected_recovery"),
    [
        ("G01", replace(BASE_EVENT, gross_event_loss=900_000.0,
                        occurrence_recovery_before_capacity_constraint=0.0,
                        actual_treaty_recovery=0.0, capacity_consumed=0.0,
                        remaining_capacity_before_reinstatement=5_000_000.0,
                        capacity_available_for_next_event=5_000_000.0,
                        reinstatement_premium=0.0, net_event_loss=900_000.0),
         TreatyShares(), 0.0),
        ("G02", replace(BASE_EVENT, gross_event_loss=1_000_000.0,
                        occurrence_recovery_before_capacity_constraint=0.0,
                        actual_treaty_recovery=0.0, capacity_consumed=0.0,
                        remaining_capacity_before_reinstatement=5_000_000.0,
                        capacity_available_for_next_event=5_000_000.0,
                        reinstatement_premium=0.0, net_event_loss=1_000_000.0),
         TreatyShares(), 0.0),
        ("G03", BASE_EVENT, TreatyShares(0.9, 1.0), 1_350_000.0),
        ("G04", replace(BASE_EVENT, gross_event_loss=6_000_000.0,
                        occurrence_recovery_before_capacity_constraint=5_000_000.0,
                        actual_treaty_recovery=5_000_000.0,
                        capacity_consumed=5_000_000.0,
                        remaining_capacity_before_reinstatement=0.0,
                        capacity_available_for_next_event=0.0,
                        net_event_loss=1_000_000.0),
         TreatyShares(), 5_000_000.0),
        ("G05", replace(BASE_EVENT, gross_event_loss=8_000_000.0,
                        occurrence_recovery_before_capacity_constraint=5_000_000.0,
                        actual_treaty_recovery=5_000_000.0,
                        capacity_consumed=5_000_000.0,
                        remaining_capacity_before_reinstatement=0.0,
                        capacity_available_for_next_event=0.0,
                        net_event_loss=3_000_000.0),
         TreatyShares(), 5_000_000.0),
        ("G06", BASE_EVENT, TreatyShares(), 1_500_000.0),
    ],
)
def test_g01_to_g06_preserve_authoritative_occurrence_results(
    case_id: str,
    source: SourceEvent,
    shares: TreatyShares,
    expected_recovery: float,
) -> None:
    """CT1 adapts, shares and reconciles validated source results."""

    result = adapt_processed_event_record(source, shares=shares)

    assert case_id in {f"G{number:02d}" for number in range(1, 7)}
    assert result.gross_contractual_recovery == expected_recovery
    assert result.net_subject_loss == pytest.approx(
        result.event.subject_loss - expected_recovery
    )


def test_g08_settlement_presentation_invariant_is_available_in_ct1() -> None:
    separately = adapt_processed_event_record(
        BASE_EVENT,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )
    deducted = adapt_processed_event_record(
        BASE_EVENT,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert separately.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert separately.capacity_consumed == deducted.capacity_consumed
    assert separately.amount_reinstated == deducted.amount_reinstated
    assert separately.settlement is not None
    assert deducted.settlement is not None
    assert separately.settlement.net_cash_settlement == 1_500_000.0
    assert deducted.settlement.net_cash_settlement == 1_470_000.0


def test_g14_two_event_fixed_share_capacity_equivalence() -> None:
    shares = TreatyShares(0.9, 0.75)
    factor = 0.675
    events = (
        dict(initial_capacity_100_percent=10_000_000.0,
             available_before_100_percent=10_000_000.0,
             consumed_100_percent=2_000_000.0,
             reinstated_100_percent=1_000_000.0,
             remaining_100_percent=9_000_000.0,
             capacity_utilization_100_percent=0.2),
        dict(initial_capacity_100_percent=10_000_000.0,
             available_before_100_percent=9_000_000.0,
             consumed_100_percent=3_000_000.0,
             reinstated_100_percent=0.0,
             remaining_100_percent=6_000_000.0,
             capacity_utilization_100_percent=0.5),
    )

    scaled = [scale_payable_capacity(**event, shares=shares) for event in events]

    for source, result in zip(events, scaled, strict=True):
        assert result.initial_capacity == pytest.approx(
            source["initial_capacity_100_percent"] * factor
        )
        assert result.available_before == pytest.approx(
            source["available_before_100_percent"] * factor
        )
        assert result.consumed == pytest.approx(
            source["consumed_100_percent"] * factor
        )
        assert result.reinstated == pytest.approx(
            source["reinstated_100_percent"] * factor
        )
        assert result.remaining == pytest.approx(
            source["remaining_100_percent"] * factor
        )
        assert result.capacity_utilization == (
            source["capacity_utilization_100_percent"]
        )


@pytest.mark.parametrize(
    ("case_id", "shares"),
    [
        ("G15", TreatyShares(0.0, 1.0)),
        ("G16", TreatyShares(1.0, 0.0)),
    ],
)
def test_g15_g16_zero_capacity_is_explicitly_not_applicable(
    case_id: str,
    shares: TreatyShares,
) -> None:
    result = scale_payable_capacity(
        initial_capacity_100_percent=10_000_000.0,
        available_before_100_percent=8_000_000.0,
        consumed_100_percent=2_000_000.0,
        reinstated_100_percent=0.0,
        remaining_100_percent=6_000_000.0,
        capacity_utilization_100_percent=0.4,
        shares=shares,
    )

    assert case_id in {"G15", "G16"}
    assert result.initial_capacity == 0.0
    assert result.consumed == 0.0
    assert result.capacity_utilization is None
    assert result.capacity_utilization_status is (
        CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
    )


def test_golden_case_milestone_traceability_is_complete() -> None:
    milestones = {
        "G01": "CT1", "G02": "CT1", "G03": "CT1", "G04": "CT1",
        "G05": "CT1", "G06": "CT1", "G07": "CT3", "G08": "CT3",
        "G09": "CT3", "G10": "CT2/CT3", "G11": "CT4", "G12": "CT6",
        "G13": "CT0 occurrence-election scenario", "G14": "CT1",
        "G15": "CT1", "G16": "CT1",
    }

    assert set(milestones) == {f"G{number:02d}" for number in range(1, 17)}
