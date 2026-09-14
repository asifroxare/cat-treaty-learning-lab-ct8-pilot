"""EdInsured Catastrophe Treaty Learning Lab."""

from cat_treaty.adapter import (
    PricingEventRecord,
    adapt_event_record,
    adapt_event_records,
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
    SettlementBreakdown,
    SettlementMode,
    TreatyShares,
)
from cat_treaty.shares import (
    apply_contractual_shares,
    calculate_share_factor,
    scale_payable_capacity,
)

__version__ = "0.1.0"

__all__ = [
    "CapacityBasis",
    "CapacityState",
    "CapacityUtilizationStatus",
    "CanonicalEvent",
    "ENGINE_VERSION",
    "PRODUCT_ID",
    "PRODUCT_ROUTE",
    "PricingEventRecord",
    "RunMetadata",
    "SCHEMA_VERSION",
    "SettlementBreakdown",
    "SettlementMode",
    "TreatyShares",
    "__version__",
    "adapt_event_record",
    "adapt_event_records",
    "apply_contractual_shares",
    "build_run_metadata",
    "calculate_share_factor",
    "scale_payable_capacity",
]
