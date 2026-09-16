"""CT5 F31 three-way settlement tests."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct5_models import CT5Settlement
from cat_treaty.ct5_settlement import calculate_ct5_settlement
from cat_treaty.models import SettlementMode
from cat_treaty.reinstatement import calculate_reinstatement_premium
from tests.test_ct5_models import layer_terms
from tests.test_ct5_reinstatement import transition_for


def test_paid_separately_is_the_default() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=20.0,
        reinstatement_premium_payable=2.0,
    )
    assert result == CT5Settlement(
        gross_contractual_recovery=20.0,
        reinstatement_premium_payable=2.0,
        net_cash_settlement=20.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )


def test_deducted_mode_subtracts_premium_once() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=20.0,
        reinstatement_premium_payable=2.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    assert result.net_cash_settlement == 18.0


def test_g65_negative_cash_settlement_is_valid_and_unfloored() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=1.0,
        reinstatement_premium_payable=1.5,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    assert result.net_cash_settlement == -0.5


def test_switching_mode_changes_only_net_cash_settlement() -> None:
    separate = calculate_ct5_settlement(
        gross_contractual_recovery=10.0,
        reinstatement_premium_payable=3.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )
    deducted = calculate_ct5_settlement(
        gross_contractual_recovery=10.0,
        reinstatement_premium_payable=3.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    assert separate.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert separate.reinstatement_premium_payable == deducted.reinstatement_premium_payable
    assert separate.net_cash_settlement == 10.0
    assert deducted.net_cash_settlement == 7.0


def test_g56_modes_do_not_change_capacity_tranches_or_f30_premium() -> None:
    terms = layer_terms()
    transition = transition_for(10.0, terms=terms)
    premium = calculate_reinstatement_premium(
        transition=transition,
        terms=terms,
        event_time=100.0,
    )
    state_before = transition.state_after
    allocations_before = premium.tranche_allocations
    separate = calculate_ct5_settlement(
        gross_contractual_recovery=transition.gross_contractual_recovery,
        reinstatement_premium_payable=premium.reinstatement_premium_payable,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )
    deducted = calculate_ct5_settlement(
        gross_contractual_recovery=transition.gross_contractual_recovery,
        reinstatement_premium_payable=premium.reinstatement_premium_payable,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    assert transition.state_after == state_before
    assert premium.tranche_allocations == allocations_before
    assert separate.gross_contractual_recovery == deducted.gross_contractual_recovery
    assert separate.reinstatement_premium_payable == deducted.reinstatement_premium_payable


def test_zero_recovery_and_zero_premium_are_valid() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=0.0,
        reinstatement_premium_payable=0.0,
    )
    assert result.net_cash_settlement == 0.0


def test_zero_recovery_can_have_negative_deducted_cash() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=0.0,
        reinstatement_premium_payable=2.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    assert result.net_cash_settlement == -2.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("gross_contractual_recovery", -1.0),
        ("gross_contractual_recovery", math.nan),
        ("gross_contractual_recovery", math.inf),
        ("gross_contractual_recovery", True),
        ("gross_contractual_recovery", "10"),
        ("reinstatement_premium_payable", -1.0),
        ("reinstatement_premium_payable", math.nan),
        ("reinstatement_premium_payable", math.inf),
        ("reinstatement_premium_payable", False),
        ("reinstatement_premium_payable", "2"),
    ],
)
def test_invalid_authoritative_values_are_rejected(field: str, value: object) -> None:
    values: dict[str, object] = {
        "gross_contractual_recovery": 10.0,
        "reinstatement_premium_payable": 2.0,
    }
    values[field] = value
    with pytest.raises(ValueError):
        calculate_ct5_settlement(**values)  # type: ignore[arg-type]


def test_raw_string_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="SettlementMode"):
        calculate_ct5_settlement(
            gross_contractual_recovery=10.0,
            reinstatement_premium_payable=2.0,
            settlement_mode="deducted_from_settlement",  # type: ignore[arg-type]
        )


def test_settlement_result_is_immutable() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=10.0,
        reinstatement_premium_payable=2.0,
    )
    with pytest.raises(FrozenInstanceError):
        result.net_cash_settlement = 8.0  # type: ignore[misc]


def test_model_rejects_inconsistent_mode_equation() -> None:
    result = calculate_ct5_settlement(
        gross_contractual_recovery=10.0,
        reinstatement_premium_payable=2.0,
    )
    with pytest.raises(ValueError, match="F31"):
        replace(result, net_cash_settlement=8.0)


def test_ct5_settlement_does_not_import_capacity_or_pricing_engines() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(Path("cat_treaty/ct5_settlement.py").read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "cat_treaty.annual_capacity" not in imports
    assert "cat_treaty.reinstatement" not in imports


def test_ct5_settlement_public_export() -> None:
    import cat_treaty

    assert "calculate_ct5_settlement" in cat_treaty.__all__
    assert cat_treaty.calculate_ct5_settlement is calculate_ct5_settlement
