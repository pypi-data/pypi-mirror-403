"""Tests for the vulnerability matcher module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from cve_sentinel.analyzers.base import Package
from cve_sentinel.fetchers.osv import OSVVulnerability
from cve_sentinel.matcher import (
    VersionMatcher,
    VulnerabilityMatch,
    VulnerabilityMatcher,
)


class TestVersionMatcher:
    """Tests for VersionMatcher utility class."""

    def test_parse_version_valid(self) -> None:
        """Test parsing valid version strings."""
        assert VersionMatcher.parse_version("1.0.0") is not None
        assert VersionMatcher.parse_version("2.3.4") is not None
        assert VersionMatcher.parse_version("0.0.1") is not None

    def test_parse_version_with_v_prefix(self) -> None:
        """Test parsing versions with 'v' prefix."""
        ver = VersionMatcher.parse_version("v1.0.0")
        assert ver is not None
        assert str(ver) == "1.0.0"

    def test_parse_version_empty(self) -> None:
        """Test parsing empty version returns None."""
        assert VersionMatcher.parse_version("") is None
        assert VersionMatcher.parse_version("*") is None

    def test_parse_version_invalid(self) -> None:
        """Test parsing invalid versions."""
        # Should try to extract valid part
        ver = VersionMatcher.parse_version("1.0.0-beta")
        # The packaging library handles pre-release versions
        assert ver is not None

    def test_compare_versions(self) -> None:
        """Test version comparison."""
        assert VersionMatcher.compare_versions("1.0.0", "2.0.0") == -1
        assert VersionMatcher.compare_versions("2.0.0", "1.0.0") == 1
        assert VersionMatcher.compare_versions("1.0.0", "1.0.0") == 0

    def test_compare_versions_with_different_lengths(self) -> None:
        """Test comparing versions with different segment counts."""
        assert VersionMatcher.compare_versions("1.0", "1.0.0") == 0
        assert VersionMatcher.compare_versions("1.0.0", "1.0.1") == -1

    def test_is_version_affected_in_range(self) -> None:
        """Test version affected check when in range."""
        affected_ranges = [
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
        ]

        # Version in range
        is_affected, fix_ver = VersionMatcher.is_version_affected("1.5.0", affected_ranges)
        assert is_affected is True
        assert fix_ver == "2.0.0"

    def test_is_version_affected_before_range(self) -> None:
        """Test version affected check when before range."""
        affected_ranges = [
            {
                "ranges": [
                    {
                        "type": "SEMVER",
                        "events": [
                            {"introduced": "2.0.0"},
                            {"fixed": "3.0.0"},
                        ],
                    }
                ]
            }
        ]

        is_affected, fix_ver = VersionMatcher.is_version_affected("1.5.0", affected_ranges)
        assert is_affected is False

    def test_is_version_affected_after_fix(self) -> None:
        """Test version affected check when after fix."""
        affected_ranges = [
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
        ]

        is_affected, fix_ver = VersionMatcher.is_version_affected("2.5.0", affected_ranges)
        assert is_affected is False

    def test_is_version_affected_explicit_versions(self) -> None:
        """Test version affected check with explicit version list."""
        affected_ranges = [
            {
                "versions": ["1.0.0", "1.1.0", "1.2.0"],
                "ranges": [
                    {
                        "type": "SEMVER",
                        "events": [{"fixed": "1.3.0"}],
                    }
                ],
            }
        ]

        is_affected, fix_ver = VersionMatcher.is_version_affected("1.1.0", affected_ranges)
        assert is_affected is True
        assert fix_ver == "1.3.0"

    def test_is_version_affected_no_upper_bound(self) -> None:
        """Test version affected when there's no fixed version."""
        affected_ranges = [
            {
                "ranges": [
                    {
                        "type": "SEMVER",
                        "events": [{"introduced": "0"}],
                    }
                ]
            }
        ]

        is_affected, fix_ver = VersionMatcher.is_version_affected("1.0.0", affected_ranges)
        assert is_affected is True
        assert fix_ver is None


