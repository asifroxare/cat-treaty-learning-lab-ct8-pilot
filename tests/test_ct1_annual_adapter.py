"""CT1 annual-trial compatibility adapter tests."""

from dataclasses import dataclass, replace
import math
from types import SimpleNamespace

import pytest

from cat_treaty.adapter import adapt_treaty_year_record
from cat_treaty.models import CapacityBasis, SettlementMode, TreatyShares


@dataclass(frozen=True, slots=True)
class TreatyYearFixture:
    year: int = 1
    event_count: int = 3
    qualifying_event_count: int = 2
    gross_annual_loss: float = 8_000_000.0
    largest_gross_event_loss: float = 4_000_000.0
    total_annual_recovery: float = 3_000_000.0
    net_annual_loss: float = 5_000_000.0
    reinstatements_used: float = 0.6
    total_reinstatement_premium: float | None = None
    maximum_occurrence_recovery: float = 2_000_000.0
    layer_attached: bool = True
    layer_exhausted: bool = False


BASE_YEAR = TreatyYearFixture()


def test_default_mapping_preserves_annual_identity() -> None:
    result = adapt_treaty_year_record(BASE_YEAR)

    assert result.annual_trial_id == 1
    assert result.event_count == 3
    assert result.qualifying_event_count == 2
    assert result.gross_annual_loss == 8_000_000.0
    assert result.largest_gross_event_loss == 4_000_000.0
    assert result.gross_contractual_recovery == 3_000_000.0
    assert result.net_subject_loss == 5_000_000.0
    assert result.reinstatements_used == 0.6
    assert result.maximum_occurrence_recovery == 2_000_000.0
    assert result.layer_attached is True
    assert result.layer_exhausted is False
    assert result.reinstatement_premium_payable is None
    assert result.settlement is None
    assert result.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE


def test_nondefault_shares_scale_recovery_and_recalculate_net() -> None:
    result = adapt_treaty_year_record(
        BASE_YEAR,
        shares=TreatyShares(0.9, 0.75),
    )
    factor = 0.675

    assert result.gross_annual_loss == 8_000_000.0
    assert result.gross_contractual_recovery == pytest.approx(
        3_000_000.0 * factor
    )
    assert result.maximum_occurrence_recovery == pytest.approx(
        2_000_000.0 * factor
    )
    assert result.net_subject_loss == pytest.approx(
        8_000_000.0 - 3_000_000.0 * factor
    )
    assert result.reinstatements_used == 0.6


def test_finalized_annual_premium_creates_settlement() -> None:
    result = adapt_treaty_year_record(
        replace(BASE_YEAR, total_reinstatement_premium=60_000.0),
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert result.reinstatement_premium_payable == 60_000.0
    assert result.settlement is not None
    assert result.settlement.gross_contractual_recovery == 3_000_000.0
    assert result.settlement.net_cash_settlement == 2_940_000.0


def test_annual_premium_scales_with_fixed_shares() -> None:
    result = adapt_treaty_year_record(
        replace(BASE_YEAR, total_reinstatement_premium=60_000.0),
        shares=TreatyShares(0.9, 0.75),
    )

    assert result.reinstatement_premium_payable == pytest.approx(40_500.0)
    assert result.settlement is not None
    assert result.settlement.net_cash_settlement == pytest.approx(2_025_000.0)


@pytest.mark.parametrize(
    "shares",
    [TreatyShares(0.0, 1.0), TreatyShares(1.0, 0.0)],
)
def test_zero_share_has_zero_recovery_and_full_net_loss(
    shares: TreatyShares,
) -> None:
    result = adapt_treaty_year_record(
        replace(BASE_YEAR, total_reinstatement_premium=60_000.0),
        shares=shares,
    )

    assert result.gross_contractual_recovery == 0.0
    assert result.maximum_occurrence_recovery == 0.0
    assert result.reinstatement_premium_payable == 0.0
    assert result.net_subject_loss == BASE_YEAR.gross_annual_loss


def test_settlement_mode_changes_cash_only() -> None:
    source = replace(BASE_YEAR, total_reinstatement_premium=60_000.0)
    separately = adapt_treaty_year_record(source)
    deducted = adapt_treaty_year_record(
        source,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert separately.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert separately.net_subject_loss == deducted.net_subject_loss
    assert separately.reinstatements_used == deducted.reinstatements_used
    assert separately.reinstatement_premium_payable == deducted.reinstatement_premium_payable
    assert separately.settlement is not None
    assert deducted.settlement is not None
    assert separately.settlement.net_cash_settlement == 3_000_000.0
    assert deducted.settlement.net_cash_settlement == 2_940_000.0


@pytest.mark.parametrize(
    "missing_field",
    list(BASE_YEAR.__dataclass_fields__),
)
def test_missing_annual_source_field_is_rejected(missing_field: str) -> None:
    values = {
        field_name: getattr(BASE_YEAR, field_name)
        for field_name in BASE_YEAR.__dataclass_fields__
    }
    del values[missing_field]

    with pytest.raises(
        TypeError,
        match=f"missing required field: {missing_field}",
    ):
        adapt_treaty_year_record(SimpleNamespace(**values))


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("year", 0),
        ("event_count", -1),
        ("event_count", True),
        ("qualifying_event_count", -1),
        ("qualifying_event_count", 4),
        ("gross_annual_loss", -1.0),
        ("gross_annual_loss", math.nan),
        ("largest_gross_event_loss", -1.0),
        ("total_annual_recovery", -1.0),
        ("net_annual_loss", -1.0),
        ("reinstatements_used", -1.0),
        ("maximum_occurrence_recovery", -1.0),
        ("layer_attached", 1),
        ("layer_exhausted", 0),
    ],
)
def test_invalid_annual_source_value_is_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    with pytest.raises(ValueError):
        adapt_treaty_year_record(
            replace(BASE_YEAR, **{field_name: invalid_value})
        )


def test_source_annual_net_loss_must_reconcile() -> None:
    with pytest.raises(ValueError, match="net_annual_loss"):
        adapt_treaty_year_record(
            replace(BASE_YEAR, net_annual_loss=4_900_000.0)
        )


def test_maximum_recovery_cannot_exceed_total_recovery() -> None:
    with pytest.raises(ValueError, match="maximum_occurrence_recovery"):
        adapt_treaty_year_record(
            replace(BASE_YEAR, maximum_occurrence_recovery=3_100_000.0)
        )


def test_largest_event_cannot_exceed_annual_gross_loss() -> None:
    with pytest.raises(ValueError, match="largest_gross_event_loss"):
        adapt_treaty_year_record(
            replace(BASE_YEAR, largest_gross_event_loss=8_100_000.0)
        )
