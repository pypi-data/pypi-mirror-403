"""Tests for the combined vulnerability matcher module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from cve_sentinel.analyzers.base import Package
from cve_sentinel.fetchers.nvd import CVEData
from cve_sentinel.fetchers.nvd_package_matcher import ConfidenceLevel
from cve_sentinel.fetchers.osv import OSVVulnerability
from cve_sentinel.matcher_combined import (
    CombinedVulnerabilityMatch,
    CombinedVulnerabilityMatcher,
)


class TestCombinedVulnerabilityMatch:
    """Tests for CombinedVulnerabilityMatch dataclass."""

    def test_match_creation(self) -> None:
        """Test creating a combined vulnerability match."""
        pkg = Package(
            name="vite",
            version="3.0.0",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        match = CombinedVulnerabilityMatch(
            cve_id="CVE-2024-12345",
            package=pkg,
            severity="HIGH",
            cvss_score=7.5,
            description="Test vulnerability",
            fix_version="3.0.1",
            fix_command="npm install vite@3.0.1",
            source="osv",
            confidence="high",
            nvd_verified=False,
        )

        assert match.cve_id == "CVE-2024-12345"
        assert match.source == "osv"
        assert match.confidence == "high"
        assert match.nvd_verified is False

    def test_match_to_dict(self) -> None:
        """Test serialization to dictionary."""
        pkg = Package("vite", "3.0.0", "npm", Path("package.json"))
        match = CombinedVulnerabilityMatch(
            cve_id="CVE-2024-12345",
            package=pkg,
            severity="HIGH",
            cvss_score=7.5,
            description="Test vulnerability",
            fix_version="3.0.1",
            fix_command="npm install vite@3.0.1",
            source="both",
            confidence="high",
            nvd_verified=True,
        )

        d = match.to_dict()

        assert d["cve_id"] == "CVE-2024-12345"
        assert d["source"] == "both"
        assert d["confidence"] == "high"
        assert d["nvd_verified"] is True


class TestCombinedVulnerabilityMatcher:
    """Tests for CombinedVulnerabilityMatcher class."""

    def test_initialization_with_clients(self) -> None:
        """Test initialization with OSV and NVD clients."""
        osv_mock = MagicMock()
        nvd_mock = MagicMock()

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=osv_mock,
        )

        assert matcher.osv_client is osv_mock
        assert matcher.nvd_client is nvd_mock
        assert matcher._nvd_matcher is not None

    def test_initialization_without_nvd(self) -> None:
        """Test initialization without NVD client."""
        osv_mock = MagicMock()

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        assert matcher.osv_client is osv_mock
        assert matcher.nvd_client is None
        assert matcher._nvd_matcher is None

    def test_match_osv_only(self) -> None:
        """Test matching with OSV only."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=["CVE-2024-12345"],
            summary="Test vulnerability",
            severity=[{"type": "CVSS_V3", "score": 7.5}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "3.0.1"},
                            ],
                        }
                    ]
                }
            ],
            fixed_versions=["3.0.1"],
        )

        osv_mock.query.return_value = [osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        assert len(matches) == 1
        assert matches[0].cve_id == "CVE-2024-12345"
        assert matches[0].source == "osv"
        assert matches[0].confidence == "high"

    def test_match_nvd_only(self) -> None:
        """Test matching with NVD only (no OSV)."""
        nvd_mock = MagicMock()

        cve_data = CVEData(
            cve_id="CVE-2024-12345",
            description="Test vulnerability",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=["cpe:2.3:a:vitejs:vite:3.0.0:*:*:*:*:node.js:*:*"],
            fixed_versions=None,
            references=["https://example.com"],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        nvd_mock.search_by_keyword.return_value = [cve_data]
        nvd_mock.get_cve.return_value = cve_data

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=None,
            nvd_min_confidence=ConfidenceLevel.MEDIUM,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        assert len(matches) == 1
        assert matches[0].cve_id == "CVE-2024-12345"
        assert matches[0].source == "nvd"
        assert matches[0].nvd_verified is True

    def test_match_both_sources(self) -> None:
        """Test matching with both OSV and NVD for different CVEs."""
        osv_mock = MagicMock()
        nvd_mock = MagicMock()

        # OSV returns one CVE
        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=["CVE-2024-11111"],
            summary="OSV vulnerability",
            severity=[{"type": "CVSS_V3", "score": 7.0}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "3.0.1"},
                            ],
                        }
                    ]
                }
            ],
            fixed_versions=["3.0.1"],
        )

        osv_mock.query.return_value = [osv_vuln]

        # NVD returns a different CVE (not found by OSV)
        cve_data = CVEData(
            cve_id="CVE-2024-22222",
            description="NVD-only vulnerability",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=["cpe:2.3:a:vitejs:vite:3.0.0:*:*:*:*:node.js:*:*"],
            fixed_versions=None,
            references=["https://example.com"],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        nvd_mock.search_by_keyword.return_value = [cve_data]
        nvd_mock.get_cve.return_value = cve_data

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=osv_mock,
            nvd_min_confidence=ConfidenceLevel.MEDIUM,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        # Should have 2 CVEs: one from OSV, one from NVD
        assert len(matches) == 2
        cve_ids = {m.cve_id for m in matches}
        assert "CVE-2024-11111" in cve_ids
        assert "CVE-2024-22222" in cve_ids

        # Check sources
        osv_match = next(m for m in matches if m.cve_id == "CVE-2024-11111")
        nvd_match = next(m for m in matches if m.cve_id == "CVE-2024-22222")

        assert osv_match.source == "osv"
        assert nvd_match.source == "nvd"
        assert nvd_match.nvd_verified is True

    def test_match_deduplication(self) -> None:
        """Test that duplicate CVEs are deduplicated."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="CVE-2024-12345",
            aliases=[],
            summary="Test vulnerability",
            severity=[{"type": "CVSS_V3", "score": 7.5}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        # Return same vuln twice
        osv_mock.query.return_value = [osv_vuln, osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        # Should be deduplicated
        assert len(matches) == 1

    def test_match_unaffected_version(self) -> None:
        """Test that unaffected versions are not matched."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=["CVE-2024-12345"],
            summary="Test vulnerability",
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [
                                {"introduced": "1.0.0"},
                                {"fixed": "2.0.0"},
                            ],
                        }
                    ]
                }
            ],
        )

        osv_mock.query.return_value = [osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        # Version 3.0.0 is after the fix
        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        assert len(matches) == 0

    def test_osv_error_handling(self) -> None:
        """Test error handling when OSV fails."""
        osv_mock = MagicMock()
        osv_mock.query.side_effect = Exception("OSV API error")

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        # Should return empty list, not raise
        assert matches == []

    def test_nvd_error_handling(self) -> None:
        """Test error handling when NVD fails."""
        nvd_mock = MagicMock()
        nvd_mock.search_by_keyword.side_effect = Exception("NVD API error")

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=None,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        # Should return empty list, not raise
        assert matches == []

    def test_generate_fix_command_npm(self) -> None:
        """Test fix command generation for npm."""
        matcher = CombinedVulnerabilityMatcher()
        pkg = Package("vite", "3.0.0", "npm", Path("package.json"))

        cmd = matcher._generate_fix_command(pkg, "3.0.1")
        assert cmd == "npm install vite@3.0.1"

    def test_generate_fix_command_pypi(self) -> None:
        """Test fix command generation for pypi."""
        matcher = CombinedVulnerabilityMatcher()
        pkg = Package("requests", "2.25.0", "pypi", Path("requirements.txt"))

        cmd = matcher._generate_fix_command(pkg, "2.28.0")
        assert cmd == "pip install requests==2.28.0"

    def test_generate_fix_command_unsupported(self) -> None:
        """Test fix command for unsupported ecosystem."""
        matcher = CombinedVulnerabilityMatcher()
        pkg = Package("something", "1.0.0", "unknown", Path("file"))

        cmd = matcher._generate_fix_command(pkg, "2.0.0")
        assert cmd is None

    def test_get_statistics(self) -> None:
        """Test statistics generation."""
        matcher = CombinedVulnerabilityMatcher()
        pkg = Package("test", "1.0.0", "npm", Path("p"))

        matches = [
            CombinedVulnerabilityMatch(
                "CVE-1",
                pkg,
                "CRITICAL",
                9.8,
                "",
                None,
                None,
                source="osv",
                confidence="high",
            ),
            CombinedVulnerabilityMatch(
                "CVE-2",
                pkg,
                "HIGH",
                7.5,
                "",
                None,
                None,
                source="nvd",
                confidence="medium",
            ),
            CombinedVulnerabilityMatch(
                "CVE-3",
                pkg,
                "MEDIUM",
                5.0,
                "",
                None,
                None,
                source="both",
                confidence="high",
            ),
        ]

        stats = matcher.get_statistics(matches)

        assert stats["total"] == 3
        assert stats["by_source"]["osv_only"] == 1
        assert stats["by_source"]["nvd_only"] == 1
        assert stats["by_source"]["both"] == 1
        assert stats["by_confidence"]["high"] == 2
        assert stats["by_confidence"]["medium"] == 1
        assert stats["by_severity"]["CRITICAL"] == 1
        assert stats["by_severity"]["HIGH"] == 1
        assert stats["by_severity"]["MEDIUM"] == 1

    def test_match_multiple_packages(self) -> None:
        """Test matching multiple packages."""
        osv_mock = MagicMock()

        osv_vuln_vite = OSVVulnerability(
            id="GHSA-vite-1234",
            aliases=["CVE-2024-11111"],
            summary="Vite vulnerability",
            severity=[{"type": "CVSS_V3", "score": 7.5}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        osv_vuln_express = OSVVulnerability(
            id="GHSA-express-5678",
            aliases=["CVE-2024-22222"],
            summary="Express vulnerability",
            severity=[{"type": "CVSS_V3", "score": 6.0}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        def osv_query(package_name, ecosystem, version):
            if package_name == "vite":
                return [osv_vuln_vite]
            elif package_name == "express":
                return [osv_vuln_express]
            return []

        osv_mock.query.side_effect = osv_query

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [
            Package("vite", "3.0.0", "npm", Path("package.json")),
            Package("express", "4.17.0", "npm", Path("package.json")),
        ]
        matches = matcher.match(packages)

        assert len(matches) == 2
        cve_ids = {m.cve_id for m in matches}
        assert "CVE-2024-11111" in cve_ids
        assert "CVE-2024-22222" in cve_ids

    def test_match_with_wildcard_version(self) -> None:
        """Test matching with wildcard version."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=["CVE-2024-12345"],
            summary="Test vulnerability",
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        osv_mock.query.return_value = [osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [Package("vite", "*", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        # Should still work with wildcard version
        assert len(matches) == 1

    def test_match_with_source_file(self) -> None:
        """Test that source file information is included."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=["CVE-2024-12345"],
            summary="Test vulnerability",
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        osv_mock.query.return_value = [osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [
            Package(
                "vite",
                "3.0.0",
                "npm",
                source_file=Path("frontend/package.json"),
                source_line=10,
            )
        ]
        matches = matcher.match(packages)

        assert len(matches) == 1
        assert len(matches[0].affected_files) == 1
        assert "frontend/package.json" in matches[0].affected_files[0]["file"]
        assert matches[0].affected_files[0]["line"] == 10

    def test_osv_id_fallback(self) -> None:
        """Test that OSV ID is used as fallback when no CVE alias exists."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234",
            aliases=[],  # No CVE alias
            summary="Test vulnerability",
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}],
                        }
                    ]
                }
            ],
        )

        osv_mock.query.return_value = [osv_vuln]

        matcher = CombinedVulnerabilityMatcher(
            nvd_client=None,
            osv_client=osv_mock,
        )

        packages = [Package("vite", "3.0.0", "npm", Path("package.json"))]
        matches = matcher.match(packages)

        assert len(matches) == 1
        # Should use GHSA ID as primary ID
        assert matches[0].cve_id == "GHSA-test-1234"