class TestVulnerabilityMatch:
    """Tests for VulnerabilityMatch dataclass."""

    def test_match_creation(self) -> None:
        """Test creating a VulnerabilityMatch."""
        pkg = Package(
            name="requests",
            version="2.25.0",
            ecosystem="pypi",
            source_file=Path("requirements.txt"),
        )
        match = VulnerabilityMatch(
            cve_id="CVE-2021-12345",
            package=pkg,
            severity="HIGH",
            cvss_score=7.5,
            description="Test vulnerability",
            fix_version="2.26.0",
            fix_command="pip install requests==2.26.0",
        )

        assert match.cve_id == "CVE-2021-12345"
        assert match.package.name == "requests"
        assert match.severity == "HIGH"
        assert match.cvss_score == 7.5

    def test_match_equality(self) -> None:
        """Test VulnerabilityMatch equality."""
        pkg1 = Package("requests", "2.25.0", "pypi", Path("a"))
        pkg2 = Package("requests", "2.25.0", "pypi", Path("b"))

        match1 = VulnerabilityMatch(
            cve_id="CVE-2021-12345",
            package=pkg1,
            severity="HIGH",
            cvss_score=7.5,
            description="Test",
            fix_version="2.26.0",
            fix_command=None,
        )
        match2 = VulnerabilityMatch(
            cve_id="CVE-2021-12345",
            package=pkg2,
            severity="MEDIUM",  # Different severity
            cvss_score=5.0,
            description="Different",
            fix_version="2.27.0",
            fix_command=None,
        )

        # Same CVE + package name + ecosystem = equal
        assert match1 == match2

    def test_match_hash(self) -> None:
        """Test VulnerabilityMatch can be used in sets."""
        pkg = Package("lodash", "4.17.0", "npm", Path("package.json"))

        match1 = VulnerabilityMatch(
            cve_id="CVE-2021-54321",
            package=pkg,
            severity="CRITICAL",
            cvss_score=9.8,
            description="Test",
            fix_version="4.17.21",
            fix_command=None,
        )
        match2 = VulnerabilityMatch(
            cve_id="CVE-2021-54321",
            package=pkg,
            severity="CRITICAL",
            cvss_score=9.8,
            description="Test",
            fix_version="4.17.21",
            fix_command=None,
        )

        match_set = {match1, match2}
        assert len(match_set) == 1

    def test_match_to_dict(self) -> None:
        """Test VulnerabilityMatch serialization."""
        pkg = Package("flask", "1.0.0", "pypi", Path("req.txt"))
        match = VulnerabilityMatch(
            cve_id="CVE-2021-99999",
            package=pkg,
            severity="MEDIUM",
            cvss_score=5.5,
            description="A test vuln",
            fix_version="1.1.0",
            fix_command="pip install flask==1.1.0",
            affected_files=[{"file": "req.txt", "line": 5}],
            references=["https://example.com"],
            osv_id="GHSA-xxxx-xxxx-xxxx",
        )

        d = match.to_dict()
        assert d["cve_id"] == "CVE-2021-99999"
        assert d["osv_id"] == "GHSA-xxxx-xxxx-xxxx"
        assert d["package"]["name"] == "flask"
        assert d["severity"] == "MEDIUM"
        assert len(d["affected_files"]) == 1


