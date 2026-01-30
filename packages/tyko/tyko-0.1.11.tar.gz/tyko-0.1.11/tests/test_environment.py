"""Test environment capture functionality."""

import platform
import sys

from tyko.environment import capture_environment


def test_capture_environment_basic():
    """Test that capture_environment returns expected keys."""
    env = capture_environment()

    # These should always be present
    assert "python_version" in env
    assert "platform" in env
    assert "cpu_count" in env

    # Verify python version format
    assert env["python_version"] == sys.version.split()[0]

    # Verify platform
    assert env["platform"] == platform.platform()

    # CPU count should be a positive integer
    assert isinstance(env["cpu_count"], int)
    assert env["cpu_count"] > 0


def test_capture_environment_optional_fields():
    """Test optional fields that may or may not be present."""
    env = capture_environment()

    # These are optional and depend on installed packages
    # If present, they should have the right types
    if "ram_gb" in env:
        assert isinstance(env["ram_gb"], (int, float))
        assert env["ram_gb"] > 0

    if "gpu_count" in env:
        assert isinstance(env["gpu_count"], int)
        assert env["gpu_count"] >= 0

    if "gpu_names" in env:
        assert isinstance(env["gpu_names"], list)
