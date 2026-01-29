"""Tests for the main scanner module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cve_sentinel.analyzers.base import Package
from cve_sentinel.config import Config
from cve_sentinel.matcher import VulnerabilityMatch
from cve_sentinel.scanner import (
    CVESentinelScanner,
    ScanResult,
    create_argument_parser,
    main,
    setup_logging,
)

# =============================================================================
# ScanResult Tests
# =============================================================================


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_scan_result_defaults(self) -> None:
        """Test ScanResult with default values."""
        result = ScanResult(success=True, packages_scanned=10)
        assert result.success is True
        assert result.packages_scanned == 10
        assert result.vulnerabilities == []
        assert result.errors == []
        assert result.scan_duration == 0.0

    def test_has_vulnerabilities_false(self) -> None:
        """Test has_vulnerabilities when no vulnerabilities."""
        result = ScanResult(success=True, packages_scanned=10)
        assert result.has_vulnerabilities is False

    def test_has_vulnerabilities_true(self) -> None:
        """Test has_vulnerabilities when vulnerabilities exist."""
        pkg = Package(
            name="test",
            version="1.0.0",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        vuln = VulnerabilityMatch(
            cve_id="CVE-2021-12345",
            package=pkg,
            severity="HIGH",
            cvss_score=7.5,
            description="Test vulnerability",
            fix_version="1.0.1",
            fix_command="npm install test@1.0.1",
        )
        result = ScanResult(
            success=True,
            packages_scanned=10,
            vulnerabilities=[vuln],
        )
        assert result.has_vulnerabilities is True

    def test_critical_count(self) -> None:
        """Test critical_count property."""
        pkg = Package(
            name="test",
            version="1.0.0",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        vulns = [
            VulnerabilityMatch(
                cve_id="CVE-2021-12345",
                package=pkg,
                severity="CRITICAL",
                cvss_score=9.8,
                description="Critical vulnerability",
                fix_version=None,
                fix_command=None,
            ),
            VulnerabilityMatch(
                cve_id="CVE-2021-12346",
                package=pkg,
                severity="HIGH",
                cvss_score=7.5,
                description="High vulnerability",
                fix_version=None,
                fix_command=None,
            ),
            VulnerabilityMatch(
                cve_id="CVE-2021-12347",
                package=pkg,
                severity="CRITICAL",
                cvss_score=9.1,
                description="Another critical",
                fix_version=None,
                fix_command=None,
            ),
        ]
        result = ScanResult(
            success=True,
            packages_scanned=10,
            vulnerabilities=vulns,
        )
        assert result.critical_count == 2
        assert result.high_count == 1


# =============================================================================
# CVESentinelScanner Tests
# =============================================================================


class TestCVESentinelScanner:
    """Tests for CVESentinelScanner class."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> Config:
        """Create a test configuration."""
        return Config(
            target_path=tmp_path,
            exclude=["node_modules/"],
            analysis_level=2,
            auto_scan_on_startup=True,
            cache_ttl_hours=24,
            nvd_api_key=None,  # No API key for tests
        )

    @pytest.fixture
    def scanner(self, config: Config) -> CVESentinelScanner:
        """Create a test scanner."""
        return CVESentinelScanner(config)

    def test_scanner_initialization(self, scanner: CVESentinelScanner) -> None:
        """Test scanner initialization."""
        assert scanner.config is not None
        assert scanner._nvd_client is None
        assert scanner._osv_client is None
        assert scanner._initialized is False

    def test_scan_empty_project(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test scanning an empty project directory."""
        result = scanner.scan(tmp_path)

        assert result.success is True
        assert result.packages_scanned == 0
        assert result.vulnerabilities == []

        # Check status file was created
        status_file = tmp_path / ".cve-sentinel" / "status.json"
        assert status_file.exists()
        status_data = json.loads(status_file.read_text())
        assert status_data["status"] == "completed"

    def test_scan_with_npm_project(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test scanning a project with package.json."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "version": "1.0.0",
                    "dependencies": {
                        "lodash": "4.17.21",
                        "express": "4.18.2",
                    },
                }
            )
        )

        # Mock OSV client to return no vulnerabilities
        with patch.object(scanner, "_osv_client") as mock_osv:
            mock_osv.query_batch.return_value = {}
            scanner._osv_client = mock_osv

            result = scanner.scan(tmp_path)

        assert result.success is True
        assert result.packages_scanned >= 2

        # Check results file
        results_file = tmp_path / ".cve-sentinel" / "results.json"
        assert results_file.exists()

    def test_scan_nonexistent_path(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test scanning a nonexistent path."""
        nonexistent = tmp_path / "nonexistent"
        result = scanner.scan(nonexistent)

        assert result.success is False
        assert any("does not exist" in err for err in result.errors)

    def test_scan_file_instead_of_directory(
        self, scanner: CVESentinelScanner, tmp_path: Path
    ) -> None:
        """Test scanning a file instead of directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = scanner.scan(test_file)

        assert result.success is False
        assert any("not a directory" in err for err in result.errors)

    def test_deduplicate_packages(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test package deduplication."""
        packages = [
            Package(
                name="lodash",
                version="4.17.21",
                ecosystem="npm",
                source_file=Path("package.json"),
                is_direct=True,
            ),
            Package(
                name="lodash",
                version="4.17.21",
                ecosystem="npm",
                source_file=Path("package-lock.json"),
                is_direct=False,
            ),
            Package(
                name="express",
                version="4.18.2",
                ecosystem="npm",
                source_file=Path("package.json"),
                is_direct=True,
            ),
        ]

        result = scanner._deduplicate_packages(packages)

        assert len(result) == 2
        # Direct dependency should be preferred
        lodash = next(p for p in result if p.name == "lodash")
        assert lodash.is_direct is True

    def test_scan_with_python_project(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test scanning a Python project with requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\nflask==2.3.0\n")

        result = scanner.scan(tmp_path)

        assert result.success is True
        assert result.packages_scanned >= 2

    def test_scan_error_handling(self, scanner: CVESentinelScanner, tmp_path: Path) -> None:
        """Test error handling during scan."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test",
                    "dependencies": {"test-pkg": "1.0.0"},
                }
            )
        )

        # Force an error in matcher
        scanner._initialize_components(tmp_path)
        scanner._matcher = MagicMock()
        scanner._matcher.match.side_effect = Exception("Test error")

        result = scanner.scan(tmp_path)

        # Scan should still succeed but have errors
        assert result.success is True
        assert any("Test error" in err for err in result.errors)


# =============================================================================
# CLI Tests
# =============================================================================


class TestCLI:
    """Tests for CLI argument parsing."""

    def test_argument_parser_defaults(self) -> None:
        """Test argument parser with default values."""
        parser = create_argument_parser()
        args = parser.parse_args([])

        assert args.path == Path(".")
        assert args.config is None
        assert args.verbose is False
        assert args.fail_on == "HIGH"
        assert args.no_color is False
        assert args.json is False

    def test_argument_parser_path(self) -> None:
        """Test --path argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["--path", "/tmp/project"])

        assert args.path == Path("/tmp/project")

    def test_argument_parser_short_path(self) -> None:
        """Test -p argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["-p", "/tmp/project"])

        assert args.path == Path("/tmp/project")

    def test_argument_parser_verbose(self) -> None:
        """Test --verbose argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["--verbose"])

        assert args.verbose is True

    def test_argument_parser_fail_on(self) -> None:
        """Test --fail-on argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["--fail-on", "CRITICAL"])

        assert args.fail_on == "CRITICAL"

    def test_argument_parser_no_color(self) -> None:
        """Test --no-color argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["--no-color"])

        assert args.no_color is True

    def test_argument_parser_json(self) -> None:
        """Test --json argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["--json"])

        assert args.json is True


class TestMainFunction:
    """Tests for main() function."""

    def test_main_success_no_vulnerabilities(self, tmp_path: Path) -> None:
        """Test main function with successful scan and no vulnerabilities."""
        result = main(["--path", str(tmp_path)])
        assert result == 0

    def test_main_with_vulnerabilities(self, tmp_path: Path) -> None:
        """Test main function when vulnerabilities are found."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "dependencies": {"vulnerable-pkg": "1.0.0"},
                }
            )
        )

        # Mock the scanner to return vulnerabilities
        with patch("cve_sentinel.scanner.CVESentinelScanner") as MockScanner:
            pkg = Package(
                name="vulnerable-pkg",
                version="1.0.0",
                ecosystem="npm",
                source_file=package_json,
            )
            vuln = VulnerabilityMatch(
                cve_id="CVE-2021-12345",
                package=pkg,
                severity="HIGH",
                cvss_score=7.5,
                description="Test vulnerability",
                fix_version="1.0.1",
                fix_command="npm install vulnerable-pkg@1.0.1",
            )
            mock_result = ScanResult(
                success=True,
                packages_scanned=1,
                vulnerabilities=[vuln],
                scan_duration=0.1,
            )
            MockScanner.return_value.scan.return_value = mock_result

            result = main(["--path", str(tmp_path)])

        assert result == 1

    def test_main_with_fail_on_critical(self, tmp_path: Path) -> None:
        """Test main with --fail-on CRITICAL only fails on critical."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "dependencies": {"test-pkg": "1.0.0"},
                }
            )
        )

        # Mock scanner with HIGH severity vulnerability
        with patch("cve_sentinel.scanner.CVESentinelScanner") as MockScanner:
            pkg = Package(
                name="test-pkg",
                version="1.0.0",
                ecosystem="npm",
                source_file=package_json,
            )
            vuln = VulnerabilityMatch(
                cve_id="CVE-2021-12345",
                package=pkg,
                severity="HIGH",
                cvss_score=7.5,
                description="Test vulnerability",
                fix_version=None,
                fix_command=None,
            )
            mock_result = ScanResult(
                success=True,
                packages_scanned=1,
                vulnerabilities=[vuln],
                scan_duration=0.1,
            )
            MockScanner.return_value.scan.return_value = mock_result

            result = main(["--path", str(tmp_path), "--fail-on", "CRITICAL"])

        # Should return 0 because HIGH is not CRITICAL
        assert result == 0

    def test_main_scan_failure(self, tmp_path: Path) -> None:
        """Test main when scan fails."""
        with patch("cve_sentinel.scanner.CVESentinelScanner") as MockScanner:
            mock_result = ScanResult(
                success=False,
                packages_scanned=0,
                errors=["Test error"],
                scan_duration=0.1,
            )
            MockScanner.return_value.scan.return_value = mock_result

            result = main(["--path", str(tmp_path)])

        assert result == 2

    def test_main_config_error(self, tmp_path: Path) -> None:
        """Test main with configuration error."""
        with patch("cve_sentinel.scanner.load_config") as mock_load:
            from cve_sentinel.config import ConfigError

            mock_load.side_effect = ConfigError("Invalid config")

            result = main(["--path", str(tmp_path)])

        assert result == 2


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_logging_default(self) -> None:
        """Test default logging setup."""
        import logging

        # Save original level
        root_logger = logging.getLogger()
        original_level = root_logger.level

        try:
            setup_logging(verbose=False)
            # Check that a handler was added with INFO level
            assert (
                any(h.level <= logging.INFO for h in root_logger.handlers)
                or root_logger.level <= logging.INFO
            )
        finally:
            # Restore original state
            root_logger.setLevel(original_level)

    def test_setup_logging_verbose(self) -> None:
        """Test verbose logging setup."""
        import logging

        # Save original level
        root_logger = logging.getLogger()
        original_level = root_logger.level

        try:
            setup_logging(verbose=True)
            # Check that a handler was added with DEBUG level
            assert (
                any(h.level <= logging.DEBUG for h in root_logger.handlers)
                or root_logger.level <= logging.DEBUG
            )
        finally:
            # Restore original state
            root_logger.setLevel(original_level)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the scanner."""

    @pytest.fixture
    def project_with_deps(self, tmp_path: Path) -> Path:
        """Create a project with multiple dependency files."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "version": "1.0.0",
                    "dependencies": {
                        "lodash": "4.17.21",
                    },
                }
            )
        )

        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\n")

        return tmp_path

    def test_full_scan_flow(self, project_with_deps: Path) -> None:
        """Test complete scan flow from start to finish."""
        config = Config(
            target_path=project_with_deps,
            analysis_level=2,
            nvd_api_key=None,
        )

        scanner = CVESentinelScanner(config)
        result = scanner.scan(project_with_deps)

        # Verify scan completed
        assert result.success is True
        assert result.packages_scanned >= 2

        # Verify output files
        output_dir = project_with_deps / ".cve-sentinel"
        assert output_dir.exists()

        status_file = output_dir / "status.json"
        assert status_file.exists()
        status = json.loads(status_file.read_text())
        assert status["status"] == "completed"

        results_file = output_dir / "results.json"
        assert results_file.exists()
        results = json.loads(results_file.read_text())
        assert "vulnerabilities" in results
        assert "summary" in results

    def test_scan_with_analyzer_error(self, tmp_path: Path) -> None:
        """Test scan continues even when one analyzer fails."""
        # Create invalid package.json (will cause parsing error)
        package_json = tmp_path / "package.json"
        package_json.write_text("{ invalid json }")

        # Create valid requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\n")

        config = Config(
            target_path=tmp_path,
            analysis_level=2,
            nvd_api_key=None,
        )

        scanner = CVESentinelScanner(config)
        result = scanner.scan(tmp_path)

        # Scan should still succeed
        assert result.success is True
        # Should have error from npm analyzer
        assert len(result.errors) > 0 or result.packages_scanned >= 1
