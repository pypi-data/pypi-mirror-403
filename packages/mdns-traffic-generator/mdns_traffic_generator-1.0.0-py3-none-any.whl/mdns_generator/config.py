"""
Configuration management for MDNS Traffic Generator.

Uses an INI file for persistent configuration with built-in defaults.
Configuration can only be modified through the CLI tool.
"""

import configparser
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Default configuration directory
if os.name == "nt":  # Windows
    CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "mdns-generator"
else:  # Linux/macOS
    CONFIG_DIR = Path.home() / ".config" / "mdns-generator"

CONFIG_FILE = CONFIG_DIR / "config.ini"


@dataclass
class MDNSSettings:
    """Application settings with built-in defaults."""

    # Service Configuration - Defaults
    service_name: str = "test-service"
    service_type: str = "_http._tcp.local."
    service_port: int = 8080

    # Network Configuration - Defaults
    interface: str = "0.0.0.0"
    ttl: int = 4500

    # Traffic Generation Settings - Defaults
    broadcast_interval: float = 5.0
    service_count: int = 1

    # Logging Configuration - Defaults
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize settings after initialization."""
        # Validate service_type format
        if not self.service_type.endswith(".local."):
            if self.service_type.endswith(".local"):
                self.service_type = f"{self.service_type}."
            else:
                self.service_type = f"{self.service_type}.local."

        # Validate log_level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        self.log_level = self.log_level.upper()
        if self.log_level not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.log_level}. Must be one of {valid_levels}"
            )

        # Validate port
        if not 1 <= self.service_port <= 65535:
            raise ValueError(
                f"Port must be between 1 and 65535, got {self.service_port}"
            )

        # Validate service_count
        if not 1 <= self.service_count <= 100:
            raise ValueError(
                f"Service count must be between 1 and 100, got {self.service_count}"
            )

        # Validate broadcast_interval
        if self.broadcast_interval < 0.1:
            raise ValueError(
                f"Broadcast interval must be >= 0.1, got {self.broadcast_interval}"
            )

        # Validate ttl
        if self.ttl < 0:
            raise ValueError(f"TTL must be >= 0, got {self.ttl}")


def _ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_default_settings() -> MDNSSettings:
    """Get default settings instance."""
    return MDNSSettings()


def load_config_from_file(config_path: Optional[Path] = None) -> MDNSSettings:
    """
    Load configuration from INI file.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        MDNSSettings: Settings loaded from file or defaults if file doesn't exist.
    """
    path = config_path or CONFIG_FILE
    defaults = _get_default_settings()

    if not path.exists():
        return defaults

    config = configparser.ConfigParser()
    config.read(path)

    # Extract values with defaults
    service_name = config.get("service", "name", fallback=defaults.service_name)
    service_type = config.get("service", "type", fallback=defaults.service_type)
    service_port = config.getint("service", "port", fallback=defaults.service_port)

    interface = config.get("network", "interface", fallback=defaults.interface)
    ttl = config.getint("network", "ttl", fallback=defaults.ttl)

    broadcast_interval = config.getfloat(
        "traffic", "broadcast_interval", fallback=defaults.broadcast_interval
    )
    service_count = config.getint(
        "traffic", "service_count", fallback=defaults.service_count
    )

    log_level = config.get("logging", "level", fallback=defaults.log_level)
    log_file = config.get("logging", "file", fallback=None) or None

    return MDNSSettings(
        service_name=service_name,
        service_type=service_type,
        service_port=service_port,
        interface=interface,
        ttl=ttl,
        broadcast_interval=broadcast_interval,
        service_count=service_count,
        log_level=log_level,
        log_file=log_file,
    )


def save_config_to_file(
    settings: MDNSSettings,
    config_path: Optional[Path] = None,
) -> Path:
    """
    Save configuration to INI file.

    Args:
        settings: Settings to save.
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Path: Path to the saved config file.
    """
    path = config_path or CONFIG_FILE

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()

    config["service"] = {
        "name": settings.service_name,
        "type": settings.service_type,
        "port": str(settings.service_port),
    }

    config["network"] = {
        "interface": settings.interface,
        "ttl": str(settings.ttl),
    }

    config["traffic"] = {
        "broadcast_interval": str(settings.broadcast_interval),
        "service_count": str(settings.service_count),
    }

    config["logging"] = {
        "level": settings.log_level,
    }
    if settings.log_file:
        config["logging"]["file"] = settings.log_file

    with open(path, "w", encoding="utf-8") as f:
        config.write(f)

    return path


def update_config_value(
    section: str,
    key: str,
    value: str,
    config_path: Optional[Path] = None,
) -> None:
    """
    Update a single configuration value.

    Args:
        section: Config section (service, network, traffic, logging).
        key: Configuration key.
        value: New value.
        config_path: Optional path to config file.
    """
    path = config_path or CONFIG_FILE

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()

    # Read existing config if it exists
    if path.exists():
        config.read(path)

    # Ensure section exists
    if section not in config:
        config[section] = {}

    # Update value
    config[section][key] = value

    # Write back
    with open(path, "w", encoding="utf-8") as f:
        config.write(f)


def reset_config(config_path: Optional[Path] = None) -> Path:
    """
    Reset configuration to defaults.

    Args:
        config_path: Optional path to config file.

    Returns:
        Path: Path to the reset config file.
    """
    defaults = _get_default_settings()
    return save_config_to_file(defaults, config_path)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return CONFIG_FILE


def config_exists(config_path: Optional[Path] = None) -> bool:
    """Check if configuration file exists."""
    path = config_path or CONFIG_FILE
    return path.exists()


@lru_cache
def get_settings() -> MDNSSettings:
    """
    Get cached application settings.

    Returns:
        MDNSSettings: Application settings instance.
    """
    return load_config_from_file()


def reload_settings() -> MDNSSettings:
    """
    Reload settings by clearing the cache.

    Returns:
        MDNSSettings: Fresh application settings instance.
    """
    get_settings.cache_clear()
    return get_settings()
