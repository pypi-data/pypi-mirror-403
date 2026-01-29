"""Tests for the CVE Sentinel CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cve_sentinel.cli import (
    CONFIG_TEMPLATE,
    cmd_init,
    cmd_scan,
    cmd_uninstall,
    cmd_update,
    create_parser,
    main,
)

# =============================================================================
# Parser Tests
# =============================================================================


class TestParser:
    """Tests for the argument parser."""

    def test_parser_creation(self) -> None:
        """Test parser can be created."""
        parser = create_parser()
        assert parser is not None

    def test_parser_version(self) -> None:
        """Test --version flag."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_scan_command(self) -> None:
        """Test scan command parsing."""
        parser = create_parser()
        args = parser.parse_args(["scan"])
        assert args.command == "scan"
        assert args.path == Path(".")
        assert args.verbose is False

    def test_parser_scan_with_options(self) -> None:
        """Test scan command with options."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "scan",
                "/tmp/project",
                "--level",
                "2",
                "--exclude",
                "test/*",
                "--verbose",
                "--fail-on",
                "CRITICAL",
            ]
        )
        assert args.command == "scan"
        assert args.path == Path("/tmp/project")
        assert args.level == 2
        assert args.exclude == ["test/*"]
        assert args.verbose is True
        assert args.fail_on == "CRITICAL"

    def test_parser_init_command(self) -> None:
        """Test init command parsing."""
        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"
        assert args.force is False

    def test_parser_init_with_force(self) -> None:
        """Test init command with --force."""
        parser = create_parser()
        args = parser.parse_args(["init", "--force"])
        assert args.command == "init"
        assert args.force is True

    def test_parser_uninstall_command(self) -> None:
        """Test uninstall command parsing."""
        parser = create_parser()
        args = parser.parse_args(["uninstall"])
        assert args.command == "uninstall"
        assert args.yes is False
        assert args.remove_cache is False

    def test_parser_uninstall_with_options(self) -> None:
        """Test uninstall command with options."""
        parser = create_parser()
        args = parser.parse_args(["uninstall", "--yes", "--remove-cache"])
        assert args.command == "uninstall"
        assert args.yes is True
        assert args.remove_cache is True

    def test_parser_update_command(self) -> None:
        """Test update command parsing."""
        parser = create_parser()
        args = parser.parse_args(["update"])
        assert args.command == "update"


# =============================================================================
# Init Command Tests
# =============================================================================


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_config_file(self, tmp_path: Path) -> None:
        """Test init creates .cve-sentinel.yaml."""
        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path)])

        result = cmd_init(args)

        assert result == 0
        config_file = tmp_path / ".cve-sentinel.yaml"
        assert config_file.exists()
        assert "target_path" in config_file.read_text()

    def test_init_creates_sentinel_dir(self, tmp_path: Path) -> None:
        """Test init creates .cve-sentinel directory."""
        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path)])

        cmd_init(args)

        sentinel_dir = tmp_path / ".cve-sentinel"
        assert sentinel_dir.exists()
        assert sentinel_dir.is_dir()

    def test_init_creates_gitignore(self, tmp_path: Path) -> None:
        """Test init creates/updates .gitignore."""
        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path)])

        cmd_init(args)

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".cve-sentinel/" in content

    def test_init_updates_existing_gitignore(self, tmp_path: Path) -> None:
        """Test init updates existing .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n")

        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path)])

        cmd_init(args)

        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".cve-sentinel/" in content

    def test_init_skip_existing_config(self, tmp_path: Path) -> None:
        """Test init doesn't overwrite existing config without --force."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("# Custom config\n")

        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path)])

        cmd_init(args)

        # Should not be overwritten
        assert "Custom config" in config_file.read_text()

    def test_init_force_overwrite(self, tmp_path: Path) -> None:
        """Test init --force overwrites existing config."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("# Custom config\n")

        parser = create_parser()
        args = parser.parse_args(["init", "--path", str(tmp_path), "--force"])

        cmd_init(args)

        # Should be overwritten with template
        content = config_file.read_text()
        assert "target_path" in content
        assert "Custom config" not in content


# =============================================================================
# Scan Command Tests
# =============================================================================


