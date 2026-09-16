"""F19-F24 empirical tail analytics for completed CT4 annual ledgers."""

import math
from numbers import Real

from cat_treaty.ct4_models import (
    CT4AnnualLedgerRow,
    CT4CatalogueResult,
    CT4TailAnalytics,
    EmpiricalExceedancePoint,
    MetricPerspective,
    PerspectiveAnalytics,
    RatioStatus,
    TailConfiguration,
    TailEstimate,
    TailWarning,
    TailWarningCode,
)


def nearest_rank_quantile(values: tuple[float, ...], probability: float) -> float:
    """Return F21 without interpolation."""

    sample = _sample(values)
    p = _probability(probability)
    ordered = sorted(sample)
    return ordered[math.ceil(p * len(ordered)) - 1]


def empirical_tvar(values: tuple[float, ...], probability: float) -> float:
    """Return F23 including the nearest-rank observation and every larger one."""

    sample = _sample(values)
    p = _probability(probability)
    ordered = sorted(sample)
    start = math.ceil(p * len(ordered)) - 1
    tail = ordered[start:]
    return math.fsum(tail) / len(tail)


def empirical_exceedance_curve(
    values: tuple[float, ...],
) -> tuple[EmpiricalExceedancePoint, ...]:
    """Return F22 ranked points with duplicate observations retained."""

    sample = _sample(values)
    count = len(sample)
    return tuple(
        EmpiricalExceedancePoint(rank, loss, rank / count)
        for rank, loss in enumerate(sorted(sample, reverse=True), start=1)
    )


def return_period_warnings(
    trial_count: int,
    return_period: float,
) -> tuple[TailWarning, ...]:
    """Return every applicable section-15 warning in frozen severity order."""

    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise ValueError("trial_count must be a positive integer")
    period = _finite_positive("return_period", return_period)
    if period <= 1:
        raise ValueError("return_period must be greater than one")
    observations = trial_count / period
    warnings: list[TailWarning] = []
    if observations < 20:
        warnings.append(
            TailWarning(
                TailWarningCode.LIMITED_TAIL_CREDIBILITY,
                period,
                observations,
                "Fewer than 20 observations per return period limits empirical-tail credibility.",
            )
        )
    if observations < 5:
        warnings.append(
            TailWarning(
                TailWarningCode.SEVERE_TAIL_CREDIBILITY_WARNING,
                period,
                observations,
                "Fewer than 5 observations per return period creates severe empirical-tail uncertainty.",
            )
        )
    if period > trial_count:
        warnings.append(
            TailWarning(
                TailWarningCode.RETURN_PERIOD_EXCEEDS_SAMPLE,
                period,
                observations,
                "Return period exceeds the declared annual-trial sample.",
            )
        )
    return tuple(warnings)


def calculate_tail_analytics(
    catalogue_result: CT4CatalogueResult,
) -> CT4TailAnalytics:
    """Calculate F19-F24 for subject, recovery and insurer-net perspectives."""

    if not isinstance(catalogue_result, CT4CatalogueResult):
        raise TypeError("catalogue_result must be CT4CatalogueResult")
    simulation_input = catalogue_result.simulation_input
    return calculate_tail_analytics_from_rows(
        catalogue_result.annual_rows,
        config=simulation_input.tail_configuration,
        relative_tolerance=simulation_input.tolerance_profile.relative_tolerance,
        absolute_tolerance=simulation_input.tolerance_profile.absolute_currency_tolerance,
    )


def calculate_tail_analytics_from_rows(
    annual_rows: tuple[CT4AnnualLedgerRow, ...],
    *,
    config: TailConfiguration,
    relative_tolerance: float,
    absolute_tolerance: float,
) -> CT4TailAnalytics:
    """Calculate F19-F24 from a complete ordered annual ledger population."""

    if not isinstance(annual_rows, tuple) or not annual_rows or not all(
        isinstance(item, CT4AnnualLedgerRow) for item in annual_rows
    ):
        raise ValueError("annual_rows must contain at least one CT4AnnualLedgerRow")
    if tuple(item.annual_trial_id for item in annual_rows) != tuple(range(1, len(annual_rows) + 1)):
        raise ValueError("annual_rows must be in contiguous annual-trial order")
    if not isinstance(config, TailConfiguration):
        raise ValueError("config must be TailConfiguration")
    relative = _finite_positive("relative_tolerance", relative_tolerance)
    absolute = _finite_positive("absolute_tolerance", absolute_tolerance)
    perspectives = tuple(
        _perspective(annual_rows, perspective, config)
        for perspective in (
            MetricPerspective.SUBJECT,
            MetricPerspective.RECOVERY_PRE_ANNUAL_CAPACITY,
            MetricPerspective.INSURER_NET_PRE_ANNUAL_CAPACITY,
        )
    )
    subject, recovery, net = (
        item.annual_average_loss for item in perspectives
    )
    return CT4TailAnalytics(
        perspectives=perspectives,
        aal_reconciliation_passed=math.isclose(
            subject,
            recovery + net,
            rel_tol=relative,
            abs_tol=absolute,
        ),
    )


