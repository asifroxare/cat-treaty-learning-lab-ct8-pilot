"""Public-package tests for the Catastrophe Treaty Learning Lab."""

import cat_treaty


def test_package_import_and_version() -> None:
    assert cat_treaty.__version__ == "0.1.0"


def test_ct1_public_package_exports() -> None:
    expected_exports = {
        "CapacityBasis",
        "CapacityState",
        "CapacityUtilizationStatus",
        "CanonicalEvent",
        "CanonicalProcessedEvent",
        "CanonicalPremiumMetrics",
        "CanonicalPricingComponents",
        "CanonicalPricingResult",
        "CanonicalPricingView",
        "CanonicalYearRecord",
        "SettlementBreakdown",
        "SettlementMode",
        "TreatyShares",
        "ENGINE_VERSION",
        "PRODUCT_ID",
        "PRODUCT_ROUTE",
        "PricingEventRecord",
        "PricingProcessedEventRecord",
        "PricingTreatyYearRecord",
        "SCHEMA_VERSION",
        "RunMetadata",
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
    }

    assert expected_exports.issubset(set(cat_treaty.__all__))

    for export_name in expected_exports:
        assert hasattr(cat_treaty, export_name)
