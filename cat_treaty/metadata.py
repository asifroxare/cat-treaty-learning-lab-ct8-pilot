"""Deterministic CT1 run metadata and actuarial-input hashing."""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Integral, Real
from typing import Any

from cat_treaty.models import CapacityBasis


PRODUCT_ID = "cat_treaty_learning_lab"
PRODUCT_ROUTE = "/cat-treaty"
ENGINE_VERSION = "ct1.0.0"
SCHEMA_VERSION = "ct1.0"


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Reproducibility and product-identity metadata for one treaty run."""

    product_id: str
    product_route: str
    catalogue_version: str
    engine_version: str
    schema_version: str
    simulation_seed: int | None
    input_hash: str
    capacity_basis: CapacityBasis


def _require_non_blank_string(field_name: str, value: object) -> str:
    """Validate and return a non-empty version or identity string."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")

    return value


def _normalize_for_hash(value: Any) -> Any:
    """Convert supported actuarial values to stable JSON-compatible values."""

    if isinstance(value, Enum):
        return _normalize_for_hash(value.value)

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _normalize_for_hash(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(
                    "actuarial input mapping keys must be strings"
                )
            normalized[key] = _normalize_for_hash(item)

        return normalized

    if isinstance(value, (list, tuple)):
        return [_normalize_for_hash(item) for item in value]

    if isinstance(value, (set, frozenset)):
        raise ValueError(
            "unordered sets are not supported in actuarial inputs"
        )

    if value is None or isinstance(value, (str, bool)):
        return value

    if isinstance(value, Integral):
        return int(value)

    if isinstance(value, Real):
        numeric_value = float(value)

        if not math.isfinite(numeric_value):
            raise ValueError(
                "actuarial input numbers must be finite"
            )

        return numeric_value

    raise ValueError(
        f"unsupported actuarial input type: {type(value).__name__}"
    )


def _validate_simulation_seed(
    simulation_seed: object,
) -> int | None:
    """Require a non-negative integer seed or an explicit null."""

    if simulation_seed is None:
        return None

    if (
        isinstance(simulation_seed, bool)
        or not isinstance(simulation_seed, int)
        or simulation_seed < 0
    ):
        raise ValueError(
            "simulation_seed must be a non-negative integer or null"
        )

    return simulation_seed


def _calculate_input_hash(
    *,
    actuarial_inputs: Mapping[str, Any],
    catalogue_version: str,
    engine_version: str,
    schema_version: str,
    simulation_seed: int | None,
) -> str:
    """Return SHA-256 for normalized actuarial inputs and version metadata."""

    payload = {
        "actuarial_inputs": _normalize_for_hash(actuarial_inputs),
        "capacity_basis": CapacityBasis.PAYABLE_PLACED_SHARE.value,
        "catalogue_version": catalogue_version,
        "engine_version": engine_version,
        "product_id": PRODUCT_ID,
        "schema_version": schema_version,
        "simulation_seed": simulation_seed,
    }

    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(serialized).hexdigest()


def build_run_metadata(
    *,
    actuarial_inputs: Mapping[str, Any],
    catalogue_version: str,
    simulation_seed: int | None = None,
    engine_version: str = ENGINE_VERSION,
    schema_version: str = SCHEMA_VERSION,
) -> RunMetadata:
    """Build immutable, reproducible metadata for one canonical treaty run."""

    if not isinstance(actuarial_inputs, Mapping):
        raise ValueError("actuarial_inputs must be a mapping")

    validated_catalogue_version = _require_non_blank_string(
        "catalogue_version",
        catalogue_version,
    )
    validated_engine_version = _require_non_blank_string(
        "engine_version",
        engine_version,
    )
    validated_schema_version = _require_non_blank_string(
        "schema_version",
        schema_version,
    )
    validated_seed = _validate_simulation_seed(simulation_seed)

    input_hash = _calculate_input_hash(
        actuarial_inputs=actuarial_inputs,
        catalogue_version=validated_catalogue_version,
        engine_version=validated_engine_version,
        schema_version=validated_schema_version,
        simulation_seed=validated_seed,
    )

    return RunMetadata(
        product_id=PRODUCT_ID,
        product_route=PRODUCT_ROUTE,
        catalogue_version=validated_catalogue_version,
        engine_version=validated_engine_version,
        schema_version=validated_schema_version,
        simulation_seed=validated_seed,
        input_hash=input_hash,
        capacity_basis=CapacityBasis.PAYABLE_PLACED_SHARE,
    )