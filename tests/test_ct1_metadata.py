"""Contract tests for CT1 version metadata and deterministic input hashing."""

from dataclasses import FrozenInstanceError
import math

import pytest

from cat_treaty.metadata import (
    ENGINE_VERSION,
    PRODUCT_ID,
    PRODUCT_ROUTE,
    SCHEMA_VERSION,
    RunMetadata,
    build_run_metadata,
)
from cat_treaty.models import CapacityBasis, SettlementMode, TreatyShares


BASE_INPUTS = {
    "attachment": 1_000_000.0,
    "occurrence_limit": 5_000_000.0,
    "shares": TreatyShares(
        ceded_share=0.9,
        placement_share=0.75,
    ),
    "settlement_mode": SettlementMode.PAID_SEPARATELY,
    "events": [
        {
            "event_id": "EVT-001",
            "event_time": 10.0,
            "subject_loss": 2_000_000.0,
        },
        {
            "event_id": "EVT-002",
            "event_time": 20.0,
            "subject_loss": 3_000_000.0,
        },
    ],
}


def build_default_metadata(**overrides: object) -> RunMetadata:
    values: dict[str, object] = {
        "actuarial_inputs": BASE_INPUTS,
        "catalogue_version": "cat-xol-a47eb246",
        "simulation_seed": 42,
    }
    values.update(overrides)
    return build_run_metadata(**values)


def test_frozen_product_and_version_literals() -> None:
    assert PRODUCT_ID == "cat_treaty_learning_lab"
    assert PRODUCT_ROUTE == "/cat-treaty"
    assert ENGINE_VERSION == "ct1.0.0"
    assert SCHEMA_VERSION == "ct1.0"


def test_build_run_metadata_populates_required_fields() -> None:
    metadata = build_default_metadata()

    assert metadata.product_id == PRODUCT_ID
    assert metadata.product_route == PRODUCT_ROUTE
    assert metadata.catalogue_version == "cat-xol-a47eb246"
    assert metadata.engine_version == ENGINE_VERSION
    assert metadata.schema_version == SCHEMA_VERSION
    assert metadata.simulation_seed == 42
    assert metadata.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE


def test_input_hash_is_lowercase_sha256_hex() -> None:
    input_hash = build_default_metadata().input_hash

    assert len(input_hash) == 64
    assert input_hash == input_hash.lower()
    assert set(input_hash) <= set("0123456789abcdef")


def test_equivalent_inputs_produce_identical_hashes() -> None:
    first = build_default_metadata()
    second = build_default_metadata(
        actuarial_inputs={
            "events": BASE_INPUTS["events"],
            "settlement_mode": SettlementMode.PAID_SEPARATELY,
            "shares": TreatyShares(0.9, 0.75),
            "occurrence_limit": 5_000_000.0,
            "attachment": 1_000_000.0,
        }
    )

    assert first.input_hash == second.input_hash


def test_dictionary_key_order_does_not_change_hash() -> None:
    first = build_run_metadata(
        actuarial_inputs={"a": 1, "b": 2},
        catalogue_version="catalogue-v1",
        simulation_seed=1,
    )
    second = build_run_metadata(
        actuarial_inputs={"b": 2, "a": 1},
        catalogue_version="catalogue-v1",
        simulation_seed=1,
    )

    assert first.input_hash == second.input_hash


def test_event_list_order_changes_hash() -> None:
    reversed_inputs = dict(BASE_INPUTS)
    reversed_inputs["events"] = list(reversed(BASE_INPUTS["events"]))

    assert (
        build_default_metadata().input_hash
        != build_default_metadata(
            actuarial_inputs=reversed_inputs,
        ).input_hash
    )


@pytest.mark.parametrize(
    "changed_inputs",
    [
        {**BASE_INPUTS, "attachment": 2_000_000.0},
        {**BASE_INPUTS, "occurrence_limit": 10_000_000.0},
        {
            **BASE_INPUTS,
            "shares": TreatyShares(
                ceded_share=1.0,
                placement_share=0.75,
            ),
        },
        {
            **BASE_INPUTS,
            "settlement_mode":
                SettlementMode.DEDUCTED_FROM_SETTLEMENT,
        },
    ],
)
def test_actuarial_input_change_changes_hash(
    changed_inputs: dict[str, object],
) -> None:
    assert (
        build_default_metadata().input_hash
        != build_default_metadata(
            actuarial_inputs=changed_inputs,
        ).input_hash
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"catalogue_version": "catalogue-v2"},
        {"simulation_seed": 43},
        {"engine_version": "ct1.0.1"},
        {"schema_version": "ct1.1"},
    ],
)
def test_version_or_seed_change_changes_hash(
    overrides: dict[str, object],
) -> None:
    assert (
        build_default_metadata().input_hash
        != build_default_metadata(**overrides).input_hash
    )


def test_dataclass_and_enum_normalization_is_semantic() -> None:
    typed = build_run_metadata(
        actuarial_inputs={
            "shares": TreatyShares(0.9, 0.75),
            "mode": SettlementMode.PAID_SEPARATELY,
        },
        catalogue_version="catalogue-v1",
    )
    plain = build_run_metadata(
        actuarial_inputs={
            "shares": {
                "ceded_share": 0.9,
                "placement_share": 0.75,
            },
            "mode": "paid_separately",
        },
        catalogue_version="catalogue-v1",
    )

    assert typed.input_hash == plain.input_hash


@pytest.mark.parametrize(
    "invalid_value",
    [math.nan, math.inf, -math.inf],
)
def test_nonfinite_numbers_are_rejected(
    invalid_value: float,
) -> None:
    with pytest.raises(ValueError):
        build_run_metadata(
            actuarial_inputs={"invalid": invalid_value},
            catalogue_version="catalogue-v1",
        )


def test_non_string_mapping_keys_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_run_metadata(
            actuarial_inputs={1: "invalid"},
            catalogue_version="catalogue-v1",
        )


def test_unordered_sets_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_run_metadata(
            actuarial_inputs={"events": {"A", "B"}},
            catalogue_version="catalogue-v1",
        )


@pytest.mark.parametrize(
    "catalogue_version",
    ["", "   "],
)
def test_blank_catalogue_version_is_rejected(
    catalogue_version: str,
) -> None:
    with pytest.raises(ValueError):
        build_run_metadata(
            actuarial_inputs={},
            catalogue_version=catalogue_version,
        )


@pytest.mark.parametrize(
    "simulation_seed",
    [-1, 1.5, True],
)
def test_invalid_simulation_seed_is_rejected(
    simulation_seed: object,
) -> None:
    with pytest.raises(ValueError):
        build_run_metadata(
            actuarial_inputs={},
            catalogue_version="catalogue-v1",
            simulation_seed=simulation_seed,
        )


def test_none_simulation_seed_is_allowed() -> None:
    metadata = build_run_metadata(
        actuarial_inputs={},
        catalogue_version="catalogue-v1",
        simulation_seed=None,
    )

    assert metadata.simulation_seed is None


def test_run_metadata_is_immutable() -> None:
    metadata = build_default_metadata()

    with pytest.raises(FrozenInstanceError):
        metadata.input_hash = "changed"  # type: ignore[misc]


def test_ui_state_is_not_an_accepted_hash_argument() -> None:
    with pytest.raises(TypeError):
        build_run_metadata(
            actuarial_inputs={},
            catalogue_version="catalogue-v1",
            ui_state={"selected_tab": "pricing"},
        )