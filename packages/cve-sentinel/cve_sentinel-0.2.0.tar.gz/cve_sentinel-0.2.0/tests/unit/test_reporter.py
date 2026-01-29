"""Tests for the reporter module."""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from cve_sentinel.analyzers.base import Package
from cve_sentinel.matcher import VulnerabilityMatch
from cve_sentinel.reporter import (
    Reporter,
    ScanSummary,
    TerminalColors,
    create_reporter,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    return tmp_path / ".cve-sentinel"


@pytest.fixture
def sample_package() -> Package:
    """Create a sample package."""
    return Package(
        name="lodash",
        version="4.17.20",
        ecosystem="npm",
        source_file=Path("package.json"),
        source_line=15,
        is_direct=True,
    )


@pytest.fixture
def sample_vulnerability(sample_package: Package) -> VulnerabilityMatch:
    """Create a sample vulnerability match."""
    return VulnerabilityMatch(
        cve_id="CVE-2024-12345",
        package=sample_package,
        severity="CRITICAL",
        cvss_score=9.8,
        description="A critical vulnerability in lodash that allows remote code execution.",
        fix_version="4.17.21",
        fix_command="npm install lodash@4.17.21",
        affected_files=[{"file": "package.json", "line": 15}],
        references=["https://nvd.nist.gov/vuln/detail/CVE-2024-12345"],
        osv_id="GHSA-xxxx-yyyy-zzzz",
    )


@pytest.fixture
def multiple_vulnerabilities() -> List[VulnerabilityMatch]:
    """Create multiple vulnerabilities with different severities."""
    packages = [
        Package(
            name="lodash", version="4.17.20", ecosystem="npm", source_file=Path("package.json")
        ),
        Package(
            name="express", version="4.17.0", ecosystem="npm", source_file=Path("package.json")
        ),
        Package(
            name="requests",
            version="2.25.0",
            ecosystem="pypi",
            source_file=Path("requirements.txt"),
        ),
        Package(
            name="flask", version="1.1.0", ecosystem="pypi", source_file=Path("requirements.txt")
        ),
        Package(
            name="unknown-pkg", version="1.0.0", ecosystem="npm", source_file=Path("package.json")
        ),
    ]

    return [
        VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=packages[0],
            severity="CRITICAL",
            cvss_score=9.8,
            description="Critical vulnerability",
            fix_version="4.17.21",
            fix_command="npm install lodash@4.17.21",
            affected_files=[{"file": "package.json", "line": 10}],
            references=[],
        ),
        VulnerabilityMatch(
            cve_id="CVE-2024-0002",
            package=packages[1],
            severity="HIGH",
            cvss_score=8.5,
            description="High severity vulnerability",
            fix_version="4.18.0",
            fix_command="npm install express@4.18.0",
            affected_files=[{"file": "package.json", "line": 15}],
            references=[],
        ),
        VulnerabilityMatch(
            cve_id="CVE-2024-0003",
            package=packages[2],
            severity="MEDIUM",
            cvss_score=5.5,
            description="Medium severity vulnerability",
            fix_version="2.26.0",
            fix_command="pip install requests==2.26.0",
            affected_files=[{"file": "requirements.txt", "line": 5}],
            references=[],
        ),
        VulnerabilityMatch(
            cve_id="CVE-2024-0004",
            package=packages[3],
            severity="LOW",
            cvss_score=2.0,
            description="Low severity vulnerability",
            fix_version="2.0.0",
            fix_command="pip install flask==2.0.0",
            affected_files=[{"file": "requirements.txt", "line": 8}],
            references=[],
        ),
        VulnerabilityMatch(
            cve_id="CVE-2024-0005",
            package=packages[4],
            severity=None,  # Unknown severity
            cvss_score=None,
            description="Unknown severity vulnerability",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        ),
    ]


# =============================================================================
# ScanSummary Tests
# =============================================================================


