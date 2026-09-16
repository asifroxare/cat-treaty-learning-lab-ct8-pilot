"""Occurrence and annual frequency denominator tests."""

from dataclasses import FrozenInstanceError

import pytest

from cat_treaty.ct4_models import CT4AnnualTrialInput, RatioStatus
from cat_treaty.frequency import calculate_frequency_analytics
from cat_treaty.simulation import apply_catalogue_simulation
from tests.test_ct4_simulation import catalogue, event


def test_occurrence_and_annual_attachment_denominators_are_distinct() -> None:
    result = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(
                1,
                "T1",
                (
                    event("E1", 5_000_000.0, event_time=1.0),
                    event("E2", 45_000_000.0, event_time=2.0),
                ),
            ),
            CT4AnnualTrialInput(2, "T2", ()),
        )
    )
    metrics = calculate_frequency_analytics(result)
    occurrence = metrics.occurrence_attachment_frequency
    annual = metrics.annual_attachment_frequency
    assert (occurrence.numerator, occurrence.denominator, occurrence.value) == (1, 2, 0.5)
    assert occurrence.denominator_label == "evaluated occurrences"
    assert (annual.numerator, annual.denominator, annual.value) == (1, 2, 0.5)
    assert annual.denominator_label == "declared annual trials"


def test_layer_exhaustion_has_occurrence_and_annual_views() -> None:
    result = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(
                1,
                "T1",
                (
                    event("E1", 45_000_000.0, event_time=1.0),
                    event("E2", 80_000_000.0, event_time=2.0),
                ),
            ),
            CT4AnnualTrialInput(2, "T2", (event("E3", 5_000_000.0, trial_id=2),)),
        )
    )
    layers = calculate_frequency_analytics(result).layer_exhaustion_frequencies
    first, second = layers
    assert first.layer_id == "L1"
    assert (first.occurrence_exhaustion_frequency.numerator, first.occurrence_exhaustion_frequency.denominator) == (2, 3)
    assert (first.annual_exhaustion_frequency.numerator, first.annual_exhaustion_frequency.denominator) == (1, 2)
    assert second.layer_id == "L2"
    assert (second.occurrence_exhaustion_frequency.numerator, second.occurrence_exhaustion_frequency.denominator) == (1, 3)


def test_zero_occurrences_returns_null_occurrence_frequency_and_zero_annual_frequency() -> None:
    result = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(1, "T1", ()),
            CT4AnnualTrialInput(2, "T2", ()),
        )
    )
    metrics = calculate_frequency_analytics(result)
    occurrence = metrics.occurrence_attachment_frequency
    annual = metrics.annual_attachment_frequency
    assert occurrence.value is None
    assert occurrence.status is RatioStatus.NOT_APPLICABLE_NO_OCCURRENCES
    assert (annual.numerator, annual.denominator, annual.value) == (0, 2, 0.0)
    assert annual.status is RatioStatus.APPLICABLE
    assert metrics.layer_exhaustion_frequencies == ()


def test_frequency_response_is_immutable_and_type_checked() -> None:
    result = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "T1", ()))
    )
    metrics = calculate_frequency_analytics(result)
    with pytest.raises(FrozenInstanceError):
        metrics.annual_attachment_frequency = None  # type: ignore[misc]
    with pytest.raises(TypeError):
        calculate_frequency_analytics({})  # type: ignore[arg-type]
