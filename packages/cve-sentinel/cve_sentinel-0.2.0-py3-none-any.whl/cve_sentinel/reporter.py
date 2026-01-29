"""Result reporter for CVE Sentinel."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from cve_sentinel.matcher import VulnerabilityMatch


@dataclass
class ScanSummary:
    """Summary of a vulnerability scan.

    Attributes:
        total_vulnerabilities: Total number of vulnerabilities found.
        critical_count: Number of critical severity vulnerabilities.
        high_count: Number of high severity vulnerabilities.
        medium_count: Number of medium severity vulnerabilities.
        low_count: Number of low severity vulnerabilities.
        unknown_count: Number of unknown severity vulnerabilities.
        packages_scanned: Total number of packages scanned.
    """

    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    unknown_count: int
    packages_scanned: int

    @classmethod
    def from_vulnerabilities(
        cls,
        vulnerabilities: List[VulnerabilityMatch],
        packages_scanned: int,
    ) -> ScanSummary:
        """Create summary from vulnerability list.

        Args:
            vulnerabilities: List of vulnerability matches.
            packages_scanned: Number of packages scanned.

        Returns:
            ScanSummary instance.
        """
        counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
        }

        for vuln in vulnerabilities:
            severity = (vuln.severity or "UNKNOWN").upper()
            if severity in counts:
                counts[severity] += 1
            else:
                counts["UNKNOWN"] += 1

        return cls(
            total_vulnerabilities=len(vulnerabilities),
            critical_count=counts["CRITICAL"],
            high_count=counts["HIGH"],
            medium_count=counts["MEDIUM"],
            low_count=counts["LOW"],
            unknown_count=counts["UNKNOWN"],
            packages_scanned=packages_scanned,
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "total": self.total_vulnerabilities,
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "unknown": self.unknown_count,
            "packages_scanned": self.packages_scanned,
        }


class TerminalColors:
    """ANSI color codes for terminal output."""

    # Basic colors
    RED = "\033[91m"
    ORANGE = "\033[38;5;208m"  # 256-color orange
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    # Severity colors
    CRITICAL = RED + BOLD
    HIGH = ORANGE
    MEDIUM = YELLOW
    LOW = GREEN
    UNKNOWN = GRAY

    # Symbols
    WARNING_SYMBOL = "⚠"
    CHECK_SYMBOL = "✓"
    BULLET_SYMBOL = "•"

    @classmethod
    def supports_color(cls) -> bool:
        """Check if terminal supports color output.

        Returns:
            True if colors are supported.
        """
        # Check for NO_COLOR environment variable
        if os.environ.get("NO_COLOR"):
            return False

        # Check for FORCE_COLOR environment variable
        if os.environ.get("FORCE_COLOR"):
            return True

        # Check if stdout is a TTY
        if not hasattr(sys.stdout, "isatty"):
            return False

        if not sys.stdout.isatty():
            return False

        # Check for dumb terminal
        if os.environ.get("TERM") == "dumb":
            return False

        return True

    @classmethod
    def get_severity_color(cls, severity: str, use_color: bool = True) -> str:
        """Get color code for severity level.

        Args:
            severity: Severity level string.
            use_color: Whether to use color codes.

        Returns:
            Color code string or empty string.
        """
        if not use_color:
            return ""

        severity_upper = (severity or "UNKNOWN").upper()
        color_map = {
            "CRITICAL": cls.CRITICAL,
            "HIGH": cls.HIGH,
            "MEDIUM": cls.MEDIUM,
            "LOW": cls.LOW,
            "UNKNOWN": cls.UNKNOWN,
        }
        return color_map.get(severity_upper, cls.GRAY)


class Reporter:
    """Generates scan reports and status files."""

    def __init__(
        self,
        output_dir: Path,
        use_color: Optional[bool] = None,
    ) -> None:
        """Initialize reporter with output directory.

        Args:
            output_dir: Directory to write output files.
            use_color: Whether to use colored output. Auto-detects if None.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if use_color is None:
            self.use_color = TerminalColors.supports_color()
        else:
            self.use_color = use_color

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled.

        Args:
            text: Text to colorize.
            color: ANSI color code.

        Returns:
            Colorized text or plain text.
        """
        if self.use_color and color:
            return f"{color}{text}{TerminalColors.RESET}"
        return text

    def update_status(
        self,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update status.json file.

        Args:
            status: Current status ('scanning', 'completed', 'error').
            error_message: Error message if status is 'error'.
        """
        status_file = self.output_dir / "status.json"
        now = datetime.now(timezone.utc).isoformat()

        data: Dict[str, Any] = {"status": status}

        if status == "scanning":
            data["started_at"] = now
        elif status in ("completed", "error"):
            # Try to preserve started_at from existing file
            if status_file.exists():
                try:
                    existing = json.loads(status_file.read_text())
                    data["started_at"] = existing.get("started_at", now)
                except (json.JSONDecodeError, KeyError):
                    data["started_at"] = now
            else:
                data["started_at"] = now
            data["completed_at"] = now

        if error_message:
            data["error_message"] = error_message

        status_file.write_text(json.dumps(data, indent=2))

    def write_results(
        self,
        project_path: Path,
        packages_scanned: int,
        vulnerabilities: List[VulnerabilityMatch],
    ) -> Path:
        """Write results.json file.

        Args:
            project_path: Path to the scanned project.
            packages_scanned: Number of packages scanned.
            vulnerabilities: List of vulnerability matches.

        Returns:
            Path to the results file.
        """
        results_file = self.output_dir / "results.json"
        summary = ScanSummary.from_vulnerabilities(vulnerabilities, packages_scanned)

        data = {
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "project_path": str(project_path.absolute()),
            "packages_scanned": packages_scanned,
            "summary": summary.to_dict(),
            "vulnerabilities": [self._format_vulnerability_for_json(v) for v in vulnerabilities],
        }

        results_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return results_file

    def _format_vulnerability_for_json(self, vuln: VulnerabilityMatch) -> Dict[str, Any]:
        """Format a vulnerability for JSON output.

        Args:
            vuln: Vulnerability match to format.

        Returns:
            Dictionary representation.
        """
        result = {
            "cve_id": vuln.cve_id,
            "osv_id": vuln.osv_id,
            "package_name": vuln.package.name,
            "installed_version": vuln.package.version,
            "ecosystem": vuln.package.ecosystem,
            "severity": vuln.severity,
            "cvss_score": vuln.cvss_score,
            "description": vuln.description,
            "affected_files": vuln.affected_files,
            "fix_version": vuln.fix_version,
            "fix_command": vuln.fix_command,
            "references": vuln.references[:5] if vuln.references else [],
        }

        # Add combined matcher fields if available
        if hasattr(vuln, "source"):
            result["source"] = vuln.source
        if hasattr(vuln, "confidence"):
            result["confidence"] = vuln.confidence
        if hasattr(vuln, "nvd_verified"):
            result["nvd_verified"] = vuln.nvd_verified

        return result

    def print_summary(
        self,
        packages_scanned: int,
        vulnerabilities: List[VulnerabilityMatch],
        output: Optional[TextIO] = None,
    ) -> None:
        """Print scan summary to terminal.

        Args:
            packages_scanned: Number of packages scanned.
            vulnerabilities: List of vulnerability matches.
            output: Output stream (defaults to stdout).
        """
        if output is None:
            output = sys.stdout

        summary = ScanSummary.from_vulnerabilities(vulnerabilities, packages_scanned)

        if vulnerabilities:
            self._print_vulnerabilities_found(summary, vulnerabilities, output)
        else:
            self._print_no_vulnerabilities(summary, output)

    def _print_vulnerabilities_found(
        self,
        summary: ScanSummary,
        vulnerabilities: List[VulnerabilityMatch],
        output: TextIO,
    ) -> None:
        """Print output when vulnerabilities are found.

        Args:
            summary: Scan summary.
            vulnerabilities: List of vulnerability matches.
            output: Output stream.
        """
        # Header with warning
        warning_symbol = TerminalColors.WARNING_SYMBOL
        header = f"{warning_symbol} CVE Scan Complete: {summary.total_vulnerabilities} vulnerabilities found"
        output.write(self._colorize(header, TerminalColors.RED + TerminalColors.BOLD) + "\n\n")

        # Severity summary
        self._print_severity_summary(summary, output)
        output.write("\n")

        # Sort vulnerabilities by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: severity_order.get((v.severity or "UNKNOWN").upper(), 5),
        )

        # Print each vulnerability
        for vuln in sorted_vulns:
            self._print_vulnerability(vuln, output)

    def _print_no_vulnerabilities(
        self,
        summary: ScanSummary,
        output: TextIO,
    ) -> None:
        """Print output when no vulnerabilities are found.

        Args:
            summary: Scan summary.
            output: Output stream.
        """
        check_symbol = TerminalColors.CHECK_SYMBOL
        header = f"{check_symbol} CVE Scan Complete: No vulnerabilities detected"
        output.write(self._colorize(header, TerminalColors.GREEN + TerminalColors.BOLD) + "\n")
        output.write(f"  Scanned: {summary.packages_scanned} packages\n")

    def _print_severity_summary(self, summary: ScanSummary, output: TextIO) -> None:
        """Print severity breakdown summary.

        Args:
            summary: Scan summary.
            output: Output stream.
        """
        parts = []

        if summary.critical_count > 0:
            critical_text = f"Critical: {summary.critical_count}"
            parts.append(self._colorize(critical_text, TerminalColors.CRITICAL))

        if summary.high_count > 0:
            high_text = f"High: {summary.high_count}"
            parts.append(self._colorize(high_text, TerminalColors.HIGH))

        if summary.medium_count > 0:
            medium_text = f"Medium: {summary.medium_count}"
            parts.append(self._colorize(medium_text, TerminalColors.MEDIUM))

        if summary.low_count > 0:
            low_text = f"Low: {summary.low_count}"
            parts.append(self._colorize(low_text, TerminalColors.LOW))

        if summary.unknown_count > 0:
            unknown_text = f"Unknown: {summary.unknown_count}"
            parts.append(self._colorize(unknown_text, TerminalColors.UNKNOWN))

        if parts:
            output.write("  By Severity: " + " | ".join(parts) + "\n")

        output.write(f"  Scanned: {summary.packages_scanned} packages\n")

    def _print_vulnerability(self, vuln: VulnerabilityMatch, output: TextIO) -> None:
        """Print a single vulnerability entry.

        Args:
            vuln: Vulnerability match to print.
            output: Output stream.
        """
        severity_color = TerminalColors.get_severity_color(vuln.severity, self.use_color)

        # CVE ID and package info
        cve_display = f"[{vuln.cve_id}]"
        pkg_display = f"{vuln.package.name}@{vuln.package.version}"
        output.write(f"{self._colorize(cve_display, TerminalColors.BOLD)} {pkg_display}\n")

        # Severity and CVSS score
        severity_text = vuln.severity or "UNKNOWN"
        cvss_text = f"CVSS {vuln.cvss_score}" if vuln.cvss_score else "CVSS N/A"

        # Add source and confidence if available (from CombinedVulnerabilityMatch)
        source_text = ""
        if hasattr(vuln, "source") and hasattr(vuln, "confidence"):
            source = getattr(vuln, "source", "unknown")
            confidence = getattr(vuln, "confidence", "unknown")
            source_display = {"osv": "OSV", "nvd": "NVD", "both": "OSV+NVD"}.get(source, source)
            source_text = f" [{source_display}, {confidence}]"

        output.write(
            f"  Severity: {self._colorize(severity_text, severity_color)} ({cvss_text}){source_text}\n"
        )

        # Description (truncated)
        if vuln.description:
            desc = (
                vuln.description[:100] + "..." if len(vuln.description) > 100 else vuln.description
            )
            output.write(f"  Description: {desc}\n")

        # Affected files
        if vuln.affected_files:
            output.write("  Affected Files:\n")
            for af in vuln.affected_files[:5]:  # Limit to 5 files
                file_path = af.get("file", "unknown")
                line_num = af.get("line")
                if line_num:
                    output.write(f"    {file_path}:{line_num}\n")
                else:
                    output.write(f"    {file_path}\n")

        # Fix command
        if vuln.fix_command:
            fix_text = f"  Fix: {vuln.fix_command}"
            output.write(self._colorize(fix_text, TerminalColors.GREEN) + "\n")

        output.write("\n")

    def format_cli_report(
        self,
        packages_scanned: int,
        vulnerabilities: List[VulnerabilityMatch],
    ) -> str:
        """Format scan results as CLI report string.

        Args:
            packages_scanned: Number of packages scanned.
            vulnerabilities: List of vulnerability matches.

        Returns:
            Formatted report string.
        """
        buffer = StringIO()
        self.print_summary(packages_scanned, vulnerabilities, buffer)
        return buffer.getvalue()

    def get_summary(
        self,
        packages_scanned: int,
        vulnerabilities: List[VulnerabilityMatch],
    ) -> ScanSummary:
        """Get scan summary object.

        Args:
            packages_scanned: Number of packages scanned.
            vulnerabilities: List of vulnerability matches.

        Returns:
            ScanSummary instance.
        """
        return ScanSummary.from_vulnerabilities(vulnerabilities, packages_scanned)

    def has_critical_vulnerabilities(
        self,
        vulnerabilities: List[VulnerabilityMatch],
    ) -> bool:
        """Check if any critical vulnerabilities exist.

        Args:
            vulnerabilities: List of vulnerability matches.

        Returns:
            True if critical vulnerabilities exist.
        """
        for vuln in vulnerabilities:
            if (vuln.severity or "").upper() == "CRITICAL":
                return True
        return False

    def get_exit_code(
        self,
        vulnerabilities: List[VulnerabilityMatch],
        fail_on_severity: str = "HIGH",
    ) -> int:
        """Get suggested exit code based on vulnerabilities.

        Args:
            vulnerabilities: List of vulnerability matches.
            fail_on_severity: Minimum severity to cause failure.

        Returns:
            0 if no issues, 1 if vulnerabilities exceed threshold.
        """
        if not vulnerabilities:
            return 0

        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        try:
            threshold_index = severity_order.index(fail_on_severity.upper())
        except ValueError:
            threshold_index = 1  # Default to HIGH

        for vuln in vulnerabilities:
            severity = (vuln.severity or "UNKNOWN").upper()
            try:
                severity_index = severity_order.index(severity)
                if severity_index <= threshold_index:
                    return 1
            except ValueError:
                continue

        return 0


def create_reporter(
    project_path: Path,
    use_color: Optional[bool] = None,
) -> Reporter:
    """Create a reporter instance with default output directory.

    Args:
        project_path: Path to the project being scanned.
        use_color: Whether to use colored output.

    Returns:
        Configured Reporter instance.
    """
    output_dir = project_path / ".cve-sentinel"
    return Reporter(output_dir, use_color=use_color)