class TestScanSummary:
    """Tests for ScanSummary dataclass."""

    def test_from_empty_vulnerabilities(self) -> None:
        """Test creating summary from empty vulnerability list."""
        summary = ScanSummary.from_vulnerabilities([], packages_scanned=10)

        assert summary.total_vulnerabilities == 0
        assert summary.critical_count == 0
        assert summary.high_count == 0
        assert summary.medium_count == 0
        assert summary.low_count == 0
        assert summary.unknown_count == 0
        assert summary.packages_scanned == 10

    def test_from_single_vulnerability(self, sample_vulnerability: VulnerabilityMatch) -> None:
        """Test creating summary from single vulnerability."""
        summary = ScanSummary.from_vulnerabilities([sample_vulnerability], packages_scanned=5)

        assert summary.total_vulnerabilities == 1
        assert summary.critical_count == 1
        assert summary.high_count == 0
        assert summary.medium_count == 0
        assert summary.low_count == 0
        assert summary.unknown_count == 0
        assert summary.packages_scanned == 5

    def test_from_multiple_vulnerabilities(
        self, multiple_vulnerabilities: List[VulnerabilityMatch]
    ) -> None:
        """Test creating summary from multiple vulnerabilities."""
        summary = ScanSummary.from_vulnerabilities(multiple_vulnerabilities, packages_scanned=50)

        assert summary.total_vulnerabilities == 5
        assert summary.critical_count == 1
        assert summary.high_count == 1
        assert summary.medium_count == 1
        assert summary.low_count == 1
        assert summary.unknown_count == 1
        assert summary.packages_scanned == 50

    def test_from_lowercase_severity(self) -> None:
        """Test handling lowercase severity strings."""
        package = Package(
            name="test", version="1.0.0", ecosystem="npm", source_file=Path("package.json")
        )
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=package,
            severity="critical",  # lowercase
            cvss_score=9.5,
            description="Test",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        summary = ScanSummary.from_vulnerabilities([vuln], packages_scanned=1)
        assert summary.critical_count == 1

    def test_from_invalid_severity(self) -> None:
        """Test handling invalid severity string."""
        package = Package(
            name="test", version="1.0.0", ecosystem="npm", source_file=Path("package.json")
        )
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=package,
            severity="INVALID_SEVERITY",
            cvss_score=5.0,
            description="Test",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        summary = ScanSummary.from_vulnerabilities([vuln], packages_scanned=1)
        assert summary.unknown_count == 1

    def test_to_dict(self, multiple_vulnerabilities: List[VulnerabilityMatch]) -> None:
        """Test converting summary to dictionary."""
        summary = ScanSummary.from_vulnerabilities(multiple_vulnerabilities, packages_scanned=100)
        data = summary.to_dict()

        assert data == {
            "total": 5,
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 1,
            "unknown": 1,
            "packages_scanned": 100,
        }


# =============================================================================
# TerminalColors Tests
# =============================================================================


