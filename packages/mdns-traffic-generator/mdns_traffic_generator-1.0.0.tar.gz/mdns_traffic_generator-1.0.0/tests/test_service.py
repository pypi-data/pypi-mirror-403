"""Unit tests for service module."""

import pytest

from mdns_generator.service import ServiceConfig, ServiceInfo, create_service_configs


class TestServiceConfig:
    """Tests for ServiceConfig class."""

    def test_basic_config_creation(self):
        """Test creating a basic service config."""
        config = ServiceConfig(
            name="test-service",
            service_type="_http._tcp.local.",
            port=8080,
        )

        assert config.name == "test-service"
        assert config.service_type == "_http._tcp.local."
        assert config.port == 8080
        assert config.properties == {}
        assert config.weight == 0
        assert config.priority == 0

    def test_config_with_properties(self):
        """Test creating config with properties."""
        config = ServiceConfig(
            name="test-service",
            service_type="_http._tcp.local.",
            port=8080,
            properties={"version": "1.0", "path": "/api"},
        )

        assert config.properties == {"version": "1.0", "path": "/api"}

    def test_service_type_normalization(self):
        """Test that service type gets normalized."""
        config = ServiceConfig(
            name="test",
            service_type="_test._tcp",
            port=8080,
        )

        assert config.service_type == "_test._tcp.local."

    def test_full_name_property(self):
        """Test full_name property."""
        config = ServiceConfig(
            name="my-service",
            service_type="_http._tcp.local.",
            port=8080,
        )

        assert config.full_name == "my-service._http._tcp.local."

    def test_name_max_length(self):
        """Test that name exceeding max length raises error."""
        with pytest.raises(ValueError):
            ServiceConfig(
                name="a" * 64,  # Max is 63
                service_type="_http._tcp.local.",
                port=8080,
            )

    def test_name_empty(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError):
            ServiceConfig(
                name="",
                service_type="_http._tcp.local.",
                port=8080,
            )

    def test_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError):
            ServiceConfig(
                name="test",
                service_type="_http._tcp.local.",
                port=0,
            )

        with pytest.raises(ValueError):
            ServiceConfig(
                name="test",
                service_type="_http._tcp.local.",
                port=65536,
            )

    def test_get_host_default(self):
        """Test get_host returns local hostname."""
        config = ServiceConfig(
            name="test",
            service_type="_http._tcp.local.",
            port=8080,
        )

        host = config.get_host()
        assert host.endswith(".local.")

    def test_get_host_custom(self):
        """Test get_host with custom host."""
        config = ServiceConfig(
            name="test",
            service_type="_http._tcp.local.",
            port=8080,
            host="custom-host.local.",
        )

        assert config.get_host() == "custom-host.local."

    def test_get_addresses_default(self):
        """Test get_addresses returns local addresses."""
        config = ServiceConfig(
            name="test",
            service_type="_http._tcp.local.",
            port=8080,
        )

        addresses = config.get_addresses()
        assert len(addresses) >= 1

    def test_get_addresses_custom(self):
        """Test get_addresses with custom addresses."""
        config = ServiceConfig(
            name="test",
            service_type="_http._tcp.local.",
            port=8080,
            addresses=["192.168.1.100", "192.168.1.101"],
        )

        assert config.get_addresses() == ["192.168.1.100", "192.168.1.101"]


class TestServiceInfo:
    """Tests for ServiceInfo class."""

    def test_basic_info_creation(self):
        """Test creating basic service info."""
        info = ServiceInfo(
            name="discovered-service",
            service_type="_http._tcp.local.",
            server="host.local.",
            port=8080,
        )

        assert info.name == "discovered-service"
        assert info.server == "host.local."
        assert info.port == 8080

    def test_full_name_property(self):
        """Test full_name property."""
        info = ServiceInfo(
            name="my-service",
            service_type="_http._tcp.local.",
            server="host.local.",
            port=8080,
        )

        assert info.full_name == "my-service._http._tcp.local."

    def test_to_dict(self):
        """Test to_dict method."""
        info = ServiceInfo(
            name="my-service",
            service_type="_http._tcp.local.",
            server="host.local.",
            port=8080,
            addresses=["192.168.1.100"],
            properties={"version": "1.0"},
        )

        result = info.to_dict()

        assert result["name"] == "my-service"
        assert result["type"] == "_http._tcp.local."
        assert result["server"] == "host.local."
        assert result["port"] == 8080
        assert result["addresses"] == ["192.168.1.100"]
        assert result["properties"] == {"version": "1.0"}


class TestCreateServiceConfigs:
    """Tests for create_service_configs function."""

    def test_create_single_service(self):
        """Test creating a single service config."""
        configs = create_service_configs(
            base_name="test",
            service_type="_http._tcp.local.",
            base_port=8080,
            count=1,
        )

        assert len(configs) == 1
        assert configs[0].name == "test"
        assert configs[0].port == 8080

    def test_create_multiple_services(self):
        """Test creating multiple service configs."""
        configs = create_service_configs(
            base_name="test",
            service_type="_http._tcp.local.",
            base_port=8080,
            count=3,
        )

        assert len(configs) == 3
        assert configs[0].name == "test-0"
        assert configs[0].port == 8080
        assert configs[1].name == "test-1"
        assert configs[1].port == 8081
        assert configs[2].name == "test-2"
        assert configs[2].port == 8082

    def test_create_with_properties(self):
        """Test creating configs with custom properties."""
        props = {"custom": "value"}
        configs = create_service_configs(
            base_name="test",
            service_type="_http._tcp.local.",
            base_port=8080,
            count=1,
            properties=props,
        )

        assert configs[0].properties == props

    def test_create_invalid_count_zero(self):
        """Test that count of 0 raises error."""
        with pytest.raises(ValueError, match="Count must be at least 1"):
            create_service_configs(
                base_name="test",
                service_type="_http._tcp.local.",
                base_port=8080,
                count=0,
            )

    def test_create_invalid_count_over_max(self):
        """Test that count over 100 raises error."""
        with pytest.raises(ValueError, match="Count must not exceed 100"):
            create_service_configs(
                base_name="test",
                service_type="_http._tcp.local.",
                base_port=8080,
                count=101,
            )
