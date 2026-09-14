"""Identity and validation tests for the CT1 event compatibility adapter."""

from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from cat_treaty.adapter import (
    adapt_event_record,
    adapt_event_records,
)
from cat_treaty.models import CanonicalEvent


@dataclass(frozen=True, slots=True)
class PricingEventFixture:
    """Exact structural equivalent of cat_xol.models.EventRecord."""

    year: int
    event_id: str
    event_time: float
    event_sequence: int
    peril: str
    region: str
    risks_affected: int
    gross_event_loss: float


BASE_EVENT = PricingEventFixture(
    year=1,
    event_id="EVT-0001",
    event_time=25.125,
    event_sequence=1,
    peril="hurricane",
    region="gulf_coast",
    risks_affected=12,
    gross_event_loss=2_500_000.125,
)


def test_single_event_maps_to_canonical_names() -> None:
    event = adapt_event_record(BASE_EVENT)

    assert event == CanonicalEvent(
        annual_trial_id=1,
        event_id="EVT-0001",
        event_time=25.125,
        event_sequence=1,
        peril="hurricane",
        region="gulf_coast",
        risks_affected=12,
        subject_loss=2_500_000.125,
    )


def test_adapter_preserves_numeric_values_without_rounding() -> None:
    source = replace(
        BASE_EVENT,
        event_time=0.123456789012345,
        gross_event_loss=1_234_567.8901234567,
    )

    event = adapt_event_record(source)

    assert event.event_time.hex() == source.event_time.hex()
    assert event.subject_loss.hex() == source.gross_event_loss.hex()


def test_adapter_preserves_source_class_unchanged() -> None:
    source = BASE_EVENT

    adapt_event_record(source)

    assert source == BASE_EVENT


def test_equivalent_structural_object_is_supported() -> None:
    source = SimpleNamespace(
        year=2,
        event_id="EVT-0002",
        event_time=40.0,
        event_sequence=1,
        peril="earthquake",
        region="west",
        risks_affected=20,
        gross_event_loss=7_500_000.0,
    )

    event = adapt_event_record(source)

    assert event.annual_trial_id == 2
    assert event.peril == "earthquake"
    assert event.region == "west"
    assert event.risks_affected == 20
    assert event.subject_loss == 7_500_000.0


def test_event_collection_preserves_valid_source_order() -> None:
    first = BASE_EVENT
    second = replace(
        BASE_EVENT,
        event_id="EVT-0002",
        event_time=30.0,
        event_sequence=2,
    )

    events = adapt_event_records((first, second))

    assert isinstance(events, tuple)
    assert [event.event_id for event in events] == [
        "EVT-0001",
        "EVT-0002",
    ]


def test_equal_times_are_ordered_by_event_id() -> None:
    first = replace(
        BASE_EVENT,
        event_id="EVT-0001",
        event_time=25.0,
        event_sequence=1,
    )
    second = replace(
        BASE_EVENT,
        event_id="EVT-0002",
        event_time=25.0,
        event_sequence=2,
    )

    events = adapt_event_records((first, second))

    assert [event.event_id for event in events] == [
        "EVT-0001",
        "EVT-0002",
    ]


def test_unordered_events_within_trial_are_rejected() -> None:
    later = replace(
        BASE_EVENT,
        event_id="EVT-0002",
        event_time=30.0,
        event_sequence=2,
    )
    earlier = replace(
        BASE_EVENT,
        event_id="EVT-0001",
        event_time=20.0,
        event_sequence=1,
    )

    with pytest.raises(ValueError, match="chronologically ordered"):
        adapt_event_records((later, earlier))


def test_equal_time_reverse_event_id_order_is_rejected() -> None:
    second = replace(
        BASE_EVENT,
        event_id="EVT-0002",
        event_time=25.0,
        event_sequence=2,
    )
    first = replace(
        BASE_EVENT,
        event_id="EVT-0001",
        event_time=25.0,
        event_sequence=1,
    )

    with pytest.raises(ValueError, match="chronologically ordered"):
        adapt_event_records((second, first))


def test_duplicate_event_id_within_trial_is_rejected() -> None:
    duplicate = replace(
        BASE_EVENT,
        event_time=30.0,
        event_sequence=2,
    )

    with pytest.raises(ValueError, match="duplicate event_id"):
        adapt_event_records((BASE_EVENT, duplicate))


def test_same_event_id_in_different_trials_is_allowed() -> None:
    next_trial = replace(
        BASE_EVENT,
        year=2,
        event_time=10.0,
        event_sequence=1,
    )

    events = adapt_event_records((BASE_EVENT, next_trial))

    assert len(events) == 2
    assert events[0].annual_trial_id == 1
    assert events[1].annual_trial_id == 2


@pytest.mark.parametrize(
    "missing_field",
    [
        "year",
        "event_id",
        "event_time",
        "event_sequence",
        "peril",
        "region",
        "risks_affected",
        "gross_event_loss",
    ],
)
def test_missing_source_field_is_rejected(
    missing_field: str,
) -> None:
    values = {
        "year": BASE_EVENT.year,
        "event_id": BASE_EVENT.event_id,
        "event_time": BASE_EVENT.event_time,
        "event_sequence": BASE_EVENT.event_sequence,
        "peril": BASE_EVENT.peril,
        "region": BASE_EVENT.region,
        "risks_affected": BASE_EVENT.risks_affected,
        "gross_event_loss": BASE_EVENT.gross_event_loss,
    }
    del values[missing_field]

    with pytest.raises(
        TypeError,
        match=f"missing required field: {missing_field}",
    ):
        adapt_event_record(SimpleNamespace(**values))


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("year", 0),
        ("event_id", ""),
        ("event_time", -1.0),
        ("event_sequence", 0),
        ("peril", ""),
        ("region", "   "),
        ("risks_affected", -1),
        ("gross_event_loss", -1.0),
    ],
)
def test_invalid_source_value_is_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    source = replace(
        BASE_EVENT,
        **{field_name: invalid_value},
    )

    with pytest.raises(ValueError):
        adapt_event_record(source)


def test_empty_event_collection_is_valid() -> None:
    assert adapt_event_records(()) == ()


def test_non_iterable_event_collection_is_rejected() -> None:
    with pytest.raises(TypeError, match="events must be iterable"):
        adapt_event_records(123)