class TestTerminalColors:
    """Tests for TerminalColors class."""

    def test_supports_color_with_no_color_env(self) -> None:
        """Test that NO_COLOR environment variable disables colors."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert TerminalColors.supports_color() is False

    def test_supports_color_with_force_color_env(self) -> None:
        """Test that FORCE_COLOR environment variable enables colors."""
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False):
            # Clear NO_COLOR if present
            env = dict(os.environ)
            env.pop("NO_COLOR", None)
            env["FORCE_COLOR"] = "1"
            with patch.dict(os.environ, env, clear=True):
                assert TerminalColors.supports_color() is True

    def test_supports_color_dumb_terminal(self) -> None:
        """Test that dumb terminals don't support color."""
        with patch.dict(os.environ, {"TERM": "dumb"}, clear=False):
            env = dict(os.environ)
            env.pop("NO_COLOR", None)
            env.pop("FORCE_COLOR", None)
            env["TERM"] = "dumb"
            with patch.dict(os.environ, env, clear=True):
                with patch.object(sys.stdout, "isatty", return_value=True):
                    assert TerminalColors.supports_color() is False

    def test_supports_color_non_tty(self) -> None:
        """Test that non-TTY stdout doesn't support color."""
        with patch.dict(os.environ, {}, clear=False):
            env = dict(os.environ)
            env.pop("NO_COLOR", None)
            env.pop("FORCE_COLOR", None)
            with patch.dict(os.environ, env, clear=True):
                with patch.object(sys.stdout, "isatty", return_value=False):
                    assert TerminalColors.supports_color() is False

    def test_get_severity_color_with_color_enabled(self) -> None:
        """Test getting severity colors when colors enabled."""
        assert (
            TerminalColors.get_severity_color("CRITICAL", use_color=True) == TerminalColors.CRITICAL
        )
        assert TerminalColors.get_severity_color("HIGH", use_color=True) == TerminalColors.HIGH
        assert TerminalColors.get_severity_color("MEDIUM", use_color=True) == TerminalColors.MEDIUM
        assert TerminalColors.get_severity_color("LOW", use_color=True) == TerminalColors.LOW
        assert (
            TerminalColors.get_severity_color("UNKNOWN", use_color=True) == TerminalColors.UNKNOWN
        )

    def test_get_severity_color_with_color_disabled(self) -> None:
        """Test getting severity colors when colors disabled."""
        assert TerminalColors.get_severity_color("CRITICAL", use_color=False) == ""
        assert TerminalColors.get_severity_color("HIGH", use_color=False) == ""

    def test_get_severity_color_lowercase(self) -> None:
        """Test that lowercase severity works."""
        assert (
            TerminalColors.get_severity_color("critical", use_color=True) == TerminalColors.CRITICAL
        )
        assert TerminalColors.get_severity_color("high", use_color=True) == TerminalColors.HIGH

    def test_get_severity_color_none(self) -> None:
        """Test handling None severity."""
        assert TerminalColors.get_severity_color(None, use_color=True) == TerminalColors.UNKNOWN

    def test_get_severity_color_invalid(self) -> None:
        """Test handling invalid severity."""
        assert TerminalColors.get_severity_color("INVALID", use_color=True) == TerminalColors.GRAY


# =============================================================================
# Reporter Tests - Initialization
# =============================================================================


