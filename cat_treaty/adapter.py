"""Numerical-identity adapters for the validated Cat XOL source records."""

from collections.abc import Iterable
from typing import Protocol

from cat_treaty.models import CanonicalEvent


class PricingEventRecord(Protocol):
    """Structural contract matching cat_xol.models.EventRecord."""

    year: int
    event_id: str
    event_time: float
    event_sequence: int
    peril: str
    region: str
    risks_affected: int
    gross_event_loss: float


_REQUIRED_EVENT_FIELDS = (
    "year",
    "event_id",
    "event_time",
    "event_sequence",
    "peril",
    "region",
    "risks_affected",
    "gross_event_loss",
)


def _required_field(source: object, field_name: str) -> object:
    """Read one required structural field with an explicit error."""

    try:
        return getattr(source, field_name)
    except AttributeError as exc:
        raise TypeError(
            f"source event missing required field: {field_name}"
        ) from exc


def adapt_event_record(source: PricingEventRecord) -> CanonicalEvent:
    """Map one validated pricing event without numerical transformation."""

    values = {
        field_name: _required_field(source, field_name)
        for field_name in _REQUIRED_EVENT_FIELDS
    }

    return CanonicalEvent(
        annual_trial_id=values["year"],
        event_id=values["event_id"],
        event_time=values["event_time"],
        event_sequence=values["event_sequence"],
        peril=values["peril"],
        region=values["region"],
        risks_affected=values["risks_affected"],
        subject_loss=values["gross_event_loss"],
    )


def adapt_event_records(
    events: Iterable[PricingEventRecord],
) -> tuple[CanonicalEvent, ...]:
    """Adapt events while enforcing source chronology and identity."""

    try:
        iterator = iter(events)
    except TypeError as exc:
        raise TypeError("events must be iterable") from exc

    adapted_events: list[CanonicalEvent] = []
    event_ids_by_trial: dict[int, set[str]] = {}
    last_order_key_by_trial: dict[int, tuple[float, str]] = {}

    for source_event in iterator:
        event = adapt_event_record(source_event)
        trial_id = event.annual_trial_id

        event_ids = event_ids_by_trial.setdefault(trial_id, set())

        if event.event_id in event_ids:
            raise ValueError(
                "duplicate event_id within annual trial: "
                f"{event.event_id}"
            )

        order_key = (event.event_time, event.event_id)
        previous_order_key = last_order_key_by_trial.get(trial_id)

        if (
            previous_order_key is not None
            and order_key < previous_order_key
        ):
            raise ValueError(
                f"events for annual trial {trial_id} are not "
                "chronologically ordered"
            )

        event_ids.add(event.event_id)
        last_order_key_by_trial[trial_id] = order_key
        adapted_events.append(event)

    return tuple(adapted_events)