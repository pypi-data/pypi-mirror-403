"""Unit tests for configuration module."""

import pytest

from mdns_generator.config import (
    MDNSSettings,
    config_exists,
    get_settings,
    load_config_from_file,
    reload_settings,
    reset_config,
    save_config_to_file,
    update_config_value,
)


class TestMDNSSettings:
    """Tests for MDNSSettings class."""

    def test_default_settings(self):
        """Test that default settings are valid."""
        settings = MDNSSettings()

        assert settings.service_name == "test-service"
        assert settings.service_type == "_http._tcp.local."
        assert settings.service_port == 8080
        assert settings.interface == "0.0.0.0"
        assert settings.ttl == 4500
        assert settings.broadcast_interval == 5.0
        assert settings.service_count == 1
        assert settings.log_level == "INFO"
        assert settings.log_file is None

    def test_custom_settings(self):
        """Test creating settings with custom values."""
        settings = MDNSSettings(
            service_name="custom-service",
            service_type="_custom._tcp.local.",
            service_port=9000,
            broadcast_interval=2.0,
        )

        assert settings.service_name == "custom-service"
        assert settings.service_type == "_custom._tcp.local."
        assert settings.service_port == 9000
        assert settings.broadcast_interval == 2.0

    def test_service_type_validation_adds_local_suffix(self):
        """Test that service type gets .local. suffix added."""
        settings = MDNSSettings(service_type="_test._tcp")

        assert settings.service_type == "_test._tcp.local."

    def test_service_type_validation_adds_dot(self):
        """Test that service type gets trailing dot added."""
        settings = MDNSSettings(service_type="_test._tcp.local")

        assert settings.service_type == "_test._tcp.local."

    def test_port_validation_min(self):
        """Test that port below 1 raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(service_port=0)

    def test_port_validation_max(self):
        """Test that port above 65535 raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(service_port=70000)

    def test_service_count_validation_min(self):
        """Test that service count below 1 raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(service_count=0)

    def test_service_count_validation_max(self):
        """Test that service count above 100 raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(service_count=101)

    def test_log_level_validation_valid(self):
        """Test valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = MDNSSettings(log_level=level)
            assert settings.log_level == level

    def test_log_level_validation_case_insensitive(self):
        """Test log level is case insensitive."""
        settings = MDNSSettings(log_level="debug")
        assert settings.log_level == "DEBUG"

    def test_log_level_validation_invalid(self):
        """Test invalid log level raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(log_level="INVALID")

    def test_broadcast_interval_min(self):
        """Test that broadcast interval below 0.1 raises error."""
        with pytest.raises(ValueError):
            MDNSSettings(broadcast_interval=0.05)


class TestConfigFile:
    """Tests for INI config file operations."""

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration."""
        config_path = tmp_path / "test_config.ini"

        settings = MDNSSettings(
            service_name="saved-service",
            service_port=9999,
            log_level="DEBUG",
        )

        save_config_to_file(settings, config_path)
        loaded = load_config_from_file(config_path)

        assert loaded.service_name == "saved-service"
        assert loaded.service_port == 9999
        assert loaded.log_level == "DEBUG"

    def test_load_nonexistent_returns_defaults(self, tmp_path):
        """Test loading from nonexistent file returns defaults."""
        config_path = tmp_path / "nonexistent.ini"

        settings = load_config_from_file(config_path)

        assert settings.service_name == "test-service"
        assert settings.service_port == 8080

    def test_update_config_value(self, tmp_path):
        """Test updating a single config value."""
        config_path = tmp_path / "test_config.ini"

        # Save initial config
        save_config_to_file(MDNSSettings(), config_path)

        # Update a value
        update_config_value("service", "name", "updated-service", config_path)

        # Reload and check
        settings = load_config_from_file(config_path)
        assert settings.service_name == "updated-service"

    def test_reset_config(self, tmp_path):
        """Test resetting configuration to defaults."""
        config_path = tmp_path / "test_config.ini"

        # Save non-default config
        settings = MDNSSettings(service_name="custom", service_port=9999)
        save_config_to_file(settings, config_path)

        # Reset
        reset_config(config_path)

        # Check it's back to defaults
        loaded = load_config_from_file(config_path)
        assert loaded.service_name == "test-service"
        assert loaded.service_port == 8080

    def test_config_exists(self, tmp_path):
        """Test config_exists function."""
        config_path = tmp_path / "test_config.ini"

        assert config_exists(config_path) is False

        save_config_to_file(MDNSSettings(), config_path)

        assert config_exists(config_path) is True


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_cached_instance(self):
        """Test that get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_reload_settings_clears_cache(self):
        """Test that reload_settings returns fresh instance."""
        settings1 = get_settings()
        settings2 = reload_settings()

        # They should have same values but be different instances
        assert settings1 is not settings2
        assert settings1.service_name == settings2.service_name