class TestReporterInit:
    """Tests for Reporter initialization."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nonexistent" / ".cve-sentinel"
        reporter = Reporter(output_dir, use_color=False)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_accepts_existing_directory(self, tmp_path: Path) -> None:
        """Test that existing directory is accepted."""
        output_dir = tmp_path / ".cve-sentinel"
        output_dir.mkdir(parents=True)

        reporter = Reporter(output_dir, use_color=False)
        assert reporter.output_dir == output_dir

    def test_use_color_explicit_true(self, temp_output_dir: Path) -> None:
        """Test explicit color enabled."""
        reporter = Reporter(temp_output_dir, use_color=True)
        assert reporter.use_color is True

    def test_use_color_explicit_false(self, temp_output_dir: Path) -> None:
        """Test explicit color disabled."""
        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.use_color is False


# =============================================================================
# Reporter Tests - status.json
# =============================================================================


class TestReporterStatus:
    """Tests for Reporter status.json output."""

    def test_update_status_scanning(self, temp_output_dir: Path) -> None:
        """Test updating status to scanning."""
        reporter = Reporter(temp_output_dir, use_color=False)
        reporter.update_status("scanning")

        status_file = temp_output_dir / "status.json"
        assert status_file.exists()

        data = json.loads(status_file.read_text())
        assert data["status"] == "scanning"
        assert "started_at" in data
        assert "completed_at" not in data

    def test_update_status_completed(self, temp_output_dir: Path) -> None:
        """Test updating status to completed."""
        reporter = Reporter(temp_output_dir, use_color=False)
        reporter.update_status("scanning")
        reporter.update_status("completed")

        status_file = temp_output_dir / "status.json"
        data = json.loads(status_file.read_text())

        assert data["status"] == "completed"
        assert "started_at" in data
        assert "completed_at" in data

    def test_update_status_error(self, temp_output_dir: Path) -> None:
        """Test updating status to error with message."""
        reporter = Reporter(temp_output_dir, use_color=False)
        reporter.update_status("error", error_message="Connection failed")

        status_file = temp_output_dir / "status.json"
        data = json.loads(status_file.read_text())

        assert data["status"] == "error"
        assert data["error_message"] == "Connection failed"

    def test_update_status_preserves_started_at(self, temp_output_dir: Path) -> None:
        """Test that started_at is preserved across status updates."""
        reporter = Reporter(temp_output_dir, use_color=False)

        reporter.update_status("scanning")
        status_file = temp_output_dir / "status.json"
        data1 = json.loads(status_file.read_text())
        started_at = data1["started_at"]

        reporter.update_status("completed")
        data2 = json.loads(status_file.read_text())

        assert data2["started_at"] == started_at

    def test_update_status_iso8601_format(self, temp_output_dir: Path) -> None:
        """Test that timestamps are in ISO 8601 format."""
        reporter = Reporter(temp_output_dir, use_color=False)
        reporter.update_status("completed")

        status_file = temp_output_dir / "status.json"
        data = json.loads(status_file.read_text())

        # ISO 8601 should contain 'T' separator and timezone info
        assert "T" in data["completed_at"]
        assert "+" in data["completed_at"] or "Z" in data["completed_at"]


# =============================================================================
# Reporter Tests - results.json
# =============================================================================


class TestReporterResults:
    """Tests for Reporter results.json output."""

    def test_write_results_empty(self, temp_output_dir: Path, tmp_path: Path) -> None:
        """Test writing results with no vulnerabilities."""
        reporter = Reporter(temp_output_dir, use_color=False)
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        result_path = reporter.write_results(project_path, packages_scanned=10, vulnerabilities=[])

        assert result_path.exists()
        data = json.loads(result_path.read_text())

        assert "scan_date" in data
        assert data["project_path"] == str(project_path.absolute())
        assert data["packages_scanned"] == 10
        assert data["vulnerabilities"] == []
        assert data["summary"]["total"] == 0

    def test_write_results_with_vulnerabilities(
        self,
        temp_output_dir: Path,
        tmp_path: Path,
        multiple_vulnerabilities: List[VulnerabilityMatch],
    ) -> None:
        """Test writing results with vulnerabilities."""
        reporter = Reporter(temp_output_dir, use_color=False)
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        result_path = reporter.write_results(
            project_path,
            packages_scanned=50,
            vulnerabilities=multiple_vulnerabilities,
        )

        data = json.loads(result_path.read_text())

        assert data["packages_scanned"] == 50
        assert len(data["vulnerabilities"]) == 5
        assert data["summary"]["total"] == 5
        assert data["summary"]["critical"] == 1
        assert data["summary"]["high"] == 1

    def test_write_results_vulnerability_format(
        self,
        temp_output_dir: Path,
        tmp_path: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test vulnerability JSON format."""
        reporter = Reporter(temp_output_dir, use_color=False)
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter.write_results(
            project_path, packages_scanned=1, vulnerabilities=[sample_vulnerability]
        )

        result_path = temp_output_dir / "results.json"
        data = json.loads(result_path.read_text())
        vuln = data["vulnerabilities"][0]

        assert vuln["cve_id"] == "CVE-2024-12345"
        assert vuln["osv_id"] == "GHSA-xxxx-yyyy-zzzz"
        assert vuln["package_name"] == "lodash"
        assert vuln["installed_version"] == "4.17.20"
        assert vuln["ecosystem"] == "npm"
        assert vuln["severity"] == "CRITICAL"
        assert vuln["cvss_score"] == 9.8
        assert "remote code execution" in vuln["description"]
        assert vuln["fix_version"] == "4.17.21"
        assert vuln["fix_command"] == "npm install lodash@4.17.21"
        assert len(vuln["affected_files"]) == 1
        assert vuln["references"][0] == "https://nvd.nist.gov/vuln/detail/CVE-2024-12345"

    def test_write_results_limits_references(
        self,
        temp_output_dir: Path,
        tmp_path: Path,
        sample_package: Package,
    ) -> None:
        """Test that references are limited to 5."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=8.0,
            description="Test",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[f"https://example.com/{i}" for i in range(10)],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter.write_results(project_path, packages_scanned=1, vulnerabilities=[vuln])

        result_path = temp_output_dir / "results.json"
        data = json.loads(result_path.read_text())

        assert len(data["vulnerabilities"][0]["references"]) == 5

    def test_write_results_unicode_support(
        self,
        temp_output_dir: Path,
        tmp_path: Path,
        sample_package: Package,
    ) -> None:
        """Test that Unicode characters are preserved."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=8.0,
            description="日本語の説明文です。",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter.write_results(project_path, packages_scanned=1, vulnerabilities=[vuln])

        result_path = temp_output_dir / "results.json"
        data = json.loads(result_path.read_text())

        assert "日本語の説明文です。" in data["vulnerabilities"][0]["description"]


