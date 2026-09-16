"""CT5 six-perspective post-capacity tail and operational analytics."""

import math

from cat_treaty.ct4_models import TailConfiguration
from cat_treaty.ct5_analytics_models import (
    CT5Analytics,
    CT5ConditionalMetricStatus,
    CT5ExceedancePoint,
    CT5LayerExhaustionMetric,
    CT5OperationalAnalytics,
    CT5PerspectiveAnalytics,
    CT5RatioStatus,
    CT5TailAnalytics,
    CT5TailEstimate,
)
from cat_treaty.ct5_models import (
    CT5AnnualLedgerRow,
    CT5CatalogueResult,
    CT5MetricPerspective,
)
from cat_treaty.tail import return_period_warnings


def calculate_ct5_analytics(result: CT5CatalogueResult) -> CT5Analytics:
    """Calculate six CT5 perspectives and annual-capacity operating metrics."""

    if not isinstance(result, CT5CatalogueResult):
        raise ValueError("result must be a completed CT5CatalogueResult")
    config = result.ct4_result.simulation_input.tail_configuration
    perspectives = tuple(
        _perspective(result.annual_rows, perspective, config)
        for perspective in CT5MetricPerspective
    )
    subject, recovery, net = (
        perspectives[index].annual_average for index in (0, 1, 2)
    )
    tail = CT5TailAnalytics(
        perspectives=perspectives,
        aal_reconciliation_passed=math.isclose(
            subject,
            recovery + net,
            rel_tol=1e-12,
            abs_tol=1e-6,
        ),
    )
    return CT5Analytics(
        tail=tail,
        operational=_operational(result.annual_rows),
    )


def _perspective(
    rows: tuple[CT5AnnualLedgerRow, ...],
    perspective: CT5MetricPerspective,
    config: TailConfiguration,
) -> CT5PerspectiveAnalytics:
    if not rows:
        raise ValueError("CT5 analytics requires at least one annual row")
    oep_sample = tuple(_oep(row, perspective) for row in rows)
    aep_sample = tuple(_aep(row, perspective) for row in rows)
    mean = math.fsum(aep_sample) / len(aep_sample)
    deviation = math.sqrt(
        math.fsum((value - mean) ** 2 for value in aep_sample) / len(aep_sample)
    )
    if mean > 0:
        coefficient = deviation / mean
        coefficient_status = CT5RatioStatus.APPLICABLE
    elif mean == 0:
        coefficient = None
        coefficient_status = CT5RatioStatus.NOT_APPLICABLE_ZERO_MEAN
    else:
        coefficient = None
        coefficient_status = CT5RatioStatus.NOT_APPLICABLE_NEGATIVE_MEAN
    return CT5PerspectiveAnalytics(
        perspective=perspective,
        annual_average=mean,
        population_standard_deviation=deviation,
        coefficient_of_variation=coefficient,
        coefficient_status=coefficient_status,
        oep_sample=oep_sample,
        aep_sample=aep_sample,
        oep_curve=_curve(oep_sample),
        aep_curve=_curve(aep_sample),
        oep_var_estimates=tuple(
            CT5TailEstimate(level, _nearest_rank(oep_sample, level))
            for level in config.probability_levels
        ),
        aep_var_estimates=tuple(
            CT5TailEstimate(level, _nearest_rank(aep_sample, level))
            for level in config.probability_levels
        ),
        oep_tvar_estimates=tuple(
            CT5TailEstimate(level, _tvar(oep_sample, level))
            for level in config.tvar_levels
        ),
        aep_tvar_estimates=tuple(
            CT5TailEstimate(level, _tvar(aep_sample, level))
            for level in config.tvar_levels
        ),
        oep_return_period_estimates=tuple(
            _return_period(oep_sample, period) for period in config.return_periods
        ),
        aep_return_period_estimates=tuple(
            _return_period(aep_sample, period) for period in config.return_periods
        ),
    )


def _oep(row: CT5AnnualLedgerRow, perspective: CT5MetricPerspective) -> float:
    attribute = {
        CT5MetricPerspective.SUBJECT: "subject_loss",
        CT5MetricPerspective.GROSS_RECOVERY_POST_ANNUAL_CAPACITY: "gross_contractual_recovery",
        CT5MetricPerspective.INSURER_NET_POST_ANNUAL_CAPACITY: "insurer_net_subject_loss",
        CT5MetricPerspective.REINSTATEMENT_PREMIUM_PAYABLE: "reinstatement_premium_payable",
        CT5MetricPerspective.NET_CASH_SETTLEMENT: "net_cash_settlement",
        CT5MetricPerspective.CAPACITY_CONSTRAINED_RECOVERY_SHORTFALL: "capacity_constrained_recovery_shortfall",
    }[perspective]
    return float(max((getattr(event, attribute) for event in row.event_rows), default=0.0))


