"""Deterministic CT3 metadata and canonical actuarial-input hashing."""

import hashlib
import json

from cat_treaty.ct3_models import CT3ProgramInput, CT3RunMetadata
from cat_treaty.geometry import geometry_order
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE


CT3_ENGINE_VERSION = "ct3.0.0"
CT3_SCHEMA_VERSION = "ct3.0"


def _nonblank(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def canonicalize_ct3_inputs(program_input: CT3ProgramInput) -> dict[str, object]:
    """Return stable calculation-relevant CT3 inputs."""

    if not isinstance(program_input, CT3ProgramInput):
        raise TypeError("program_input must be CT3ProgramInput")
    basis = program_input.ct2_result.loss_basis.basis_input
    return {
        "ct2": {
            "completion_status": program_input.ct2_result.completion_status.value,
            "input_hash": program_input.ct2_metadata.input_hash,
            "occurrence_id": basis.occurrence_id,
            "reporting_currency": basis.reporting_currency,
            "subject_loss": float(program_input.ct2_result.cat_xl_subject_loss),
        },
        "intentional_gap_acknowledged": (
            program_input.intentional_gap_acknowledged
        ),
        "layers": [
            {
                "attachment": float(layer.attachment),
                "ceded_share": float(layer.ceded_share),
                "currency": layer.currency,
                "layer_id": layer.layer_id,
                "occurrence_limit": float(layer.occurrence_limit),
                "placement_share": float(layer.placement_share),
            }
            for layer in geometry_order(program_input.layers)
        ],
        "overlap_coordination": program_input.overlap_coordination.value,
        "priority_order": (
            None
            if program_input.priority_order is None
            else list(program_input.priority_order)
        ),
        "program_id": program_input.program_id,
    }


def serialize_ct3_inputs(program_input: CT3ProgramInput) -> bytes:
    """Serialize CT3 normalized inputs as canonical JSON bytes."""

    return json.dumps(
        canonicalize_ct3_inputs(program_input),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def build_ct3_run_metadata(
    *,
    program_input: CT3ProgramInput,
    source_version: str,
    engine_version: str = CT3_ENGINE_VERSION,
    schema_version: str = CT3_SCHEMA_VERSION,
) -> CT3RunMetadata:
    """Build immutable version-bound CT3 run metadata."""

    if not isinstance(program_input, CT3ProgramInput):
        raise TypeError("program_input must be CT3ProgramInput")
    validated_source = _nonblank("source_version", source_version)
    validated_engine = _nonblank("engine_version", engine_version)
    validated_schema = _nonblank("schema_version", schema_version)
    payload = {
        "actuarial_inputs": canonicalize_ct3_inputs(program_input),
        "engine_version": validated_engine,
        "product_id": PRODUCT_ID,
        "schema_version": validated_schema,
        "source_version": validated_source,
    }
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    basis = program_input.ct2_result.loss_basis.basis_input
    return CT3RunMetadata(
        product_id=PRODUCT_ID,
        product_route=PRODUCT_ROUTE,
        program_id=program_input.program_id,
        occurrence_id=basis.occurrence_id,
        reporting_currency=basis.reporting_currency,
        ct2_input_hash=program_input.ct2_metadata.input_hash,
        source_version=validated_source,
        engine_version=validated_engine,
        schema_version=validated_schema,
        input_hash=hashlib.sha256(serialized).hexdigest(),
    )
