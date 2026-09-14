"""CT2 canonical serialization and metadata tests."""

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from cat_treaty.ct2_metadata import (
    CT2_ENGINE_VERSION,
    CT2_SCHEMA_VERSION,
    CT2RunMetadata,
    build_ct2_run_metadata,
    canonicalize_ct2_inputs,
    serialize_ct2_inputs,
)
from cat_treaty.ct2_models import (
    InuringCoverInput,
    InuringCoverType,
    InuringValuationMode,
    InuringWaterfallInput,
    LossBasisInput,
    LossComponent,
    LossComponentCategory,
)
from cat_treaty.loss_basis import build_loss_basis
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE


def component(
    component_id: str,
    amount: float,
    *,
    label: str | None = None,
) -> LossComponent:
    return LossComponent(
        component_id=component_id,
        category=LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
        label=component_id if label is None else label,
        amount=amount,
        included=True,
        source_reference="scenario",
        rule_reference="F03",
    )


def build_inputs(
    *,
    initial_insured_loss: float = 1_000.0,
    components: tuple[LossComponent, ...] = (),
    description: str = "Quota share",
) -> InuringWaterfallInput:
    loss_basis = build_loss_basis(
        LossBasisInput(
            occurrence_id="OCC-001",
            reporting_currency="USD",
            source_stage_declaration="insured_loss_after_policy_terms",
            source_reference="catalogue:1",
            initial_insured_loss=initial_insured_loss,
            components=components,
        )
    )
    cover = InuringCoverInput(
        cover_id="QS-1",
        cover_type=InuringCoverType.QUOTA_SHARE,
        order=1,
        valuation_mode=InuringValuationMode.CALCULATED_PROPORTIONAL,
        scope_fraction=1.0,
        cession_rate=0.4,
        currency="USD",
        description=description,
        source_reference="contract:qs",
        rule_reference="F05-F08",
    )
    return InuringWaterfallInput(loss_basis=loss_basis, covers=(cover,))


BASE_INPUTS = build_inputs(
    components=(component("lae-b", 20.0), component("lae-a", 10.0))
)


def metadata(**changes: object) -> CT2RunMetadata:
    values: dict[str, object] = {
        "waterfall_input": BASE_INPUTS,
        "source_version": "cat-xol-a47eb246",
    }
    values.update(changes)
    return build_ct2_run_metadata(**values)


def test_ct2_version_literals_are_frozen() -> None:
    assert CT2_ENGINE_VERSION == "ct2.0.0"
    assert CT2_SCHEMA_VERSION == "ct2.0"


def test_metadata_contains_product_source_and_occurrence_identity() -> None:
    result = metadata()

    assert result.product_id == PRODUCT_ID
    assert result.product_route == PRODUCT_ROUTE
    assert result.occurrence_id == "OCC-001"
    assert result.reporting_currency == "USD"
    assert result.source_version == "cat-xol-a47eb246"
    assert result.engine_version == CT2_ENGINE_VERSION
    assert result.schema_version == CT2_SCHEMA_VERSION


def test_input_hash_is_lowercase_sha256_and_metadata_is_immutable() -> None:
    result = metadata()

    assert len(result.input_hash) == 64
    assert set(result.input_hash) <= set("0123456789abcdef")
    with pytest.raises(FrozenInstanceError):
        result.input_hash = "changed"  # type: ignore[misc]


def test_equivalent_inputs_have_byte_stable_serialization_and_hash() -> None:
    first = build_inputs(initial_insured_loss=1_000)
    second = build_inputs(initial_insured_loss=1_000.0)

    assert serialize_ct2_inputs(first) == serialize_ct2_inputs(second)
    assert metadata(waterfall_input=first).input_hash == metadata(
        waterfall_input=second
    ).input_hash


def test_component_order_is_canonicalized_by_component_id() -> None:
    first = build_inputs(
        components=(component("b", 20.0), component("a", 10.0))
    )
    second = build_inputs(
        components=(component("a", 10.0), component("b", 20.0))
    )

    assert serialize_ct2_inputs(first) == serialize_ct2_inputs(second)
    assert canonicalize_ct2_inputs(first)["loss_basis"] == (
        canonicalize_ct2_inputs(second)["loss_basis"]
    )


def test_nonactuarial_labels_descriptions_and_references_do_not_change_hash() -> None:
    first = build_inputs(
        components=(component("lae", 10.0, label="LAE"),),
        description="First description",
    )
    changed_component = replace(
        first.loss_basis.basis_input.components[0],
        label="Different display label",
        source_reference="different-source",
        rule_reference="different-rule",
    )
    changed_basis_input = replace(
        first.loss_basis.basis_input,
        source_reference="different-catalogue-reference",
        components=(changed_component,),
    )
    second = InuringWaterfallInput(
        loss_basis=build_loss_basis(changed_basis_input),
        covers=(
            replace(
                first.covers[0],
                description="Different description",
                source_reference="different-contract-reference",
                rule_reference="different-cover-rule",
            ),
        ),
    )

    assert metadata(waterfall_input=first).input_hash == metadata(
        waterfall_input=second
    ).input_hash


@pytest.mark.parametrize(
    "changed",
    [
        build_inputs(initial_insured_loss=1_001.0),
        InuringWaterfallInput(
            loss_basis=BASE_INPUTS.loss_basis,
            covers=(replace(BASE_INPUTS.covers[0], cession_rate=0.5),),
        ),
        InuringWaterfallInput(
            loss_basis=BASE_INPUTS.loss_basis,
            covers=(replace(BASE_INPUTS.covers[0], scope_fraction=0.5),),
        ),
    ],
)
def test_actuarial_changes_change_hash(changed: InuringWaterfallInput) -> None:
    assert metadata().input_hash != metadata(waterfall_input=changed).input_hash


@pytest.mark.parametrize(
    "changes",
    [
        {"source_version": "cat-xol-next"},
        {"engine_version": "ct2.0.1"},
        {"schema_version": "ct2.1"},
    ],
)
def test_version_changes_change_hash(changes: dict[str, object]) -> None:
    assert metadata().input_hash != metadata(**changes).input_hash


def test_serialized_form_is_canonical_json() -> None:
    serialized = serialize_ct2_inputs(BASE_INPUTS)
    decoded = json.loads(serialized)

    assert serialized.decode("utf-8") == json.dumps(
        decoded,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@pytest.mark.parametrize("invalid", [None, True, {}, BASE_INPUTS.loss_basis])
def test_metadata_requires_validated_waterfall_input(invalid: object) -> None:
    with pytest.raises(TypeError, match="InuringWaterfallInput"):
        build_ct2_run_metadata(
            waterfall_input=invalid,  # type: ignore[arg-type]
            source_version="source-v1",
        )


@pytest.mark.parametrize("field_name", ["source_version", "engine_version", "schema_version"])
@pytest.mark.parametrize("invalid", ["", "   ", None])
def test_blank_version_fields_are_rejected(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        metadata(**{field_name: invalid})


def test_builder_rejects_ui_state_argument() -> None:
    with pytest.raises(TypeError):
        build_ct2_run_metadata(
            waterfall_input=BASE_INPUTS,
            source_version="source-v1",
            ui_state={"selected_tab": "inuring"},
        )
