"""Deterministic CT2 metadata and actuarial-input hashing."""

from dataclasses import dataclass
import hashlib
import json
import re

from cat_treaty.ct2_models import (
    InuringCoverInput,
    InuringWaterfallInput,
    LossBasisInput,
    LossComponent,
)
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE


CT2_ENGINE_VERSION = "ct2.0.0"
CT2_SCHEMA_VERSION = "ct2.0"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _nonblank(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class CT2RunMetadata:
    """Version and identity record for one CT2 waterfall request."""

    product_id: str
    product_route: str
    occurrence_id: str
    reporting_currency: str
    source_version: str
    engine_version: str
    schema_version: str
    input_hash: str

    def __post_init__(self) -> None:
        for field_name in (
            "product_id",
            "product_route",
            "occurrence_id",
            "reporting_currency",
            "source_version",
            "engine_version",
            "schema_version",
            "input_hash",
        ):
            _nonblank(field_name, getattr(self, field_name))
        if self.product_id != PRODUCT_ID:
            raise ValueError("product_id must match the treaty product")
        if self.product_route != PRODUCT_ROUTE:
            raise ValueError("product_route must match the treaty route")
        if _SHA256_PATTERN.fullmatch(self.input_hash) is None:
            raise ValueError("input_hash must be lowercase SHA-256 hex")


def _component_payload(component: LossComponent) -> dict[str, object]:
    return {
        "amount": float(component.amount),
        "category": component.category.value,
        "component_id": component.component_id,
        "included": component.included,
    }


def _loss_basis_payload(basis_input: LossBasisInput) -> dict[str, object]:
    return {
        "components": [
            _component_payload(component)
            for component in sorted(
                basis_input.components,
                key=lambda item: item.component_id,
            )
        ],
        "ground_up_loss": (
            None
            if basis_input.ground_up_loss is None
            else float(basis_input.ground_up_loss)
        ),
        "initial_insured_loss": float(basis_input.initial_insured_loss),
        "occurrence_id": basis_input.occurrence_id,
        "reporting_currency": basis_input.reporting_currency,
        "source_stage_declaration": basis_input.source_stage_declaration,
    }


def _cover_payload(cover: InuringCoverInput) -> dict[str, object]:
    return {
        "aggregate_remaining_before": (
            None
            if cover.aggregate_remaining_before is None
            else float(cover.aggregate_remaining_before)
        ),
        "cession_rate": (
            None if cover.cession_rate is None else float(cover.cession_rate)
        ),
        "cover_id": cover.cover_id,
        "cover_type": cover.cover_type.value,
        "currency": cover.currency,
        "occurrence_limit": (
            None
            if cover.occurrence_limit is None
            else float(cover.occurrence_limit)
        ),
        "order": cover.order,
        "recovery_source_id": cover.recovery_source_id,
        "scope_fraction": float(cover.scope_fraction),
        "supplied_recovery": (
            None
            if cover.supplied_recovery is None
            else float(cover.supplied_recovery)
        ),
        "valuation_mode": cover.valuation_mode.value,
    }


def canonicalize_ct2_inputs(
    waterfall_input: InuringWaterfallInput,
) -> dict[str, object]:
    """Return stable, calculation-relevant CT2 inputs for serialization."""

    if not isinstance(waterfall_input, InuringWaterfallInput):
        raise TypeError("waterfall_input must be an InuringWaterfallInput")
    return {
        "covers": [_cover_payload(cover) for cover in waterfall_input.covers],
        "loss_basis": _loss_basis_payload(
            waterfall_input.loss_basis.basis_input
        ),
    }


def serialize_ct2_inputs(waterfall_input: InuringWaterfallInput) -> bytes:
    """Serialize normalized inputs with stable keys and no NaN values."""

    return json.dumps(
        canonicalize_ct2_inputs(waterfall_input),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def build_ct2_run_metadata(
    *,
    waterfall_input: InuringWaterfallInput,
    source_version: str,
    engine_version: str = CT2_ENGINE_VERSION,
    schema_version: str = CT2_SCHEMA_VERSION,
) -> CT2RunMetadata:
    """Build immutable CT2 metadata and a version-bound input hash."""

    validated_source_version = _nonblank("source_version", source_version)
    validated_engine_version = _nonblank("engine_version", engine_version)
    validated_schema_version = _nonblank("schema_version", schema_version)
    canonical_inputs = canonicalize_ct2_inputs(waterfall_input)
    payload = {
        "actuarial_inputs": canonical_inputs,
        "engine_version": validated_engine_version,
        "product_id": PRODUCT_ID,
        "schema_version": validated_schema_version,
        "source_version": validated_source_version,
    }
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    input_hash = hashlib.sha256(serialized).hexdigest()
    basis_input = waterfall_input.loss_basis.basis_input

    return CT2RunMetadata(
        product_id=PRODUCT_ID,
        product_route=PRODUCT_ROUTE,
        occurrence_id=basis_input.occurrence_id,
        reporting_currency=basis_input.reporting_currency,
        source_version=validated_source_version,
        engine_version=validated_engine_version,
        schema_version=validated_schema_version,
        input_hash=input_hash,
    )
