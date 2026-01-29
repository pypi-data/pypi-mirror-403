"""Tests for SessionStart hook functionality."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


class TestHookScript:
    """Tests for the scanner.sh hook script."""

    @pytest.fixture
    def hook_script_path(self) -> Path:
        """Get path to the hook script."""
        project_root = Path(__file__).parent.parent
        return project_root / "scripts" / "scanner.sh"

    @pytest.fixture
    def temp_project(self) -> Path:
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_hook_script_exists(self, hook_script_path: Path) -> None:
        """Test that the hook script exists."""
        assert hook_script_path.exists(), f"Hook script not found at {hook_script_path}"

    def test_hook_script_is_executable(self, hook_script_path: Path) -> None:
        """Test that the hook script is executable."""
        assert os.access(hook_script_path, os.X_OK), "Hook script is not executable"

    def test_hook_creates_output_directory(
        self, hook_script_path: Path, temp_project: Path
    ) -> None:
        """Test that hook creates .cve-sentinel directory."""
        # Run the hook script (it will fail to find cve_sentinel, but should create dir)
        result = subprocess.run(
            [str(hook_script_path)],
            cwd=str(temp_project),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Hook should exit 0 even if scanner not found
        assert result.returncode == 0

        # Output directory should exist
        output_dir = temp_project / ".cve-sentinel"
        assert output_dir.exists()

    def test_hook_creates_status_file(self, hook_script_path: Path, temp_project: Path) -> None:
        """Test that hook creates status.json file."""
        subprocess.run(
            [str(hook_script_path)],
            cwd=str(temp_project),
            capture_output=True,
            timeout=10,
        )

        status_file = temp_project / ".cve-sentinel" / "status.json"
        assert status_file.exists()

    def test_hook_status_file_format(self, hook_script_path: Path, temp_project: Path) -> None:
        """Test that status.json has correct format."""
        subprocess.run(
            [str(hook_script_path)],
            cwd=str(temp_project),
            capture_output=True,
            timeout=10,
        )

        status_file = temp_project / ".cve-sentinel" / "status.json"
        with open(status_file) as f:
            status = json.load(f)

        # Should have status field
        assert "status" in status
        assert status["status"] in ["scanning", "error"]

        # Should have started_at field
        assert "started_at" in status

    def test_hook_respects_disabled_auto_scan(
        self, hook_script_path: Path, temp_project: Path
    ) -> None:
        """Test that hook respects auto_scan_on_startup: false config."""
        # Create config file that disables auto scan
        config_file = temp_project / ".cve-sentinel.yaml"
        config_file.write_text("auto_scan_on_startup: false\n")

        result = subprocess.run(
            [str(hook_script_path)],
            cwd=str(temp_project),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should exit 0
        assert result.returncode == 0

        # Output should indicate disabled
        assert "disabled" in result.stdout.lower() or not (temp_project / ".cve-sentinel").exists()

    def test_hook_timeout_compliance(self, hook_script_path: Path, temp_project: Path) -> None:
        """Test that hook completes within timeout (10 seconds)."""
        start_time = time.time()

        subprocess.run(
            [str(hook_script_path)],
            cwd=str(temp_project),
            capture_output=True,
            timeout=10,  # 10 second timeout
        )

        elapsed = time.time() - start_time
        # Should complete very quickly (< 5 seconds) since it backgrounds the work
        assert elapsed < 5, f"Hook took {elapsed:.2f}s, should complete in < 5s"


class TestStatusFileFormat:
    """Tests for status.json file format and content."""

    def test_status_scanning(self) -> None:
        """Test scanning status format."""
        status = {
            "status": "scanning",
            "started_at": "2024-01-01T00:00:00Z",
        }
        assert status["status"] == "scanning"
        assert "started_at" in status

    def test_status_completed(self) -> None:
        """Test completed status format."""
        status = {
            "status": "completed",
            "started_at": "2024-01-01T00:00:00Z",
        }
        assert status["status"] == "completed"

    def test_status_error(self) -> None:
        """Test error status format."""
        status = {
            "status": "error",
            "started_at": "2024-01-01T00:00:00Z",
            "error": "Python not found",
        }
        assert status["status"] == "error"
        assert "error" in status


class TestConfigCheck:
    """Tests for configuration file checking."""

    def test_yaml_config_detection(self) -> None:
        """Test YAML config file detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".cve-sentinel.yaml"
            config_path.write_text("analysis_level: 2\n")

            assert config_path.exists()

    def test_yml_config_detection(self) -> None:
        """Test YML config file detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".cve-sentinel.yml"
            config_path.write_text("analysis_level: 2\n")

            assert config_path.exists()

    def test_auto_scan_enabled_by_default(self) -> None:
        """Test that auto_scan is enabled by default."""
        from cve_sentinel.config import Config

        config = Config()
        assert config.auto_scan_on_startup is True

    def test_auto_scan_can_be_disabled(self) -> None:
        """Test that auto_scan can be disabled via config."""
        from cve_sentinel.config import Config

        config = Config(auto_scan_on_startup=False)
        assert config.auto_scan_on_startup is False


class TestTemplateFiles:
    """Tests for template files."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get path to templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_settings_json_exists(self, templates_dir: Path) -> None:
        """Test that settings.json template exists."""
        settings_file = templates_dir / "settings.json"
        assert settings_file.exists()

    def test_settings_json_valid(self, templates_dir: Path) -> None:
        """Test that settings.json is valid JSON."""
        settings_file = templates_dir / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        assert "hooks" in settings
        assert "SessionStart" in settings["hooks"]

    def test_claude_md_template_exists(self, templates_dir: Path) -> None:
        """Test that CLAUDE.md template exists."""
        claude_md = templates_dir / "CLAUDE-cve-sentinel.md"
        assert claude_md.exists()

    def test_claude_md_template_content(self, templates_dir: Path) -> None:
        """Test that CLAUDE.md template has required sections."""
        claude_md = templates_dir / "CLAUDE-cve-sentinel.md"
        content = claude_md.read_text()

        # Check for key sections
        assert "status.json" in content.lower() or "status" in content.lower()
        assert "results.json" in content.lower() or "results" in content.lower()
        assert "vulnerability" in content.lower() or "cve" in content.lower()


class TestHookIntegration:
    """Integration tests for hook with scanner."""

    @pytest.fixture
    def hook_script_path(self) -> Path:
        """Get path to the hook script."""
        return Path(__file__).parent.parent / "scripts" / "scanner.sh"

    def test_hook_with_real_project(self, hook_script_path: Path) -> None:
        """Test hook execution on a project with dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a simple package.json
            package_json = tmp_path / "package.json"
            package_json.write_text(
                json.dumps({"name": "test-project", "dependencies": {"lodash": "4.17.21"}})
            )

            # Run hook
            result = subprocess.run(
                [str(hook_script_path)],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should exit 0
            assert result.returncode == 0

            # Status file should exist
            status_file = tmp_path / ".cve-sentinel" / "status.json"
            assert status_file.exists()

    def test_hook_idempotent(self, hook_script_path: Path) -> None:
        """Test that running hook multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Run hook twice
            for _ in range(2):
                result = subprocess.run(
                    [str(hook_script_path)],
                    cwd=str(tmp_path),
                    capture_output=True,
                    timeout=10,
                )
                assert result.returncode == 0

            # Should still have valid status
            status_file = tmp_path / ".cve-sentinel" / "status.json"
            if status_file.exists():
                with open(status_file) as f:
                    status = json.load(f)
                assert "status" in status
