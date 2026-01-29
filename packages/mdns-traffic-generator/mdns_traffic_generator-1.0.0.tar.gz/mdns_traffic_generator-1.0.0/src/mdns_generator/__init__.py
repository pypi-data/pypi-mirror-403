"""
MDNS Traffic Generator - A Python tool for generating mDNS traffic for network testing.

This package provides utilities for:
- Registering mDNS services on the network
- Discovering existing mDNS services
- Generating mDNS traffic for testing purposes

Supports Windows, macOS, and Linux.
"""

__version__ = "1.0.0"
__author__ = "MDNS Generator Team"

from mdns_generator.generator import MDNSGenerator
from mdns_generator.service import ServiceConfig, ServiceInfo
from mdns_generator.discovery import ServiceDiscovery
from mdns_generator.platform_compat import (
    IS_WINDOWS,
    IS_MACOS,
    IS_LINUX,
    check_mdns_requirements,
    get_firewall_instructions,
    setup_windows_console,
)

# Setup Windows console on import
setup_windows_console()

__all__ = [
    "MDNSGenerator",
    "ServiceConfig",
    "ServiceInfo",
    "ServiceDiscovery",
    "IS_WINDOWS",
    "IS_MACOS",
    "IS_LINUX",
    "check_mdns_requirements",
    "get_firewall_instructions",
    "__version__",
]
