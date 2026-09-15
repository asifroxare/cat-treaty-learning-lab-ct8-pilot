"""CT3 canonical serialization, versioning, and input-hash tests."""

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from cat_treaty.ct3_metadata import (
    CT3_ENGINE_VERSION,
    CT3_SCHEMA_VERSION,
    build_ct3_run_metadata,
    canonicalize_ct3_inputs,
    serialize_ct3_inputs,
)
from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE
from tests.test_ct3_models import LAYERS, program


def metadata(**changes: object):
    values: dict[str, object] = {
        "program_input": program(),
        "source_version": "ct3-638daec",
    }
    values.update(changes)
    return build_ct3_run_metadata(**values)


def test_ct3_version_literals_are_frozen() -> None:
    assert CT3_ENGINE_VERSION == "ct3.0.0"
    assert CT3_SCHEMA_VERSION == "ct3.0"


def test_metadata_binds_product_program_occurrence_ct2_and_versions() -> None:
    result = metadata()

    assert result.product_id == PRODUCT_ID
    assert result.product_route == PRODUCT_ROUTE
    assert result.program_id == "PROGRAM-1"
    assert result.occurrence_id == "OCC-CT3"
    assert result.reporting_currency == "USD"
    assert result.ct2_input_hash == program().ct2_metadata.input_hash
    assert result.source_version == "ct3-638daec"
    assert result.engine_version == CT3_ENGINE_VERSION
    assert result.schema_version == CT3_SCHEMA_VERSION


def test_hashes_are_lowercase_sha256_and_metadata_is_immutable() -> None:
    result = metadata()

    assert len(result.input_hash) == 64
    assert set(result.input_hash) <= set("0123456789abcdef")
    assert len(result.ct2_input_hash) == 64
    with pytest.raises(FrozenInstanceError):
        result.input_hash = "changed"  # type: ignore[misc]


def test_g32_request_order_is_canonicalized() -> None:
    first = program(layers=LAYERS)
    second = program(layers=tuple(reversed(LAYERS)))

    assert serialize_ct3_inputs(first) == serialize_ct3_inputs(second)
    assert metadata(program_input=first).input_hash == metadata(
        program_input=second
    ).input_hash


def test_numeric_equivalence_has_byte_stable_serialization() -> None:
    integer_terms = program(
        layers=(
            replace(LAYERS[0], attachment=10_000_000, occurrence_limit=20_000_000),
            replace(LAYERS[1], attachment=30_000_000, occurrence_limit=30_000_000),
        )
    )

    assert serialize_ct3_inputs(integer_terms) == serialize_ct3_inputs(program())


def test_display_text_and_references_do_not_change_hash() -> None:
    first = program()
    second = replace(
        first,
        description="Different display description",
        source_reference="different-source",
        rule_reference="different-rule",
        layers=tuple(
            replace(
                item,
                description="Different layer label",
                source_reference="different-layer-source",
                rule_reference="different-layer-rule",
            )
            for item in first.layers
        ),
    )

    assert metadata(program_input=first).input_hash == metadata(
        program_input=second
    ).input_hash


@pytest.mark.parametrize(
    "changed",
    [
        program(program_id="PROGRAM-2"),
        program(layers=(replace(LAYERS[0], attachment=11_000_000.0), LAYERS[1])),
        program(layers=(replace(LAYERS[0], occurrence_limit=19_000_000.0), LAYERS[1])),
        program(layers=(replace(LAYERS[0], ceded_share=0.9), LAYERS[1])),
        program(layers=(replace(LAYERS[0], placement_share=0.9), LAYERS[1])),
        program(intentional_gap_acknowledged=True),
        program(
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L1", "L2"),
        ),
        program(
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L2", "L1"),
        ),
    ],
)
def test_contractual_changes_change_hash(changed: object) -> None:
    assert metadata().input_hash != metadata(program_input=changed).input_hash


@pytest.mark.parametrize(
    "changes",
    [
        {"source_version": "ct3-next"},
        {"engine_version": "ct3.0.1"},
        {"schema_version": "ct3.1"},
    ],
)
def test_version_changes_change_hash(changes: dict[str, object]) -> None:
    assert metadata().input_hash != metadata(**changes).input_hash


def test_priority_order_is_preserved_as_contractual_input() -> None:
    first = program(
        overlap_coordination=OverlapCoordination.PRIORITY,
        priority_order=("L1", "L2"),
    )
    second = replace(first, priority_order=("L2", "L1"))

    assert canonicalize_ct3_inputs(first)["priority_order"] == ["L1", "L2"]
    assert serialize_ct3_inputs(first) != serialize_ct3_inputs(second)


def test_serialized_form_is_canonical_json() -> None:
    serialized = serialize_ct3_inputs(program())
    decoded = json.loads(serialized)

    assert serialized.decode("utf-8") == json.dumps(
        decoded,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@pytest.mark.parametrize("invalid", [None, True, {}, LAYERS[0]])
def test_metadata_builder_requires_ct3_program_input(invalid: object) -> None:
    with pytest.raises(TypeError, match="CT3ProgramInput"):
        build_ct3_run_metadata(
            program_input=invalid,  # type: ignore[arg-type]
            source_version="ct3-test",
        )


@pytest.mark.parametrize("field_name", ["source_version", "engine_version", "schema_version"])
@pytest.mark.parametrize("invalid", ["", "   ", None])
def test_blank_version_fields_are_rejected(field_name: str, invalid: object) -> None:
    with pytest.raises(ValueError, match=field_name):
        metadata(**{field_name: invalid})


def test_builder_rejects_ui_state_argument() -> None:
    with pytest.raises(TypeError):
        build_ct3_run_metadata(
            program_input=program(),
            source_version="ct3-test",
            ui_state={"selected_layer": "L1"},
        )
