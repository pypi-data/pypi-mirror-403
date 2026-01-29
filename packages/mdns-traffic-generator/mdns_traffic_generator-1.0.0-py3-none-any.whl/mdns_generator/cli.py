"""
Command-line interface for MDNS Traffic Generator.

Provides a user-friendly CLI for generating mDNS traffic and discovering services.
Configuration is managed through CLI commands and stored in an INI file.
"""

import json
import os
import subprocess
import sys
import threading
from typing import List, Optional

import click

from mdns_generator import __version__
from mdns_generator.config import (
    MDNSSettings,
    config_exists,
    get_config_path,
    get_settings,
    reload_settings,
    reset_config,
    update_config_value,
)
from mdns_generator.discovery import ServiceDiscovery
from mdns_generator.generator import MDNSGenerator
from mdns_generator.logger import setup_logger
from mdns_generator.service import ServiceConfig, ServiceInfo, create_service_configs


# Global flag for graceful shutdown (Windows-compatible)
_shutdown_event = threading.Event()


def _wait_for_interrupt(timeout: Optional[float] = None) -> bool:
    """
    Wait for keyboard interrupt or shutdown signal.

    Works on both Windows and Unix systems.

    Args:
        timeout: Optional timeout in seconds. None means wait indefinitely.

    Returns:
        bool: True if shutdown was requested, False if timeout occurred.
    """
    try:
        if timeout is None:
            # Wait indefinitely with periodic checks for Ctrl+C
            while not _shutdown_event.is_set():
                # Use small intervals to remain responsive to Ctrl+C on Windows
                if _shutdown_event.wait(timeout=0.5):
                    return True
            return True
        # Wait with timeout
        return _shutdown_event.wait(timeout=timeout)
    except KeyboardInterrupt:
        _shutdown_event.set()
        return True


def _sleep_interruptible(duration: float) -> bool:
    """
    Sleep for duration but can be interrupted by Ctrl+C.

    Args:
        duration: Duration to sleep in seconds.

    Returns:
        bool: True if interrupted, False if completed normally.
    """
    try:
        if _shutdown_event.wait(timeout=duration):
            return True
        return False
    except KeyboardInterrupt:
        _shutdown_event.set()
        return True


@click.group()
@click.version_option(version=__version__, prog_name="mdns-generator")
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default=None,
    help="Override logging level for this session",
)
@click.pass_context
def main(ctx: click.Context, log_level: Optional[str]) -> None:
    """
    MDNS Traffic Generator - Generate and discover mDNS services.

    A tool for testing mDNS traffic across networks. Can register services,
    generate continuous traffic, and discover existing services.

    Configuration is stored in an INI file and can be managed with the
    'config' command group.
    """
    # Reset shutdown event for new command
    _shutdown_event.clear()

    ctx.ensure_object(dict)

    settings = get_settings()

    # Override log level for this session if provided
    effective_log_level = log_level.upper() if log_level else settings.log_level

    ctx.obj["settings"] = settings
    ctx.obj["log_level"] = effective_log_level
    ctx.obj["logger"] = setup_logger(
        level=effective_log_level,
        log_file=settings.log_file,
    )


