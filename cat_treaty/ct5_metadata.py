"""CT5 canonical serialization and CT4-bound deterministic identities."""

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import re

from cat_treaty.ct4_metadata import (
    CT4_ENGINE_VERSION,
    CT4_SCHEMA_VERSION,
    build_ct4_run_identity,
)
from cat_treaty.ct4_models import CT4RunIdentity, CT4TailAnalytics
from cat_treaty.ct5_analytics import calculate_ct5_analytics
from cat_treaty.ct5_analytics_models import CT5Analytics
from cat_treaty.ct5_models import CT5CatalogueResult, CT5TreatyTerms
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE


CT5_ENGINE_VERSION = "ct5.0.0"
CT5_SCHEMA_VERSION = "ct5.0"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_DISPLAY_FIELDS = {
    "description",
    "message",
    "rule_reference",
    "source_reference",
    "trace_references",
}


@dataclass(frozen=True, slots=True)
class CT5RunIdentity:
    simulation_id: str
    ct4_input_hash: str
    ct4_result_hash: str
    input_hash: str
    result_hash: str
    engine_version: str
    schema_version: str

    def __post_init__(self) -> None:
        for name in ("simulation_id", "engine_version", "schema_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        for name in ("ct4_input_hash", "ct4_result_hash", "input_hash", "result_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise ValueError(f"{name} must be lowercase SHA-256 hex")


def validate_ct4_identity(
    *,
    ct5_result: CT5CatalogueResult,
    ct4_analytics: CT4TailAnalytics,
    ct4_identity: CT4RunIdentity,
) -> None:
    """Reproduce and require the exact authoritative CT4 identity."""

    if not isinstance(ct5_result, CT5CatalogueResult):
        raise ValueError("ct5_result must be CT5CatalogueResult")
    if not isinstance(ct4_identity, CT4RunIdentity):
        raise ValueError("ct4_identity must be CT4RunIdentity")
    if ct4_identity.engine_version != CT4_ENGINE_VERSION or ct4_identity.schema_version != CT4_SCHEMA_VERSION:
        raise ValueError("CT4 engine/schema identity is not supported by CT5 v1")
    simulation_input = (
        ct5_result.ct4_result.simulation_input
        if hasattr(ct5_result.ct4_result, "simulation_input")
        else ct5_result.ct4_simulation_input
    )
    if simulation_input is None:
        raise ValueError("CT5 result has no CT4 simulation input")
    expected = build_ct4_run_identity(
        simulation_input=simulation_input,
        result=ct5_result.ct4_result,
        analytics=ct4_analytics,
    )
    if ct4_identity != expected:
        raise ValueError("CT4 identity reproduction failed")


def canonicalize_ct5_inputs(
    treaty_terms: CT5TreatyTerms,
    ct4_identity: CT4RunIdentity,
    *,
    engine_version: str = CT5_ENGINE_VERSION,
    schema_version: str = CT5_SCHEMA_VERSION,
) -> dict[str, object]:
    if not isinstance(treaty_terms, CT5TreatyTerms):
        raise ValueError("treaty_terms must be CT5TreatyTerms")
    if not isinstance(ct4_identity, CT4RunIdentity):
        raise ValueError("ct4_identity must be CT4RunIdentity")
    return {
        "absolute_currency_tolerance": 1e-6,
        "ct4_engine_version": ct4_identity.engine_version,
        "ct4_input_hash": ct4_identity.input_hash,
        "ct4_result_hash": ct4_identity.result_hash,
        "ct4_schema_version": ct4_identity.schema_version,
        "ct5_engine_version": _nonblank("engine_version", engine_version),
        "ct5_schema_version": _nonblank("schema_version", schema_version),
        "product_id": PRODUCT_ID,
        "product_route": PRODUCT_ROUTE,
        "relative_tolerance": 1e-12,
        "simulation_id": ct4_identity.simulation_id,
        "treaty_terms": {
            "program_id": treaty_terms.program_id,
            "layers": [
                _normalize(item)
                for item in sorted(treaty_terms.layer_terms, key=lambda value: value.layer_id)
            ],
        },
    }


def serialize_ct5_inputs(
    treaty_terms: CT5TreatyTerms,
    ct4_identity: CT4RunIdentity,
    *,
    engine_version: str = CT5_ENGINE_VERSION,
    schema_version: str = CT5_SCHEMA_VERSION,
) -> bytes:
    return _serialize(
        canonicalize_ct5_inputs(
            treaty_terms,
            ct4_identity,
            engine_version=engine_version,
            schema_version=schema_version,
        )
    )


def canonicalize_ct5_result(
    result: CT5CatalogueResult,
    analytics: CT5Analytics,
) -> dict[str, object]:
    if not isinstance(result, CT5CatalogueResult):
        raise ValueError("result must be CT5CatalogueResult")
    if not isinstance(analytics, CT5Analytics):
        raise ValueError("analytics must be CT5Analytics")
    if analytics != calculate_ct5_analytics(result):
        raise ValueError("CT5 analytics do not match the completed ledgers")
    return {
        "annual_rows": _normalize(result.annual_rows),
        "analytics": _normalize(analytics),
        "completed": result.completed,
        "occurrence_rows": _normalize(result.occurrence_rows),
    }


def serialize_ct5_result(
    result: CT5CatalogueResult,
    analytics: CT5Analytics,
) -> bytes:
    return _serialize(canonicalize_ct5_result(result, analytics))


def build_ct5_run_identity(
    *,
    result: CT5CatalogueResult,
    analytics: CT5Analytics,
    ct4_analytics: CT4TailAnalytics,
    ct4_identity: CT4RunIdentity,
    engine_version: str = CT5_ENGINE_VERSION,
    schema_version: str = CT5_SCHEMA_VERSION,
) -> CT5RunIdentity:
    validate_ct4_identity(
        ct5_result=result,
        ct4_analytics=ct4_analytics,
        ct4_identity=ct4_identity,
    )
    engine = _nonblank("engine_version", engine_version)
    schema = _nonblank("schema_version", schema_version)
    inputs = canonicalize_ct5_inputs(
        result.treaty_terms,
        ct4_identity,
        engine_version=engine,
        schema_version=schema,
    )
    input_hash = _hash(inputs)
    result_hash = _hash(
        {
            "canonical_result": canonicalize_ct5_result(result, analytics),
            "ct5_engine_version": engine,
            "ct5_schema_version": schema,
            "input_hash": input_hash,
        }
    )
    return CT5RunIdentity(
        simulation_id=ct4_identity.simulation_id,
        ct4_input_hash=ct4_identity.input_hash,
        ct4_result_hash=ct4_identity.result_hash,
        input_hash=input_hash,
        result_hash=result_hash,
        engine_version=engine,
        schema_version=schema,
    )


def _normalize(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            field.name: _normalize(getattr(value, field.name))
            for field in fields(value)
            if field.name not in _DISPLAY_FIELDS
        }
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("canonical values must be finite")
        return value
    return value


def _serialize(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(_serialize(payload)).hexdigest()


def _nonblank(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value
