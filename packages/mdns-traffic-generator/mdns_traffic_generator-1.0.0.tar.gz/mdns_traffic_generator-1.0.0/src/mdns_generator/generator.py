"""
MDNS Traffic Generator - Core module for generating mDNS traffic.

Provides functionality to register and announce mDNS services on the network.
"""

import socket
import threading
import time
from typing import Dict, List, Optional

from zeroconf import ServiceInfo as ZeroconfServiceInfo
from zeroconf import Zeroconf

from mdns_generator.config import MDNSSettings, get_settings
from mdns_generator.logger import LoggerMixin, setup_logger
from mdns_generator.service import ServiceConfig, create_service_configs


class MDNSGenerator(LoggerMixin):
    """
    mDNS Traffic Generator for registering and announcing services.

    This class manages mDNS service registration and provides methods
    for generating traffic patterns useful for network testing.
    """

    def __init__(
        self,
        settings: Optional[MDNSSettings] = None,
    ) -> None:
        """
        Initialize the MDNS Generator.

        Args:
            settings: Optional settings object. Uses defaults if not provided.
        """
        self._settings = settings or get_settings()
        self._zeroconf: Optional[Zeroconf] = None
        self._registered_services: Dict[str, ZeroconfServiceInfo] = {}
        self._running = False
        self._broadcast_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Setup logging
        setup_logger(
            name="mdns_generator",
            level=self._settings.log_level,
            log_file=self._settings.log_file,
        )

    @property
    def is_running(self) -> bool:
        """Check if the generator is currently running."""
        return self._running

    @property
    def registered_services(self) -> List[str]:
        """Get list of registered service names."""
        with self._lock:
            return list(self._registered_services.keys())

    def _get_zeroconf(self) -> Zeroconf:
        """Get or create Zeroconf instance."""
        if self._zeroconf is None:
            self._zeroconf = Zeroconf()
            self.logger.debug("Zeroconf instance created")
        return self._zeroconf

    def _create_zeroconf_service_info(
        self,
        config: ServiceConfig,
    ) -> ZeroconfServiceInfo:
        """
        Create a Zeroconf ServiceInfo from our ServiceConfig.

        Args:
            config: Service configuration.

        Returns:
            ZeroconfServiceInfo: Zeroconf-compatible service info.
        """
        addresses = config.get_addresses()
        parsed_addresses = []
        for addr in addresses:
            try:
                parsed_addresses.append(socket.inet_aton(addr))
            except OSError:
                self.logger.warning("Invalid IP address: %s", addr)

        properties = {k: v.encode("utf-8") for k, v in config.properties.items()}

        return ZeroconfServiceInfo(
            type_=config.service_type,
            name=config.full_name,
            port=config.port,
            properties=properties,
            server=config.get_host(),
            addresses=parsed_addresses,
            weight=config.weight,
            priority=config.priority,
        )

    def register_service(self, config: ServiceConfig) -> bool:
        """
        Register a single mDNS service.

        Args:
            config: Service configuration.

        Returns:
            bool: True if registration succeeded, False otherwise.
        """
        try:
            zc = self._get_zeroconf()
            service_info = self._create_zeroconf_service_info(config)

            self.logger.info(
                "Registering service: %s on port %d",
                config.full_name,
                config.port,
            )

            zc.register_service(service_info)

            with self._lock:
                self._registered_services[config.full_name] = service_info

            self.logger.info("Service registered successfully: %s", config.full_name)
            return True

        except Exception as exc:
            self.logger.error("Failed to register service %s: %s", config.name, exc)
            return False

    def register_services(self, configs: List[ServiceConfig]) -> int:
        """
        Register multiple mDNS services.

        Args:
            configs: List of service configurations.

        Returns:
            int: Number of successfully registered services.
        """
        success_count = 0
        for config in configs:
            if self.register_service(config):
                success_count += 1
        return success_count

    def unregister_service(self, service_name: str) -> bool:
        """
        Unregister a specific mDNS service.

        Args:
            service_name: Full name of the service to unregister.

        Returns:
            bool: True if unregistration succeeded, False otherwise.
        """
        try:
            with self._lock:
                if service_name not in self._registered_services:
                    self.logger.warning("Service not found: %s", service_name)
                    return False

                service_info = self._registered_services.pop(service_name)

            if self._zeroconf:
                self._zeroconf.unregister_service(service_info)
                self.logger.info("Service unregistered: %s", service_name)

            return True

        except Exception as exc:
            self.logger.error("Failed to unregister service %s: %s", service_name, exc)
            return False

    def unregister_all_services(self) -> int:
        """
        Unregister all registered services.

        Returns:
            int: Number of successfully unregistered services.
        """
        with self._lock:
            service_names = list(self._registered_services.keys())

        success_count = 0
        for name in service_names:
            if self.unregister_service(name):
                success_count += 1

        return success_count

    def _broadcast_loop(self, interval: float) -> None:
        """
        Internal broadcast loop for continuous service announcements.

        Args:
            interval: Time between announcements in seconds.
        """
        self.logger.info("Starting broadcast loop with %.1fs interval", interval)

        while self._running:
            with self._lock:
                services = list(self._registered_services.values())

            for service_info in services:
                if not self._running:
                    break
                try:
                    if self._zeroconf:
                        self._zeroconf.update_service(service_info)
                        self.logger.debug("Announced service: %s", service_info.name)
                except Exception as exc:
                    self.logger.error("Failed to announce service: %s", exc)

            # Sleep in small intervals to allow quick shutdown
            sleep_time = 0.0
            while sleep_time < interval and self._running:
                time.sleep(0.1)
                sleep_time += 0.1

        self.logger.info("Broadcast loop stopped")

    def start_broadcasting(self, interval: Optional[float] = None) -> bool:
        """
        Start continuous service broadcasting.

        Args:
            interval: Optional broadcast interval. Uses settings default if not provided.

        Returns:
            bool: True if broadcasting started, False if already running.
        """
        if self._running:
            self.logger.warning("Broadcasting is already running")
            return False

        broadcast_interval = interval or self._settings.broadcast_interval
        self._running = True

        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop,
            args=(broadcast_interval,),
            daemon=True,
            name="mdns-broadcast",
        )
        self._broadcast_thread.start()

        self.logger.info("Broadcasting started")
        return True

    def stop_broadcasting(self) -> bool:
        """
        Stop continuous service broadcasting.

        Returns:
            bool: True if broadcasting stopped, False if not running.
        """
        if not self._running:
            self.logger.warning("Broadcasting is not running")
            return False

        self._running = False

        if self._broadcast_thread and self._broadcast_thread.is_alive():
            self._broadcast_thread.join(timeout=5.0)

        self.logger.info("Broadcasting stopped")
        return True

    def generate_traffic(
        self,
        duration: float = 60.0,
        interval: Optional[float] = None,
    ) -> Dict:
        """
        Generate mDNS traffic for a specified duration.

        Args:
            duration: Duration to generate traffic in seconds.
            interval: Optional broadcast interval.

        Returns:
            Dict: Statistics about the traffic generation.
        """
        broadcast_interval = interval or self._settings.broadcast_interval

        # Create and register services if none exist
        if not self._registered_services:
            configs = create_service_configs(
                base_name=self._settings.service_name,
                service_type=self._settings.service_type,
                base_port=self._settings.service_port,
                count=self._settings.service_count,
            )
            self.register_services(configs)

        self.logger.info(
            "Generating mDNS traffic for %.1f seconds with %.1fs interval",
            duration,
            broadcast_interval,
        )

        start_time = time.time()
        announcement_count = 0

        self.start_broadcasting(interval=broadcast_interval)

        try:
            while time.time() - start_time < duration:
                time.sleep(0.5)
                with self._lock:
                    announcement_count = len(self._registered_services)
        finally:
            self.stop_broadcasting()

        elapsed = time.time() - start_time

        stats = {
            "duration_seconds": elapsed,
            "services_registered": len(self._registered_services),
            "broadcast_interval": broadcast_interval,
            "estimated_announcements": int(elapsed / broadcast_interval)
            * announcement_count,
        }

        self.logger.info("Traffic generation complete: %s", stats)
        return stats

    def close(self) -> None:
        """Clean up resources and close the generator."""
        self.logger.info("Closing MDNS Generator")

        self.stop_broadcasting()
        self.unregister_all_services()

        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None

        self.logger.info("MDNS Generator closed")

    def __enter__(self) -> "MDNSGenerator":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