def _perspective(
    annual_rows: tuple[CT4AnnualLedgerRow, ...],
    perspective: MetricPerspective,
    config: TailConfiguration,
) -> PerspectiveAnalytics:
    oep_attribute, aep_attribute = {
        MetricPerspective.SUBJECT: ("subject_oep", "subject_aep"),
        MetricPerspective.RECOVERY_PRE_ANNUAL_CAPACITY: (
            "recovery_oep_pre_annual_capacity",
            "recovery_aep_pre_annual_capacity",
        ),
        MetricPerspective.INSURER_NET_PRE_ANNUAL_CAPACITY: (
            "net_oep_pre_annual_capacity",
            "net_aep_pre_annual_capacity",
        ),
    }[perspective]
    oep_sample = tuple(float(getattr(row, oep_attribute)) for row in annual_rows)
    aep_sample = tuple(float(getattr(row, aep_attribute)) for row in annual_rows)
    mean = math.fsum(aep_sample) / len(aep_sample)
    squared_deviations = math.fsum((value - mean) ** 2 for value in aep_sample)
    standard_deviation = math.sqrt(squared_deviations / len(aep_sample))
    if mean == 0:
        coefficient = None
        coefficient_status = RatioStatus.NOT_APPLICABLE_ZERO_MEAN
    else:
        coefficient = standard_deviation / mean
        coefficient_status = RatioStatus.APPLICABLE

    oep_var_estimates = tuple(
        TailEstimate(level, nearest_rank_quantile(oep_sample, level))
        for level in config.probability_levels
    )
    aep_var_estimates = tuple(
        TailEstimate(level, nearest_rank_quantile(aep_sample, level))
        for level in config.probability_levels
    )
    oep_tvar_estimates = tuple(
        TailEstimate(level, empirical_tvar(oep_sample, level))
        for level in config.tvar_levels
    )
    aep_tvar_estimates = tuple(
        TailEstimate(level, empirical_tvar(aep_sample, level))
        for level in config.tvar_levels
    )
    oep_return_periods = tuple(
        _return_period_estimate(oep_sample, period) for period in config.return_periods
    )
    aep_return_periods = tuple(
        _return_period_estimate(aep_sample, period) for period in config.return_periods
    )
    return PerspectiveAnalytics(
        perspective=perspective,
        annual_average_loss=mean,
        population_standard_deviation=standard_deviation,
        coefficient_of_variation=coefficient,
        coefficient_status=coefficient_status,
        oep_sample=oep_sample,
        aep_sample=aep_sample,
        # Retained compatibility fields are the AEP series.
        var_estimates=aep_var_estimates,
        tvar_estimates=aep_tvar_estimates,
        # Retained compatibility field is the AEP return-period series.
        return_period_estimates=aep_return_periods,
        oep_curve=empirical_exceedance_curve(oep_sample),
        aep_curve=empirical_exceedance_curve(aep_sample),
        oep_return_period_estimates=oep_return_periods,
        aep_return_period_estimates=aep_return_periods,
        oep_var_estimates=oep_var_estimates,
        aep_var_estimates=aep_var_estimates,
        oep_tvar_estimates=oep_tvar_estimates,
        aep_tvar_estimates=aep_tvar_estimates,
    )


def _return_period_estimate(
    sample: tuple[float, ...],
    return_period: float,
) -> TailEstimate:
    return TailEstimate(
        level=float(return_period),
        value=nearest_rank_quantile(sample, 1.0 - 1.0 / float(return_period)),
        warnings=return_period_warnings(len(sample), return_period),
    )


def _sample(values: tuple[float, ...]) -> tuple[float, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError("values must be a non-empty tuple")
    return tuple(_finite_non_negative("sample value", value) for value in values)


def _probability(value: float) -> float:
    probability = _finite_positive("probability", value)
    if probability >= 1:
        raise ValueError("probability must lie in (0, 1)")
    return probability


def _finite_positive(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return number


def _finite_non_negative(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return number