@main.command()
@click.option(
    "--name",
    "-n",
    default=None,
    help="Service name (overrides config for this session)",
)
@click.option(
    "--type",
    "-t",
    "service_type",
    default=None,
    help="Service type (e.g., _http._tcp.local.)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=None,
    help="Service port",
)
@click.option(
    "--count",
    "-c",
    type=int,
    default=None,
    help="Number of services to register",
)
@click.option(
    "--duration",
    "-d",
    type=float,
    default=60.0,
    help="Duration to run in seconds (0 for indefinite)",
)
@click.option(
    "--interval",
    "-i",
    type=float,
    default=None,
    help="Broadcast interval in seconds",
)
@click.option(
    "--property",
    "-P",
    "properties",
    multiple=True,
    help="Service property in key=value format (can be used multiple times)",
)
@click.pass_context
def generate(
    ctx: click.Context,
    name: Optional[str],
    service_type: Optional[str],
    port: Optional[int],
    count: Optional[int],
    duration: float,
    interval: Optional[float],
    properties: tuple,
) -> None:
    """Generate mDNS traffic by registering and announcing services."""
    settings: MDNSSettings = ctx.obj["settings"]

    # Use CLI overrides or fall back to config
    service_name = name or settings.service_name
    svc_type = service_type or settings.service_type
    service_port = port or settings.service_port
    service_count = count or settings.service_count
    broadcast_interval = interval or settings.broadcast_interval

    # Parse properties
    props = {}
    for prop in properties:
        if "=" in prop:
            key, value = prop.split("=", 1)
            props[key.strip()] = value.strip()

    if not props:
        props = {"version": "1.0", "generator": "mdns-traffic-generator"}

    click.echo(f"MDNS Traffic Generator v{__version__}")
    click.echo("-" * 40)
    click.echo(f"Service Name: {service_name}")
    click.echo(f"Service Type: {svc_type}")
    click.echo(f"Port: {service_port}")
    click.echo(f"Count: {service_count}")
    click.echo(f"Interval: {broadcast_interval}s")
    click.echo(f"Duration: {'indefinite' if duration == 0 else f'{duration}s'}")
    click.echo("-" * 40)

    # Create service configs
    configs = create_service_configs(
        base_name=service_name,
        service_type=svc_type,
        base_port=service_port,
        count=service_count,
        properties=props,
    )

    with MDNSGenerator(settings=settings) as generator:
        # Register services
        registered = generator.register_services(configs)
        click.echo(f"Registered {registered}/{service_count} services")

        if registered == 0:
            click.echo("No services registered. Exiting.")
            return

        # Start broadcasting
        generator.start_broadcasting(interval=broadcast_interval)
        click.echo("Broadcasting started. Press Ctrl+C to stop.")

        try:
            if duration == 0:
                # Run indefinitely
                _wait_for_interrupt()
            else:
                _sleep_interruptible(duration)
        except KeyboardInterrupt:
            pass
        finally:
            generator.stop_broadcasting()
            click.echo("\nBroadcasting stopped.")

        # Show stats
        click.echo(f"Services registered: {len(generator.registered_services)}")


@main.command()
@click.option(
    "--type",
    "-t",
    "service_types",
    multiple=True,
    help="Service type to discover (can be used multiple times)",
)
@click.option(
    "--duration",
    "-d",
    type=float,
    default=5.0,
    help="Discovery duration in seconds",
)
@click.option(
    "--all",
    "-a",
    "discover_all",
    is_flag=True,
    help="Discover all common service types",
)
@click.option(
    "--json",
    "-j",
    "output_json",
    is_flag=True,
    help="Output results as JSON",
)
@click.option(
    "--continuous",
    "-c",
    is_flag=True,
    help="Continuously discover and display services",
)
@click.pass_context
def discover(
    ctx: click.Context,
    service_types: tuple,
    duration: float,
    discover_all: bool,
    output_json: bool,
    continuous: bool,
) -> None:
    """Discover mDNS services on the network."""
    settings: MDNSSettings = ctx.obj["settings"]

    click.echo(f"MDNS Service Discovery v{__version__}")
    click.echo("-" * 40)

    types_to_discover: Optional[List[str]] = None
    if service_types:
        types_to_discover = list(service_types)
        click.echo(f"Discovering: {', '.join(types_to_discover)}")
    elif discover_all:
        click.echo("Discovering all common service types")
    else:
        types_to_discover = ["_http._tcp.local."]
        click.echo(f"Discovering: {types_to_discover[0]}")

    click.echo(f"Duration: {duration}s")
    click.echo("-" * 40)

    with ServiceDiscovery(settings=settings) as disc:
        if continuous:
            _continuous_discovery(disc, types_to_discover, output_json)
        else:
            services = disc.discover_services(
                service_types=types_to_discover if not discover_all else None,
                duration=duration,
            )
            _display_services(services, output_json)


def _continuous_discovery(
    disc: ServiceDiscovery,
    service_types: Optional[List[str]],
    output_json: bool,
) -> None:
    """Run continuous discovery with live updates."""

    def on_add(service: ServiceInfo) -> None:
        if output_json:
            click.echo(json.dumps({"event": "added", "service": service.to_dict()}))
        else:
            addr = service.addresses[0] if service.addresses else "unknown"
            click.echo(f"[+] {service.name} at {addr}:{service.port}")

    def on_remove(name: str) -> None:
        if output_json:
            click.echo(json.dumps({"event": "removed", "name": name}))
        else:
            click.echo(f"[-] {name}")

    if service_types:
        for svc_type in service_types:
            disc.browse_service_type(svc_type, on_add=on_add, on_remove=on_remove)
    else:
        disc.browse_common_services(on_add=on_add, on_remove=on_remove)

    click.echo("Continuous discovery started. Press Ctrl+C to stop.")

    try:
        _wait_for_interrupt()
    except KeyboardInterrupt:
        pass