def _aep(row: CT5AnnualLedgerRow, perspective: CT5MetricPerspective) -> float:
    attribute = {
        CT5MetricPerspective.SUBJECT: "subject_loss",
        CT5MetricPerspective.GROSS_RECOVERY_POST_ANNUAL_CAPACITY: "gross_contractual_recovery",
        CT5MetricPerspective.INSURER_NET_POST_ANNUAL_CAPACITY: "insurer_net_subject_loss",
        CT5MetricPerspective.REINSTATEMENT_PREMIUM_PAYABLE: "reinstatement_premium_payable",
        CT5MetricPerspective.NET_CASH_SETTLEMENT: "net_cash_settlement",
        CT5MetricPerspective.CAPACITY_CONSTRAINED_RECOVERY_SHORTFALL: "capacity_constrained_recovery_shortfall",
    }[perspective]
    return float(getattr(row, attribute))


def _nearest_rank(sample: tuple[float, ...], probability: float) -> float:
    ordered = sorted(float(value) for value in sample)
    return ordered[math.ceil(float(probability) * len(ordered)) - 1]


def _tvar(sample: tuple[float, ...], probability: float) -> float:
    ordered = sorted(float(value) for value in sample)
    start = math.ceil(float(probability) * len(ordered)) - 1
    tail = ordered[start:]
    return math.fsum(tail) / len(tail)


def _curve(sample: tuple[float, ...]) -> tuple[CT5ExceedancePoint, ...]:
    count = len(sample)
    return tuple(
        CT5ExceedancePoint(rank, value, rank / count)
        for rank, value in enumerate(sorted(sample, reverse=True), start=1)
    )


def _return_period(
    sample: tuple[float, ...],
    period: float,
) -> CT5TailEstimate:
    return CT5TailEstimate(
        level=float(period),
        value=_nearest_rank(sample, 1.0 - 1.0 / float(period)),
        warnings=return_period_warnings(len(sample), period),
    )


def _operational(
    rows: tuple[CT5AnnualLedgerRow, ...],
) -> CT5OperationalAnalytics:
    count = len(rows)
    constrained_years = sum(
        row.capacity_constrained_recovery_shortfall > 0 for row in rows
    )
    layer_ids = tuple(item.layer_id for item in rows[0].layer_summaries)
    exhaustion = tuple(
        CT5LayerExhaustionMetric(
            layer_id=layer_id,
            exhaustion_probability=sum(
                _is_exhausted(
                    next(item for item in row.layer_summaries if item.layer_id == layer_id)
                )
                for row in rows
            )
            / count,
        )
        for layer_id in layer_ids
    )
    reinstatement_counts = tuple(
        summary.total_reinstated / summary.initial_capacity
        for row in rows
        for summary in row.layer_summaries
        if summary.initial_capacity > 0
    )
    premiums = tuple(row.reinstatement_premium_payable for row in rows)
    positive_premiums = tuple(value for value in premiums if value > 0)
    conditional = (
        math.fsum(positive_premiums) / len(positive_premiums)
        if positive_premiums
        else None
    )
    return CT5OperationalAnalytics(
        probability_capacity_constrains_event=constrained_years / count,
        average_recovery_constrained=math.fsum(
            row.capacity_constrained_recovery_shortfall for row in rows
        )
        / count,
        layer_exhaustion=exhaustion,
        average_reinstatements_used=(
            math.fsum(reinstatement_counts) / len(reinstatement_counts)
            if reinstatement_counts
            else 0.0
        ),
        maximum_reinstatements_used=max(reinstatement_counts, default=0.0),
        average_reinstatement_premium_unconditional=math.fsum(premiums) / count,
        average_reinstatement_premium_conditional=conditional,
        conditional_premium_status=(
            CT5ConditionalMetricStatus.APPLICABLE
            if conditional is not None
            else CT5ConditionalMetricStatus.NOT_APPLICABLE_NO_POSITIVE_PREMIUM
        ),
    )


def _is_exhausted(summary) -> bool:
    maximum = summary.initial_capacity + summary.initial_reinstatement_reserve
    return maximum > 0 and math.isclose(
        summary.total_recovery,
        maximum,
        rel_tol=1e-12,
        abs_tol=1e-6,
    )
