"""CT1 processed-recovery compatibility adapter tests."""

from dataclasses import dataclass, replace
import math
from types import SimpleNamespace

import pytest

from cat_treaty.adapter import adapt_processed_event_record
from cat_treaty.models import (
    CapacityBasis,
    SettlementMode,
    TreatyShares,
)


@dataclass(frozen=True, slots=True)
class ProcessedPricingEventFixture:
    """Structural equivalent of cat_xol.models.ProcessedEventRecord."""

    year: int = 1
    event_id: str = "EVT-0001"
    event_time: float = 25.0
    event_sequence: int = 1
    peril: str = "hurricane"
    region: str = "gulf_coast"
    risks_affected: int = 12
    gross_event_loss: float = 2_500_000.0
    qualifies_under_two_risk_warranty: bool = True
    occurrence_recovery_before_capacity_constraint: float = 1_500_000.0
    capacity_before_event: float = 5_000_000.0
    actual_treaty_recovery: float = 1_500_000.0
    capacity_consumed: float = 1_500_000.0
    remaining_capacity_before_reinstatement: float = 3_500_000.0
    amount_reinstated: float = 1_500_000.0
    reinstatement_premium: float | None = None
    capacity_available_for_next_event: float = 5_000_000.0
    reinstatements_remaining: float = 0.7
    net_event_loss: float = 1_000_000.0


BASE_EVENT = ProcessedPricingEventFixture()


def test_default_shares_preserve_source_recovery_and_capacity() -> None:
    result = adapt_processed_event_record(BASE_EVENT)

    assert result.event.annual_trial_id == BASE_EVENT.year
    assert result.event.subject_loss == BASE_EVENT.gross_event_loss
    assert result.covered_loss_before_capacity_100_percent == 1_500_000.0
    assert result.payable_recovery_before_capacity_constraint == 1_500_000.0
    assert result.gross_contractual_recovery == 1_500_000.0
    assert result.capacity_before_event == 5_000_000.0
    assert result.capacity_consumed == 1_500_000.0
    assert result.remaining_capacity_before_reinstatement == 3_500_000.0
    assert result.amount_reinstated == 1_500_000.0
    assert result.capacity_available_for_next_event == 5_000_000.0
    assert result.reinstatements_remaining == 0.7
    assert result.net_subject_loss == 1_000_000.0
    assert result.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE
    assert result.settlement is None


def test_nondefault_shares_scale_all_payable_monetary_fields() -> None:
    result = adapt_processed_event_record(
        BASE_EVENT,
        shares=TreatyShares(0.9, 0.75),
    )
    factor = 0.675

    assert result.covered_loss_before_capacity_100_percent == 1_500_000.0
    assert result.payable_recovery_before_capacity_constraint == pytest.approx(
        1_500_000.0 * factor
    )
    assert result.gross_contractual_recovery == pytest.approx(
        1_500_000.0 * factor
    )
    assert result.capacity_before_event == pytest.approx(5_000_000.0 * factor)
    assert result.capacity_consumed == pytest.approx(1_500_000.0 * factor)
    assert result.remaining_capacity_before_reinstatement == pytest.approx(
        3_500_000.0 * factor
    )
    assert result.amount_reinstated == pytest.approx(1_500_000.0 * factor)
    assert result.capacity_available_for_next_event == pytest.approx(
        5_000_000.0 * factor
    )
    assert result.reinstatements_remaining == 0.7
    assert result.net_subject_loss == pytest.approx(
        2_500_000.0 - 1_500_000.0 * factor
    )


def test_unfinalized_reinstatement_premium_has_no_settlement() -> None:
    result = adapt_processed_event_record(
        replace(BASE_EVENT, reinstatement_premium=None)
    )

    assert result.reinstatement_premium_payable is None
    assert result.settlement is None


def test_finalized_premium_creates_paid_separately_settlement() -> None:
    result = adapt_processed_event_record(
        replace(BASE_EVENT, reinstatement_premium=30_000.0)
    )

    assert result.reinstatement_premium_payable == 30_000.0
    assert result.settlement is not None
    assert result.settlement.gross_contractual_recovery == 1_500_000.0
    assert result.settlement.reinstatement_premium_payable == 30_000.0
    assert result.settlement.net_cash_settlement == 1_500_000.0
    assert result.settlement.settlement_mode is SettlementMode.PAID_SEPARATELY


