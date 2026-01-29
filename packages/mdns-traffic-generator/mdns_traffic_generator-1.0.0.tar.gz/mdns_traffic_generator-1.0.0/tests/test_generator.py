"""Unit tests for generator module."""

import threading

import pytest

from mdns_generator.generator import MDNSGenerator
from mdns_generator.service import ServiceConfig


class TestMDNSGenerator:
    """Tests for MDNSGenerator class."""

    @pytest.fixture
    def generator(self, mock_settings, mock_zeroconf):
        """Create generator with mocked Zeroconf."""
        gen = MDNSGenerator(settings=mock_settings)
        yield gen
        gen.close()

    def test_init_with_default_settings(self, mock_zeroconf):
        """Test initialization with default settings."""
        with MDNSGenerator() as gen:
            assert gen.is_running is False
            assert gen.registered_services == []

    def test_init_with_custom_settings(self, mock_settings, mock_zeroconf):
        """Test initialization with custom settings."""
        with MDNSGenerator(settings=mock_settings) as gen:
            assert gen.is_running is False

    def test_register_service_success(
        self, generator, mock_zeroconf, sample_service_config
    ):
        """Test successful service registration."""
        result = generator.register_service(sample_service_config)

        assert result is True
        assert len(generator.registered_services) == 1
        mock_zeroconf.register_service.assert_called_once()

    def test_register_service_failure(
        self, generator, mock_zeroconf, sample_service_config
    ):
        """Test service registration failure."""
        mock_zeroconf.register_service.side_effect = Exception("Registration failed")

        result = generator.register_service(sample_service_config)

        assert result is False
        assert len(generator.registered_services) == 0

    def test_register_multiple_services(self, generator, mock_zeroconf):
        """Test registering multiple services."""
        configs = [
            ServiceConfig(name="svc1", service_type="_http._tcp.local.", port=8080),
            ServiceConfig(name="svc2", service_type="_http._tcp.local.", port=8081),
            ServiceConfig(name="svc3", service_type="_http._tcp.local.", port=8082),
        ]

        count = generator.register_services(configs)

        assert count == 3
        assert len(generator.registered_services) == 3

    def test_unregister_service(self, generator, mock_zeroconf, sample_service_config):
        """Test unregistering a service."""
        generator.register_service(sample_service_config)
        full_name = sample_service_config.full_name

        result = generator.unregister_service(full_name)

        assert result is True
        assert len(generator.registered_services) == 0

    def test_unregister_nonexistent_service(self, generator, mock_zeroconf):
        """Test unregistering a service that doesn't exist."""
        result = generator.unregister_service("nonexistent._http._tcp.local.")

        assert result is False

    def test_unregister_all_services(self, generator, mock_zeroconf):
        """Test unregistering all services."""
        configs = [
            ServiceConfig(name="svc1", service_type="_http._tcp.local.", port=8080),
            ServiceConfig(name="svc2", service_type="_http._tcp.local.", port=8081),
        ]
        generator.register_services(configs)

        count = generator.unregister_all_services()

        assert count == 2
        assert len(generator.registered_services) == 0

    def test_start_broadcasting(self, generator, mock_zeroconf, sample_service_config):
        """Test starting broadcast loop."""
        generator.register_service(sample_service_config)

        result = generator.start_broadcasting(interval=0.1)

        assert result is True
        assert generator.is_running is True

        # Stop to clean up
        generator.stop_broadcasting()

    def test_start_broadcasting_already_running(
        self, generator, mock_zeroconf, sample_service_config
    ):
        """Test starting broadcast when already running."""
        generator.register_service(sample_service_config)
        generator.start_broadcasting(interval=0.1)

        result = generator.start_broadcasting()

        assert result is False

        generator.stop_broadcasting()

    def test_stop_broadcasting(self, generator, mock_zeroconf, sample_service_config):
        """Test stopping broadcast loop."""
        generator.register_service(sample_service_config)
        generator.start_broadcasting(interval=0.1)

        result = generator.stop_broadcasting()

        assert result is True
        assert generator.is_running is False

    def test_stop_broadcasting_not_running(self, generator, mock_zeroconf):
        """Test stopping broadcast when not running."""
        result = generator.stop_broadcasting()

        assert result is False

    def test_context_manager(self, mock_settings, mock_zeroconf):
        """Test using generator as context manager."""
        with MDNSGenerator(settings=mock_settings) as gen:
            config = ServiceConfig(
                name="test", service_type="_http._tcp.local.", port=8080
            )
            gen.register_service(config)
            assert len(gen.registered_services) == 1

        # After context, should be cleaned up
        mock_zeroconf.close.assert_called()

    def test_generate_traffic(self, generator, mock_zeroconf):
        """Test traffic generation for short duration."""
        stats = generator.generate_traffic(duration=0.5, interval=0.1)

        assert "duration_seconds" in stats
        assert "services_registered" in stats
        assert "broadcast_interval" in stats
        assert stats["broadcast_interval"] == 0.1

    def test_close_cleanup(self, mock_settings, mock_zeroconf):
        """Test that close properly cleans up resources."""
        gen = MDNSGenerator(settings=mock_settings)
        config = ServiceConfig(name="test", service_type="_http._tcp.local.", port=8080)
        gen.register_service(config)
        gen.start_broadcasting(interval=0.1)

        gen.close()

        assert gen.is_running is False
        mock_zeroconf.close.assert_called()


class TestMDNSGeneratorThreadSafety:
    """Tests for thread safety of MDNSGenerator."""

    def test_concurrent_registration(self, mock_settings, mock_zeroconf):
        """Test concurrent service registration."""
        gen = MDNSGenerator(settings=mock_settings)
        results = []

        def register_service(idx):
            config = ServiceConfig(
                name=f"concurrent-{idx}",
                service_type="_http._tcp.local.",
                port=8080 + idx,
            )
            result = gen.register_service(config)
            results.append(result)

        threads = [
            threading.Thread(target=register_service, args=(i,)) for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        gen.close()

        assert all(results)
        assert len(gen.registered_services) == 0  # Closed
