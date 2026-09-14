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
        "SettlementBreakdown",
        "SettlementMode",
        "TreatyShares",
        "ENGINE_VERSION",
        "PRODUCT_ID",
        "PRODUCT_ROUTE",
        "SCHEMA_VERSION",
        "RunMetadata",
        "build_run_metadata",
    }

    assert expected_exports.issubset(set(cat_treaty.__all__))

    for export_name in expected_exports:
        assert hasattr(cat_treaty, export_name)