def _display_services(services: List[ServiceInfo], output_json: bool) -> None:
    """Display discovered services."""
    if output_json:
        output = [service.to_dict() for service in services]
        click.echo(json.dumps(output, indent=2))
        return

    if not services:
        click.echo("No services discovered.")
        return

    click.echo(f"\nDiscovered {len(services)} service(s):\n")

    for service in services:
        click.echo(f"  Name: {service.name}")
        click.echo(f"  Type: {service.service_type}")
        click.echo(f"  Server: {service.server}")
        click.echo(f"  Port: {service.port}")
        if service.addresses:
            click.echo(f"  Addresses: {', '.join(service.addresses)}")
        if service.properties:
            click.echo(f"  Properties: {service.properties}")
        click.echo()


@main.command()
@click.option(
    "--name",
    "-n",
    required=True,
    help="Service name",
)
@click.option(
    "--type",
    "-t",
    "service_type",
    default="_http._tcp.local.",
    help="Service type",
)
@click.option(
    "--port",
    "-p",
    type=int,
    required=True,
    help="Service port",
)
@click.option(
    "--property",
    "-P",
    "properties",
    multiple=True,
    help="Service property in key=value format",
)
@click.pass_context
def register(
    ctx: click.Context,
    name: str,
    service_type: str,
    port: int,
    properties: tuple,
) -> None:
    """Register a single mDNS service and keep it active."""
    settings: MDNSSettings = ctx.obj["settings"]

    # Parse properties
    props = {}
    for prop in properties:
        if "=" in prop:
            key, value = prop.split("=", 1)
            props[key.strip()] = value.strip()

    click.echo(f"Registering service: {name}")
    click.echo(f"Type: {service_type}")
    click.echo(f"Port: {port}")

    svc_config = ServiceConfig(
        name=name,
        service_type=service_type,
        port=port,
        properties=props or {"registered_by": "mdns-generator"},
    )

    with MDNSGenerator(settings=settings) as generator:
        if generator.register_service(svc_config):
            click.echo("Service registered. Press Ctrl+C to unregister and exit.")
            try:
                _wait_for_interrupt()
            except KeyboardInterrupt:
                pass
        else:
            click.echo("Failed to register service.")


@main.command()
@click.pass_context
def list_types(_ctx: click.Context) -> None:
    """List common mDNS service types."""
    click.echo("Common mDNS Service Types:")
    click.echo("-" * 40)
    for svc_type in ServiceDiscovery.COMMON_SERVICE_TYPES:
        click.echo(f"  {svc_type}")


@main.command()
@click.option(
    "--firewall", "-f", is_flag=True, help="Show firewall configuration instructions"
)
@click.pass_context
def check(_ctx: click.Context, firewall: bool) -> None:
    """Check platform requirements and mDNS readiness."""
    from mdns_generator.platform_compat import (  # pylint: disable=import-outside-toplevel
        IS_WINDOWS,
        IS_MACOS,
        IS_LINUX,
        check_mdns_requirements,
        get_firewall_instructions,
        get_local_ip_addresses,
        get_hostname,
    )

    click.echo("Platform Check")
    click.echo("-" * 40)

    # Platform info
    if IS_WINDOWS:
        platform_name = "Windows"
    elif IS_MACOS:
        platform_name = "macOS"
    elif IS_LINUX:
        platform_name = "Linux"
    else:
        platform_name = sys.platform

    click.echo(f"Platform: {platform_name}")
    click.echo(f"Python: {sys.version.split()[0]}")
    click.echo(f"Hostname: {get_hostname()}")
    click.echo(f"IP Addresses: {', '.join(get_local_ip_addresses())}")
    click.echo("-" * 40)

    # Check requirements
    result = check_mdns_requirements()

    if result["ready"] and not result["warnings"] and not result["errors"]:
        click.echo("Status: Ready")
        click.secho("All mDNS requirements met!", fg="green")
    else:
        if result["errors"]:
            click.echo("Status: Not Ready")
            click.secho("Errors:", fg="red")
            for error in result["errors"]:
                click.echo(f"  - {error}")

        if result["warnings"]:
            click.echo("Status: Ready (with warnings)")
            click.secho("Warnings:", fg="yellow")
            for warning in result["warnings"]:
                click.echo(f"  - {warning}")

    # Show firewall instructions if requested
    if firewall:
        click.echo()
        instructions = get_firewall_instructions()
        if instructions:
            click.echo(instructions)


# ============================================================================
# Configuration Management Commands
# ============================================================================


@main.group("config")
def config_group() -> None:
    """Manage configuration settings.

    Configuration is stored in an INI file and persists between sessions.
    Use these commands to view, set, and reset configuration values.
    """


