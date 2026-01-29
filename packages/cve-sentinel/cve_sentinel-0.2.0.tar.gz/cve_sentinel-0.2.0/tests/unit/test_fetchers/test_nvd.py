"""Tests for NVD API client."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import requests

from cve_sentinel.fetchers.nvd import (
    CVEData,
    NVDAPIError,
    NVDClient,
    NVDRateLimitError,
    RateLimiter,
)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_allows_requests_under_limit(self) -> None:
        """Test that requests under the limit are allowed immediately."""
        limiter = RateLimiter(max_requests=5, window_seconds=30)

        # Should not raise or sleep
        for _ in range(5):
            limiter.wait_if_needed()

        assert len(limiter.request_times) == 5

    def test_rate_limiter_cleans_old_requests(self) -> None:
        """Test that old requests are cleaned from the window."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)

        # Make some requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Wait for window to expire
        time.sleep(1.1)

        # Old requests should be cleaned
        limiter.wait_if_needed()

        # Should only have the new request
        assert len(limiter.request_times) == 1


class TestCVEData:
    """Tests for CVEData dataclass."""

    def test_cve_data_to_dict(self) -> None:
        """Test CVEData serialization to dictionary."""
        now = datetime.now(timezone.utc)
        cve_data = CVEData(
            cve_id="CVE-2021-44228",
            description="Test description",
            cvss_score=10.0,
            cvss_severity="CRITICAL",
            affected_cpes=["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            fixed_versions=["2.17.0"],
            references=["https://example.com"],
            published_date=now,
            last_modified=now,
        )

        result = cve_data.to_dict()

        assert result["cve_id"] == "CVE-2021-44228"
        assert result["description"] == "Test description"
        assert result["cvss_score"] == 10.0
        assert result["cvss_severity"] == "CRITICAL"
        assert result["affected_cpes"] == ["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"]
        assert result["fixed_versions"] == ["2.17.0"]
        assert result["references"] == ["https://example.com"]
        assert result["published_date"] == now.isoformat()
        assert result["last_modified"] == now.isoformat()

    def test_cve_data_from_dict(self) -> None:
        """Test CVEData deserialization from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            "cve_id": "CVE-2021-44228",
            "description": "Test description",
            "cvss_score": 10.0,
            "cvss_severity": "CRITICAL",
            "affected_cpes": ["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            "fixed_versions": ["2.17.0"],
            "references": ["https://example.com"],
            "published_date": now.isoformat(),
            "last_modified": now.isoformat(),
        }

        cve_data = CVEData.from_dict(data)

        assert cve_data.cve_id == "CVE-2021-44228"
        assert cve_data.description == "Test description"
        assert cve_data.cvss_score == 10.0
        assert cve_data.cvss_severity == "CRITICAL"
        assert cve_data.affected_cpes == ["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"]
        assert cve_data.fixed_versions == ["2.17.0"]
        assert cve_data.references == ["https://example.com"]

    def test_cve_data_roundtrip(self) -> None:
        """Test CVEData serialization/deserialization roundtrip."""
        now = datetime.now(timezone.utc)
        original = CVEData(
            cve_id="CVE-2021-44228",
            description="Test description",
            cvss_score=10.0,
            cvss_severity="CRITICAL",
            affected_cpes=["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            fixed_versions=None,
            references=["https://example.com"],
            published_date=now,
            last_modified=now,
        )

        data = original.to_dict()
        restored = CVEData.from_dict(data)

        assert restored.cve_id == original.cve_id
        assert restored.description == original.description
        assert restored.cvss_score == original.cvss_score


class TestNVDClient:
    """Tests for NVDClient class."""

    @pytest.fixture
    def mock_response(self, sample_nvd_response: Dict[str, Any]) -> MagicMock:
        """Create a mock response object."""
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = sample_nvd_response
        return mock

    @pytest.fixture
    def client(self, temp_dir: Path) -> NVDClient:
        """Create an NVD client for testing."""
        return NVDClient(
            api_key="test-api-key",
            cache_dir=temp_dir / "cache",
            cache_ttl_hours=24,
        )

    @pytest.fixture
    def client_no_cache(self) -> NVDClient:
        """Create an NVD client without caching."""
        return NVDClient(api_key="test-api-key")

    def test_client_initialization(self, temp_dir: Path) -> None:
        """Test client initialization with API key and cache."""
        client = NVDClient(
            api_key="test-api-key",
            cache_dir=temp_dir / "cache",
            cache_ttl_hours=12,
        )

        assert client.api_key == "test-api-key"
        assert client.cache is not None
        assert (temp_dir / "cache").exists()

    def test_client_initialization_no_cache(self) -> None:
        """Test client initialization without cache."""
        client = NVDClient(api_key="test-api-key")

        assert client.api_key == "test-api-key"
        assert client.cache is None

    def test_client_headers(self, client: NVDClient) -> None:
        """Test that client sets correct headers."""
        assert client._session.headers.get("apiKey") == "test-api-key"
        assert client._session.headers.get("Accept") == "application/json"

    @patch("requests.Session.get")
    def test_search_by_keyword(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test searching CVEs by keyword."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_nvd_response
        mock_get.return_value = mock_response

        results = client.search_by_keyword("log4j")

        assert len(results) == 1
        assert results[0].cve_id == "CVE-2021-44228"
        assert results[0].cvss_score == 10.0
        assert results[0].cvss_severity == "CRITICAL"
        assert "log4j" in results[0].description.lower()

    @patch("requests.Session.get")
    def test_search_by_cpe(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test searching CVEs by CPE name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_nvd_response
        mock_get.return_value = mock_response

        results = client.search_by_cpe("cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*")

        assert len(results) == 1
        assert results[0].cve_id == "CVE-2021-44228"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "cpeName" in call_args.kwargs.get("params", call_args[1].get("params", {}))

    @patch("requests.Session.get")
    def test_get_cve(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test getting a specific CVE by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_nvd_response
        mock_get.return_value = mock_response

        result = client.get_cve("CVE-2021-44228")

        assert result is not None
        assert result.cve_id == "CVE-2021-44228"

    @patch("requests.Session.get")
    def test_get_cve_not_found(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_empty_nvd_response: Dict[str, Any],
    ) -> None:
        """Test getting a CVE that doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_empty_nvd_response
        mock_get.return_value = mock_response

        result = client.get_cve("CVE-9999-99999")

        assert result is None

    @patch("requests.Session.get")
    def test_search_empty_results(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_empty_nvd_response: Dict[str, Any],
    ) -> None:
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_empty_nvd_response
        mock_get.return_value = mock_response

        results = client.search_by_keyword("nonexistent-package-xyz")

        assert results == []

    @patch("requests.Session.get")
    def test_api_error_handling(
        self,
        mock_get: MagicMock,
        client: NVDClient,
    ) -> None:
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with pytest.raises(NVDAPIError) as exc_info:
            client.search_by_keyword("test")

        assert exc_info.value.status_code == 500

    @patch("requests.Session.get")
    def test_rate_limit_error(
        self,
        mock_get: MagicMock,
        client: NVDClient,
    ) -> None:
        """Test handling of rate limit errors."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        with pytest.raises(NVDRateLimitError):
            client.search_by_keyword("test")

    @patch("requests.Session.get")
    def test_timeout_retry(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test retry on timeout."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = sample_nvd_response

        # First call times out, second succeeds
        mock_get.side_effect = [
            requests.exceptions.Timeout("Connection timed out"),
            success_response,
        ]

        results = client.search_by_keyword("log4j")

        assert len(results) == 1
        assert mock_get.call_count == 2

    @patch("requests.Session.get")
    def test_connection_error_retry(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test retry on connection error."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = sample_nvd_response

        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            success_response,
        ]

        results = client.search_by_keyword("log4j")

        assert len(results) == 1
        assert mock_get.call_count == 2

    @patch("requests.Session.get")
    def test_max_retries_exceeded(
        self,
        mock_get: MagicMock,
        client: NVDClient,
    ) -> None:
        """Test error after max retries exceeded."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with pytest.raises(NVDAPIError) as exc_info:
            client.search_by_keyword("test")

        assert "timeout" in str(exc_info.value).lower()
        assert mock_get.call_count == 3  # MAX_RETRIES

    @patch("requests.Session.get")
    def test_caching(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test that responses are cached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_nvd_response
        mock_get.return_value = mock_response

        # First call
        results1 = client.search_by_keyword("log4j")

        # Second call should use cache
        results2 = client.search_by_keyword("log4j")

        assert len(results1) == len(results2)
        assert mock_get.call_count == 1  # Only one actual request

    @patch("requests.Session.get")
    def test_search_by_date_range(
        self,
        mock_get: MagicMock,
        client: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test searching CVEs by date range."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_nvd_response
        mock_get.return_value = mock_response

        start_date = datetime(2021, 12, 1, tzinfo=timezone.utc)
        end_date = datetime(2021, 12, 31, tzinfo=timezone.utc)

        results = client.search_by_date_range(start_date, end_date)

        assert len(results) == 1
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert "lastModStartDate" in params
        assert "lastModEndDate" in params

    @patch("requests.Session.get")
    def test_get_total_results(
        self,
        mock_get: MagicMock,
        client: NVDClient,
    ) -> None:
        """Test getting total results count."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "totalResults": 150,
            "vulnerabilities": [],
        }
        mock_get.return_value = mock_response

        total = client.get_total_results("log4j")

        assert total == 150

    @patch("requests.Session.get")
    def test_search_all_by_keyword_pagination(
        self,
        mock_get: MagicMock,
        client_no_cache: NVDClient,
        sample_nvd_response: Dict[str, Any],
    ) -> None:
        """Test paginated search."""
        # Create page with exactly 100 results to trigger pagination
        # (search_all_by_keyword uses results_per_page=100)
        page1_vulns = [sample_nvd_response["vulnerabilities"][0]] * 100
        page1 = {
            "totalResults": 150,
            "vulnerabilities": page1_vulns,
        }

        # Second page with 50 results
        page2_vulns = [sample_nvd_response["vulnerabilities"][0]] * 50
        page2 = {
            "totalResults": 150,
            "vulnerabilities": page2_vulns,
        }

        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2

        mock_get.side_effect = [mock_response1, mock_response2]

        results = client_no_cache.search_all_by_keyword("log4j", max_results=200)

        assert len(results) == 150
        assert mock_get.call_count == 2


class TestNVDClientParsing:
    """Tests for NVD response parsing."""

    @pytest.fixture
    def client(self) -> NVDClient:
        """Create an NVD client for testing."""
        return NVDClient(api_key="test-api-key")

    def test_parse_cve_with_cvss_v31(self, client: NVDClient) -> None:
        """Test parsing CVE with CVSS v3.1 metrics."""
        cve_item = {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [{"lang": "en", "value": "Test description"}],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "cvssData": {
                                "baseScore": 10.0,
                                "baseSeverity": "CRITICAL",
                            }
                        }
                    ]
                },
                "configurations": [],
                "references": [],
                "published": "2021-12-10T10:15:09.143",
                "lastModified": "2023-11-07T03:39:36.750",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert result.cvss_score == 10.0
        assert result.cvss_severity == "CRITICAL"

    def test_parse_cve_with_cvss_v30_fallback(self, client: NVDClient) -> None:
        """Test parsing CVE with CVSS v3.0 fallback."""
        cve_item = {
            "cve": {
                "id": "CVE-2020-12345",
                "descriptions": [{"lang": "en", "value": "Test description"}],
                "metrics": {
                    "cvssMetricV30": [
                        {
                            "cvssData": {
                                "baseScore": 7.5,
                                "baseSeverity": "HIGH",
                            }
                        }
                    ]
                },
                "configurations": [],
                "references": [],
                "published": "2020-01-01T00:00:00.000",
                "lastModified": "2020-01-01T00:00:00.000",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert result.cvss_score == 7.5
        assert result.cvss_severity == "HIGH"

    def test_parse_cve_without_cvss(self, client: NVDClient) -> None:
        """Test parsing CVE without CVSS metrics."""
        cve_item = {
            "cve": {
                "id": "CVE-2020-12345",
                "descriptions": [{"lang": "en", "value": "Test description"}],
                "metrics": {},
                "configurations": [],
                "references": [],
                "published": "2020-01-01T00:00:00.000",
                "lastModified": "2020-01-01T00:00:00.000",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert result.cvss_score is None
        assert result.cvss_severity is None

    def test_parse_cve_with_affected_cpes(self, client: NVDClient) -> None:
        """Test parsing CVE with affected CPEs."""
        cve_item = {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [{"lang": "en", "value": "Test"}],
                "metrics": {},
                "configurations": [
                    {
                        "nodes": [
                            {
                                "cpeMatch": [
                                    {
                                        "vulnerable": True,
                                        "criteria": "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*",
                                    },
                                    {
                                        "vulnerable": False,
                                        "criteria": "cpe:2.3:a:apache:log4j:2.17.0:*:*:*:*:*:*:*",
                                    },
                                ]
                            }
                        ]
                    }
                ],
                "references": [],
                "published": "2021-12-10T10:15:09.143",
                "lastModified": "2023-11-07T03:39:36.750",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert len(result.affected_cpes) == 1
        assert "cpe:2.3:a:apache:log4j:*" in result.affected_cpes[0]

    def test_parse_cve_with_references(self, client: NVDClient) -> None:
        """Test parsing CVE with references."""
        cve_item = {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [{"lang": "en", "value": "Test"}],
                "metrics": {},
                "configurations": [],
                "references": [
                    {"url": "https://example.com/advisory"},
                    {"url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"},
                ],
                "published": "2021-12-10T10:15:09.143",
                "lastModified": "2023-11-07T03:39:36.750",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert len(result.references) == 2
        assert "https://example.com/advisory" in result.references

    def test_parse_cve_non_english_description_fallback(self, client: NVDClient) -> None:
        """Test parsing CVE when English description is not first."""
        cve_item = {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [
                    {"lang": "es", "value": "Descripción en español"},
                    {"lang": "en", "value": "English description"},
                ],
                "metrics": {},
                "configurations": [],
                "references": [],
                "published": "2021-12-10T10:15:09.143",
                "lastModified": "2023-11-07T03:39:36.750",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert result.description == "English description"

    def test_parse_cve_dates_with_z_suffix(self, client: NVDClient) -> None:
        """Test parsing CVE with Z suffix in dates."""
        cve_item = {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [{"lang": "en", "value": "Test"}],
                "metrics": {},
                "configurations": [],
                "references": [],
                "published": "2021-12-10T10:15:09.143Z",
                "lastModified": "2023-11-07T03:39:36.750Z",
            }
        }

        result = client._parse_cve_item(cve_item)

        assert result.published_date.year == 2021
        assert result.published_date.month == 12
        assert result.published_date.day == 10


class TestNVDAPIError:
    """Tests for NVD API error classes."""

    def test_nvd_api_error_with_status_code(self) -> None:
        """Test NVDAPIError with status code."""
        error = NVDAPIError("Test error", status_code=500)

        assert str(error) == "Test error"
        assert error.status_code == 500

    def test_nvd_api_error_without_status_code(self) -> None:
        """Test NVDAPIError without status code."""
        error = NVDAPIError("Test error")

        assert str(error) == "Test error"
        assert error.status_code is None

    def test_nvd_rate_limit_error_is_api_error(self) -> None:
        """Test that NVDRateLimitError is a subclass of NVDAPIError."""
        error = NVDRateLimitError("Rate limit exceeded", status_code=403)

        assert isinstance(error, NVDAPIError)
        assert error.status_code == 403
