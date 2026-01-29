"""
Platform compatibility utilities for MDNS Traffic Generator.

Provides cross-platform support for Windows, macOS, and Linux.
"""

import socket
import sys
from typing import Any, List, Optional, TypedDict

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def get_local_ip_addresses() -> List[str]:
    """
    Get list of local IP addresses.

    Works across Windows, macOS, and Linux.

    Returns:
        List[str]: List of local IPv4 addresses.
    """
    addresses = []

    try:
        # Method 1: Connect to external address to find default interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Doesn't actually connect, just determines route
            s.connect(("8.8.8.8", 80))
            addr = s.getsockname()[0]
            if addr and addr != "0.0.0.0":
                addresses.append(addr)
    except (OSError, socket.error):
        pass

    try:
        # Method 2: Get all addresses from hostname
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addr = info[4][0]
            if addr not in addresses and not addr.startswith("127."):
                addresses.append(addr)
    except (OSError, socket.gaierror):
        pass

    # Fallback to localhost if nothing found
    if not addresses:
        addresses.append("127.0.0.1")

    return addresses


def get_hostname() -> str:
    """
    Get the local hostname with .local suffix for mDNS.

    Returns:
        str: Hostname suitable for mDNS.
    """
    hostname = socket.gethostname()

    # Remove any existing domain suffix
    if "." in hostname:
        hostname = hostname.split(".")[0]

    # Add .local suffix for mDNS
    return f"{hostname}.local."


class MdnsRequirements(TypedDict):
    ready: bool
    warnings: List[str]
    errors: List[str]


def check_mdns_requirements() -> MdnsRequirements:
    """
    Check if mDNS requirements are met on the current platform.

    Returns:
        dict: Status of mDNS requirements with keys:
            - 'ready': bool - True if mDNS should work
            - 'warnings': List[str] - List of warning messages
            - 'errors': List[str] - List of error messages
    """
    result: MdnsRequirements = {
        "ready": True,
        "warnings": [],
        "errors": [],
    }

    if IS_WINDOWS:
        # Check for Bonjour/mDNS service on Windows
        try:
            import winreg  # pylint: disable=import-outside-toplevel

            winreg_module: Any = winreg
        except ImportError:
            winreg_module = None

        if winreg_module is not None:
            try:
                # Check if Bonjour is installed
                winreg_module.OpenKey(
                    winreg_module.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Apple Inc.\Bonjour",
                )
            except FileNotFoundError:
                result["warnings"].append(
                    "Bonjour service not detected. mDNS may not work properly. "
                    "Consider installing Bonjour Print Services or iTunes."
                )

        # Check if running as admin might be needed
        try:
            import ctypes  # pylint: disable=import-outside-toplevel

            windll = getattr(ctypes, "windll", None)
            if windll is not None and not windll.shell32.IsUserAnAdmin():
                result["warnings"].append(
                    "Not running as Administrator. Some network operations may fail."
                )
        except (AttributeError, OSError):
            pass

    # Check if we can bind to mDNS port
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Don't actually bind to 5353 as it might conflict
        test_socket.close()
    except OSError as e:
        result["warnings"].append(f"Socket test warning: {e}")

    return result


def setup_windows_console() -> None:
    """
    Setup Windows console for proper UTF-8 output and ANSI colors.

    Should be called at startup on Windows.
    """
    if not IS_WINDOWS:
        return

    try:
        # Enable ANSI escape sequences on Windows 10+
        import ctypes  # pylint: disable=import-outside-toplevel

        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return
        kernel32 = windll.kernel32

        # Enable virtual terminal processing
        std_output_handle = -11
        enable_vt_processing = 0x0004

        handle = kernel32.GetStdHandle(std_output_handle)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | enable_vt_processing)
    except (AttributeError, OSError):
        pass

    try:
        # Set console code page to UTF-8
        import ctypes  # pylint: disable=import-outside-toplevel

        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return
        windll.kernel32.SetConsoleOutputCP(65001)
    except (AttributeError, OSError):
        pass


def get_firewall_instructions() -> Optional[str]:
    """
    Get platform-specific firewall instructions for mDNS.

    Returns:
        str: Instructions for configuring firewall, or None if not needed.
    """
    if IS_WINDOWS:
        return """
Windows Firewall Configuration:
-------------------------------
Run PowerShell as Administrator and execute:

  New-NetFirewallRule -DisplayName "mDNS-In" -Direction Inbound -Protocol UDP -LocalPort 5353 -Action Allow
  New-NetFirewallRule -DisplayName "mDNS-Out" -Direction Outbound -Protocol UDP -LocalPort 5353 -Action Allow

Or use Windows Firewall GUI:
1. Open "Windows Defender Firewall with Advanced Security"
2. Create inbound rule for UDP port 5353
3. Create outbound rule for UDP port 5353
"""

    if IS_MACOS:
        return """
macOS Firewall Configuration:
-----------------------------
mDNS (port 5353/UDP) should work by default on macOS (Bonjour is built-in).
If you have firewall enabled, go to:
  System Preferences > Security & Privacy > Firewall > Firewall Options
  Ensure your terminal/Python is allowed incoming connections on port 5353.
"""

    if IS_LINUX:
        return """
Linux Firewall Configuration:
-----------------------------
For iptables:
  sudo iptables -A INPUT -p udp --dport 5353 -j ACCEPT
  sudo iptables -A OUTPUT -p udp --dport 5353 -j ACCEPT

For firewalld:
  sudo firewall-cmd --add-service=mdns --permanent
  sudo firewall-cmd --reload

For ufw:
  sudo ufw allow 5353/udp
"""

    return None
