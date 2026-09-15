"""F19-F24 hand-worked empirical-tail and credibility tests."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct4_models import (
    CT4AnnualTrialInput,
    CT4TailAnalytics,
    MetricPerspective,
    RatioStatus,
    TailConfiguration,
    TailWarningCode,
)
from cat_treaty.simulation import apply_catalogue_simulation
from cat_treaty.tail import (
    calculate_tail_analytics,
    empirical_exceedance_curve,
    empirical_tvar,
    nearest_rank_quantile,
    return_period_warnings,
)
from tests.test_ct4_simulation import catalogue, event


def test_g38_f21_nearest_rank_has_no_interpolation() -> None:
    sample = (0.0, 10.0, 20.0, 30.0)
    assert nearest_rank_quantile(sample, 0.25) == 0.0
    assert nearest_rank_quantile(sample, 0.50) == 10.0
    assert nearest_rank_quantile(sample, 0.95) == 30.0


def test_f21_validates_sample_and_probability_boundaries() -> None:
    for probability in (0.0, 1.0, math.nan, math.inf):
        with pytest.raises(ValueError):
            nearest_rank_quantile((1.0,), probability)
    for sample in ((), (-1.0,), (math.nan,), (True,)):
        with pytest.raises(ValueError):
            nearest_rank_quantile(sample, 0.5)  # type: ignore[arg-type]


def test_f22_curve_uses_r_over_y_and_retains_duplicate_losses() -> None:
    curve = empirical_exceedance_curve((10.0, 30.0, 30.0, 0.0))
    assert tuple((item.rank, item.loss, item.exceedance_probability) for item in curve) == (
        (1, 30.0, 0.25),
        (2, 30.0, 0.50),
        (3, 10.0, 0.75),
        (4, 0.0, 1.0),
    )


def test_g39_f23_includes_quantile_observation_and_all_larger_values() -> None:
    sample = (0.0, 10.0, 20.0, 30.0)
    assert empirical_tvar(sample, 0.50) == 20.0
    assert empirical_tvar(sample, 0.75) == 25.0
    assert empirical_tvar(sample, 0.99) == 30.0


@pytest.mark.parametrize(
    ("trial_count", "period", "expected"),
    [
        (200, 10.0, ()),
        (100, 5.0, ()),
        (100, 10.0, (TailWarningCode.LIMITED_TAIL_CREDIBILITY,)),
        (100, 20.0, (TailWarningCode.LIMITED_TAIL_CREDIBILITY,)),
        (
            100,
            25.0,
            (
                TailWarningCode.LIMITED_TAIL_CREDIBILITY,
                TailWarningCode.SEVERE_TAIL_CREDIBILITY_WARNING,
            ),
        ),
        (
            100,
            200.0,
            (
                TailWarningCode.LIMITED_TAIL_CREDIBILITY,
                TailWarningCode.SEVERE_TAIL_CREDIBILITY_WARNING,
                TailWarningCode.RETURN_PERIOD_EXCEEDS_SAMPLE,
            ),
        ),
    ],
)
def test_credibility_thresholds_are_strict_and_cumulative(
    trial_count: int,
    period: float,
    expected: tuple[TailWarningCode, ...],
) -> None:
    warnings = return_period_warnings(trial_count, period)
    assert tuple(item.code for item in warnings) == expected
    assert all(item.observations_per_return_period == trial_count / period for item in warnings)


def test_credibility_validation_rejects_invalid_denominators() -> None:
    for count, period in ((0, 10.0), (True, 10.0), (100, 1.0), (100, math.inf)):
        with pytest.raises(ValueError):
            return_period_warnings(count, period)  # type: ignore[arg-type]


def test_f19_f24_three_perspectives_and_aal_reconciliation() -> None:
    request = catalogue(
        CT4AnnualTrialInput(1, "T1", ()),
        CT4AnnualTrialInput(2, "T2", (event("E2", 5_000_000.0, trial_id=2),)),
        CT4AnnualTrialInput(3, "T3", (event("E3", 45_000_000.0, trial_id=3),)),
        CT4AnnualTrialInput(4, "T4", (event("E4", 80_000_000.0, trial_id=4),)),
    )
    analytics = calculate_tail_analytics(apply_catalogue_simulation(request))

    assert isinstance(analytics, CT4TailAnalytics)
    assert tuple(item.perspective for item in analytics.perspectives) == tuple(MetricPerspective)
    subject, recovery, net = analytics.perspectives
    assert subject.aep_sample == (0.0, 5_000_000.0, 45_000_000.0, 80_000_000.0)
    assert recovery.aep_sample == (0.0, 0.0, 35_000_000.0, 50_000_000.0)
    assert net.aep_sample == (0.0, 5_000_000.0, 10_000_000.0, 30_000_000.0)
    assert subject.annual_average_loss == 32_500_000.0
    assert recovery.annual_average_loss == 21_250_000.0
    assert net.annual_average_loss == 11_250_000.0
    assert analytics.aal_reconciliation_passed is True
    expected_std = math.sqrt(
        sum((value - 32_500_000.0) ** 2 for value in subject.aep_sample) / 4
    )
    assert subject.population_standard_deviation == expected_std
    assert subject.coefficient_of_variation == expected_std / 32_500_000.0
    assert subject.coefficient_status is RatioStatus.APPLICABLE


def test_tail_response_contains_both_oep_and_aep_return_period_series() -> None:
    request = catalogue(
        CT4AnnualTrialInput(
            1,
            "T1",
            (
                event("E1A", 45_000_000.0, event_time=1.0),
                event("E1B", 45_000_000.0, event_time=2.0),
            ),
        ),
        CT4AnnualTrialInput(2, "T2", ()),
    )
    config = TailConfiguration(
        probability_levels=(0.5,),
        tvar_levels=(0.5,),
        return_periods=(2.0, 5.0),
    )
    request = replace(request, tail_configuration=config)
    subject = calculate_tail_analytics(
        apply_catalogue_simulation(request)
    ).perspectives[0]

    assert tuple(item.value for item in subject.oep_return_period_estimates) == (0.0, 45_000_000.0)
    assert tuple(item.value for item in subject.aep_return_period_estimates) == (0.0, 90_000_000.0)
    assert subject.return_period_estimates == subject.aep_return_period_estimates
    assert subject.var_estimates[0].value == 0.0
    assert subject.tvar_estimates[0].value == 45_000_000.0
    assert subject.oep_var_estimates[0].value == 0.0
    assert subject.aep_var_estimates == subject.var_estimates
    assert subject.oep_tvar_estimates[0].value == 22_500_000.0
    assert subject.aep_tvar_estimates == subject.tvar_estimates
    assert len(subject.oep_curve) == len(subject.aep_curve) == 2


def test_all_zero_perspective_has_null_cv_not_fabricated_zero() -> None:
    request = catalogue(
        CT4AnnualTrialInput(1, "T1", ()),
        CT4AnnualTrialInput(2, "T2", ()),
    )
    perspectives = calculate_tail_analytics(
        apply_catalogue_simulation(request)
    ).perspectives
    assert all(item.annual_average_loss == 0.0 for item in perspectives)
    assert all(item.population_standard_deviation == 0.0 for item in perspectives)
    assert all(item.coefficient_of_variation is None for item in perspectives)
    assert all(item.coefficient_status is RatioStatus.NOT_APPLICABLE_ZERO_MEAN for item in perspectives)


def test_tail_analytics_are_deterministic_and_immutable() -> None:
    result = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "T1", (event("E1", 45_000_000.0),)))
    )
    first = calculate_tail_analytics(result)
    second = calculate_tail_analytics(result)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.aal_reconciliation_passed = False  # type: ignore[misc]


def test_tail_entry_requires_completed_catalogue_result() -> None:
    with pytest.raises(TypeError, match="CT4CatalogueResult"):
        calculate_tail_analytics({})  # type: ignore[arg-type]
