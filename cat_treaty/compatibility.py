"""CT1 versioned request compatibility and migration rules."""

from dataclasses import dataclass
from enum import Enum

from cat_treaty.metadata import SCHEMA_VERSION
from cat_treaty.models import SettlementMode, TreatyShares


LEGACY_PRICING_API_VERSION = "1.0.0"


class CompatibilityMode(str, Enum):
    """How a request entered the CT1 compatibility boundary."""

    LEGACY_PRICING_DEFAULTS = "legacy_pricing_defaults"
    CANONICAL_CT1 = "canonical_ct1"


@dataclass(frozen=True, slots=True)
class CompatibilityResolution:
    """Validated, explicit CT1 interpretation of one request."""

    mode: CompatibilityMode
    schema_version: str
    source_api_version: str
    shares: TreatyShares
    settlement_mode: SettlementMode
    migration_notices: tuple[str, ...]


def _resolve_settlement_mode(value: object) -> SettlementMode:
    if value is None:
        return SettlementMode.PAID_SEPARATELY
    if not isinstance(value, str):
        raise ValueError("settlement_mode is unsupported")
    try:
        return SettlementMode(value)
    except ValueError as exc:
        raise ValueError("settlement_mode is unsupported") from exc


def resolve_compatibility_request(
    *,
    schema_version: object = None,
    source_api_version: object = LEGACY_PRICING_API_VERSION,
    ceded_share: object = None,
    placement_share: object = None,
    settlement_mode: object = None,
) -> CompatibilityResolution:
    """Resolve legacy defaults or an explicit canonical CT1 request.

    Legacy requests may omit every new CT1 field. Any use of a new field
    requires the explicit CT1 schema version, preventing silent reinterpretation.
    """

    if source_api_version != LEGACY_PRICING_API_VERSION:
        raise ValueError(
            "source_api_version must be the supported pricing API version "
            f"{LEGACY_PRICING_API_VERSION}"
        )

    new_fields_supplied = any(
        value is not None
        for value in (ceded_share, placement_share, settlement_mode)
    )

    if schema_version is None:
        if new_fields_supplied:
            raise ValueError(
                "schema_version must be explicit when CT1 fields are supplied"
            )
        mode = CompatibilityMode.LEGACY_PRICING_DEFAULTS
        notices = ("legacy_request_defaults_applied",)
    else:
        if schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be the supported value {SCHEMA_VERSION}"
            )
        mode = CompatibilityMode.CANONICAL_CT1
        notices = ()

    shares = TreatyShares(
        ceded_share=1.0 if ceded_share is None else ceded_share,
        placement_share=(
            1.0 if placement_share is None else placement_share
        ),
    )

    return CompatibilityResolution(
        mode=mode,
        schema_version=SCHEMA_VERSION,
        source_api_version=LEGACY_PRICING_API_VERSION,
        shares=shares,
        settlement_mode=_resolve_settlement_mode(settlement_mode),
        migration_notices=notices,
    )