class TestScanCommand:
    """Tests for the scan command."""

    def test_scan_empty_project(self, tmp_path: Path) -> None:
        """Test scan on empty project."""
        parser = create_parser()
        args = parser.parse_args(["scan", str(tmp_path)])

        result = cmd_scan(args)

        assert result == 0

    def test_scan_with_package_json(self, tmp_path: Path) -> None:
        """Test scan with package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test",
                    "dependencies": {"lodash": "4.17.21"},
                }
            )
        )

        parser = create_parser()
        args = parser.parse_args(["scan", str(tmp_path)])

        result = cmd_scan(args)

        # Should succeed (no vulnerabilities or exit based on threshold)
        assert result in (0, 1)

    def test_scan_nonexistent_path(self, tmp_path: Path) -> None:
        """Test scan on nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        parser = create_parser()
        args = parser.parse_args(["scan", str(nonexistent)])

        result = cmd_scan(args)

        assert result == 2  # Error


# =============================================================================
# Update Command Tests
# =============================================================================


class TestUpdateCommand:
    """Tests for the update command."""

    def test_update_command_runs(self, tmp_path: Path) -> None:
        """Test update command executes."""
        parser = create_parser()
        args = parser.parse_args(["update"])

        # Mock subprocess to avoid actual pip operations
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = cmd_update(args)

        assert result == 0
        mock_run.assert_called()

    def test_update_command_handles_failure(self) -> None:
        """Test update command handles pip failure."""
        parser = create_parser()
        args = parser.parse_args(["update"])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            result = cmd_update(args)

        assert result == 1


# =============================================================================
# Uninstall Command Tests
# =============================================================================


class TestUninstallCommand:
    """Tests for the uninstall command."""

    def test_uninstall_with_yes(self, tmp_path: Path) -> None:
        """Test uninstall with --yes skips confirmation."""
        parser = create_parser()
        args = parser.parse_args(["uninstall", "--yes"])

        # Mock subprocess and file operations
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
            patch("builtins.open", MagicMock()),
        ):
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = False

            result = cmd_uninstall(args)

        # Should attempt uninstall
        mock_run.assert_called()

    def test_uninstall_cancelled(self) -> None:
        """Test uninstall cancellation on 'n' input."""
        parser = create_parser()
        args = parser.parse_args(["uninstall"])

        with patch("builtins.input", return_value="n"):
            result = cmd_uninstall(args)

        assert result == 0


# =============================================================================
# Main Function Tests
# =============================================================================


class TestMainFunction:
    """Tests for the main function."""

    def test_main_no_args_runs_scan(self, tmp_path: Path, monkeypatch) -> None:
        """Test main with no args runs scan on current directory."""
        # Change to tmp_path so scan runs on empty directory
        monkeypatch.chdir(tmp_path)
        result = main([])
        # Should succeed (scan on empty project)
        assert result == 0

    def test_main_scan_command(self, tmp_path: Path) -> None:
        """Test main with scan command."""
        result = main(["scan", str(tmp_path)])
        assert result in (0, 1, 2)

    def test_main_scan_with_path_only(self, tmp_path: Path) -> None:
        """Test main with path only (no scan command)."""
        result = main([str(tmp_path)])
        assert result in (0, 1, 2)

    def test_main_init_command(self, tmp_path: Path) -> None:
        """Test main with init command."""
        result = main(["init", "--path", str(tmp_path)])
        assert result == 0

    def test_main_version(self) -> None:
        """Test main with --version."""
        with pytest.raises(SystemExit):
            main(["--version"])


# =============================================================================
# Config Template Tests
# =============================================================================


class TestConfigTemplate:
    """Tests for the configuration template."""

    def test_config_template_valid_yaml(self) -> None:
        """Test config template is valid YAML."""
        import yaml

        config = yaml.safe_load(CONFIG_TEMPLATE)
        assert config is not None
        assert "target_path" in config
        assert "exclude" in config
        assert "analysis_level" in config

    def test_config_template_default_values(self) -> None:
        """Test config template has sensible defaults."""
        import yaml

        config = yaml.safe_load(CONFIG_TEMPLATE)
        assert config["target_path"] == "."
        assert config["analysis_level"] == 2
        assert config["auto_scan_on_startup"] is True
        assert config["cache_ttl_hours"] == 24
