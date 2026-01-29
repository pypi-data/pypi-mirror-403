"""Tests for configuration management."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from cve_sentinel.config import (
    Config,
    ConfigError,
    ConfigValidationError,
    _find_config_file,
    _load_env_vars,
    _load_yaml_config,
    _validate_config,
    get_default_config,
    load_config,
)


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self) -> None:
        """Test Config has correct default values."""
        config = Config()
        assert config.target_path == Path(".")
        assert config.exclude == ["node_modules/", "vendor/", ".git/", "__pycache__/", "venv/"]
        assert config.analysis_level == 2
        assert config.auto_scan_on_startup is True
        assert config.cache_ttl_hours == 24
        assert config.nvd_api_key is None

    def test_custom_values(self) -> None:
        """Test Config with custom values."""
        config = Config(
            target_path=Path("/custom/path"),
            exclude=["custom/"],
            analysis_level=1,
            auto_scan_on_startup=False,
            cache_ttl_hours=48,
            nvd_api_key="test-key",
        )
        assert config.target_path == Path("/custom/path")
        assert config.exclude == ["custom/"]
        assert config.analysis_level == 1
        assert config.auto_scan_on_startup is False
        assert config.cache_ttl_hours == 48
        assert config.nvd_api_key == "test-key"

    def test_string_target_path_converted_to_path(self) -> None:
        """Test that string target_path is converted to Path."""
        config = Config(target_path="/some/path")  # type: ignore
        assert isinstance(config.target_path, Path)
        assert config.target_path == Path("/some/path")


class TestFindConfigFile:
    """Tests for _find_config_file function."""

    def test_find_yaml_file(self, tmp_path: Path) -> None:
        """Test finding .cve-sentinel.yaml file."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("analysis_level: 2")

        result = _find_config_file(tmp_path)
        assert result == config_file

    def test_find_yml_file(self, tmp_path: Path) -> None:
        """Test finding .cve-sentinel.yml file."""
        config_file = tmp_path / ".cve-sentinel.yml"
        config_file.write_text("analysis_level: 2")

        result = _find_config_file(tmp_path)
        assert result == config_file

    def test_yaml_takes_precedence_over_yml(self, tmp_path: Path) -> None:
        """Test that .yaml takes precedence over .yml."""
        yaml_file = tmp_path / ".cve-sentinel.yaml"
        yml_file = tmp_path / ".cve-sentinel.yml"
        yaml_file.write_text("analysis_level: 1")
        yml_file.write_text("analysis_level: 2")

        result = _find_config_file(tmp_path)
        assert result == yaml_file

    def test_no_config_file_returns_none(self, tmp_path: Path) -> None:
        """Test that None is returned when no config file exists."""
        result = _find_config_file(tmp_path)
        assert result is None


class TestLoadYamlConfig:
    """Tests for _load_yaml_config function."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Test loading valid YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
target_path: ./src
analysis_level: 2
exclude:
  - node_modules/
  - dist/
""")
        result = _load_yaml_config(config_file)
        assert result["target_path"] == "./src"
        assert result["analysis_level"] == 2
        assert result["exclude"] == ["node_modules/", "dist/"]

    def test_load_empty_yaml(self, tmp_path: Path) -> None:
        """Test loading empty YAML file returns empty dict."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        result = _load_yaml_config(config_file)
        assert result == {}

    def test_load_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid YAML raises ConfigError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigError, match="Failed to parse YAML"):
            _load_yaml_config(config_file)

    def test_load_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent file raises ConfigError."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigError, match="Failed to read config file"):
            _load_yaml_config(config_file)


class TestLoadEnvVars:
    """Tests for _load_env_vars function."""

    def test_load_nvd_api_key(self) -> None:
        """Test loading NVD API key from environment."""
        with mock.patch.dict(os.environ, {"CVE_SENTINEL_NVD_API_KEY": "test-api-key"}):
            result = _load_env_vars()
            assert result["nvd_api_key"] == "test-api-key"

    def test_no_env_vars_returns_empty_dict(self) -> None:
        """Test that empty dict is returned when no env vars are set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Clear specific vars
            env = os.environ.copy()
            env.pop("CVE_SENTINEL_NVD_API_KEY", None)
            with mock.patch.dict(os.environ, env, clear=True):
                result = _load_env_vars()
                assert "nvd_api_key" not in result


