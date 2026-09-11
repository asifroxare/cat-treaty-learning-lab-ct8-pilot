"""Baseline tests for the Catastrophe Treaty Learning Lab project."""


def test_package_import_and_version() -> None:
    import cat_treaty

    assert cat_treaty.__version__ == "0.1.0"