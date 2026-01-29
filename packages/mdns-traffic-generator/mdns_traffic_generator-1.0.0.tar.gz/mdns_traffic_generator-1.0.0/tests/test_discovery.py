"""Unit tests for discovery module."""

from unittest.mock import MagicMock, patch

import pytest

from mdns_generator.discovery import ServiceDiscovery, ServiceDiscoveryListener


class TestServiceDiscoveryListener:
    """Tests for ServiceDiscoveryListener class."""

    def test_init_with_callbacks(self):
        """Test initialization with callbacks."""
        on_add = MagicMock()
        on_remove = MagicMock()
        on_update = MagicMock()

        listener = ServiceDiscoveryListener(
            on_add=on_add,
            on_remove=on_remove,
            on_update=on_update,
        )

        assert listener._on_add is on_add
        assert listener._on_remove is on_remove
        assert listener._on_update is on_update

    def test_discovered_services_empty(self):
        """Test discovered_services returns empty dict initially."""
        listener = ServiceDiscoveryListener()

        assert listener.discovered_services == {}

    def test_add_service_callback(self):
        """Test that add callback is called."""
        on_add = MagicMock()
        listener = ServiceDiscoveryListener(on_add=on_add)

        mock_zc = MagicMock()
        mock_info = MagicMock()
        mock_info.addresses = [b"\xc0\xa8\x01\x01"]  # 192.168.1.1
        mock_info.properties = {b"version": b"1.0"}
        mock_info.server = "test.local."
        mock_info.port = 8080
        mock_info.weight = 0
        mock_info.priority = 0
        mock_zc.get_service_info.return_value = mock_info

        listener.add_service(mock_zc, "_http._tcp.local.", "test._http._tcp.local.")

        assert on_add.called

    def test_add_service_missing_port(self):
        """Test missing port skips adding service."""
        on_add = MagicMock()
        listener = ServiceDiscoveryListener(on_add=on_add)

        mock_zc = MagicMock()
        mock_info = MagicMock()
        mock_info.addresses = [b"\xc0\xa8\x01\x01"]  # 192.168.1.1
        mock_info.properties = {b"version": b"1.0"}
        mock_info.server = "test.local."
        mock_info.port = None
        mock_info.weight = 0
        mock_info.priority = 0
        mock_zc.get_service_info.return_value = mock_info

        listener.add_service(mock_zc, "_http._tcp.local.", "test._http._tcp.local.")

        assert not on_add.called
        assert listener.discovered_services == {}

    def test_remove_service_callback(self):
        """Test that remove callback is called."""
        on_remove = MagicMock()
        listener = ServiceDiscoveryListener(on_remove=on_remove)

        mock_zc = MagicMock()
        listener.remove_service(mock_zc, "_http._tcp.local.", "test._http._tcp.local.")

        on_remove.assert_called_once_with("test._http._tcp.local.")


class TestServiceDiscovery:
    """Tests for ServiceDiscovery class."""

    @pytest.fixture
    def discovery(self, mock_settings, mock_zeroconf_discovery):
        """Create discovery with mocked Zeroconf."""
        disc = ServiceDiscovery(settings=mock_settings)
        yield disc
        disc.close()

    def test_init_with_default_settings(self, mock_zeroconf_discovery):
        """Test initialization with default settings."""
        with ServiceDiscovery() as disc:
            assert disc._zeroconf is None  # Lazy initialization

    def test_browse_service_type(self, discovery, mock_zeroconf_discovery):
        """Test starting to browse a service type."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            result = discovery.browse_service_type("_http._tcp.local.")

            assert result is True

    def test_browse_service_type_duplicate(self, discovery, mock_zeroconf_discovery):
        """Test browsing same type twice."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            discovery.browse_service_type("_http._tcp.local.")
            result = discovery.browse_service_type("_http._tcp.local.")

            assert result is False

    def test_stop_browsing(self, discovery, mock_zeroconf_discovery):
        """Test stopping browsing for a service type."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            discovery.browse_service_type("_http._tcp.local.")

            result = discovery.stop_browsing("_http._tcp.local.")

            assert result is True

    def test_stop_browsing_not_active(self, discovery, mock_zeroconf_discovery):
        """Test stopping browsing when not active."""
        result = discovery.stop_browsing("_http._tcp.local.")

        assert result is False

    def test_stop_all_browsing(self, discovery, mock_zeroconf_discovery):
        """Test stopping all browsing."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            discovery.browse_service_type("_http._tcp.local.")
            discovery.browse_service_type("_ssh._tcp.local.")

            count = discovery.stop_all_browsing()

            assert count == 2

    def test_get_discovered_services_empty(self, discovery, mock_zeroconf_discovery):
        """Test getting services when none discovered."""
        services = discovery.get_discovered_services()

        assert services == []

    def test_context_manager(self, mock_settings, mock_zeroconf_discovery):
        """Test using discovery as context manager."""
        with ServiceDiscovery(settings=mock_settings) as disc:
            with patch("mdns_generator.discovery.ServiceBrowser"):
                disc.browse_service_type("_http._tcp.local.")

        mock_zeroconf_discovery.close.assert_called()

    def test_common_service_types(self):
        """Test that common service types are defined."""
        assert len(ServiceDiscovery.COMMON_SERVICE_TYPES) > 0
        assert "_http._tcp.local." in ServiceDiscovery.COMMON_SERVICE_TYPES

    def test_browse_common_services(self, discovery, mock_zeroconf_discovery):
        """Test browsing all common services."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            count = discovery.browse_common_services()

            assert count == len(ServiceDiscovery.COMMON_SERVICE_TYPES)

    def test_service_type_normalization(self, discovery, mock_zeroconf_discovery):
        """Test that service type is normalized."""
        with patch("mdns_generator.discovery.ServiceBrowser"):
            # Without .local. suffix
            result = discovery.browse_service_type("_test._tcp")

            assert result is True