class TestVulnerabilityMatcher:
    """Tests for VulnerabilityMatcher class."""

    def test_matcher_initialization(self) -> None:
        """Test matcher initialization."""
        matcher = VulnerabilityMatcher()
        assert matcher.nvd_client is None
        assert matcher.osv_client is None

    def test_matcher_with_clients(self) -> None:
        """Test matcher with mock clients."""
        nvd_mock = MagicMock()
        osv_mock = MagicMock()

        matcher = VulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=osv_mock,
        )

        assert matcher.nvd_client is nvd_mock
        assert matcher.osv_client is osv_mock

    def test_generate_fix_command_npm(self) -> None:
        """Test fix command generation for npm."""
        matcher = VulnerabilityMatcher()
        pkg = Package("lodash", "4.17.0", "npm", Path("package.json"))

        cmd = matcher.generate_fix_command(pkg, "4.17.21")
        assert cmd == "npm install lodash@4.17.21"

    def test_generate_fix_command_pypi(self) -> None:
        """Test fix command generation for pypi."""
        matcher = VulnerabilityMatcher()
        pkg = Package("requests", "2.25.0", "pypi", Path("requirements.txt"))

        cmd = matcher.generate_fix_command(pkg, "2.28.0")
        assert cmd == "pip install requests==2.28.0"

    def test_generate_fix_command_go(self) -> None:
        """Test fix command generation for go."""
        matcher = VulnerabilityMatcher()
        pkg = Package("github.com/gin-gonic/gin", "1.7.0", "go", Path("go.mod"))

        cmd = matcher.generate_fix_command(pkg, "1.8.0")
        assert cmd == "go get github.com/gin-gonic/gin@v1.8.0"

    def test_generate_fix_command_unsupported(self) -> None:
        """Test fix command for unsupported ecosystem."""
        matcher = VulnerabilityMatcher()
        pkg = Package("something", "1.0.0", "unknown", Path("file"))

        cmd = matcher.generate_fix_command(pkg, "2.0.0")
        assert cmd is None

    def test_match_without_osv_client(self) -> None:
        """Test match returns empty when no OSV client."""
        matcher = VulnerabilityMatcher()
        packages = [Package("test", "1.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)
        assert matches == []

    def test_match_with_osv_results(self) -> None:
        """Test matching with OSV results."""
        osv_mock = MagicMock()

        # Create mock OSV vulnerability
        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234-5678",
            aliases=["CVE-2021-12345"],
            summary="Test vulnerability",
            severity=[{"type": "CVSS_V3", "score": 7.5}],
            affected=[
                {
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "2.0.0"},
                            ],
                        }
                    ]
                }
            ],
            fixed_versions=["2.0.0"],
        )

        osv_mock.query_batch.return_value = {
            "npm:test-package": [osv_vuln],
        }

        matcher = VulnerabilityMatcher(osv_client=osv_mock, fetch_nvd_details=False)
        packages = [Package("test-package", "1.5.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)

        assert len(matches) == 1
        assert matches[0].cve_id == "CVE-2021-12345"
        assert matches[0].fix_version == "2.0.0"
        assert matches[0].severity == "HIGH"

    def test_match_deduplication(self) -> None:
        """Test that duplicate vulnerabilities are deduplicated."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234-5678",
            aliases=["CVE-2021-12345"],
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

        osv_mock.query_batch.return_value = {
            "npm:test-package": [osv_vuln, osv_vuln],  # Duplicate
        }

        matcher = VulnerabilityMatcher(osv_client=osv_mock, fetch_nvd_details=False)
        packages = [Package("test-package", "1.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)

        # Should only have one match despite duplicate vulns
        assert len(matches) == 1

    def test_match_version_not_affected(self) -> None:
        """Test that unaffected versions are not matched."""
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test-1234-5678",
            aliases=["CVE-2021-12345"],
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

        osv_mock.query_batch.return_value = {
            "npm:test-package": [osv_vuln],
        }

        matcher = VulnerabilityMatcher(osv_client=osv_mock, fetch_nvd_details=False)
        # Version 3.0.0 is after the fix
        packages = [Package("test-package", "3.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)
        assert len(matches) == 0

    def test_get_severity_counts(self) -> None:
        """Test severity count aggregation."""
        matcher = VulnerabilityMatcher()
        pkg = Package("test", "1.0.0", "npm", Path("p"))

        matches = [
            VulnerabilityMatch("CVE-1", pkg, "CRITICAL", 9.8, "", None, None),
            VulnerabilityMatch("CVE-2", pkg, "HIGH", 7.5, "", None, None),
            VulnerabilityMatch("CVE-3", pkg, "HIGH", 7.0, "", None, None),
            VulnerabilityMatch("CVE-4", pkg, "MEDIUM", 5.0, "", None, None),
            VulnerabilityMatch("CVE-5", pkg, "LOW", 2.0, "", None, None),
        ]

        counts = matcher.get_severity_counts(matches)
        assert counts["CRITICAL"] == 1
        assert counts["HIGH"] == 2
        assert counts["MEDIUM"] == 1
        assert counts["LOW"] == 1
        assert counts["UNKNOWN"] == 0

    def test_filter_by_severity(self) -> None:
        """Test filtering by minimum severity."""
        matcher = VulnerabilityMatcher()
        pkg = Package("test", "1.0.0", "npm", Path("p"))

        matches = [
            VulnerabilityMatch("CVE-1", pkg, "CRITICAL", 9.8, "", None, None),
            VulnerabilityMatch("CVE-2", pkg, "HIGH", 7.5, "", None, None),
            VulnerabilityMatch("CVE-3", pkg, "MEDIUM", 5.0, "", None, None),
            VulnerabilityMatch("CVE-4", pkg, "LOW", 2.0, "", None, None),
        ]

        # Filter to HIGH and above
        filtered = matcher.filter_by_severity(matches, "HIGH")
        assert len(filtered) == 2
        severities = [m.severity for m in filtered]
        assert "CRITICAL" in severities
        assert "HIGH" in severities
        assert "MEDIUM" not in severities

    def test_match_single(self) -> None:
        """Test matching a single package."""
        osv_mock = MagicMock()
        osv_mock.query_batch.return_value = {}

        matcher = VulnerabilityMatcher(osv_client=osv_mock, fetch_nvd_details=False)
        pkg = Package("test", "1.0.0", "npm", Path("package.json"))

        matches = matcher.match_single(pkg)
        assert matches == []
        osv_mock.query_batch.assert_called_once()

    def test_match_fallback_to_individual_queries(self) -> None:
        """Test fallback to individual queries when batch fails."""
        osv_mock = MagicMock()

        # Batch query fails
        osv_mock.query_batch.side_effect = Exception("Batch failed")

        # Individual query succeeds
        osv_vuln = OSVVulnerability(
            id="GHSA-test",
            aliases=["CVE-2021-99999"],
            summary="Test",
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

        matcher = VulnerabilityMatcher(osv_client=osv_mock, fetch_nvd_details=False)
        packages = [Package("test", "1.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)

        assert len(matches) == 1
        osv_mock.query.assert_called()

    def test_fix_commands_all_ecosystems(self) -> None:
        """Test fix commands for all supported ecosystems."""
        matcher = VulnerabilityMatcher()

        test_cases = [
            ("npm", "npm install pkg@1.0.0"),
            ("pypi", "pip install pkg==1.0.0"),
            ("go", "go get pkg@v1.0.0"),
            ("maven", "Update version in pom.xml to 1.0.0"),
            ("rubygems", "bundle update pkg"),
            ("crates.io", "cargo update -p pkg"),
            ("packagist", "composer require pkg:1.0.0"),
        ]

        for ecosystem, expected in test_cases:
            pkg = Package("pkg", "0.9.0", ecosystem, Path("file"))
            cmd = matcher.generate_fix_command(pkg, "1.0.0")
            assert cmd == expected, f"Failed for {ecosystem}"


class TestVulnerabilityMatcherWithNVD:
    """Tests for VulnerabilityMatcher with NVD integration."""

    def test_fetch_nvd_details(self) -> None:
        """Test fetching NVD details for CVE."""
        from datetime import datetime, timezone

        from cve_sentinel.fetchers.nvd import CVEData

        nvd_mock = MagicMock()
        osv_mock = MagicMock()

        # Mock NVD response
        nvd_data = CVEData(
            cve_id="CVE-2021-12345",
            description="Detailed NVD description",
            cvss_score=8.5,
            cvss_severity="HIGH",
            affected_cpes=[],
            fixed_versions=None,
            references=["https://nvd.nist.gov/vuln/detail/CVE-2021-12345"],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )
        nvd_mock.get_cve.return_value = nvd_data

        # Mock OSV response
        osv_vuln = OSVVulnerability(
            id="GHSA-test",
            aliases=["CVE-2021-12345"],
            summary="Short summary",
            severity=[{"type": "CVSS_V3", "score": 7.0}],  # Lower score
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
        osv_mock.query_batch.return_value = {"npm:test": [osv_vuln]}

        matcher = VulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=osv_mock,
            fetch_nvd_details=True,
        )
        packages = [Package("test", "1.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)

        assert len(matches) == 1
        # Should use NVD's higher CVSS score
        assert matches[0].cvss_score == 8.5
        assert matches[0].severity == "HIGH"
        assert "Detailed NVD description" in matches[0].description

    def test_nvd_fetch_disabled(self) -> None:
        """Test that NVD fetch can be disabled."""
        nvd_mock = MagicMock()
        osv_mock = MagicMock()

        osv_vuln = OSVVulnerability(
            id="GHSA-test",
            aliases=["CVE-2021-12345"],
            summary="OSV summary",
            severity=[{"type": "CVSS_V3", "score": 5.0}],
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
        osv_mock.query_batch.return_value = {"npm:test": [osv_vuln]}

        matcher = VulnerabilityMatcher(
            nvd_client=nvd_mock,
            osv_client=osv_mock,
            fetch_nvd_details=False,  # Disabled
        )
        packages = [Package("test", "1.0.0", "npm", Path("package.json"))]

        matches = matcher.match(packages)

        # NVD should not be called
        nvd_mock.get_cve.assert_not_called()
        assert len(matches) == 1
        assert matches[0].cvss_score == 5.0  # OSV score