# =============================================================================
# Reporter Tests - CLI Output
# =============================================================================


class TestReporterCLIOutput:
    """Tests for Reporter CLI output."""

    def test_print_summary_no_vulnerabilities(self, temp_output_dir: Path) -> None:
        """Test CLI output when no vulnerabilities found."""
        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(packages_scanned=45, vulnerabilities=[], output=output)

        result = output.getvalue()
        assert "✓" in result
        assert "No vulnerabilities detected" in result
        assert "45 packages" in result

    def test_print_summary_with_vulnerabilities(
        self,
        temp_output_dir: Path,
        multiple_vulnerabilities: List[VulnerabilityMatch],
    ) -> None:
        """Test CLI output when vulnerabilities found."""
        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(
            packages_scanned=50,
            vulnerabilities=multiple_vulnerabilities,
            output=output,
        )

        result = output.getvalue()
        assert "⚠" in result
        assert "5 vulnerabilities found" in result
        assert "CVE-2024-0001" in result
        assert "By Severity" in result

    def test_print_summary_sorted_by_severity(
        self,
        temp_output_dir: Path,
        multiple_vulnerabilities: List[VulnerabilityMatch],
    ) -> None:
        """Test that vulnerabilities are sorted by severity."""
        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(
            packages_scanned=50,
            vulnerabilities=multiple_vulnerabilities,
            output=output,
        )

        result = output.getvalue()
        # Critical should appear before High
        critical_pos = result.find("CVE-2024-0001")
        high_pos = result.find("CVE-2024-0002")
        assert critical_pos < high_pos

    def test_print_vulnerability_details(
        self,
        temp_output_dir: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test vulnerability detail display."""
        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(
            packages_scanned=10,
            vulnerabilities=[sample_vulnerability],
            output=output,
        )

        result = output.getvalue()
        assert "[CVE-2024-12345]" in result
        assert "lodash@4.17.20" in result
        assert "Severity: CRITICAL" in result
        assert "CVSS 9.8" in result
        assert "Description:" in result
        assert "Affected Files:" in result
        assert "package.json:15" in result
        assert "Fix:" in result
        assert "npm install lodash@4.17.21" in result

    def test_print_vulnerability_truncates_description(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test that long descriptions are truncated."""
        long_desc = "A" * 200  # 200 character description
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=8.0,
            description=long_desc,
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(packages_scanned=1, vulnerabilities=[vuln], output=output)

        result = output.getvalue()
        # Should be truncated to 100 chars + "..."
        assert "..." in result
        assert "A" * 200 not in result

    def test_print_vulnerability_no_cvss(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test display when CVSS score is not available."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=None,
            description="Test",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        output = StringIO()

        reporter.print_summary(packages_scanned=1, vulnerabilities=[vuln], output=output)

        result = output.getvalue()
        assert "CVSS N/A" in result

    def test_format_cli_report_returns_string(
        self,
        temp_output_dir: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test format_cli_report returns formatted string."""
        reporter = Reporter(temp_output_dir, use_color=False)

        result = reporter.format_cli_report(
            packages_scanned=10,
            vulnerabilities=[sample_vulnerability],
        )

        assert isinstance(result, str)
        assert "CVE-2024-12345" in result


# =============================================================================
# Reporter Tests - Color Output
# =============================================================================


class TestReporterColorOutput:
    """Tests for Reporter color output."""

    def test_colorize_with_color_enabled(self, temp_output_dir: Path) -> None:
        """Test colorizing text when colors enabled."""
        reporter = Reporter(temp_output_dir, use_color=True)
        result = reporter._colorize("test", TerminalColors.RED)

        assert TerminalColors.RED in result
        assert TerminalColors.RESET in result
        assert "test" in result

    def test_colorize_with_color_disabled(self, temp_output_dir: Path) -> None:
        """Test that colorizing returns plain text when disabled."""
        reporter = Reporter(temp_output_dir, use_color=False)
        result = reporter._colorize("test", TerminalColors.RED)

        assert result == "test"
        assert TerminalColors.RED not in result

    def test_severity_colors_in_output(self, temp_output_dir: Path) -> None:
        """Test that severity colors appear in colored output."""
        packages = [
            Package(name="pkg1", version="1.0", ecosystem="npm", source_file=Path("package.json")),
            Package(name="pkg2", version="1.0", ecosystem="npm", source_file=Path("package.json")),
        ]
        vulns = [
            VulnerabilityMatch(
                cve_id="CVE-2024-0001",
                package=packages[0],
                severity="CRITICAL",
                cvss_score=9.8,
                description="Critical",
                fix_version=None,
                fix_command=None,
                affected_files=[],
                references=[],
            ),
            VulnerabilityMatch(
                cve_id="CVE-2024-0002",
                package=packages[1],
                severity="LOW",
                cvss_score=2.0,
                description="Low",
                fix_version=None,
                fix_command=None,
                affected_files=[],
                references=[],
            ),
        ]

        reporter = Reporter(temp_output_dir, use_color=True)
        output = StringIO()

        reporter.print_summary(packages_scanned=2, vulnerabilities=vulns, output=output)

        result = output.getvalue()
        assert TerminalColors.CRITICAL in result or TerminalColors.RED in result


# =============================================================================
# Reporter Tests - Utility Methods
# =============================================================================


class TestReporterUtilities:
    """Tests for Reporter utility methods."""

    def test_get_summary(
        self,
        temp_output_dir: Path,
        multiple_vulnerabilities: List[VulnerabilityMatch],
    ) -> None:
        """Test get_summary method."""
        reporter = Reporter(temp_output_dir, use_color=False)

        summary = reporter.get_summary(
            packages_scanned=50,
            vulnerabilities=multiple_vulnerabilities,
        )

        assert isinstance(summary, ScanSummary)
        assert summary.total_vulnerabilities == 5
        assert summary.packages_scanned == 50

    def test_has_critical_vulnerabilities_true(
        self,
        temp_output_dir: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test detecting critical vulnerabilities."""
        reporter = Reporter(temp_output_dir, use_color=False)

        assert reporter.has_critical_vulnerabilities([sample_vulnerability]) is True

    def test_has_critical_vulnerabilities_false(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test when no critical vulnerabilities exist."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=8.0,
            description="High severity",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.has_critical_vulnerabilities([vuln]) is False

    def test_has_critical_vulnerabilities_empty(self, temp_output_dir: Path) -> None:
        """Test with empty vulnerability list."""
        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.has_critical_vulnerabilities([]) is False


# =============================================================================
# Reporter Tests - Exit Codes
# =============================================================================


class TestReporterExitCode:
    """Tests for Reporter exit code calculation."""

    def test_exit_code_no_vulnerabilities(self, temp_output_dir: Path) -> None:
        """Test exit code with no vulnerabilities."""
        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.get_exit_code([]) == 0

    def test_exit_code_critical_default_threshold(
        self,
        temp_output_dir: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test exit code with critical vulnerability (default HIGH threshold)."""
        reporter = Reporter(temp_output_dir, use_color=False)
        # Default threshold is HIGH, CRITICAL should fail
        assert reporter.get_exit_code([sample_vulnerability]) == 1

    def test_exit_code_high_with_high_threshold(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test exit code with HIGH vulnerability and HIGH threshold."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="HIGH",
            cvss_score=8.0,
            description="High severity",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.get_exit_code([vuln], fail_on_severity="HIGH") == 1

    def test_exit_code_medium_with_high_threshold(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test exit code with MEDIUM vulnerability and HIGH threshold."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="MEDIUM",
            cvss_score=5.0,
            description="Medium severity",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        # MEDIUM is below HIGH threshold, should pass
        assert reporter.get_exit_code([vuln], fail_on_severity="HIGH") == 0

    def test_exit_code_medium_with_medium_threshold(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test exit code with MEDIUM vulnerability and MEDIUM threshold."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="MEDIUM",
            cvss_score=5.0,
            description="Medium severity",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.get_exit_code([vuln], fail_on_severity="MEDIUM") == 1

    def test_exit_code_low_with_critical_threshold(
        self,
        temp_output_dir: Path,
        sample_package: Package,
    ) -> None:
        """Test exit code with LOW vulnerability and CRITICAL threshold."""
        vuln = VulnerabilityMatch(
            cve_id="CVE-2024-0001",
            package=sample_package,
            severity="LOW",
            cvss_score=2.0,
            description="Low severity",
            fix_version=None,
            fix_command=None,
            affected_files=[],
            references=[],
        )

        reporter = Reporter(temp_output_dir, use_color=False)
        assert reporter.get_exit_code([vuln], fail_on_severity="CRITICAL") == 0

    def test_exit_code_invalid_threshold(
        self,
        temp_output_dir: Path,
        sample_vulnerability: VulnerabilityMatch,
    ) -> None:
        """Test exit code with invalid threshold (defaults to HIGH)."""
        reporter = Reporter(temp_output_dir, use_color=False)
        # Invalid threshold defaults to HIGH, CRITICAL should fail
        assert reporter.get_exit_code([sample_vulnerability], fail_on_severity="INVALID") == 1


# =============================================================================
# create_reporter Tests
# =============================================================================


class TestCreateReporter:
    """Tests for create_reporter factory function."""

    def test_creates_reporter_with_default_directory(self, tmp_path: Path) -> None:
        """Test that reporter is created with .cve-sentinel directory."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter = create_reporter(project_path)

        expected_dir = project_path / ".cve-sentinel"
        assert reporter.output_dir == expected_dir
        assert expected_dir.exists()

    def test_passes_use_color_parameter(self, tmp_path: Path) -> None:
        """Test that use_color is passed to reporter."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter_color = create_reporter(project_path, use_color=True)
        reporter_no_color = create_reporter(project_path, use_color=False)

        assert reporter_color.use_color is True
        assert reporter_no_color.use_color is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestReporterIntegration:
    """Integration tests for Reporter."""

    def test_full_scan_workflow(
        self,
        tmp_path: Path,
        multiple_vulnerabilities: List[VulnerabilityMatch],
    ) -> None:
        """Test complete scan workflow."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter = create_reporter(project_path, use_color=False)

        # Start scan
        reporter.update_status("scanning")

        # Write results
        reporter.write_results(
            project_path,
            packages_scanned=50,
            vulnerabilities=multiple_vulnerabilities,
        )

        # Complete scan
        reporter.update_status("completed")

        # Verify all files exist
        output_dir = project_path / ".cve-sentinel"
        assert (output_dir / "status.json").exists()
        assert (output_dir / "results.json").exists()

        # Verify status
        status_data = json.loads((output_dir / "status.json").read_text())
        assert status_data["status"] == "completed"

        # Verify results
        results_data = json.loads((output_dir / "results.json").read_text())
        assert len(results_data["vulnerabilities"]) == 5

    def test_error_workflow(self, tmp_path: Path) -> None:
        """Test scan error workflow."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()

        reporter = create_reporter(project_path, use_color=False)

        # Start scan
        reporter.update_status("scanning")

        # Error occurred
        reporter.update_status("error", error_message="API connection timeout")

        # Verify status
        output_dir = project_path / ".cve-sentinel"
        status_data = json.loads((output_dir / "status.json").read_text())

        assert status_data["status"] == "error"
        assert status_data["error_message"] == "API connection timeout"
