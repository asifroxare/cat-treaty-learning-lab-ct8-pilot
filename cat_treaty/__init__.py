"""EdInsured Catastrophe Treaty Learning Lab."""

from cat_treaty.adapter import (
    PricingEventRecord,
    PricingProcessedEventRecord,
    adapt_event_record,
    adapt_event_records,
    adapt_processed_event_record,
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
    "CanonicalEvent",
    "CanonicalProcessedEvent",
    "ENGINE_VERSION",
    "PRODUCT_ID",
    "PRODUCT_ROUTE",
    "PricingEventRecord",
    "PricingProcessedEventRecord",
    "RunMetadata",
    "SCHEMA_VERSION",
    "SettlementBreakdown",
    "SettlementMode",
    "TreatyShares",
    "__version__",
    "adapt_event_record",
    "adapt_event_records",
    "adapt_processed_event_record",
    "apply_contractual_shares",
    "build_run_metadata",
    "calculate_settlement",
    "calculate_share_factor",
    "scale_payable_capacity",
]
