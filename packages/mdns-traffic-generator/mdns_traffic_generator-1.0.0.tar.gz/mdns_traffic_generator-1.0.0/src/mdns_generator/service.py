"""
Service configuration and data models for MDNS Traffic Generator.

Provides data classes for mDNS service definitions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from mdns_generator.platform_compat import get_hostname, get_local_ip_addresses


@dataclass
class ServiceConfig:
    """Configuration for an mDNS service to be registered."""

    name: str
    service_type: str
    port: int
    properties: Dict[str, str] = field(default_factory=dict)
    host: Optional[str] = None
    addresses: Optional[List[str]] = None
    weight: int = 0
    priority: int = 0

    def __post_init__(self):
        """Validate and normalize configuration after initialization."""
        # Validate name
        if not self.name or len(self.name) > 63:
            raise ValueError(
                f"Service name must be 1-63 characters, got {len(self.name or '')}"
            )

        # Validate port
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {self.port}")

        # Normalize service type
        if not self.service_type.endswith(".local."):
            if self.service_type.endswith(".local"):
                self.service_type = f"{self.service_type}."
            elif not self.service_type.endswith("."):
                self.service_type = f"{self.service_type}.local."

        # Validate weight and priority
        if self.weight < 0:
            raise ValueError(f"Weight must be >= 0, got {self.weight}")
        if self.priority < 0:
            raise ValueError(f"Priority must be >= 0, got {self.priority}")

    @property
    def full_name(self) -> str:
        """Get the full service name including type."""
        return f"{self.name}.{self.service_type}"

    def get_host(self) -> str:
        """Get the host name, defaulting to local hostname."""
        if self.host:
            return self.host
        return get_hostname()

    def get_addresses(self) -> List[str]:
        """Get IP addresses, defaulting to local addresses."""
        if self.addresses:
            return self.addresses
        return get_local_ip_addresses()


@dataclass
class ServiceInfo:
    """Information about a discovered mDNS service."""

    name: str
    service_type: str
    server: str
    port: int
    addresses: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    weight: int = 0
    priority: int = 0

    @property
    def full_name(self) -> str:
        """Get the full service name."""
        return f"{self.name}.{self.service_type}"

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.service_type,
            "server": self.server,
            "port": self.port,
            "addresses": self.addresses,
            "properties": self.properties,
            "weight": self.weight,
            "priority": self.priority,
        }


def create_service_configs(
    base_name: str,
    service_type: str,
    base_port: int,
    count: int = 1,
    properties: Optional[Dict[str, str]] = None,
) -> List[ServiceConfig]:
    """
    Create multiple service configurations.

    Args:
        base_name: Base name for services (will be suffixed with index).
        service_type: mDNS service type.
        base_port: Starting port number.
        count: Number of services to create.
        properties: Optional TXT record properties.

    Returns:
        List[ServiceConfig]: List of service configurations.
    """
    if count < 1:
        raise ValueError("Count must be at least 1")

    if count > 100:
        raise ValueError("Count must not exceed 100")

    configs = []
    for i in range(count):
        name = f"{base_name}-{i}" if count > 1 else base_name
        port = base_port + i
        config = ServiceConfig(
            name=name,
            service_type=service_type,
            port=port,
            properties=properties or {"version": "1.0", "test": "true"},
        )
        configs.append(config)

    return configs
