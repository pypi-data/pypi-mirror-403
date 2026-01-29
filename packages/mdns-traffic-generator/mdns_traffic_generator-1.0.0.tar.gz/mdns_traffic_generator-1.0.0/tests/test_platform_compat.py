"""Unit tests for platform compatibility module."""

import sys


from mdns_generator.platform_compat import (
    IS_WINDOWS,
    IS_MACOS,
    IS_LINUX,
    get_local_ip_addresses,
    get_hostname,
    check_mdns_requirements,
    get_firewall_instructions,
    setup_windows_console,
)


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_platform_flags_are_mutually_exclusive(self):
        """Test that only one platform flag is True."""
        # At most one should be True (could be none on unusual platforms)
        true_count = sum([IS_WINDOWS, IS_MACOS, IS_LINUX])
        assert true_count <= 1

    def test_platform_matches_sys_platform(self):
        """Test that platform detection matches sys.platform."""
        if sys.platform == "win32":
            assert IS_WINDOWS is True
        elif sys.platform == "darwin":
            assert IS_MACOS is True
        elif sys.platform.startswith("linux"):
            assert IS_LINUX is True


class TestGetLocalIpAddresses:
    """Tests for get_local_ip_addresses function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_local_ip_addresses()
        assert isinstance(result, list)

    def test_returns_non_empty(self):
        """Test that function returns at least one address."""
        result = get_local_ip_addresses()
        assert len(result) >= 1

    def test_returns_valid_ip_format(self):
        """Test that returned addresses are valid IPv4 format."""
        result = get_local_ip_addresses()
        for addr in result:
            parts = addr.split(".")
            assert len(parts) == 4
            for part in parts:
                assert part.isdigit()
                assert 0 <= int(part) <= 255


class TestGetHostname:
    """Tests for get_hostname function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_hostname()
        assert isinstance(result, str)

    def test_ends_with_local(self):
        """Test that hostname ends with .local."""
        result = get_hostname()
        assert result.endswith(".local.")

    def test_non_empty_hostname(self):
        """Test that hostname is not just '.local.'"""
        result = get_hostname()
        assert len(result) > len(".local.")


class TestCheckMdnsRequirements:
    """Tests for check_mdns_requirements function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = check_mdns_requirements()
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Test that result has required keys."""
        result = check_mdns_requirements()
        assert "ready" in result
        assert "warnings" in result
        assert "errors" in result

    def test_ready_is_bool(self):
        """Test that 'ready' is a boolean."""
        result = check_mdns_requirements()
        assert isinstance(result["ready"], bool)

    def test_warnings_is_list(self):
        """Test that 'warnings' is a list."""
        result = check_mdns_requirements()
        assert isinstance(result["warnings"], list)

    def test_errors_is_list(self):
        """Test that 'errors' is a list."""
        result = check_mdns_requirements()
        assert isinstance(result["errors"], list)


class TestGetFirewallInstructions:
    """Tests for get_firewall_instructions function."""

    def test_returns_string_or_none(self):
        """Test that function returns a string or None."""
        result = get_firewall_instructions()
        assert result is None or isinstance(result, str)

    def test_returns_instructions_for_known_platforms(self):
        """Test that function returns instructions for known platforms."""
        if IS_WINDOWS or IS_MACOS or IS_LINUX:
            result = get_firewall_instructions()
            assert result is not None
            assert len(result) > 0

    def test_instructions_mention_5353(self):
        """Test that instructions mention mDNS port 5353."""
        result = get_firewall_instructions()
        if result:
            assert "5353" in result


class TestSetupWindowsConsole:
    """Tests for setup_windows_console function."""

    def test_does_not_raise(self):
        """Test that function doesn't raise exceptions."""
        # Should not raise on any platform
        setup_windows_console()

    def test_runs_on_non_windows(self):
        """Test that function runs safely on non-Windows."""
        if not IS_WINDOWS:
            # Should be a no-op on non-Windows
            setup_windows_console()
