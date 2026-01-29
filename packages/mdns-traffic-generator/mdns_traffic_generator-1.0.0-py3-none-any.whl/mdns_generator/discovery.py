"""
MDNS Service Discovery module.

Provides functionality to discover and browse mDNS services on the network.
"""

import socket
import threading
import time
from typing import Callable, Dict, List, Optional

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from mdns_generator.config import MDNSSettings, get_settings
from mdns_generator.logger import LoggerMixin, setup_logger
from mdns_generator.service import ServiceInfo


class ServiceDiscoveryListener(ServiceListener, LoggerMixin):
    """Listener for mDNS service discovery events."""

    def __init__(
        self,
        on_add: Optional[Callable[[ServiceInfo], None]] = None,
        on_remove: Optional[Callable[[str], None]] = None,
        on_update: Optional[Callable[[ServiceInfo], None]] = None,
    ) -> None:
        """
        Initialize the service discovery listener.

        Args:
            on_add: Callback when a service is added.
            on_remove: Callback when a service is removed.
            on_update: Callback when a service is updated.
        """
        self._on_add = on_add
        self._on_remove = on_remove
        self._on_update = on_update
        self._discovered_services: Dict[str, ServiceInfo] = {}
        self._lock = threading.Lock()

    @property
    def discovered_services(self) -> Dict[str, ServiceInfo]:
        """Get copy of discovered services."""
        with self._lock:
            return dict(self._discovered_services)

    def _parse_service_info(
        self,
        zc: Zeroconf,
        service_type: str,
        name: str,
    ) -> Optional[ServiceInfo]:
        """Parse Zeroconf service info into our ServiceInfo model."""
        try:
            info = zc.get_service_info(service_type, name)
            if info is None:
                return None

            # Parse addresses
            addresses = []
            if info.addresses:
                for addr in info.addresses:
                    try:
                        addresses.append(socket.inet_ntoa(addr))
                    except (OSError, ValueError):
                        pass

            # Parse properties
            properties: Dict[str, str] = {}
            if info.properties:
                for raw_key, raw_value in info.properties.items():
                    key = (
                        raw_key.decode("utf-8", errors="replace")
                        if isinstance(raw_key, bytes)
                        else str(raw_key)
                    )
                    if raw_value is None:
                        value = ""
                    else:
                        value = (
                            raw_value.decode("utf-8", errors="replace")
                            if isinstance(raw_value, bytes)
                            else str(raw_value)
                        )
                    properties[key] = value

            # Extract instance name from full name
            instance_name = name.replace(f".{service_type}", "")

            if info.port is None:
                self.logger.warning("Service %s missing port; skipping", name)
                return None

            return ServiceInfo(
                name=instance_name,
                service_type=service_type,
                server=info.server or "",
                port=info.port,
                addresses=addresses,
                properties=properties,
                weight=info.weight,
                priority=info.priority,
            )

        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            self.logger.error("Failed to parse service info for %s: %s", name, exc)
            return None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service added event."""
        self.logger.debug("Service discovered: %s", name)

        service_info = self._parse_service_info(zc, type_, name)
        if service_info:
            with self._lock:
                self._discovered_services[name] = service_info

            self.logger.info(
                "Service added: %s at %s:%d",
                name,
                service_info.addresses[0] if service_info.addresses else "unknown",
                service_info.port,
            )

            if self._on_add:
                self._on_add(service_info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service removed event."""
        self.logger.debug("Service removed: %s", name)
        _ = type_

        with self._lock:
            if name in self._discovered_services:
                del self._discovered_services[name]

        self.logger.info("Service removed: %s", name)

        if self._on_remove:
            self._on_remove(name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service updated event."""
        self.logger.debug("Service updated: %s", name)

        service_info = self._parse_service_info(zc, type_, name)
        if service_info:
            with self._lock:
                self._discovered_services[name] = service_info

            self.logger.info("Service updated: %s", name)

            if self._on_update:
                self._on_update(service_info)


class ServiceDiscovery(LoggerMixin):
    """
    mDNS Service Discovery manager.

    Provides methods to discover and browse mDNS services on the network.
    """

    # Common mDNS service types
    COMMON_SERVICE_TYPES = [
        "_http._tcp.local.",
        "_https._tcp.local.",
        "_ssh._tcp.local.",
        "_ftp._tcp.local.",
        "_smb._tcp.local.",
        "_printer._tcp.local.",
        "_ipp._tcp.local.",
        "_airplay._tcp.local.",
        "_raop._tcp.local.",
        "_spotify-connect._tcp.local.",
        "_googlecast._tcp.local.",
        "_homekit._tcp.local.",
    ]

    def __init__(
        self,
        settings: Optional[MDNSSettings] = None,
    ) -> None:
        """
        Initialize the Service Discovery manager.

        Args:
            settings: Optional settings object.
        """
        self._settings = settings or get_settings()
        self._zeroconf: Optional[Zeroconf] = None
        self._browsers: Dict[str, ServiceBrowser] = {}
        self._listeners: Dict[str, ServiceDiscoveryListener] = {}
        self._lock = threading.Lock()

        # Setup logging
        setup_logger(
            name="mdns_generator",
            level=self._settings.log_level,
            log_file=self._settings.log_file,
        )

    def _get_zeroconf(self) -> Zeroconf:
        """Get or create Zeroconf instance."""
        if self._zeroconf is None:
            self._zeroconf = Zeroconf()
            self.logger.debug("Zeroconf instance created for discovery")
        return self._zeroconf

    def browse_service_type(
        self,
        service_type: str,
        on_add: Optional[Callable[[ServiceInfo], None]] = None,
        on_remove: Optional[Callable[[str], None]] = None,
        on_update: Optional[Callable[[ServiceInfo], None]] = None,
    ) -> bool:
        """
        Start browsing for a specific service type.

        Args:
            service_type: mDNS service type to browse (e.g., "_http._tcp.local.").
            on_add: Optional callback for service added events.
            on_remove: Optional callback for service removed events.
            on_update: Optional callback for service updated events.

        Returns:
            bool: True if browsing started, False if already browsing this type.
        """
        # Normalize service type
        if not service_type.endswith(".local."):
            if service_type.endswith(".local"):
                service_type = f"{service_type}."
            else:
                service_type = f"{service_type}.local."

        with self._lock:
            if service_type in self._browsers:
                self.logger.warning("Already browsing for %s", service_type)
                return False

        listener = ServiceDiscoveryListener(
            on_add=on_add,
            on_remove=on_remove,
            on_update=on_update,
        )

        try:
            zc = self._get_zeroconf()
            browser = ServiceBrowser(zc, service_type, listener)

            with self._lock:
                self._browsers[service_type] = browser
                self._listeners[service_type] = listener

            self.logger.info("Started browsing for %s", service_type)
            return True

        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.logger.error("Failed to start browsing for %s: %s", service_type, exc)
            return False

    def stop_browsing(self, service_type: str) -> bool:
        """
        Stop browsing for a specific service type.

        Args:
            service_type: Service type to stop browsing.

        Returns:
            bool: True if stopped, False if not browsing this type.
        """
        with self._lock:
            if service_type not in self._browsers:
                self.logger.warning("Not browsing for %s", service_type)
                return False

            browser = self._browsers.pop(service_type)
            self._listeners.pop(service_type, None)

        browser.cancel()
        self.logger.info("Stopped browsing for %s", service_type)
        return True

    def stop_all_browsing(self) -> int:
        """
        Stop all active service browsing.

        Returns:
            int: Number of browsers stopped.
        """
        with self._lock:
            service_types = list(self._browsers.keys())

        count = 0
        for service_type in service_types:
            if self.stop_browsing(service_type):
                count += 1

        return count

    def get_discovered_services(
        self,
        service_type: Optional[str] = None,
    ) -> List[ServiceInfo]:
        """
        Get list of discovered services.

        Args:
            service_type: Optional filter by service type.

        Returns:
            List[ServiceInfo]: List of discovered services.
        """
        services: List[ServiceInfo] = []

        with self._lock:
            if service_type:
                if service_type in self._listeners:
                    services.extend(
                        self._listeners[service_type].discovered_services.values()
                    )
            else:
                for listener in self._listeners.values():
                    services.extend(listener.discovered_services.values())

        return services

    def discover_services(
        self,
        service_types: Optional[List[str]] = None,
        duration: float = 5.0,
    ) -> List[ServiceInfo]:
        """
        Discover services for a specified duration.

        Args:
            service_types: List of service types to discover. Uses common types if not provided.
            duration: Duration to discover in seconds.

        Returns:
            List[ServiceInfo]: List of discovered services.
        """
        types_to_browse = service_types or self.COMMON_SERVICE_TYPES

        self.logger.info(
            "Starting discovery for %d service types for %.1f seconds",
            len(types_to_browse),
            duration,
        )

        # Start browsing all types
        for service_type in types_to_browse:
            self.browse_service_type(service_type)

        # Wait for discovery
        time.sleep(duration)

        # Collect results
        services = self.get_discovered_services()

        # Stop browsing
        self.stop_all_browsing()

        self.logger.info("Discovery complete. Found %d services", len(services))
        return services

    def browse_common_services(
        self,
        on_add: Optional[Callable[[ServiceInfo], None]] = None,
        on_remove: Optional[Callable[[str], None]] = None,
    ) -> int:
        """
        Start browsing for all common service types.

        Args:
            on_add: Optional callback for service added events.
            on_remove: Optional callback for service removed events.

        Returns:
            int: Number of service types now being browsed.
        """
        count = 0
        for service_type in self.COMMON_SERVICE_TYPES:
            if self.browse_service_type(
                service_type, on_add=on_add, on_remove=on_remove
            ):
                count += 1
        return count

    def close(self) -> None:
        """Clean up resources and close discovery."""
        self.logger.info("Closing Service Discovery")

        self.stop_all_browsing()

        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None

        self.logger.info("Service Discovery closed")

    def __enter__(self) -> "ServiceDiscovery":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
