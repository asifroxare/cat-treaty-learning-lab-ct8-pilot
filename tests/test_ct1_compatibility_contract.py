"""CT1 versioned request-compatibility and migration tests."""

from dataclasses import FrozenInstanceError

import pytest

from cat_treaty.compatibility import (
    LEGACY_PRICING_API_VERSION,
    CompatibilityMode,
    resolve_compatibility_request,
)
from cat_treaty.metadata import SCHEMA_VERSION
from cat_treaty.models import SettlementMode


def test_existing_request_receives_exact_compatibility_defaults() -> None:
    result = resolve_compatibility_request()

    assert result.mode is CompatibilityMode.LEGACY_PRICING_DEFAULTS
    assert result.schema_version == SCHEMA_VERSION
    assert result.source_api_version == LEGACY_PRICING_API_VERSION
    assert result.shares.ceded_share == 1.0
    assert result.shares.placement_share == 1.0
    assert result.settlement_mode is SettlementMode.PAID_SEPARATELY
    assert result.migration_notices == (
        "legacy_request_defaults_applied",
    )


def test_explicit_ct1_request_has_no_legacy_notice() -> None:
    result = resolve_compatibility_request(
        schema_version="ct1.0",
        ceded_share=0.9,
        placement_share=0.75,
        settlement_mode="deducted_from_settlement",
    )

    assert result.mode is CompatibilityMode.CANONICAL_CT1
    assert result.shares.ceded_share == 0.9
    assert result.shares.placement_share == 0.75
    assert (
        result.settlement_mode
        is SettlementMode.DEDUCTED_FROM_SETTLEMENT
    )
    assert result.migration_notices == ()


@pytest.mark.parametrize(
    "new_field",
    [
        {"ceded_share": 0.9},
        {"placement_share": 0.75},
        {"settlement_mode": "deducted_from_settlement"},
    ],
)
def test_new_fields_require_explicit_ct1_schema(
    new_field: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="schema_version"):
        resolve_compatibility_request(**new_field)


@pytest.mark.parametrize("schema_version", ["", "1.0", "ct2.0", 1])
def test_unsupported_schema_version_is_rejected(
    schema_version: object,
) -> None:
    with pytest.raises(ValueError, match="schema_version"):
        resolve_compatibility_request(schema_version=schema_version)


@pytest.mark.parametrize(
    "source_api_version",
    ["", "0.9.0", "2.0.0", 1],
)
def test_unsupported_source_api_version_is_rejected(
    source_api_version: object,
) -> None:
    with pytest.raises(ValueError, match="source_api_version"):
        resolve_compatibility_request(
            source_api_version=source_api_version
        )


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("paid_separately", SettlementMode.PAID_SEPARATELY),
        (
            "deducted_from_settlement",
            SettlementMode.DEDUCTED_FROM_SETTLEMENT,
        ),
    ],
)
def test_exact_settlement_literals_are_supported(
    literal: str,
    expected: SettlementMode,
) -> None:
    result = resolve_compatibility_request(
        schema_version="ct1.0",
        settlement_mode=literal,
    )

    assert result.settlement_mode is expected


@pytest.mark.parametrize(
    "invalid_mode",
    ["", "deducted", "Paid_Separately", 1, True],
)
def test_unknown_settlement_mode_is_rejected(
    invalid_mode: object,
) -> None:
    with pytest.raises(ValueError, match="settlement_mode"):
        resolve_compatibility_request(
            schema_version="ct1.0",
            settlement_mode=invalid_mode,
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("ceded_share", -0.01),
        ("ceded_share", 1.01),
        ("placement_share", -0.01),
        ("placement_share", 1.01),
    ],
)
def test_invalid_explicit_share_is_rejected(
    field_name: str,
    invalid_value: float,
) -> None:
    with pytest.raises(ValueError):
        resolve_compatibility_request(
            schema_version="ct1.0",
            **{field_name: invalid_value},
        )


def test_omitted_canonical_fields_use_documented_defaults() -> None:
    result = resolve_compatibility_request(schema_version="ct1.0")

    assert result.mode is CompatibilityMode.CANONICAL_CT1
    assert result.shares.ceded_share == 1.0
    assert result.shares.placement_share == 1.0
    assert result.settlement_mode is SettlementMode.PAID_SEPARATELY
    assert result.migration_notices == ()


def test_resolution_is_immutable() -> None:
    result = resolve_compatibility_request()

    with pytest.raises(FrozenInstanceError):
        result.schema_version = "changed"  # type: ignore[misc]
