"""CT1 pricing numerical-identity adapter tests."""

from dataclasses import dataclass, replace
import math
from types import SimpleNamespace

import pytest

from cat_treaty.adapter import adapt_pricing_result


@dataclass(frozen=True, slots=True)
class ComponentsFixture:
    pure_premium: float = 1_000_000.0
    risk_loading: float = 200_000.0
    expense_loading: float = 50_000.0
    capital_loading: float = 100_000.0
    pre_profit_subtotal: float = 1_350_000.0
    profit_loading: float = 135_000.0
    original_technical_premium: float = 1_485_000.0


@dataclass(frozen=True, slots=True)
class MetricsFixture:
    premium: float
    rate_on_line: float
    payback_period: float | None
    expected_loss_ratio: float | None
    commercial_rate_on_epi: float | None


@dataclass(frozen=True, slots=True)
class ViewFixture:
    name: str
    original: MetricsFixture
    expected_reinstatement_premium: float
    expected_all_in: MetricsFixture
    reinstatement_premium_basis: str = "original_technical_premium"


@dataclass(frozen=True, slots=True)
class PricingResultFixture:
    components: ComponentsFixture
    expected_reinstatement_premium: float
    expected_all_in_premium: float
    technical: ViewFixture
    target_rol: ViewFixture | None
    target_payback: ViewFixture | None


ORIGINAL_METRICS = MetricsFixture(
    premium=1_485_000.0,
    rate_on_line=0.297,
    payback_period=3.367003367,
    expected_loss_ratio=0.6734006734,
    commercial_rate_on_epi=0.01485,
)
ALL_IN_METRICS = MetricsFixture(
    premium=1_545_000.0,
    rate_on_line=0.309,
    payback_period=3.236245955,
    expected_loss_ratio=0.6472491909,
    commercial_rate_on_epi=0.01545,
)
TECHNICAL_VIEW = ViewFixture(
    name="technical",
    original=ORIGINAL_METRICS,
    expected_reinstatement_premium=60_000.0,
    expected_all_in=ALL_IN_METRICS,
)
BASE_PRICING = PricingResultFixture(
    components=ComponentsFixture(),
    expected_reinstatement_premium=60_000.0,
    expected_all_in_premium=1_545_000.0,
    technical=TECHNICAL_VIEW,
    target_rol=None,
    target_payback=None,
)


def test_pricing_components_map_without_numerical_change() -> None:
    result = adapt_pricing_result(BASE_PRICING)

    assert result.components.pure_premium == 1_000_000.0
    assert result.components.risk_loading == 200_000.0
    assert result.components.expense_loading == 50_000.0
    assert result.components.capital_loading == 100_000.0
    assert result.components.pre_profit_subtotal == 1_350_000.0
    assert result.components.profit_loading == 135_000.0
    assert result.components.original_technical_premium == 1_485_000.0


def test_top_level_pricing_identity_is_preserved() -> None:
    result = adapt_pricing_result(BASE_PRICING)

    assert result.expected_reinstatement_premium == 60_000.0
    assert result.expected_all_in_premium == 1_545_000.0
    assert result.technical.name == "technical"
    assert result.technical.reinstatement_premium_basis == (
        "original_technical_premium"
    )


def test_original_and_all_in_metrics_remain_separate() -> None:
    result = adapt_pricing_result(BASE_PRICING)

    assert result.technical.original.premium == 1_485_000.0
    assert result.technical.original.expected_loss_ratio == pytest.approx(
        0.6734006734
    )
    assert result.technical.expected_all_in.premium == 1_545_000.0
    assert result.technical.expected_all_in.expected_loss_ratio == pytest.approx(
        0.6472491909
    )


def test_optional_target_views_are_preserved() -> None:
    target = replace(TECHNICAL_VIEW, name="target_rol")
    result = adapt_pricing_result(
        replace(BASE_PRICING, target_rol=target, target_payback=target)
    )

    assert result.target_rol is not None
    assert result.target_rol.name == "target_rol"
    assert result.target_payback is not None
    assert result.target_payback.name == "target_rol"


def test_optional_metric_values_remain_none() -> None:
    metrics = replace(
        ORIGINAL_METRICS,
        payback_period=None,
        expected_loss_ratio=None,
        commercial_rate_on_epi=None,
    )
    view = replace(TECHNICAL_VIEW, original=metrics)
    result = adapt_pricing_result(replace(BASE_PRICING, technical=view))

    assert result.technical.original.payback_period is None
    assert result.technical.original.expected_loss_ratio is None
    assert result.technical.original.commercial_rate_on_epi is None


def test_source_pricing_object_is_not_mutated() -> None:
    adapt_pricing_result(BASE_PRICING)

    assert BASE_PRICING.components == ComponentsFixture()
    assert BASE_PRICING.technical == TECHNICAL_VIEW


@pytest.mark.parametrize(
    "missing_field",
    [
        "components",
        "expected_reinstatement_premium",
        "expected_all_in_premium",
        "technical",
        "target_rol",
        "target_payback",
    ],
)
def test_missing_pricing_result_field_is_rejected(missing_field: str) -> None:
    values = {
        field_name: getattr(BASE_PRICING, field_name)
        for field_name in BASE_PRICING.__dataclass_fields__
    }
    del values[missing_field]

    with pytest.raises(TypeError, match=f"missing required field: {missing_field}"):
        adapt_pricing_result(SimpleNamespace(**values))


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("pure_premium", -1.0),
        ("risk_loading", math.nan),
        ("expense_loading", math.inf),
        ("capital_loading", True),
        ("pre_profit_subtotal", -1.0),
        ("profit_loading", -1.0),
        ("original_technical_premium", -1.0),
    ],
)
def test_invalid_component_value_is_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    components = replace(ComponentsFixture(), **{field_name: invalid_value})

    with pytest.raises(ValueError):
        adapt_pricing_result(replace(BASE_PRICING, components=components))


@pytest.mark.parametrize(
    "invalid_value",
    [-1.0, math.nan, math.inf, True],
)
def test_invalid_expected_reinstatement_premium_is_rejected(
    invalid_value: object,
) -> None:
    with pytest.raises(ValueError):
        adapt_pricing_result(
            replace(BASE_PRICING, expected_reinstatement_premium=invalid_value)
        )


def test_expected_all_in_premium_must_reconcile() -> None:
    with pytest.raises(ValueError, match="expected_all_in_premium"):
        adapt_pricing_result(
            replace(BASE_PRICING, expected_all_in_premium=1_500_000.0)
        )


def test_view_expected_reinstatement_premium_must_reconcile() -> None:
    bad_view = replace(
        TECHNICAL_VIEW,
        expected_reinstatement_premium=50_000.0,
        expected_all_in=replace(
            ALL_IN_METRICS,
            premium=1_535_000.0,
        ),
    )

    with pytest.raises(ValueError, match="expected_reinstatement_premium"):
        adapt_pricing_result(replace(BASE_PRICING, technical=bad_view))


def test_all_in_view_premium_must_reconcile() -> None:
    bad_metrics = replace(ALL_IN_METRICS, premium=1_500_000.0)
    bad_view = replace(TECHNICAL_VIEW, expected_all_in=bad_metrics)

    with pytest.raises(ValueError, match="expected_all_in"):
        adapt_pricing_result(replace(BASE_PRICING, technical=bad_view))
