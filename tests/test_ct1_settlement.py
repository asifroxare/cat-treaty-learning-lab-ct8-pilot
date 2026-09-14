"""CT1 three-way settlement and presentation-invariant tests."""

import math

import pytest

from cat_treaty.models import SettlementBreakdown, SettlementMode
from cat_treaty.settlement import calculate_settlement


def test_default_mode_pays_reinstatement_premium_separately() -> None:
    result = calculate_settlement(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
    )

    assert result == SettlementBreakdown(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
        net_cash_settlement=500_000.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )


def test_advanced_mode_deducts_premium_from_settlement() -> None:
    result = calculate_settlement(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert result.net_cash_settlement == 475_000.0


def test_presentation_mode_changes_net_cash_only() -> None:
    separately = calculate_settlement(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )
    deducted = calculate_settlement(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert (
        separately.gross_contractual_recovery
        == deducted.gross_contractual_recovery
    )
    assert (
        separately.reinstatement_premium_payable
        == deducted.reinstatement_premium_payable
    )
    assert separately.net_cash_settlement == 500_000.0
    assert deducted.net_cash_settlement == 475_000.0


def test_deduction_mode_does_not_clamp_negative_cash() -> None:
    result = calculate_settlement(
        gross_contractual_recovery=10_000.0,
        reinstatement_premium_payable=15_000.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert result.net_cash_settlement == -5_000.0


def test_zero_values_are_supported() -> None:
    result = calculate_settlement(
        gross_contractual_recovery=0.0,
        reinstatement_premium_payable=0.0,
    )

    assert result.gross_contractual_recovery == 0.0
    assert result.reinstatement_premium_payable == 0.0
    assert result.net_cash_settlement == 0.0


def test_paid_separately_preserves_gross_value_without_rounding() -> None:
    gross = 1_234_567.8901234567

    result = calculate_settlement(
        gross_contractual_recovery=gross,
        reinstatement_premium_payable=12_345.6789012345,
    )

    assert result.gross_contractual_recovery.hex() == gross.hex()
    assert result.net_cash_settlement.hex() == gross.hex()


@pytest.mark.parametrize(
    "invalid_recovery",
    [-1.0, math.nan, math.inf, -math.inf, True, "500000"],
)
def test_invalid_gross_contractual_recovery_is_rejected(
    invalid_recovery: object,
) -> None:
    with pytest.raises(ValueError):
        calculate_settlement(
            gross_contractual_recovery=invalid_recovery,
            reinstatement_premium_payable=0.0,
        )


@pytest.mark.parametrize(
    "invalid_premium",
    [-1.0, math.nan, math.inf, -math.inf, True, "25000"],
)
def test_invalid_reinstatement_premium_is_rejected(
    invalid_premium: object,
) -> None:
    with pytest.raises(ValueError):
        calculate_settlement(
            gross_contractual_recovery=500_000.0,
            reinstatement_premium_payable=invalid_premium,
        )


@pytest.mark.parametrize(
    "invalid_mode",
    ["paid_separately", "unknown", None, True],
)
def test_settlement_mode_must_be_explicit_enum(
    invalid_mode: object,
) -> None:
    with pytest.raises(ValueError, match="settlement_mode"):
        calculate_settlement(
            gross_contractual_recovery=500_000.0,
            reinstatement_premium_payable=25_000.0,
            settlement_mode=invalid_mode,
        )
