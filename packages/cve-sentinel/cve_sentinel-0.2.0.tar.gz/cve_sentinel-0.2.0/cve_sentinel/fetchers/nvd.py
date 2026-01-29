"""NVD (National Vulnerability Database) API client."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from cve_sentinel.utils.cache import Cache

logger = logging.getLogger(__name__)


class NVDAPIError(Exception):
    """Exception raised for NVD API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NVDRateLimitError(NVDAPIError):
    """Exception raised when rate limit is exceeded."""

    pass


@dataclass
class CVEData:
    """CVE data from NVD.

    Attributes:
        cve_id: The CVE identifier (e.g., CVE-2021-44228).
        description: Description of the vulnerability.
        cvss_score: CVSS v3.x base score (0.0-10.0).
        cvss_severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW).
        affected_cpes: List of affected CPE URIs.
        fixed_versions: List of fixed versions if known.
        references: List of reference URLs.
        published_date: Date the CVE was published.
        last_modified: Date the CVE was last modified.
    """

    cve_id: str
    description: str
    cvss_score: Optional[float]
    cvss_severity: Optional[str]
    affected_cpes: List[str]
    fixed_versions: Optional[List[str]]
    references: List[str]
    published_date: datetime
    last_modified: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "cvss_severity": self.cvss_severity,
            "affected_cpes": self.affected_cpes,
            "fixed_versions": self.fixed_versions,
            "references": self.references,
            "published_date": self.published_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CVEData:
        """Create CVEData from dictionary."""
        return cls(
            cve_id=data["cve_id"],
            description=data["description"],
            cvss_score=data["cvss_score"],
            cvss_severity=data["cvss_severity"],
            affected_cpes=data["affected_cpes"],
            fixed_versions=data["fixed_versions"],
            references=data["references"],
            published_date=datetime.fromisoformat(data["published_date"]),
            last_modified=datetime.fromisoformat(data["last_modified"]),
        )


@dataclass
class RateLimiter:
    """Rate limiter for API requests.

    Implements a sliding window rate limiter for NVD API.
    With API key: 50 requests per 30 seconds.
    """

    max_requests: int = 50
    window_seconds: int = 30
    request_times: List[float] = field(default_factory=list)

    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Remove old requests outside the window
        self.request_times = [t for t in self.request_times if now - t < self.window_seconds]

        if len(self.request_times) >= self.max_requests:
            # Need to wait until oldest request exits the window
            oldest = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest) + 0.1
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                # Recursively check again
                self.wait_if_needed()
                return

        self.request_times.append(time.time())


