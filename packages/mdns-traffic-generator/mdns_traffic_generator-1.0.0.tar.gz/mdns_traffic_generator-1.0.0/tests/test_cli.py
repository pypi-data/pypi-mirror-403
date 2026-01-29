"""Unit tests for CLI module."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mdns_generator.cli import main


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestMainGroup:
    """Tests for main CLI group."""

    def test_version(self, runner):
        """Test version option."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "mdns-generator" in result.output

    def test_help(self, runner):
        """Test help option."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "MDNS Traffic Generator" in result.output
        assert "generate" in result.output
        assert "discover" in result.output
        assert "config" in result.output


class TestConfigCommands:
    """Tests for config command group."""

    def test_config_show(self, runner):
        """Test config show command displays settings."""
        result = runner.invoke(main, ["config", "show"])

        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert "[service]" in result.output
        assert "name" in result.output

    def test_config_show_path(self, runner):
        """Test config show --path displays only path."""
        result = runner.invoke(main, ["config", "show", "--path"])

        assert result.exit_code == 0
        assert "config.ini" in result.output

    def test_config_set_invalid_format(self, runner):
        """Test config set with invalid key format."""
        result = runner.invoke(main, ["config", "set", "invalid", "value"])

        assert result.exit_code != 0
        assert "section.key" in result.output

    def test_config_set_invalid_section(self, runner):
        """Test config set with invalid section."""
        result = runner.invoke(main, ["config", "set", "invalid.key", "value"])

        assert result.exit_code != 0
        assert "Invalid section" in result.output

    def test_config_init_help(self, runner):
        """Test config init help."""
        result = runner.invoke(main, ["config", "init", "--help"])

        assert result.exit_code == 0
        assert "--force" in result.output


class TestListTypesCommand:
    """Tests for list-types command."""

    def test_list_types_output(self, runner):
        """Test list-types command displays service types."""
        result = runner.invoke(main, ["list-types"])

        assert result.exit_code == 0
        assert "Common mDNS Service Types" in result.output
        assert "_http._tcp.local." in result.output


class TestGenerateCommand:
    """Tests for generate command."""

    def test_generate_help(self, runner):
        """Test generate command help."""
        result = runner.invoke(main, ["generate", "--help"])

        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--type" in result.output
        assert "--port" in result.output
        assert "--duration" in result.output

    @patch("mdns_generator.cli.MDNSGenerator")
    def test_generate_short_duration(self, mock_gen_class, runner):
        """Test generate command with short duration."""
        mock_gen = MagicMock()
        mock_gen.__enter__ = MagicMock(return_value=mock_gen)
        mock_gen.__exit__ = MagicMock(return_value=False)
        mock_gen.register_services.return_value = 1
        mock_gen.registered_services = ["test._http._tcp.local."]
        mock_gen_class.return_value = mock_gen

        runner.invoke(
            main,
            [
                "generate",
                "--name",
                "test",
                "--duration",
                "0.1",
            ],
        )

        # Command should complete without error
        assert mock_gen.register_services.called


class TestDiscoverCommand:
    """Tests for discover command."""

    def test_discover_help(self, runner):
        """Test discover command help."""
        result = runner.invoke(main, ["discover", "--help"])

        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--duration" in result.output
        assert "--json" in result.output

    @patch("mdns_generator.cli.ServiceDiscovery")
    def test_discover_short_duration(self, mock_disc_class, runner):
        """Test discover command with short duration."""
        mock_disc = MagicMock()
        mock_disc.__enter__ = MagicMock(return_value=mock_disc)
        mock_disc.__exit__ = MagicMock(return_value=False)
        mock_disc.discover_services.return_value = []
        mock_disc_class.return_value = mock_disc

        result = runner.invoke(
            main,
            [
                "discover",
                "--duration",
                "0.1",
            ],
        )

        assert "No services discovered" in result.output or result.exit_code == 0

    @patch("mdns_generator.cli.ServiceDiscovery")
    def test_discover_json_output(self, mock_disc_class, runner):
        """Test discover command with JSON output."""
        mock_disc = MagicMock()
        mock_disc.__enter__ = MagicMock(return_value=mock_disc)
        mock_disc.__exit__ = MagicMock(return_value=False)
        mock_disc.discover_services.return_value = []
        mock_disc_class.return_value = mock_disc

        result = runner.invoke(
            main,
            [
                "discover",
                "--duration",
                "0.1",
                "--json",
            ],
        )

        assert "[]" in result.output or result.exit_code == 0


class TestRegisterCommand:
    """Tests for register command."""

    def test_register_help(self, runner):
        """Test register command help."""
        result = runner.invoke(main, ["register", "--help"])

        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--port" in result.output

    def test_register_requires_name_and_port(self, runner):
        """Test register command requires name and port."""
        result = runner.invoke(main, ["register"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()
