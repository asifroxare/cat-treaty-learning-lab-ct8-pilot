"""CT4 occurrence and annual attachment/exhaustion frequency analytics."""

from cat_treaty.ct4_models import (
    CT4AnnualLedgerRow,
    CT4CatalogueResult,
    CT4FrequencyAnalytics,
    FrequencyMetric,
    LayerFrequencyAnalytics,
    RatioStatus,
)


def calculate_frequency_analytics(result: CT4CatalogueResult) -> CT4FrequencyAnalytics:
    if not isinstance(result, CT4CatalogueResult):
        raise TypeError("result must be CT4CatalogueResult")
    return calculate_frequency_analytics_from_rows(result.annual_rows)


def calculate_frequency_analytics_from_rows(
    annual_rows: tuple[CT4AnnualLedgerRow, ...],
) -> CT4FrequencyAnalytics:
    if not isinstance(annual_rows, tuple) or not annual_rows or not all(
        isinstance(item, CT4AnnualLedgerRow) for item in annual_rows
    ):
        raise ValueError("annual_rows must contain at least one CT4AnnualLedgerRow")
    occurrences = tuple(row for annual in annual_rows for row in annual.occurrence_rows)
    attached = sum(
        row.gross_contractual_recovery_pre_annual_capacity > 0 for row in occurrences
    )
    annual_attached = sum(
        any(row.gross_contractual_recovery_pre_annual_capacity > 0 for row in annual.occurrence_rows)
        for annual in annual_rows
    )
    layer_ids = tuple(
        layer.layer_input.layer_id
        for layer in occurrences[0].assessment.program_result.layer_results
    ) if occurrences else ()
    layer_metrics = tuple(
        LayerFrequencyAnalytics(
            layer_id=layer_id,
            occurrence_exhaustion_frequency=_metric(
                sum(
                    _layer(row, layer_id).exhaustion_reached
                    for row in occurrences
                ),
                len(occurrences),
                "evaluated occurrences",
            ),
            annual_exhaustion_frequency=_metric(
                sum(
                    any(_layer(row, layer_id).exhaustion_reached for row in annual.occurrence_rows)
                    for annual in annual_rows
                ),
                len(annual_rows),
                "declared annual trials",
            ),
        )
        for layer_id in layer_ids
    )
    return CT4FrequencyAnalytics(
        occurrence_attachment_frequency=_metric(
            attached,
            len(occurrences),
            "evaluated occurrences",
        ),
        annual_attachment_frequency=_metric(
            annual_attached,
            len(annual_rows),
            "declared annual trials",
        ),
        layer_exhaustion_frequencies=layer_metrics,
    )


def _layer(row, layer_id):
    return next(
        item for item in row.assessment.program_result.layer_results
        if item.layer_input.layer_id == layer_id
    )


def _metric(numerator: int, denominator: int, label: str) -> FrequencyMetric:
    if denominator == 0:
        return FrequencyMetric(
            numerator=0,
            denominator=0,
            value=None,
            status=RatioStatus.NOT_APPLICABLE_NO_OCCURRENCES,
            denominator_label=label,
        )
    return FrequencyMetric(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator,
        status=RatioStatus.APPLICABLE,
        denominator_label=label,
    )
