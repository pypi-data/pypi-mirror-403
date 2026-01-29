"""Tests for NVD API client."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest
import requests

from cve_sentinel.fetchers.nvd import (
    CVEData,
    NVDAPIError,
    NVDClient,
    NVDRateLimitError,
    RateLimiter,
)


class TestCVEData:
    """Tests for CVEData dataclass."""

    def test_create_cve_data(self) -> None:
        """Test creating CVEData instance."""
        cve = CVEData(
            cve_id="CVE-2021-44228",
            description="Log4j vulnerability",
            cvss_score=10.0,
            cvss_severity="CRITICAL",
            affected_cpes=["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            fixed_versions=["2.17.0"],
            references=["https://example.com"],
            published_date=datetime(2021, 12, 10, tzinfo=timezone.utc),
            last_modified=datetime(2021, 12, 15, tzinfo=timezone.utc),
        )

        assert cve.cve_id == "CVE-2021-44228"
        assert cve.cvss_score == 10.0
        assert cve.cvss_severity == "CRITICAL"

    def test_to_dict(self) -> None:
        """Test CVEData to_dict serialization."""
        cve = CVEData(
            cve_id="CVE-2021-44228",
            description="Test",
            cvss_score=10.0,
            cvss_severity="CRITICAL",
            affected_cpes=["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            fixed_versions=None,
            references=[],
            published_date=datetime(2021, 12, 10, tzinfo=timezone.utc),
            last_modified=datetime(2021, 12, 10, tzinfo=timezone.utc),
        )

        data = cve.to_dict()
        assert data["cve_id"] == "CVE-2021-44228"
        assert "published_date" in data
        assert isinstance(data["published_date"], str)

    def test_from_dict(self) -> None:
        """Test CVEData from_dict deserialization."""
        data = {
            "cve_id": "CVE-2021-44228",
            "description": "Test",
            "cvss_score": 10.0,
            "cvss_severity": "CRITICAL",
            "affected_cpes": ["cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"],
            "fixed_versions": None,
            "references": [],
            "published_date": "2021-12-10T00:00:00+00:00",
            "last_modified": "2021-12-10T00:00:00+00:00",
        }

        cve = CVEData.from_dict(data)
        assert cve.cve_id == "CVE-2021-44228"
        assert isinstance(cve.published_date, datetime)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_allows_requests_under_limit(self) -> None:
        """Test that requests under limit are allowed without waiting."""
        limiter = RateLimiter(max_requests=5, window_seconds=30)

        start = time.time()
        for _ in range(3):
            limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should complete quickly without waiting
        assert elapsed < 1.0

    def test_waits_when_limit_reached(self) -> None:
        """Test that limiter waits when limit is reached."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # Make 2 requests (at limit)
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Third request should wait
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should have waited approximately 1 second
        assert elapsed >= 0.5

    def test_old_requests_expire(self) -> None:
        """Test that old requests are removed from window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Wait for window to expire
        time.sleep(1.1)

        # Should be able to make requests without waiting
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        assert elapsed < 0.5


class TestNVDClient:
    """Tests for NVDClient class."""

    @pytest.fixture
    def mock_response(self) -> dict:
        """Sample NVD API response."""
        return {
            "totalResults": 1,
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2021-44228",
                        "descriptions": [{"lang": "en", "value": "Apache Log4j2 vulnerability"}],
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
                        "configurations": [
                            {
                                "nodes": [
                                    {
                                        "cpeMatch": [
                                            {
                                                "vulnerable": True,
                                                "criteria": "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*",
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                        "references": [
                            {"url": "https://logging.apache.org/log4j/2.x/security.html"}
                        ],
                        "published": "2021-12-10T10:15:00.000Z",
                        "lastModified": "2021-12-15T10:15:00.000Z",
                    }
                }
            ],
        }

    @pytest.fixture
    def client(self, tmp_path: Path) -> NVDClient:
        """Create NVDClient instance for testing."""
        cache_dir = tmp_path / "cache"
        return NVDClient(
            api_key="test-api-key",
            cache_dir=cache_dir,
            cache_ttl_hours=24,
        )

    def test_client_initialization(self, client: NVDClient) -> None:
        """Test NVDClient initialization."""
        assert client.api_key == "test-api-key"
        assert client.cache is not None
        assert client.rate_limiter is not None

    def test_client_without_cache(self) -> None:
        """Test NVDClient without caching."""
        client = NVDClient(api_key="test-key", cache_dir=None)
        assert client.cache is None

    @mock.patch("requests.Session.get")
    def test_search_by_keyword(
        self, mock_get: mock.Mock, client: NVDClient, mock_response: dict
    ) -> None:
        """Test search_by_keyword method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        results = client.search_by_keyword("log4j")

        assert len(results) == 1
        assert results[0].cve_id == "CVE-2021-44228"
        assert results[0].cvss_score == 10.0
        assert results[0].cvss_severity == "CRITICAL"
        assert "log4j" in results[0].affected_cpes[0]

    @mock.patch("requests.Session.get")
    def test_search_by_cpe(
        self, mock_get: mock.Mock, client: NVDClient, mock_response: dict
    ) -> None:
        """Test search_by_cpe method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        results = client.search_by_cpe("cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*")

        assert len(results) == 1
        assert results[0].cve_id == "CVE-2021-44228"

    @mock.patch("requests.Session.get")
    def test_get_cve(self, mock_get: mock.Mock, client: NVDClient, mock_response: dict) -> None:
        """Test get_cve method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = client.get_cve("CVE-2021-44228")

        assert result is not None
        assert result.cve_id == "CVE-2021-44228"

    @mock.patch("requests.Session.get")
    def test_get_cve_not_found(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test get_cve returns None for nonexistent CVE."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"vulnerabilities": [], "totalResults": 0}

        result = client.get_cve("CVE-9999-99999")

        assert result is None

    @mock.patch("requests.Session.get")
    def test_rate_limit_error(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test rate limit error handling."""
        mock_get.return_value.status_code = 403

        with pytest.raises(NVDRateLimitError):
            client.search_by_keyword("test")

    @mock.patch("requests.Session.get")
    def test_api_error(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test API error handling."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        with pytest.raises(NVDAPIError) as exc_info:
            client.search_by_keyword("test")

        assert exc_info.value.status_code == 500

    @mock.patch("requests.Session.get")
    def test_timeout_retry(
        self, mock_get: mock.Mock, client: NVDClient, mock_response: dict
    ) -> None:
        """Test timeout with retry."""
        # First two calls timeout, third succeeds
        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout"),
            mock.Mock(status_code=200, json=lambda: mock_response),
        ]

        results = client.search_by_keyword("log4j")
        assert len(results) == 1

    @mock.patch("requests.Session.get")
    def test_connection_error_retry(
        self, mock_get: mock.Mock, client: NVDClient, mock_response: dict
    ) -> None:
        """Test connection error with retry."""
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            mock.Mock(status_code=200, json=lambda: mock_response),
        ]

        results = client.search_by_keyword("log4j")
        assert len(results) == 1

    @mock.patch("requests.Session.get")
    def test_cache_hit(self, mock_get: mock.Mock, client: NVDClient, mock_response: dict) -> None:
        """Test cache hit avoids API call."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # First call - cache miss
        client.search_by_keyword("log4j")
        assert mock_get.call_count == 1

        # Second call - cache hit
        client.search_by_keyword("log4j")
        assert mock_get.call_count == 1  # No additional call

    @mock.patch("requests.Session.get")
    def test_parse_cvss_v30_fallback(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test CVSS v3.0 fallback when v3.1 not available."""
        response = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2020-12345",
                        "descriptions": [{"lang": "en", "value": "Test vulnerability"}],
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
                        "published": "2020-01-01T00:00:00Z",
                        "lastModified": "2020-01-01T00:00:00Z",
                    }
                }
            ]
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = response

        results = client.search_by_keyword("test")
        assert results[0].cvss_score == 7.5
        assert results[0].cvss_severity == "HIGH"

    @mock.patch("requests.Session.get")
    def test_search_by_date_range(
        self, mock_get: mock.Mock, client: NVDClient, mock_response: dict
    ) -> None:
        """Test search_by_date_range method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        start_date = datetime(2021, 12, 1, tzinfo=timezone.utc)
        end_date = datetime(2021, 12, 31, tzinfo=timezone.utc)

        results = client.search_by_date_range(start_date, end_date)

        assert len(results) == 1
        # Verify date parameters were passed
        call_kwargs = mock_get.call_args
        assert "lastModStartDate" in call_kwargs.kwargs["params"]
        assert "lastModEndDate" in call_kwargs.kwargs["params"]

    @mock.patch("requests.Session.get")
    def test_get_total_results(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test get_total_results method."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"totalResults": 42, "vulnerabilities": []}

        total = client.get_total_results("log4j")

        assert total == 42

    @mock.patch("requests.Session.get")
    def test_search_all_by_keyword_pagination(self, mock_get: mock.Mock, client: NVDClient) -> None:
        """Test search_all_by_keyword with pagination."""

        # Create mock responses for pagination
        def create_cve_response(cve_id: str) -> dict:
            return {
                "cve": {
                    "id": cve_id,
                    "descriptions": [{"lang": "en", "value": "Test"}],
                    "metrics": {},
                    "configurations": [],
                    "references": [],
                    "published": "2021-01-01T00:00:00Z",
                    "lastModified": "2021-01-01T00:00:00Z",
                }
            }

        # First page returns 100 results
        page1 = {"vulnerabilities": [create_cve_response(f"CVE-2021-{i:05d}") for i in range(100)]}
        # Second page returns 50 results (less than page size, indicating end)
        page2 = {
            "vulnerabilities": [create_cve_response(f"CVE-2021-{i:05d}") for i in range(100, 150)]
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [page1, page2]

        results = client.search_all_by_keyword("test", max_results=200)

        assert len(results) == 150
        assert mock_get.call_count == 2


class TestNVDClientIntegration:
    """Integration-style tests for NVDClient (still using mocks)."""

    @mock.patch("requests.Session.get")
    def test_full_workflow(self, mock_get: mock.Mock, tmp_path: Path) -> None:
        """Test a complete workflow with caching."""
        cache_dir = tmp_path / "cache"
        client = NVDClient(
            api_key="test-key",
            cache_dir=cache_dir,
            cache_ttl_hours=24,
        )

        response = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2021-44228",
                        "descriptions": [{"lang": "en", "value": "Log4j"}],
                        "metrics": {
                            "cvssMetricV31": [
                                {"cvssData": {"baseScore": 10.0, "baseSeverity": "CRITICAL"}}
                            ]
                        },
                        "configurations": [],
                        "references": [],
                        "published": "2021-12-10T00:00:00Z",
                        "lastModified": "2021-12-10T00:00:00Z",
                    }
                }
            ]
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = response

        # First search - API call made
        results1 = client.search_by_keyword("log4j")
        assert len(results1) == 1
        assert mock_get.call_count == 1

        # Second search - cache hit
        results2 = client.search_by_keyword("log4j")
        assert len(results2) == 1
        assert mock_get.call_count == 1  # No additional API call

        # Cache files should exist
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) >= 1