class TestValidateConfig:
    """Tests for _validate_config function."""

    def test_valid_config_passes(self, tmp_path: Path) -> None:
        """Test that valid config passes validation."""
        config = Config(
            target_path=tmp_path,
            analysis_level=2,
            cache_ttl_hours=24,
            nvd_api_key="test-key",
        )
        # Should not raise
        _validate_config(config)

    def test_invalid_analysis_level_too_low(self, tmp_path: Path) -> None:
        """Test that analysis_level < 1 fails validation."""
        config = Config(
            target_path=tmp_path,
            analysis_level=0,
            nvd_api_key="test-key",
        )
        with pytest.raises(ConfigValidationError, match="analysis_level must be between 1 and 3"):
            _validate_config(config)

    def test_invalid_analysis_level_too_high(self, tmp_path: Path) -> None:
        """Test that analysis_level > 3 fails validation."""
        config = Config(
            target_path=tmp_path,
            analysis_level=4,
            nvd_api_key="test-key",
        )
        with pytest.raises(ConfigValidationError, match="analysis_level must be between 1 and 3"):
            _validate_config(config)

    def test_invalid_cache_ttl_hours(self, tmp_path: Path) -> None:
        """Test that non-positive cache_ttl_hours fails validation."""
        config = Config(
            target_path=tmp_path,
            cache_ttl_hours=0,
            nvd_api_key="test-key",
        )
        with pytest.raises(ConfigValidationError, match="cache_ttl_hours must be positive"):
            _validate_config(config)

    def test_nonexistent_target_path(self) -> None:
        """Test that nonexistent target_path fails validation."""
        config = Config(
            target_path=Path("/nonexistent/path"),
            nvd_api_key="test-key",
        )
        with pytest.raises(ConfigValidationError, match="target_path does not exist"):
            _validate_config(config)

    def test_missing_nvd_api_key(self, tmp_path: Path) -> None:
        """Test that missing NVD API key fails validation."""
        config = Config(
            target_path=tmp_path,
            nvd_api_key=None,
        )
        with pytest.raises(ConfigValidationError, match="nvd_api_key is required"):
            _validate_config(config)

    def test_multiple_validation_errors(self) -> None:
        """Test that multiple errors are reported."""
        config = Config(
            target_path=Path("/nonexistent"),
            analysis_level=5,
            cache_ttl_hours=-1,
            nvd_api_key=None,
        )
        with pytest.raises(ConfigValidationError) as exc_info:
            _validate_config(config)

        error_msg = str(exc_info.value)
        assert "analysis_level" in error_msg
        assert "cache_ttl_hours" in error_msg
        assert "target_path" in error_msg
        assert "nvd_api_key" in error_msg


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_yaml_file(self, tmp_path: Path) -> None:
        """Test loading config from YAML file."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("""
target_path: ./
analysis_level: 2
nvd_api_key: test-key
""")
        config = load_config(tmp_path, validate=True)
        assert config.analysis_level == 2
        assert config.nvd_api_key == "test-key"

    def test_env_var_overrides_file(self, tmp_path: Path) -> None:
        """Test that environment variables override file settings."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("""
target_path: ./
nvd_api_key: file-key
""")
        with mock.patch.dict(os.environ, {"CVE_SENTINEL_NVD_API_KEY": "env-key"}):
            config = load_config(tmp_path, validate=True)
            assert config.nvd_api_key == "env-key"

    def test_custom_config_path_from_env(self, tmp_path: Path) -> None:
        """Test loading config from custom path via environment variable."""
        custom_config = tmp_path / "custom" / "config.yaml"
        custom_config.parent.mkdir(parents=True)
        custom_config.write_text("""
target_path: ./
analysis_level: 1
nvd_api_key: custom-key
""")
        # Create target_path for validation
        target = tmp_path / "custom"

        with mock.patch.dict(os.environ, {"CVE_SENTINEL_CONFIG_PATH": str(custom_config)}):
            config = load_config(tmp_path, validate=True)
            assert config.analysis_level == 1
            assert config.nvd_api_key == "custom-key"

    def test_nonexistent_custom_config_path_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent custom config path raises error."""
        with (
            mock.patch.dict(os.environ, {"CVE_SENTINEL_CONFIG_PATH": "/nonexistent/config.yaml"}),
            pytest.raises(ConfigError, match="does not exist"),
        ):
            load_config(tmp_path)

    def test_load_without_validation(self, tmp_path: Path) -> None:
        """Test loading config without validation."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("""
analysis_level: 5
cache_ttl_hours: -1
""")
        # Should not raise even with invalid values
        config = load_config(tmp_path, validate=False)
        assert config.analysis_level == 5
        assert config.cache_ttl_hours == -1

    def test_load_without_api_key_requirement(self, tmp_path: Path) -> None:
        """Test loading config without requiring API key."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("""
target_path: ./
analysis_level: 2
""")
        # Should not raise without API key when not required
        config = load_config(tmp_path, validate=True, require_api_key=False)
        assert config.nvd_api_key is None
        assert config.analysis_level == 2

    def test_default_target_path_is_base_path(self, tmp_path: Path) -> None:
        """Test that default target_path is the base_path."""
        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("nvd_api_key: test-key")

        config = load_config(tmp_path, validate=True)
        assert config.target_path == tmp_path

    def test_relative_target_path_resolved(self, tmp_path: Path) -> None:
        """Test that relative target_path is resolved relative to base_path."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        config_file = tmp_path / ".cve-sentinel.yaml"
        config_file.write_text("""
target_path: ./subdir
nvd_api_key: test-key
""")
        config = load_config(tmp_path, validate=True)
        assert config.target_path == subdir


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_config_with_defaults(self) -> None:
        """Test that get_default_config returns Config with defaults."""
        config = get_default_config()
        assert isinstance(config, Config)
        assert config.target_path == Path(".")
        assert config.analysis_level == 2
        assert config.nvd_api_key is None