@config_group.command("show")
@click.option("--path", is_flag=True, help="Show config file path only")
@click.pass_context
def config_show(ctx: click.Context, path: bool) -> None:
    """Show current configuration."""
    if path:
        click.echo(get_config_path())
        return

    settings: MDNSSettings = ctx.obj["settings"]
    cfg_path = get_config_path()

    click.echo("Current Configuration:")
    click.echo("-" * 40)
    click.echo(f"Config File: {cfg_path}")
    click.echo(f"File Exists: {config_exists()}")
    click.echo("-" * 40)
    click.echo("\n[service]")
    click.echo(f"  name = {settings.service_name}")
    click.echo(f"  type = {settings.service_type}")
    click.echo(f"  port = {settings.service_port}")
    click.echo("\n[network]")
    click.echo(f"  interface = {settings.interface}")
    click.echo(f"  ttl = {settings.ttl}")
    click.echo("\n[traffic]")
    click.echo(f"  broadcast_interval = {settings.broadcast_interval}")
    click.echo(f"  service_count = {settings.service_count}")
    click.echo("\n[logging]")
    click.echo(f"  level = {settings.log_level}")
    click.echo(f"  file = {settings.log_file or '(not set)'}")


@config_group.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(_ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.

    KEY should be in format 'section.key', for example:

    \b
      mdns-generator config set service.name my-service
      mdns-generator config set service.port 9000
      mdns-generator config set traffic.broadcast_interval 10
      mdns-generator config set logging.level DEBUG
    """
    if "." not in key:
        click.echo("Error: Key must be in format 'section.key'")
        click.echo("Example: mdns-generator config set service.name my-service")
        raise SystemExit(1)

    section, config_key = key.split(".", 1)

    valid_sections = {"service", "network", "traffic", "logging"}
    if section not in valid_sections:
        click.echo(f"Error: Invalid section '{section}'")
        click.echo(f"Valid sections: {', '.join(sorted(valid_sections))}")
        raise SystemExit(1)

    # Validate the new configuration by loading and testing
    try:
        update_config_value(section, config_key, value)
        reload_settings()  # This will validate the new config
        click.echo(f"Set {key} = {value}")
        click.echo(f"Configuration saved to {get_config_path()}")
    except ValueError as exc:
        click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc


@config_group.command("reset")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def config_reset(_ctx: click.Context, yes: bool) -> None:
    """Reset configuration to defaults."""
    if not yes:
        click.confirm("Reset all configuration to defaults?", abort=True)

    path = reset_config()
    reload_settings()
    click.echo("Configuration reset to defaults")
    click.echo(f"Saved to {path}")


@config_group.command("init")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config")
@click.pass_context
def config_init(_ctx: click.Context, force: bool) -> None:
    """Initialize configuration file with defaults."""
    if config_exists() and not force:
        click.echo(f"Configuration file already exists at {get_config_path()}")
        click.echo("Use --force to overwrite")
        return

    path = reset_config()
    click.echo(f"Configuration initialized at {path}")


@config_group.command("edit")
@click.pass_context
def config_edit(_ctx: click.Context) -> None:
    """Open configuration file in default editor."""
    cfg_path = get_config_path()

    if not config_exists():
        click.echo("No configuration file exists. Creating one with defaults...")
        reset_config()

    # Determine editor based on OS
    editor = os.environ.get("EDITOR", os.environ.get("VISUAL"))

    if not editor:
        if sys.platform == "win32":
            # Windows - use notepad
            editor = "notepad.exe"
        elif sys.platform == "darwin":
            # macOS - use open command with default text editor
            editor = "open"
        else:
            # Linux/Unix - try common editors
            for edit_cmd in ["nano", "vim", "vi"]:
                try:
                    subprocess.run(["which", edit_cmd], capture_output=True, check=True)
                    editor = edit_cmd
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            if not editor:
                editor = "vi"

    try:
        if sys.platform == "darwin" and editor == "open":
            # macOS: use 'open -t' for default text editor
            subprocess.run(["open", "-t", str(cfg_path)], check=True)
        else:
            subprocess.run([editor, str(cfg_path)], check=True)
        click.echo("Configuration file closed. Reloading settings...")
        reload_settings()
    except subprocess.CalledProcessError:
        click.echo(f"Error opening editor. You can manually edit: {cfg_path}")
    except FileNotFoundError:
        click.echo(f"Editor '{editor}' not found. You can manually edit: {cfg_path}")


if __name__ == "__main__":
    # Click injects ctx/log_level at runtime; suppress pylint false positive.
    main(standalone_mode=True)  # type: ignore[call-arg]  # pylint: disable=no-value-for-parameter
