"""Tests for OSV API client."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import requests

from cve_sentinel.fetchers.osv import (
    MergedVulnerability,
    OSVAPIError,
    OSVClient,
    OSVVulnerability,
    merge_nvd_osv_data,
)


@pytest.fixture
def sample_osv_response() -> Dict[str, Any]:
    """Sample OSV API response for testing."""
    return {
        "vulns": [
            {
                "id": "GHSA-jfh8-c2jp-5v3q",
                "aliases": ["CVE-2021-44228"],
                "summary": "Remote code injection in Log4j",
                "details": "Apache Log4j2 2.0-beta9 through 2.15.0 JNDI features...",
                "severity": [
                    {
                        "type": "CVSS_V3",
                        "score": 10.0,
                    }
                ],
                "affected": [
                    {
                        "package": {
                            "ecosystem": "Maven",
                            "name": "org.apache.logging.log4j:log4j-core",
                        },
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "2.0-beta9"},
                                    {"fixed": "2.17.0"},
                                ],
                            }
                        ],
                    }
                ],
                "references": [
                    {"type": "ADVISORY", "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"},
                    {"type": "WEB", "url": "https://logging.apache.org/log4j/2.x/security.html"},
                ],
                "published": "2021-12-10T00:00:00Z",
                "modified": "2023-11-07T00:00:00Z",
            }
        ]
    }


@pytest.fixture
def sample_osv_batch_response() -> Dict[str, Any]:
    """Sample OSV batch API response for testing."""
    return {
        "results": [
            {
                "vulns": [
                    {
                        "id": "GHSA-jfh8-c2jp-5v3q",
                        "aliases": ["CVE-2021-44228"],
                        "summary": "Remote code injection in Log4j",
                    }
                ]
            },
            {
                "vulns": [
                    {
                        "id": "GHSA-xxxx-xxxx-xxxx",
                        "aliases": ["CVE-2020-12345"],
                        "summary": "Test vulnerability",
                    }
                ]
            },
        ]
    }


@pytest.fixture
def sample_empty_osv_response() -> Dict[str, Any]:
    """Empty OSV API response for testing."""
    return {"vulns": []}


class TestOSVVulnerability:
    """Tests for OSVVulnerability dataclass."""

    def test_create_vulnerability(self) -> None:
        """Test creating an OSVVulnerability."""
        vuln = OSVVulnerability(
            id="GHSA-jfh8-c2jp-5v3q",
            aliases=["CVE-2021-44228"],
            summary="Test vulnerability",
        )

        assert vuln.id == "GHSA-jfh8-c2jp-5v3q"
        assert vuln.aliases == ["CVE-2021-44228"]
        assert vuln.summary == "Test vulnerability"

    def test_get_cve_ids(self) -> None:
        """Test extracting CVE IDs from aliases."""
        vuln = OSVVulnerability(
            id="GHSA-jfh8-c2jp-5v3q",
            aliases=["CVE-2021-44228", "GHSA-xyz", "CVE-2020-12345"],
        )

        cve_ids = vuln.get_cve_ids()

        assert len(cve_ids) == 2
        assert "CVE-2021-44228" in cve_ids
        assert "CVE-2020-12345" in cve_ids
        assert "GHSA-xyz" not in cve_ids

    def test_get_cve_ids_empty(self) -> None:
        """Test get_cve_ids with no CVE aliases."""
        vuln = OSVVulnerability(
            id="GHSA-jfh8-c2jp-5v3q",
            aliases=["GHSA-xyz"],
        )

        cve_ids = vuln.get_cve_ids()

        assert cve_ids == []

    def test_get_cvss_score(self) -> None:
        """Test extracting CVSS score from severity."""
        vuln = OSVVulnerability(
            id="GHSA-test",
            severity=[{"type": "CVSS_V3", "score": 9.8}],
        )

        score = vuln.get_cvss_score()

        assert score == 9.8

    def test_get_cvss_score_none(self) -> None:
        """Test get_cvss_score with no CVSS data."""
        vuln = OSVVulnerability(id="GHSA-test")

        score = vuln.get_cvss_score()

        assert score is None

    def test_get_cvss_severity_critical(self) -> None:
        """Test CVSS severity calculation for critical."""
        vuln = OSVVulnerability(
            id="GHSA-test",
            severity=[{"type": "CVSS_V3", "score": 10.0}],
        )

        severity = vuln.get_cvss_severity()

        assert severity == "CRITICAL"

    def test_get_cvss_severity_high(self) -> None:
        """Test CVSS severity calculation for high."""
        vuln = OSVVulnerability(
            id="GHSA-test",
            severity=[{"type": "CVSS_V3", "score": 7.5}],
        )

        severity = vuln.get_cvss_severity()

        assert severity == "HIGH"

    def test_get_cvss_severity_medium(self) -> None:
        """Test CVSS severity calculation for medium."""
        vuln = OSVVulnerability(
            id="GHSA-test",
            severity=[{"type": "CVSS_V3", "score": 5.0}],
        )

        severity = vuln.get_cvss_severity()

        assert severity == "MEDIUM"

    def test_get_cvss_severity_low(self) -> None:
        """Test CVSS severity calculation for low."""
        vuln = OSVVulnerability(
            id="GHSA-test",
            severity=[{"type": "CVSS_V3", "score": 2.0}],
        )

        severity = vuln.get_cvss_severity()

        assert severity == "LOW"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        now = datetime.now(timezone.utc)
        vuln = OSVVulnerability(
            id="GHSA-test",
            aliases=["CVE-2021-44228"],
            summary="Test",
            published=now,
            modified=now,
        )

        result = vuln.to_dict()

        assert result["id"] == "GHSA-test"
        assert result["aliases"] == ["CVE-2021-44228"]
        assert result["published"] == now.isoformat()

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "id": "GHSA-test",
            "aliases": ["CVE-2021-44228"],
            "summary": "Test vulnerability",
            "published": "2021-12-10T00:00:00+00:00",
        }

        vuln = OSVVulnerability.from_dict(data)

        assert vuln.id == "GHSA-test"
        assert vuln.aliases == ["CVE-2021-44228"]
        assert vuln.published is not None
        assert vuln.published.year == 2021


class TestOSVClient:
    """Tests for OSVClient class."""

    @pytest.fixture
    def client(self, temp_dir: Path) -> OSVClient:
        """Create an OSV client for testing."""
        return OSVClient(
            cache_dir=temp_dir / "cache",
            cache_ttl_hours=24,
        )

    @pytest.fixture
    def client_no_cache(self) -> OSVClient:
        """Create an OSV client without caching."""
        return OSVClient()

    def test_client_initialization(self, temp_dir: Path) -> None:
        """Test client initialization with cache."""
        client = OSVClient(
            cache_dir=temp_dir / "cache",
            cache_ttl_hours=12,
        )

        assert client.cache is not None
        assert (temp_dir / "cache").exists()

    def test_client_initialization_no_cache(self) -> None:
        """Test client initialization without cache."""
        client = OSVClient()

        assert client.cache is None

    def test_ecosystem_mapping(self, client: OSVClient) -> None:
        """Test ecosystem name mapping."""
        assert client._get_osv_ecosystem("npm") == "npm"
        assert client._get_osv_ecosystem("pypi") == "PyPI"
        assert client._get_osv_ecosystem("go") == "Go"
        assert client._get_osv_ecosystem("maven") == "Maven"
        assert client._get_osv_ecosystem("rubygems") == "RubyGems"
        assert client._get_osv_ecosystem("crates.io") == "crates.io"
        assert client._get_osv_ecosystem("packagist") == "Packagist"

    def test_ecosystem_mapping_case_insensitive(self, client: OSVClient) -> None:
        """Test ecosystem mapping is case insensitive."""
        assert client._get_osv_ecosystem("NPM") == "npm"
        assert client._get_osv_ecosystem("PyPI") == "PyPI"
        assert client._get_osv_ecosystem("MAVEN") == "Maven"

    def test_ecosystem_mapping_unsupported(self, client: OSVClient) -> None:
        """Test unsupported ecosystem raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported ecosystem"):
            client._get_osv_ecosystem("unknown")

    def test_get_supported_ecosystems(self) -> None:
        """Test getting list of supported ecosystems."""
        ecosystems = OSVClient.get_supported_ecosystems()

        assert "npm" in ecosystems
        assert "pypi" in ecosystems
        assert "go" in ecosystems
        assert "maven" in ecosystems

    @patch("requests.Session.post")
    def test_query(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_osv_response: Dict[str, Any],
    ) -> None:
        """Test querying vulnerabilities for a package."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_osv_response
        mock_post.return_value = mock_response

        results = client.query("log4j-core", "maven")

        assert len(results) == 1
        assert results[0].id == "GHSA-jfh8-c2jp-5v3q"
        assert "CVE-2021-44228" in results[0].aliases
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_query_with_version(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_osv_response: Dict[str, Any],
    ) -> None:
        """Test querying with specific version."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_osv_response
        mock_post.return_value = mock_response

        results = client.query("log4j-core", "maven", version="2.14.0")

        assert len(results) == 1
        call_args = mock_post.call_args
        request_data = call_args.kwargs.get("json", call_args[1].get("json", {}))
        assert request_data.get("version") == "2.14.0"

    @patch("requests.Session.post")
    def test_query_empty_results(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_empty_osv_response: Dict[str, Any],
    ) -> None:
        """Test query with no vulnerabilities found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_empty_osv_response
        mock_post.return_value = mock_response

        results = client.query("safe-package", "npm")

        assert results == []

    def test_query_unsupported_ecosystem(self, client: OSVClient) -> None:
        """Test query with unsupported ecosystem returns empty list."""
        results = client.query("package", "unknown-ecosystem")

        assert results == []

    @patch("requests.Session.post")
    def test_query_batch(
        self,
        mock_post: MagicMock,
        client_no_cache: OSVClient,
        sample_osv_batch_response: Dict[str, Any],
    ) -> None:
        """Test batch query for multiple packages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_osv_batch_response
        mock_post.return_value = mock_response

        packages = [
            {"name": "log4j-core", "ecosystem": "maven"},
            {"name": "requests", "ecosystem": "pypi"},
        ]

        results = client_no_cache.query_batch(packages)

        assert len(results) == 2
        assert "maven:log4j-core" in results
        assert "pypi:requests" in results
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_query_batch_empty(
        self,
        mock_post: MagicMock,
        client_no_cache: OSVClient,
    ) -> None:
        """Test batch query with empty package list."""
        results = client_no_cache.query_batch([])

        assert results == {}
        mock_post.assert_not_called()

    @patch("requests.Session.post")
    def test_api_error_handling(
        self,
        mock_post: MagicMock,
        client: OSVClient,
    ) -> None:
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(OSVAPIError) as exc_info:
            client.query("test", "npm")

        assert exc_info.value.status_code == 500

    @patch("requests.Session.post")
    def test_bad_request_error(
        self,
        mock_post: MagicMock,
        client: OSVClient,
    ) -> None:
        """Test handling of bad request errors."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(OSVAPIError) as exc_info:
            client.query("test", "npm")

        assert exc_info.value.status_code == 400

    @patch("requests.Session.post")
    def test_timeout_retry(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_osv_response: Dict[str, Any],
    ) -> None:
        """Test retry on timeout."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = sample_osv_response

        mock_post.side_effect = [
            requests.exceptions.Timeout("Connection timed out"),
            success_response,
        ]

        results = client.query("log4j-core", "maven")

        assert len(results) == 1
        assert mock_post.call_count == 2

    @patch("requests.Session.post")
    def test_connection_error_retry(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_osv_response: Dict[str, Any],
    ) -> None:
        """Test retry on connection error."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = sample_osv_response

        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            success_response,
        ]

        results = client.query("log4j-core", "maven")

        assert len(results) == 1
        assert mock_post.call_count == 2

    @patch("requests.Session.post")
    def test_max_retries_exceeded(
        self,
        mock_post: MagicMock,
        client: OSVClient,
    ) -> None:
        """Test error after max retries exceeded."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        with pytest.raises(OSVAPIError) as exc_info:
            client.query("test", "npm")

        assert "timeout" in str(exc_info.value).lower()
        assert mock_post.call_count == 5  # MAX_RETRIES

    @patch("requests.Session.post")
    def test_caching(
        self,
        mock_post: MagicMock,
        client: OSVClient,
        sample_osv_response: Dict[str, Any],
    ) -> None:
        """Test that responses are cached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_osv_response
        mock_post.return_value = mock_response

        # First call
        results1 = client.query("log4j-core", "maven")

        # Second call should use cache
        results2 = client.query("log4j-core", "maven")

        assert len(results1) == len(results2)
        assert mock_post.call_count == 1  # Only one actual request

    @patch("requests.Session.get")
    def test_get_vulnerability(
        self,
        mock_get: MagicMock,
        client: OSVClient,
    ) -> None:
        """Test getting a specific vulnerability by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "GHSA-jfh8-c2jp-5v3q",
            "aliases": ["CVE-2021-44228"],
            "summary": "Test vulnerability",
        }
        mock_get.return_value = mock_response

        result = client.get_vulnerability("GHSA-jfh8-c2jp-5v3q")

        assert result is not None
        assert result.id == "GHSA-jfh8-c2jp-5v3q"

    @patch("requests.Session.get")
    def test_get_vulnerability_not_found(
        self,
        mock_get: MagicMock,
        client: OSVClient,
    ) -> None:
        """Test getting a vulnerability that doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = client.get_vulnerability("GHSA-nonexistent")

        assert result is None


class TestOSVClientParsing:
    """Tests for OSV response parsing."""

    @pytest.fixture
    def client(self) -> OSVClient:
        """Create an OSV client for testing."""
        return OSVClient()

    def test_parse_fixed_versions(self, client: OSVClient) -> None:
        """Test parsing fixed versions from affected data."""
        vuln_data = {
            "id": "GHSA-test",
            "affected": [
                {
                    "ranges": [
                        {
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "1.2.3"},
                            ]
                        }
                    ]
                }
            ],
        }

        result = client._parse_vulnerability(vuln_data)

        assert "1.2.3" in result.fixed_versions

    def test_parse_references(self, client: OSVClient) -> None:
        """Test parsing references from vulnerability data."""
        vuln_data = {
            "id": "GHSA-test",
            "references": [
                {"type": "ADVISORY", "url": "https://example.com/advisory"},
                {"type": "WEB", "url": "https://example.com/details"},
            ],
        }

        result = client._parse_vulnerability(vuln_data)

        assert len(result.references) == 2
        assert "https://example.com/advisory" in result.references

    def test_parse_dates(self, client: OSVClient) -> None:
        """Test parsing dates from vulnerability data."""
        vuln_data = {
            "id": "GHSA-test",
            "published": "2021-12-10T00:00:00Z",
            "modified": "2023-11-07T00:00:00Z",
        }

        result = client._parse_vulnerability(vuln_data)

        assert result.published is not None
        assert result.published.year == 2021
        assert result.modified is not None
        assert result.modified.year == 2023


class TestMergeNVDOSVData:
    """Tests for merging NVD and OSV data."""

    def test_merge_osv_only(self) -> None:
        """Test merging with only OSV data."""
        osv_vulns = [
            OSVVulnerability(
                id="GHSA-test",
                aliases=["CVE-2021-44228"],
                summary="Test vulnerability",
                fixed_versions=["2.17.0"],
            )
        ]

        merged = merge_nvd_osv_data(osv_vulns)

        assert len(merged) == 1
        assert merged[0].cve_id == "CVE-2021-44228"
        assert merged[0].osv_ids == ["GHSA-test"]
        assert merged[0].source == "osv"

    def test_merge_osv_without_cve(self) -> None:
        """Test merging OSV data without CVE ID."""
        osv_vulns = [
            OSVVulnerability(
                id="GHSA-test",
                aliases=[],  # No CVE ID
                summary="Test vulnerability",
            )
        ]

        merged = merge_nvd_osv_data(osv_vulns)

        assert len(merged) == 1
        assert merged[0].cve_id == "GHSA-test"  # Uses OSV ID as identifier

    def test_merge_duplicate_cve(self) -> None:
        """Test merging multiple OSV entries for same CVE."""
        osv_vulns = [
            OSVVulnerability(
                id="GHSA-test-1",
                aliases=["CVE-2021-44228"],
                summary="First entry",
                fixed_versions=["2.17.0"],
            ),
            OSVVulnerability(
                id="GHSA-test-2",
                aliases=["CVE-2021-44228"],
                summary="Second entry",
                fixed_versions=["2.17.1"],
            ),
        ]

        merged = merge_nvd_osv_data(osv_vulns)

        assert len(merged) == 1
        assert merged[0].cve_id == "CVE-2021-44228"
        assert len(merged[0].osv_ids) == 2
        assert "2.17.0" in merged[0].fixed_versions
        assert "2.17.1" in merged[0].fixed_versions

    def test_merge_with_nvd_client(self) -> None:
        """Test merging with NVD client data."""
        osv_vulns = [
            OSVVulnerability(
                id="GHSA-test",
                aliases=["CVE-2021-44228"],
                summary="",  # Empty summary
            )
        ]

        # Mock NVD client
        mock_nvd_client = MagicMock()
        mock_nvd_data = MagicMock()
        mock_nvd_data.cvss_score = 10.0
        mock_nvd_data.cvss_severity = "CRITICAL"
        mock_nvd_data.description = "NVD description"
        mock_nvd_data.references = ["https://nvd.nist.gov"]
        mock_nvd_client.get_cve.return_value = mock_nvd_data

        merged = merge_nvd_osv_data(osv_vulns, nvd_client=mock_nvd_client)

        assert len(merged) == 1
        assert merged[0].cvss_score == 10.0
        assert merged[0].cvss_severity == "CRITICAL"
        assert merged[0].description == "NVD description"
        assert merged[0].source == "merged"


class TestMergedVulnerability:
    """Tests for MergedVulnerability dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        now = datetime.now(timezone.utc)
        merged = MergedVulnerability(
            cve_id="CVE-2021-44228",
            osv_ids=["GHSA-test"],
            description="Test",
            cvss_score=10.0,
            cvss_severity="CRITICAL",
            fixed_versions=["2.17.0"],
            published_date=now,
            source="merged",
        )

        result = merged.to_dict()

        assert result["cve_id"] == "CVE-2021-44228"
        assert result["osv_ids"] == ["GHSA-test"]
        assert result["cvss_score"] == 10.0
        assert result["source"] == "merged"


class TestOSVAPIError:
    """Tests for OSV API error class."""

    def test_osv_api_error_with_status_code(self) -> None:
        """Test OSVAPIError with status code."""
        error = OSVAPIError("Test error", status_code=500)

        assert str(error) == "Test error"
        assert error.status_code == 500

    def test_osv_api_error_without_status_code(self) -> None:
        """Test OSVAPIError without status code."""
        error = OSVAPIError("Test error")

        assert str(error) == "Test error"
        assert error.status_code is None