def test_finalized_premium_and_recovery_share_scale_together() -> None:
    result = adapt_processed_event_record(
        replace(BASE_EVENT, reinstatement_premium=30_000.0),
        shares=TreatyShares(0.9, 0.75),
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    factor = 0.675

    assert result.reinstatement_premium_payable == pytest.approx(
        30_000.0 * factor
    )
    assert result.settlement is not None
    assert result.settlement.gross_contractual_recovery == pytest.approx(
        1_500_000.0 * factor
    )
    assert result.settlement.net_cash_settlement == pytest.approx(
        (1_500_000.0 - 30_000.0) * factor
    )


def test_settlement_mode_does_not_change_recovery_or_capacity() -> None:
    source = replace(BASE_EVENT, reinstatement_premium=30_000.0)
    separately = adapt_processed_event_record(
        source,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )
    deducted = adapt_processed_event_record(
        source,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert separately.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert separately.capacity_consumed == deducted.capacity_consumed
    assert separately.amount_reinstated == deducted.amount_reinstated
    assert (
        separately.capacity_available_for_next_event
        == deducted.capacity_available_for_next_event
    )
    assert separately.reinstatement_premium_payable == deducted.reinstatement_premium_payable
    assert separately.settlement is not None
    assert deducted.settlement is not None
    assert separately.settlement.net_cash_settlement == 1_500_000.0
    assert deducted.settlement.net_cash_settlement == 1_470_000.0


@pytest.mark.parametrize(
    "shares",
    [TreatyShares(0.0, 1.0), TreatyShares(1.0, 0.0)],
)
def test_zero_share_produces_zero_payable_ledger(
    shares: TreatyShares,
) -> None:
    result = adapt_processed_event_record(
        replace(BASE_EVENT, reinstatement_premium=30_000.0),
        shares=shares,
    )

    assert result.payable_recovery_before_capacity_constraint == 0.0
    assert result.gross_contractual_recovery == 0.0
    assert result.capacity_before_event == 0.0
    assert result.capacity_consumed == 0.0
    assert result.remaining_capacity_before_reinstatement == 0.0
    assert result.amount_reinstated == 0.0
    assert result.capacity_available_for_next_event == 0.0
    assert result.reinstatement_premium_payable == 0.0
    assert result.net_subject_loss == BASE_EVENT.gross_event_loss


def test_source_object_is_not_mutated() -> None:
    source = replace(BASE_EVENT, reinstatement_premium=30_000.0)

    adapt_processed_event_record(source, shares=TreatyShares(0.9, 0.75))

    assert source == replace(BASE_EVENT, reinstatement_premium=30_000.0)


@pytest.mark.parametrize(
    "missing_field",
    [
        "qualifies_under_two_risk_warranty",
        "occurrence_recovery_before_capacity_constraint",
        "capacity_before_event",
        "actual_treaty_recovery",
        "capacity_consumed",
        "remaining_capacity_before_reinstatement",
        "amount_reinstated",
        "reinstatement_premium",
        "capacity_available_for_next_event",
        "reinstatements_remaining",
        "net_event_loss",
    ],
)
def test_missing_processed_source_field_is_rejected(
    missing_field: str,
) -> None:
    values = {
        field_name: getattr(BASE_EVENT, field_name)
        for field_name in BASE_EVENT.__dataclass_fields__
    }
    del values[missing_field]

    with pytest.raises(
        TypeError,
        match=f"missing required field: {missing_field}",
    ):
        adapt_processed_event_record(SimpleNamespace(**values))


def test_source_recovery_and_capacity_consumed_must_match() -> None:
    source = replace(BASE_EVENT, capacity_consumed=1_400_000.0)

    with pytest.raises(ValueError, match="capacity_consumed"):
        adapt_processed_event_record(source)


def test_source_net_event_loss_must_reconcile() -> None:
    source = replace(BASE_EVENT, net_event_loss=900_000.0)

    with pytest.raises(ValueError, match="net_event_loss"):
        adapt_processed_event_record(source)


@pytest.mark.parametrize(
    "field_name",
    [
        "occurrence_recovery_before_capacity_constraint",
        "capacity_before_event",
        "actual_treaty_recovery",
        "capacity_consumed",
        "remaining_capacity_before_reinstatement",
        "amount_reinstated",
        "capacity_available_for_next_event",
        "reinstatements_remaining",
        "net_event_loss",
    ],
)
@pytest.mark.parametrize("invalid_value", [-1.0, math.nan, math.inf, True])
def test_invalid_processed_monetary_or_ratio_value_is_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    source = replace(BASE_EVENT, **{field_name: invalid_value})

    with pytest.raises(ValueError):
        adapt_processed_event_record(source)


@pytest.mark.parametrize("invalid_premium", [-1.0, math.nan, math.inf, True])
def test_invalid_finalized_premium_is_rejected(
    invalid_premium: object,
) -> None:
    with pytest.raises(ValueError):
        adapt_processed_event_record(
            replace(BASE_EVENT, reinstatement_premium=invalid_premium)
        )


def test_two_risk_qualification_must_be_boolean() -> None:
    with pytest.raises(ValueError, match="qualifies_under_two_risk_warranty"):
        adapt_processed_event_record(
            replace(BASE_EVENT, qualifies_under_two_risk_warranty=1)
        )


def test_unfinalized_event_still_requires_valid_settlement_mode() -> None:
    with pytest.raises(ValueError, match="settlement_mode"):
        adapt_processed_event_record(
            BASE_EVENT,
            settlement_mode="paid_separately",
        )


def test_actual_recovery_cannot_exceed_unconstrained_recovery() -> None:
    source = replace(
        BASE_EVENT,
        occurrence_recovery_before_capacity_constraint=1_400_000.0,
    )

    with pytest.raises(ValueError, match="unconstrained recovery"):
        adapt_processed_event_record(source)


def test_reinstated_amount_cannot_exceed_actual_recovery() -> None:
    source = replace(
        BASE_EVENT,
        amount_reinstated=1_600_000.0,
        capacity_available_for_next_event=5_100_000.0,
    )

    with pytest.raises(ValueError, match="amount_reinstated"):
        adapt_processed_event_record(source)


def test_nonqualifying_event_must_have_zero_recovery() -> None:
    source = replace(
        BASE_EVENT,
        qualifies_under_two_risk_warranty=False,
    )

    with pytest.raises(ValueError, match="nonqualifying event"):
        adapt_processed_event_record(source)
