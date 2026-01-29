"""Tests for the NVD package matcher module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from cve_sentinel.fetchers.nvd import CVEData
from cve_sentinel.fetchers.nvd_package_matcher import (
    ConfidenceLevel,
    CVEMatchResult,
    NVDPackageMatcher,
    check_ecosystem_match,
    check_name_match,
    check_version_in_range,
    is_false_positive,
    is_hardware_cve,
    normalize_name,
    parse_cpe,
)


class TestParseCPE:
    """Tests for CPE parsing."""

    def test_parse_full_cpe(self) -> None:
        """Test parsing a full CPE 2.3 URI."""
        cpe = "cpe:2.3:a:vitejs:vite:3.0.0:*:*:*:*:node.js:*:*"
        result = parse_cpe(cpe)

        assert result["part"] == "a"
        assert result["vendor"] == "vitejs"
        assert result["product"] == "vite"
        assert result["version"] == "3.0.0"
        assert result["target_sw"] == "node.js"

    def test_parse_hardware_cpe(self) -> None:
        """Test parsing a hardware CPE."""
        cpe = "cpe:2.3:h:cypress_semiconductor:cyw43455:*:*:*:*:*:*:*:*"
        result = parse_cpe(cpe)

        assert result["part"] == "h"
        assert result["vendor"] == "cypress_semiconductor"
        assert result["product"] == "cyw43455"

    def test_parse_short_cpe(self) -> None:
        """Test parsing a short CPE."""
        cpe = "cpe:2.3:a"
        result = parse_cpe(cpe)

        assert result["part"] == "a"
        assert result["vendor"] == ""
        assert result["product"] == ""


class TestNormalizeName:
    """Tests for name normalization."""

    def test_normalize_simple(self) -> None:
        """Test normalizing a simple name."""
        assert normalize_name("lodash") == "lodash"
        assert normalize_name("Express") == "express"

    def test_normalize_with_special_chars(self) -> None:
        """Test normalizing names with special characters."""
        assert normalize_name("vue-router") == "vuerouter"
        assert normalize_name("@babel/core") == "core"

    def test_normalize_scoped_npm(self) -> None:
        """Test normalizing scoped npm packages."""
        assert normalize_name("@vue/cli") == "cli"
        assert normalize_name("@types/node") == "node"


class TestCheckEcosystemMatch:
    """Tests for ecosystem matching."""

    def test_npm_ecosystem(self) -> None:
        """Test npm ecosystem matching."""
        cpe = {"target_sw": "node.js"}
        assert check_ecosystem_match(cpe, "npm") is True

        cpe = {"target_sw": "nodejs"}
        assert check_ecosystem_match(cpe, "npm") is True

    def test_pypi_ecosystem(self) -> None:
        """Test pypi ecosystem matching."""
        cpe = {"target_sw": "python"}
        assert check_ecosystem_match(cpe, "pypi") is True

        cpe = {"target_sw": "python3"}
        assert check_ecosystem_match(cpe, "pypi") is True

    def test_no_target_sw(self) -> None:
        """Test with no target_sw."""
        cpe = {"target_sw": ""}
        assert check_ecosystem_match(cpe, "npm") is False

        cpe = {"target_sw": "*"}
        assert check_ecosystem_match(cpe, "npm") is False

    def test_mismatched_ecosystem(self) -> None:
        """Test mismatched ecosystems."""
        cpe = {"target_sw": "python"}
        assert check_ecosystem_match(cpe, "npm") is False


class TestCheckNameMatch:
    """Tests for name matching."""

    def test_exact_product_match(self) -> None:
        """Test exact product name match."""
        # Use a package without known vendor mapping
        cpe = {"vendor": "example", "product": "lodash"}
        matches, reason, is_exact = check_name_match(cpe, "lodash")

        assert matches is True
        assert is_exact is True
        assert "Exact product match" in reason

    def test_known_vendor_mapping(self) -> None:
        """Test known vendor mapping."""
        cpe = {"vendor": "vitejs", "product": "somethingelse"}
        matches, reason, is_exact = check_name_match(cpe, "vite")

        assert matches is True
        assert is_exact is True
        assert "Known vendor mapping" in reason

    def test_partial_match(self) -> None:
        """Test partial name match."""
        cpe = {"vendor": "example", "product": "vite-plugin"}
        matches, reason, is_exact = check_name_match(cpe, "vite")

        assert matches is True
        assert is_exact is False
        assert "contains" in reason.lower() or "starts" in reason.lower()

    def test_false_positive_partial(self) -> None:
        """Test that false positive partial matches are rejected."""
        # Use a product where the package name is embedded but not significant
        cpe = {"vendor": "example", "product": "supervitesystem"}
        matches, reason, is_exact = check_name_match(cpe, "vite")

        # "vite" in "supervitesystem" but:
        # - ratio = 4/15 = 0.27 < 0.5
        # - doesn't start with "vite"
        assert matches is False

    def test_no_match(self) -> None:
        """Test no match."""
        cpe = {"vendor": "example", "product": "something_else"}
        matches, reason, is_exact = check_name_match(cpe, "lodash")

        assert matches is False
        assert "No name match" in reason


class TestIsHardwareCVE:
    """Tests for hardware CVE detection."""

    def test_hardware_part(self) -> None:
        """Test detection by CPE part."""
        cpe = {"part": "h", "vendor": "cypress", "product": "chip"}
        assert is_hardware_cve(cpe, "Some description") is True

    def test_hardware_vendor(self) -> None:
        """Test detection by known hardware vendor."""
        cpe = {"part": "a", "vendor": "cypress_semiconductor", "product": "sdk"}
        assert is_hardware_cve(cpe, "Some description") is True

    def test_hardware_description(self) -> None:
        """Test detection by description keywords."""
        cpe = {"part": "a", "vendor": "example", "product": "something"}
        desc = "A firmware vulnerability in the bluetooth chipset allows..."
        assert is_hardware_cve(cpe, desc) is True

    def test_software_cve(self) -> None:
        """Test that software CVEs are not flagged."""
        cpe = {"part": "a", "vendor": "vitejs", "product": "vite"}
        desc = "A cross-site scripting vulnerability in vite dev server"
        assert is_hardware_cve(cpe, desc) is False


class TestIsFalsePositive:
    """Tests for false positive detection."""

    def test_cypress_semiconductor(self) -> None:
        """Test cypress semiconductor false positive."""
        cpe = {"vendor": "cypress_semiconductor", "product": "cyw43455"}
        is_fp, reason = is_false_positive(cpe, "cypress", "")

        assert is_fp is True
        # Could match "cypress_semiconductor" or "cyw" pattern
        assert "cypress" in reason.lower() or "cyw" in reason.lower()

    def test_vitec_false_positive(self) -> None:
        """Test vitec false positive for vite."""
        cpe = {"vendor": "vitec", "product": "encoder"}
        is_fp, reason = is_false_positive(cpe, "vite", "")

        assert is_fp is True
        assert "vitec" in reason.lower()

    def test_not_false_positive(self) -> None:
        """Test that real matches are not flagged."""
        cpe = {"vendor": "vitejs", "product": "vite"}
        is_fp, reason = is_false_positive(cpe, "vite", "")

        assert is_fp is False
        assert reason == ""

    def test_hardware_vendor_false_positive(self) -> None:
        """Test hardware vendor detection."""
        cpe = {"vendor": "broadcom", "product": "sdk"}
        is_fp, reason = is_false_positive(cpe, "somepackage", "")

        assert is_fp is True
        assert "hardware vendor" in reason.lower()


class TestCheckVersionInRange:
    """Tests for version range checking."""

    def test_no_version_specified(self) -> None:
        """Test with no package version."""
        in_range, reason = check_version_in_range("", {})
        assert in_range is True

        in_range, reason = check_version_in_range("*", {})
        assert in_range is True

    def test_version_start_including(self) -> None:
        """Test versionStartIncluding constraint."""
        cpe_match = {"versionStartIncluding": "2.0.0"}

        in_range, reason = check_version_in_range("3.0.0", cpe_match)
        assert in_range is True

        in_range, reason = check_version_in_range("1.0.0", cpe_match)
        assert in_range is False

    def test_version_end_excluding(self) -> None:
        """Test versionEndExcluding constraint."""
        cpe_match = {"versionEndExcluding": "5.0.0"}

        in_range, reason = check_version_in_range("4.0.0", cpe_match)
        assert in_range is True

        in_range, reason = check_version_in_range("5.0.0", cpe_match)
        assert in_range is False

        in_range, reason = check_version_in_range("6.0.0", cpe_match)
        assert in_range is False

    def test_version_range(self) -> None:
        """Test full version range."""
        cpe_match = {
            "versionStartIncluding": "1.0.0",
            "versionEndExcluding": "2.0.0",
        }

        in_range, reason = check_version_in_range("1.5.0", cpe_match)
        assert in_range is True

        in_range, reason = check_version_in_range("0.5.0", cpe_match)
        assert in_range is False

        in_range, reason = check_version_in_range("2.5.0", cpe_match)
        assert in_range is False

    def test_version_with_v_prefix(self) -> None:
        """Test version with v prefix."""
        cpe_match = {"versionStartIncluding": "1.0.0"}

        in_range, reason = check_version_in_range("v2.0.0", cpe_match)
        assert in_range is True

    def test_invalid_version(self) -> None:
        """Test invalid version string."""
        cpe_match = {"versionStartIncluding": "1.0.0"}

        # Invalid versions should be assumed affected
        in_range, reason = check_version_in_range("invalid-version!", cpe_match)
        assert in_range is True


class TestCVEMatchResult:
    """Tests for CVEMatchResult dataclass."""

    def test_creation(self) -> None:
        """Test creating a match result."""
        result = CVEMatchResult(
            cve_id="CVE-2024-12345",
            confidence=ConfidenceLevel.HIGH,
            matched_cpes=["cpe:2.3:a:vitejs:vite:*"],
            reasons=["Exact product match"],
        )

        assert result.cve_id == "CVE-2024-12345"
        assert result.confidence == ConfidenceLevel.HIGH
        assert len(result.matched_cpes) == 1
        assert len(result.reasons) == 1


class TestNVDPackageMatcher:
    """Tests for NVDPackageMatcher class."""

    def test_match_cve_not_found(self) -> None:
        """Test matching when CVE is not found."""
        nvd_mock = MagicMock()
        nvd_mock.get_cve.return_value = None

        matcher = NVDPackageMatcher(nvd_mock)
        result = matcher.match_cve_to_package("CVE-2024-99999", "vite", "npm")

        assert result.confidence == ConfidenceLevel.EXCLUDED
        assert "not found" in result.reasons[0].lower()

    def test_match_no_cpes(self) -> None:
        """Test matching when CVE has no CPEs."""
        nvd_mock = MagicMock()
        nvd_mock.get_cve.return_value = CVEData(
            cve_id="CVE-2024-12345",
            description="Test vulnerability",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=[],
            fixed_versions=None,
            references=[],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        matcher = NVDPackageMatcher(nvd_mock)
        result = matcher.match_cve_to_package("CVE-2024-12345", "vite", "npm")

        assert result.confidence == ConfidenceLevel.LOW
        assert "No CPE information" in result.reasons[0]

    def test_match_high_confidence(self) -> None:
        """Test high confidence match."""
        nvd_mock = MagicMock()
        nvd_mock.get_cve.return_value = CVEData(
            cve_id="CVE-2024-12345",
            description="XSS vulnerability in vite dev server",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=["cpe:2.3:a:vitejs:vite:3.0.0:*:*:*:*:node.js:*:*"],
            fixed_versions=["3.0.1"],
            references=["https://example.com"],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        matcher = NVDPackageMatcher(nvd_mock)
        result = matcher.match_cve_to_package("CVE-2024-12345", "vite", "npm")

        assert result.confidence == ConfidenceLevel.HIGH
        assert len(result.matched_cpes) > 0

    def test_match_hardware_excluded(self) -> None:
        """Test that hardware CVEs are excluded."""
        nvd_mock = MagicMock()
        nvd_mock.get_cve.return_value = CVEData(
            cve_id="CVE-2024-12345",
            description="Bluetooth firmware vulnerability in cypress chip",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=["cpe:2.3:h:cypress_semiconductor:cyw43455:*:*:*:*:*:*:*:*"],
            fixed_versions=None,
            references=[],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        matcher = NVDPackageMatcher(nvd_mock)
        result = matcher.match_cve_to_package("CVE-2024-12345", "cypress", "npm")

        assert result.confidence == ConfidenceLevel.EXCLUDED

    def test_match_false_positive_excluded(self) -> None:
        """Test that false positives are excluded."""
        nvd_mock = MagicMock()
        nvd_mock.get_cve.return_value = CVEData(
            cve_id="CVE-2024-12345",
            description="Vulnerability in VITEC encoder",
            cvss_score=7.5,
            cvss_severity="HIGH",
            affected_cpes=["cpe:2.3:a:vitec:encoder:1.0:*:*:*:*:*:*:*"],
            fixed_versions=None,
            references=[],
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        matcher = NVDPackageMatcher(nvd_mock)
        result = matcher.match_cve_to_package("CVE-2024-12345", "vite", "npm")

        assert result.confidence == ConfidenceLevel.EXCLUDED

    def test_search_and_filter(self) -> None:
        """Test search and filter functionality."""
        nvd_mock = MagicMock()

        # Mock search results
        nvd_mock.search_by_keyword.return_value = [
            CVEData(
                cve_id="CVE-2024-11111",
                description="Vite XSS",
                cvss_score=7.5,
                cvss_severity="HIGH",
                affected_cpes=["cpe:2.3:a:vitejs:vite:3.0.0:*:*:*:*:node.js:*:*"],
                fixed_versions=None,
                references=[],
                published_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
            ),
            CVEData(
                cve_id="CVE-2024-22222",
                description="VITEC encoder issue",
                cvss_score=5.0,
                cvss_severity="MEDIUM",
                affected_cpes=["cpe:2.3:a:vitec:encoder:1.0:*:*:*:*:*:*:*"],
                fixed_versions=None,
                references=[],
                published_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
            ),
        ]

        # Mock get_cve to return the same data
        def get_cve(cve_id: str) -> CVEData:
            for cve in nvd_mock.search_by_keyword.return_value:
                if cve.cve_id == cve_id:
                    return cve
            return None

        nvd_mock.get_cve.side_effect = get_cve

        matcher = NVDPackageMatcher(nvd_mock)
        results = matcher.search_and_filter(
            package_name="vite",
            ecosystem="npm",
            min_confidence=ConfidenceLevel.MEDIUM,
        )

        # Only the real vite CVE should be included
        assert len(results) == 1
        assert results[0].cve_id == "CVE-2024-11111"

    def test_search_and_filter_with_low_confidence(self) -> None:
        """Test search and filter with low confidence threshold."""
        nvd_mock = MagicMock()

        nvd_mock.search_by_keyword.return_value = [
            CVEData(
                cve_id="CVE-2024-33333",
                description="Some vulnerability",
                cvss_score=5.0,
                cvss_severity="MEDIUM",
                affected_cpes=[],  # No CPEs = LOW confidence
                fixed_versions=None,
                references=[],
                published_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
            ),
        ]

        def get_cve(cve_id: str) -> CVEData:
            for cve in nvd_mock.search_by_keyword.return_value:
                if cve.cve_id == cve_id:
                    return cve
            return None

        nvd_mock.get_cve.side_effect = get_cve

        matcher = NVDPackageMatcher(nvd_mock)

        # With MEDIUM threshold, LOW confidence should be excluded
        results = matcher.search_and_filter(
            package_name="somepackage",
            ecosystem="npm",
            min_confidence=ConfidenceLevel.MEDIUM,
        )
        assert len(results) == 0

        # With LOW threshold, LOW confidence should be included
        results = matcher.search_and_filter(
            package_name="somepackage",
            ecosystem="npm",
            min_confidence=ConfidenceLevel.LOW,
        )
        assert len(results) == 1
