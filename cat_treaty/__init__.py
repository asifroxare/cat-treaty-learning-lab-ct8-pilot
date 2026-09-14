"""EdInsured Catastrophe Treaty Learning Lab."""

from cat_treaty.compatibility import (
    LEGACY_PRICING_API_VERSION,
    CompatibilityMode,
    CompatibilityResolution,
    resolve_compatibility_request,
)
from cat_treaty.adapter import (
    PricingEventRecord,
    PricingProcessedEventRecord,
    PricingTreatyYearRecord,
    adapt_event_record,
    adapt_event_records,
    adapt_pricing_result,
    adapt_processed_event_record,
    adapt_treaty_year_record,
)
from cat_treaty.metadata import (
    ENGINE_VERSION,
    PRODUCT_ID,
    PRODUCT_ROUTE,
    SCHEMA_VERSION,
    RunMetadata,
    build_run_metadata,
)
from cat_treaty.models import (
    CapacityBasis,
    CapacityState,
    CapacityUtilizationStatus,
    CanonicalEvent,
    CanonicalProcessedEvent,
    CanonicalPremiumMetrics,
    CanonicalPricingComponents,
    CanonicalPricingResult,
    CanonicalPricingView,
    CanonicalYearRecord,
    SettlementBreakdown,
    SettlementMode,
    TreatyShares,
)
from cat_treaty.shares import (
    apply_contractual_shares,
    calculate_share_factor,
    scale_payable_capacity,
)
from cat_treaty.settlement import calculate_settlement

__version__ = "0.1.0"

__all__ = [
    "CapacityBasis",
    "CapacityState",
    "CapacityUtilizationStatus",
    "CompatibilityMode",
    "CompatibilityResolution",
    "CanonicalEvent",
    "CanonicalProcessedEvent",
    "CanonicalPremiumMetrics",
    "CanonicalPricingComponents",
    "CanonicalPricingResult",
    "CanonicalPricingView",
    "CanonicalYearRecord",
    "ENGINE_VERSION",
    "LEGACY_PRICING_API_VERSION",
    "PRODUCT_ID",
    "PRODUCT_ROUTE",
    "PricingEventRecord",
    "PricingProcessedEventRecord",
    "PricingTreatyYearRecord",
    "RunMetadata",
    "SCHEMA_VERSION",
    "SettlementBreakdown",
    "SettlementMode",
    "TreatyShares",
    "__version__",
    "adapt_event_record",
    "adapt_event_records",
    "adapt_pricing_result",
    "adapt_processed_event_record",
    "adapt_treaty_year_record",
    "apply_contractual_shares",
    "build_run_metadata",
    "calculate_settlement",
    "calculate_share_factor",
    "scale_payable_capacity",
    "resolve_compatibility_request",
]