class NVDClient:
    """Client for NVD API 2.0.

    This client provides methods to search and retrieve CVE data from the
    National Vulnerability Database (NVD) API.

    Attributes:
        api_key: NVD API key for authentication.
        cache: Optional cache for storing API responses.
        rate_limiter: Rate limiter to respect API limits.
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(
        self,
        api_key: str,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
    ) -> None:
        """Initialize NVD client with API key.

        Args:
            api_key: NVD API key for authentication.
            cache_dir: Directory for caching responses. If None, caching is disabled.
            cache_ttl_hours: Cache time-to-live in hours.
        """
        self.api_key = api_key
        self.cache: Optional[Cache] = None
        if cache_dir:
            self.cache = Cache(cache_dir, ttl_hours=cache_ttl_hours)
        self.rate_limiter = RateLimiter()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "apiKey": api_key,
                "Accept": "application/json",
            }
        )

    def _make_request(
        self,
        params: Dict[str, Any],
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make a request to the NVD API with retry logic.

        Args:
            params: Query parameters for the request.
            use_cache: Whether to use caching for this request.

        Returns:
            JSON response from the API.

        Raises:
            NVDAPIError: If the API request fails after retries.
            NVDRateLimitError: If rate limit is exceeded and retries fail.
        """
        # Check cache first
        cache_key = f"nvd_{hash(frozenset(params.items()))}"
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for NVD query: {params}")
                return cached

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        last_error: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Cache successful response
                    if use_cache and self.cache:
                        self.cache.set(cache_key, data)
                    return data

                elif response.status_code == 403:
                    raise NVDRateLimitError(
                        "NVD API rate limit exceeded",
                        status_code=403,
                    )

                elif response.status_code == 404:
                    # No results found - return empty response
                    return {"vulnerabilities": [], "totalResults": 0}

                else:
                    raise NVDAPIError(
                        f"NVD API error: {response.status_code} - {response.text}",
                        status_code=response.status_code,
                    )

            except requests.exceptions.Timeout as e:
                last_error = NVDAPIError(f"Request timeout: {e}")
                logger.warning(f"NVD API timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")

            except requests.exceptions.ConnectionError as e:
                last_error = NVDAPIError(f"Connection error: {e}")
                logger.warning(
                    f"NVD API connection error (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )

            except NVDRateLimitError:
                # Wait longer for rate limit errors
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (attempt + 1) * 2
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                else:
                    raise

            except NVDAPIError:
                raise

            # Wait before retry
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error or NVDAPIError("Unknown error after retries")

    def _parse_cve_item(self, cve_item: Dict[str, Any]) -> CVEData:
        """Parse a CVE item from NVD API response.

        Args:
            cve_item: Raw CVE item from API response.

        Returns:
            Parsed CVEData object.
        """
        cve = cve_item.get("cve", {})

        # Get CVE ID
        cve_id = cve.get("id", "")

        # Get description (prefer English)
        description = ""
        descriptions = cve.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        if not description and descriptions:
            description = descriptions[0].get("value", "")

        # Get CVSS score and severity (prefer v3.1, fallback to v3.0)
        cvss_score: Optional[float] = None
        cvss_severity: Optional[str] = None
        metrics = cve.get("metrics", {})

        # Try CVSS v3.1 first
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            cvss_data = cvss_v31[0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            cvss_severity = cvss_data.get("baseSeverity")
        else:
            # Fallback to CVSS v3.0
            cvss_v30 = metrics.get("cvssMetricV30", [])
            if cvss_v30:
                cvss_data = cvss_v30[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_severity = cvss_data.get("baseSeverity")

        # Get affected CPEs
        affected_cpes: List[str] = []
        configurations = cve.get("configurations", [])
        for config in configurations:
            nodes = config.get("nodes", [])
            for node in nodes:
                cpe_matches = node.get("cpeMatch", [])
                for cpe_match in cpe_matches:
                    if cpe_match.get("vulnerable", False):
                        cpe_uri = cpe_match.get("criteria", "")
                        if cpe_uri:
                            affected_cpes.append(cpe_uri)

        # Get references
        references: List[str] = []
        refs = cve.get("references", [])
        for ref in refs:
            url = ref.get("url", "")
            if url:
                references.append(url)

        # Get dates
        published_str = cve.get("published", "")
        modified_str = cve.get("lastModified", "")

        # Parse dates (handle 'Z' suffix)
        try:
            if published_str:
                published_str = published_str.replace("Z", "+00:00")
                published_date = datetime.fromisoformat(published_str)
            else:
                published_date = datetime.now(timezone.utc)
        except ValueError:
            published_date = datetime.now(timezone.utc)

        try:
            if modified_str:
                modified_str = modified_str.replace("Z", "+00:00")
                last_modified = datetime.fromisoformat(modified_str)
            else:
                last_modified = published_date
        except ValueError:
            last_modified = published_date

        return CVEData(
            cve_id=cve_id,
            description=description,
            cvss_score=cvss_score,
            cvss_severity=cvss_severity,
            affected_cpes=affected_cpes,
            fixed_versions=None,  # NVD doesn't provide this directly
            references=references,
            published_date=published_date,
            last_modified=last_modified,
        )

    def search_by_keyword(
        self,
        keyword: str,
        start_index: int = 0,
        results_per_page: int = 100,
    ) -> List[CVEData]:
        """Search CVEs by keyword.

        Args:
            keyword: Search keyword (package name, etc.).
            start_index: Starting index for pagination.
            results_per_page: Number of results per page (max 2000).

        Returns:
            List of matching CVEData objects.
        """
        params = {
            "keywordSearch": keyword,
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, 2000),
        }

        response = self._make_request(params)
        vulnerabilities = response.get("vulnerabilities", [])

        results: List[CVEData] = []
        for vuln in vulnerabilities:
            try:
                cve_data = self._parse_cve_item(vuln)
                results.append(cve_data)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse CVE item: {e}")
                continue

        return results

    def search_by_cpe(
        self,
        cpe_name: str,
        start_index: int = 0,
        results_per_page: int = 100,
    ) -> List[CVEData]:
        """Search CVEs by CPE name.

        Args:
            cpe_name: CPE URI string (e.g., cpe:2.3:a:vendor:product:*:*:*:*:*:*:*:*).
            start_index: Starting index for pagination.
            results_per_page: Number of results per page (max 2000).

        Returns:
            List of matching CVEData objects.
        """
        params = {
            "cpeName": cpe_name,
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, 2000),
        }

        response = self._make_request(params)
        vulnerabilities = response.get("vulnerabilities", [])

        results: List[CVEData] = []
        for vuln in vulnerabilities:
            try:
                cve_data = self._parse_cve_item(vuln)
                results.append(cve_data)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse CVE item: {e}")
                continue

        return results

    def search_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        start_index: int = 0,
        results_per_page: int = 100,
    ) -> List[CVEData]:
        """Search CVEs modified within a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range (defaults to now).
            start_index: Starting index for pagination.
            results_per_page: Number of results per page (max 2000).

        Returns:
            List of matching CVEData objects.
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        params = {
            "lastModStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "lastModEndDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, 2000),
        }

        response = self._make_request(params)
        vulnerabilities = response.get("vulnerabilities", [])

        results: List[CVEData] = []
        for vuln in vulnerabilities:
            try:
                cve_data = self._parse_cve_item(vuln)
                results.append(cve_data)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse CVE item: {e}")
                continue

        return results

    def get_cve(self, cve_id: str) -> Optional[CVEData]:
        """Get a specific CVE by ID.

        Args:
            cve_id: CVE identifier (e.g., CVE-2021-44228).

        Returns:
            CVEData object if found, None otherwise.
        """
        params = {"cveId": cve_id}

        try:
            response = self._make_request(params)
            vulnerabilities = response.get("vulnerabilities", [])

            if vulnerabilities:
                return self._parse_cve_item(vulnerabilities[0])
            return None

        except NVDAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def get_total_results(self, keyword: str) -> int:
        """Get total number of results for a keyword search.

        Args:
            keyword: Search keyword.

        Returns:
            Total number of matching CVEs.
        """
        params = {
            "keywordSearch": keyword,
            "startIndex": 0,
            "resultsPerPage": 1,
        }

        response = self._make_request(params, use_cache=False)
        return response.get("totalResults", 0)

    def search_all_by_keyword(
        self,
        keyword: str,
        max_results: int = 1000,
    ) -> List[CVEData]:
        """Search all CVEs by keyword with pagination.

        Args:
            keyword: Search keyword.
            max_results: Maximum number of results to return.

        Returns:
            List of all matching CVEData objects up to max_results.
        """
        all_results: List[CVEData] = []
        start_index = 0
        results_per_page = 100

        while len(all_results) < max_results:
            results = self.search_by_keyword(
                keyword,
                start_index=start_index,
                results_per_page=results_per_page,
            )

            if not results:
                break

            all_results.extend(results)
            start_index += len(results)

            # Check if we've retrieved all results
            if len(results) < results_per_page:
                break

        return all_results[:max_results]
