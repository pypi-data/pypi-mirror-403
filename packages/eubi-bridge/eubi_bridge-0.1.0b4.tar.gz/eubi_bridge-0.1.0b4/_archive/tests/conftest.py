"""Pytest configuration and fixtures for EuBI-Bridge tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture(scope="session")
def expected_outputs_dir():
    """Return path to expected outputs directory."""
    return Path(__file__).parent / "fixtures" / "expected_outputs"


@pytest.fixture
def tmp_output_dir():
    """Create a temporary output directory for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def bridge_instance():
    """Create a fresh EuBI-Bridge instance for testing."""
    from eubi_bridge.ebridge import EuBIBridge
    
    with tempfile.TemporaryDirectory() as config_dir:
        bridge = EuBIBridge(configpath=config_dir)
        yield bridge
        bridge._cleanup_temp_dir()
