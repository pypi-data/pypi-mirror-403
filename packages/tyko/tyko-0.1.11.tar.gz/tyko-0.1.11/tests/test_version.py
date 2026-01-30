"""Test version information."""

import tyko


def test_version_exists() -> None:
    """Test that version is defined."""
    assert hasattr(tyko, "__version__")
    assert isinstance(tyko.__version__, str)
    assert len(tyko.__version__) > 0


def test_version_format() -> None:
    """Test that version follows semantic versioning."""
    parts = tyko.__version__.split(".")
    assert len(parts) >= 2  # At least major.minor
    assert parts[0].isdigit()  # Major version is numeric
    assert parts[1].isdigit()  # Minor version is numeric
