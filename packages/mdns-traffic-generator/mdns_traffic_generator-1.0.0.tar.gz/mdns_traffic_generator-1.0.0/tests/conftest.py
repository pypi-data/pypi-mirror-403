"""Pytest configuration and fixtures for MDNS Traffic Generator tests."""

from unittest.mock import MagicMock, patch

import pytest

from mdns_generator.config import MDNSSettings, reload_settings
from mdns_generator.service import ServiceConfig


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings cache before each test."""
    reload_settings()
    yield
    reload_settings()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a temporary config directory."""
    return tmp_path


@pytest.fixture
def mock_settings():
    """Provide test settings."""
    return MDNSSettings(
        service_name="test-service",
        service_type="_test._tcp.local.",
        service_port=9999,
        broadcast_interval=1.0,
        service_count=2,
        log_level="DEBUG",
    )


@pytest.fixture
def sample_service_config():
    """Provide a sample service configuration."""
    return ServiceConfig(
        name="test-service",
        service_type="_http._tcp.local.",
        port=8080,
        properties={"version": "1.0", "test": "true"},
    )


@pytest.fixture
def mock_zeroconf():
    """Mock Zeroconf instance."""
    with patch("mdns_generator.generator.Zeroconf") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_zeroconf_discovery():
    """Mock Zeroconf instance for discovery."""
    with patch("mdns_generator.discovery.Zeroconf") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance
