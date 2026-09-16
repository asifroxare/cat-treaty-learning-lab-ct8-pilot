"""CT5 six-perspective tail and operational analytics tests."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cat_treaty.ct4_models import CT4AnnualTrialInput, TailWarningCode
from cat_treaty.ct5_analytics import calculate_ct5_analytics
from cat_treaty.ct5_analytics_models import (
    CT5Analytics,
    CT5ConditionalMetricStatus,
    CT5RatioStatus,
)
from cat_treaty.ct5_models import CT5MetricPerspective
from cat_treaty.ct5_simulation import apply_ct5_catalogue
from cat_treaty.models import SettlementMode
from cat_treaty.simulation import apply_catalogue_simulation
from tests.test_ct4_simulation import catalogue, event
from tests.test_ct5_simulation import ct4_result, terms


def result_for_analytics():
    source = ct4_result(
        (event("Y1", 60_000_000.0, trial_id=1),),
        tuple(
            event(
                f"Y2-{index}",
                60_000_000.0,
                trial_id=2,
                event_time=float(index),
            )
            for index in range(1, 4)
        ),
        (),
    )
    return apply_ct5_catalogue(
        ct4_result=source,
        treaty_terms=terms(reinstatements=1),
    )


def test_six_perspectives_are_returned_in_frozen_order() -> None:
    analytics = calculate_ct5_analytics(result_for_analytics())
    assert isinstance(analytics, CT5Analytics)
    assert tuple(item.perspective for item in analytics.tail.perspectives) == tuple(CT5MetricPerspective)
    assert len(analytics.tail.perspectives) == 6


def test_all_six_samples_preserve_every_annual_trial() -> None:
    analytics = calculate_ct5_analytics(result_for_analytics())
    assert all(len(item.oep_sample) == 3 for item in analytics.tail.perspectives)
    assert all(len(item.aep_sample) == 3 for item in analytics.tail.perspectives)
    assert all(item.aep_sample[-1] == 0.0 for item in analytics.tail.perspectives)


def test_subject_recovery_and_net_aep_samples_reconcile() -> None:
    subject, recovery, net = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[:3]
    assert subject.aep_sample == (60_000_000.0, 180_000_000.0, 0.0)
    assert recovery.aep_sample == (50_000_000.0, 100_000_000.0, 0.0)
    assert net.aep_sample == (10_000_000.0, 80_000_000.0, 0.0)
    assert all(
        subject.aep_sample[index] == recovery.aep_sample[index] + net.aep_sample[index]
        for index in range(3)
    )
    assert subject.annual_average == recovery.annual_average + net.annual_average


def test_oep_and_aep_are_separate_for_multi_event_year() -> None:
    subject = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[0]
    assert subject.oep_sample == (60_000_000.0, 60_000_000.0, 0.0)
    assert subject.aep_sample == (60_000_000.0, 180_000_000.0, 0.0)


def test_f37_shortfall_has_own_oep_and_aep_samples() -> None:
    shortfall = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[-1]
    assert shortfall.perspective is CT5MetricPerspective.CAPACITY_CONSTRAINED_RECOVERY_SHORTFALL
    assert shortfall.oep_sample == (0.0, 50_000_000.0, 0.0)
    assert shortfall.aep_sample == (0.0, 50_000_000.0, 0.0)


def test_premium_samples_are_labelled_separately() -> None:
    premium = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[3]
    assert premium.perspective is CT5MetricPerspective.REINSTATEMENT_PREMIUM_PAYABLE
    assert premium.aep_sample == (5_000_000.0, 5_000_000.0, 0.0)
    assert premium.annual_average == pytest.approx(10_000_000.0 / 3)


def test_negative_net_cash_is_accepted_in_samples_curves_and_tail_estimates() -> None:
    source = ct4_result((event("E1", 11_000_000.0),))
    base_terms = terms(
        reinstatements=1,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )
    first, second = base_terms.layer_terms
    expensive_tranche = replace(first.reinstatement_tranches[0], premium_rate=3.0)
    expensive_terms = replace(
        base_terms,
        layer_terms=(
            replace(
                first,
                original_layer_premium=10_000_000.0,
                reinstatement_tranches=(expensive_tranche,),
            ),
            second,
        ),
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=expensive_terms)
    cash = calculate_ct5_analytics(result).tail.perspectives[4]
    assert cash.aep_sample == (-500_000.0,)
    assert cash.oep_curve[0].value == -500_000.0
    assert cash.aep_var_estimates[0].value == -500_000.0
    assert cash.aep_tvar_estimates[0].value == -500_000.0
    assert cash.coefficient_of_variation is None
    assert cash.coefficient_status is CT5RatioStatus.NOT_APPLICABLE_NEGATIVE_MEAN


def test_nearest_rank_tvar_curves_and_r_over_y_match_ct4_conventions() -> None:
    subject = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[0]
    assert tuple(item.value for item in subject.aep_curve) == (180_000_000.0, 60_000_000.0, 0.0)
    assert tuple(item.exceedance_probability for item in subject.aep_curve) == pytest.approx((1/3, 2/3, 1.0))
    assert subject.aep_var_estimates[0].value == 180_000_000.0
    assert subject.aep_tvar_estimates[0].value == 180_000_000.0


def test_return_period_credibility_warnings_are_cumulative() -> None:
    subject = calculate_ct5_analytics(result_for_analytics()).tail.perspectives[0]
    estimate = next(item for item in subject.aep_return_period_estimates if item.level == 200.0)
    assert tuple(item.code for item in estimate.warnings) == (
        TailWarningCode.LIMITED_TAIL_CREDIBILITY,
        TailWarningCode.SEVERE_TAIL_CREDIBILITY_WARNING,
        TailWarningCode.RETURN_PERIOD_EXCEEDS_SAMPLE,
    )


def test_operational_capacity_constraint_probability_and_average() -> None:
    operational = calculate_ct5_analytics(result_for_analytics()).operational
    assert operational.probability_capacity_constrains_event == pytest.approx(1 / 3)
    assert operational.average_recovery_constrained == pytest.approx(50_000_000.0 / 3)


def test_operational_layer_exhaustion_probability() -> None:
    exhaustion = calculate_ct5_analytics(result_for_analytics()).operational.layer_exhaustion
    assert tuple(item.layer_id for item in exhaustion) == ("L1", "L2")
    assert tuple(item.exhaustion_probability for item in exhaustion) == pytest.approx((1 / 3, 1 / 3))


def test_reinstatements_used_average_and_maximum() -> None:
    operational = calculate_ct5_analytics(result_for_analytics()).operational
    assert operational.average_reinstatements_used == pytest.approx(2 / 3)
    assert operational.maximum_reinstatements_used == 1.0


def test_conditional_and_unconditional_premium_means() -> None:
    operational = calculate_ct5_analytics(result_for_analytics()).operational
    assert operational.average_reinstatement_premium_unconditional == pytest.approx(10_000_000.0 / 3)
    assert operational.average_reinstatement_premium_conditional == 5_000_000.0
    assert operational.conditional_premium_status is CT5ConditionalMetricStatus.APPLICABLE


def test_no_paid_premium_has_explicit_conditional_na_status() -> None:
    source = ct4_result((event("E1", 45_000_000.0),), ())
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    operational = calculate_ct5_analytics(result).operational
    assert operational.average_reinstatement_premium_conditional is None
    assert operational.conditional_premium_status is CT5ConditionalMetricStatus.NOT_APPLICABLE_NO_POSITIVE_PREMIUM


def test_all_zero_perspectives_have_null_cv_and_zero_mean_status() -> None:
    source = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(1, "T1", (event("E1", 0.0),)),
            CT4AnnualTrialInput(2, "T2", ()),
        )
    )
    result = apply_ct5_catalogue(ct4_result=source, treaty_terms=terms())
    analytics = calculate_ct5_analytics(result)
    for perspective in analytics.tail.perspectives:
        assert perspective.annual_average == 0.0
        assert perspective.coefficient_of_variation is None
        assert perspective.coefficient_status is CT5RatioStatus.NOT_APPLICABLE_ZERO_MEAN


def test_analytics_are_deterministic_and_immutable() -> None:
    result = result_for_analytics()
    first = calculate_ct5_analytics(result)
    second = calculate_ct5_analytics(result)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.tail.aal_reconciliation_passed = False  # type: ignore[misc]


def test_analytics_entry_requires_completed_ct5_result() -> None:
    with pytest.raises(ValueError, match="CT5CatalogueResult"):
        calculate_ct5_analytics({})  # type: ignore[arg-type]


def test_ct5_analytics_public_exports() -> None:
    import cat_treaty

    expected = {
        "CT5Analytics",
        "CT5ConditionalMetricStatus",
        "CT5ExceedancePoint",
        "CT5LayerExhaustionMetric",
        "CT5OperationalAnalytics",
        "CT5PerspectiveAnalytics",
        "CT5RatioStatus",
        "CT5TailAnalytics",
        "CT5TailEstimate",
        "calculate_ct5_analytics",
    }
    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, name) for name in expected)
