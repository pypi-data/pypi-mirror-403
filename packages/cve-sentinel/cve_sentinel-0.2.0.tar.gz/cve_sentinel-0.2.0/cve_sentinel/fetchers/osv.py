"""OSV (Open Source Vulnerabilities) API client."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from cve_sentinel.utils.cache import Cache

logger = logging.getLogger(__name__)


class OSVAPIError(Exception):
    """Exception raised for OSV API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class OSVVulnerability:
    """Vulnerability data from OSV.

    Attributes:
        id: The OSV identifier (e.g., GHSA-xxxx-xxxx-xxxx).
        aliases: List of aliases including CVE IDs.
        summary: Short description of the vulnerability.
        details: Detailed description of the vulnerability.
        severity: List of severity information.
        affected: List of affected packages and versions.
        fixed_versions: List of fixed versions.
        references: List of reference URLs.
        published: Date the vulnerability was published.
        modified: Date the vulnerability was last modified.
    """

    id: str
    aliases: List[str] = field(default_factory=list)
    summary: str = ""
    details: str = ""
    severity: List[Dict[str, Any]] = field(default_factory=list)
    affected: List[Dict[str, Any]] = field(default_factory=list)
    fixed_versions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    published: Optional[datetime] = None
    modified: Optional[datetime] = None

    def get_cve_ids(self) -> List[str]:
        """Extract CVE IDs from aliases.

        Returns:
            List of CVE IDs found in aliases.
        """
        return [alias for alias in self.aliases if alias.startswith("CVE-")]

    def get_cvss_score(self) -> Optional[float]:
        """Extract CVSS score from severity data.

        Returns:
            CVSS score if available, None otherwise.
        """
        for sev in self.severity:
            if sev.get("type") == "CVSS_V3":
                score = sev.get("score")
                if score is not None:
                    # OSV API may return CVSS vector string instead of numeric score
                    if isinstance(score, (int, float)):
                        return float(score)
                    elif isinstance(score, str):
                        # Skip CVSS vector strings (e.g., "CVSS:3.1/AV:N/AC:L/...")
                        if score.startswith("CVSS:"):
                            continue
                        # Try to parse numeric string
                        try:
                            return float(score)
                        except ValueError:
                            continue
        return None

    def get_cvss_severity(self) -> Optional[str]:
        """Get CVSS severity level based on score.

        Returns:
            Severity level (CRITICAL, HIGH, MEDIUM, LOW, NONE) or None.
        """
        score = self.get_cvss_score()
        if score is None:
            return None

        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        elif score >= 0.1:
            return "LOW"
        else:
            return "NONE"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "aliases": self.aliases,
            "summary": self.summary,
            "details": self.details,
            "severity": self.severity,
            "affected": self.affected,
            "fixed_versions": self.fixed_versions,
            "references": self.references,
            "published": self.published.isoformat() if self.published else None,
            "modified": self.modified.isoformat() if self.modified else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OSVVulnerability:
        """Create OSVVulnerability from dictionary."""
        published = None
        modified = None

        if data.get("published"):
            published = datetime.fromisoformat(data["published"].replace("Z", "+00:00"))
        if data.get("modified"):
            modified = datetime.fromisoformat(data["modified"].replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            aliases=data.get("aliases", []),
            summary=data.get("summary", ""),
            details=data.get("details", ""),
            severity=data.get("severity", []),
            affected=data.get("affected", []),
            fixed_versions=data.get("fixed_versions", []),
            references=data.get("references", []),
            published=published,
            modified=modified,
        )


class OSVClient:
    """Client for Google OSV API.

    This client provides methods to query vulnerability data from the
    Open Source Vulnerabilities (OSV) database.

    Attributes:
        cache: Optional cache for storing API responses.
    """

    BASE_URL = "https://api.osv.dev/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 5
    RETRY_DELAY = 2
    MAX_BATCH_SIZE = 100  # Limit batch size to avoid rate limits

    # Ecosystem mapping from internal names to OSV ecosystem names
    ECOSYSTEM_MAP: Dict[str, str] = {
        "npm": "npm",
        "pypi": "PyPI",
        "go": "Go",
        "maven": "Maven",
        "rubygems": "RubyGems",
        "crates.io": "crates.io",
        "packagist": "Packagist",
        "nuget": "NuGet",
        "hex": "Hex",
        "pub": "Pub",
        "cocoapods": "CocoaPods",
        "swift": "SwiftURL",
    }

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
    ) -> None:
        """Initialize OSV client.

        Args:
            cache_dir: Directory for caching responses. If None, caching is disabled.
            cache_ttl_hours: Cache time-to-live in hours.
        """
        self.cache: Optional[Cache] = None
        if cache_dir:
            self.cache = Cache(cache_dir, ttl_hours=cache_ttl_hours)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _get_osv_ecosystem(self, ecosystem: str) -> str:
        """Convert internal ecosystem name to OSV ecosystem name.

        Args:
            ecosystem: Internal ecosystem name.

        Returns:
            OSV ecosystem name.

        Raises:
            ValueError: If ecosystem is not supported.
        """
        ecosystem_lower = ecosystem.lower()
        if ecosystem_lower in self.ECOSYSTEM_MAP:
            return self.ECOSYSTEM_MAP[ecosystem_lower]
        # If already in OSV format, return as-is
        if ecosystem in self.ECOSYSTEM_MAP.values():
            return ecosystem
        raise ValueError(f"Unsupported ecosystem: {ecosystem}")

    def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make a POST request to the OSV API with retry logic.

        Args:
            endpoint: API endpoint path.
            data: JSON data to send in the request body.
            use_cache: Whether to use caching for this request.

        Returns:
            JSON response from the API.

        Raises:
            OSVAPIError: If the API request fails after retries.
        """
        import json
        import time

        url = f"{self.BASE_URL}{endpoint}"

        # Check cache first
        cache_key = f"osv_{endpoint}_{hash(json.dumps(data, sort_keys=True))}"
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for OSV query: {data}")
                return cached

        last_error: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._session.post(
                    url,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT,
                )

                if response.status_code == 200:
                    result = response.json()
                    # Cache successful response
                    if use_cache and self.cache:
                        self.cache.set(cache_key, result)
                    return result

                elif response.status_code == 400:
                    # Check if it's a rate limit error
                    if "Too many queries" in response.text:
                        last_error = OSVAPIError(
                            f"OSV API rate limit: {response.text}",
                            status_code=400,
                        )
                        logger.warning(
                            f"OSV API rate limited (attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        # Wait longer for rate limit
                        if attempt < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY * (attempt + 2) * 2)
                        continue
                    # Bad request - don't retry
                    raise OSVAPIError(
                        f"OSV API bad request: {response.text}",
                        status_code=400,
                    )

                elif response.status_code == 429:
                    # Rate limit - retry with backoff
                    last_error = OSVAPIError(
                        f"OSV API rate limit: {response.text}",
                        status_code=429,
                    )
                    logger.warning(
                        f"OSV API rate limited (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY * (attempt + 2) * 2)
                    continue

                elif response.status_code == 404:
                    # No results found - return empty response
                    return {"vulns": []}

                else:
                    raise OSVAPIError(
                        f"OSV API error: {response.status_code} - {response.text}",
                        status_code=response.status_code,
                    )

            except requests.exceptions.Timeout as e:
                last_error = OSVAPIError(f"Request timeout: {e}")
                logger.warning(f"OSV API timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")

            except requests.exceptions.ConnectionError as e:
                last_error = OSVAPIError(f"Connection error: {e}")
                logger.warning(
                    f"OSV API connection error (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )

            except OSVAPIError:
                raise

            # Wait before retry
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error or OSVAPIError("Unknown error after retries")

    def _parse_vulnerability(self, vuln_data: Dict[str, Any]) -> OSVVulnerability:
        """Parse a vulnerability from OSV API response.

        Args:
            vuln_data: Raw vulnerability data from API response.

        Returns:
            Parsed OSVVulnerability object.
        """
        # Extract fixed versions from affected packages
        fixed_versions: List[str] = []
        affected = vuln_data.get("affected", [])
        for aff in affected:
            ranges = aff.get("ranges", [])
            for r in ranges:
                events = r.get("events", [])
                for event in events:
                    if "fixed" in event:
                        fixed_versions.append(event["fixed"])

        # Extract references
        references: List[str] = []
        refs = vuln_data.get("references", [])
        for ref in refs:
            url = ref.get("url", "")
            if url:
                references.append(url)

        # Parse dates
        published = None
        modified = None
        try:
            if vuln_data.get("published"):
                pub_str = vuln_data["published"].replace("Z", "+00:00")
                published = datetime.fromisoformat(pub_str)
        except (ValueError, TypeError):
            pass

        try:
            if vuln_data.get("modified"):
                mod_str = vuln_data["modified"].replace("Z", "+00:00")
                modified = datetime.fromisoformat(mod_str)
        except (ValueError, TypeError):
            pass

        return OSVVulnerability(
            id=vuln_data.get("id", ""),
            aliases=vuln_data.get("aliases", []),
            summary=vuln_data.get("summary", ""),
            details=vuln_data.get("details", ""),
            severity=vuln_data.get("severity", []),
            affected=affected,
            fixed_versions=fixed_versions,
            references=references,
            published=published,
            modified=modified,
        )

    def query(
        self,
        package_name: str,
        ecosystem: str,
        version: Optional[str] = None,
    ) -> List[OSVVulnerability]:
        """Query vulnerabilities for a package.

        Args:
            package_name: Name of the package.
            ecosystem: Package ecosystem (e.g., 'npm', 'pypi').
            version: Optional specific version to query.

        Returns:
            List of vulnerabilities affecting the package.
        """
        try:
            osv_ecosystem = self._get_osv_ecosystem(ecosystem)
        except ValueError as e:
            logger.warning(f"Skipping unsupported ecosystem: {e}")
            return []

        data: Dict[str, Any] = {
            "package": {
                "name": package_name,
                "ecosystem": osv_ecosystem,
            }
        }

        if version:
            data["version"] = version

        response = self._make_request("/query", data)
        vulns = response.get("vulns", [])

        results: List[OSVVulnerability] = []
        for vuln_data in vulns:
            try:
                vuln = self._parse_vulnerability(vuln_data)
                results.append(vuln)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse OSV vulnerability: {e}")
                continue

        return results

    def query_batch(
        self,
        packages: List[Dict[str, Any]],
    ) -> Dict[str, List[OSVVulnerability]]:
        """Query vulnerabilities for multiple packages.

        Args:
            packages: List of package dictionaries with 'name', 'ecosystem',
                     and optional 'version' keys.

        Returns:
            Dictionary mapping package names to their vulnerabilities.
        """
        if not packages:
            return {}

        # Build batch query
        queries: List[Dict[str, Any]] = []
        package_keys: List[str] = []

        for pkg in packages:
            name = pkg.get("name", "")
            ecosystem = pkg.get("ecosystem", "")
            version = pkg.get("version")

            try:
                osv_ecosystem = self._get_osv_ecosystem(ecosystem)
            except ValueError as e:
                logger.warning(f"Skipping unsupported ecosystem: {e}")
                continue

            query: Dict[str, Any] = {
                "package": {
                    "name": name,
                    "ecosystem": osv_ecosystem,
                }
            }

            if version:
                query["version"] = version

            queries.append(query)
            package_keys.append(f"{ecosystem}:{name}")

        if not queries:
            return {}

        results: Dict[str, List[OSVVulnerability]] = {}

        # Split into chunks to avoid rate limits
        import time

        for chunk_start in range(0, len(queries), self.MAX_BATCH_SIZE):
            chunk_end = min(chunk_start + self.MAX_BATCH_SIZE, len(queries))
            chunk_queries = queries[chunk_start:chunk_end]
            chunk_keys = package_keys[chunk_start:chunk_end]

            # Add delay between chunks (except for first chunk)
            if chunk_start > 0:
                time.sleep(1)

            data = {"queries": chunk_queries}
            response = self._make_request("/querybatch", data, use_cache=False)

            batch_results = response.get("results", [])

            for i, result in enumerate(batch_results):
                if i >= len(chunk_keys):
                    break

                pkg_key = chunk_keys[i]
                vulns = result.get("vulns", [])

                pkg_vulns: List[OSVVulnerability] = []
                for vuln_data in vulns:
                    vuln_id = vuln_data.get("id")
                    if not vuln_id:
                        continue

                    # querybatch only returns ID and modified date, not full details
                    # We need to fetch full vulnerability data for affected version info
                    try:
                        full_vuln = self.get_vulnerability(vuln_id)
                        if full_vuln:
                            pkg_vulns.append(full_vuln)
                    except (OSVAPIError, KeyError, ValueError) as e:
                        logger.warning(f"Failed to fetch vulnerability {vuln_id}: {e}")
                        continue

                results[pkg_key] = pkg_vulns

        return results

    def get_vulnerability(self, vuln_id: str) -> Optional[OSVVulnerability]:
        """Get a specific vulnerability by ID.

        Args:
            vuln_id: Vulnerability ID (e.g., GHSA-xxxx-xxxx-xxxx).

        Returns:
            OSVVulnerability object if found, None otherwise.
        """
        # Check cache first
        cache_key = f"osv_vuln_{vuln_id}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for vulnerability: {vuln_id}")
                return self._parse_vulnerability(cached)

        url = f"{self.BASE_URL}/vulns/{vuln_id}"

        try:
            response = self._session.get(url, timeout=self.DEFAULT_TIMEOUT)

            if response.status_code == 200:
                vuln_data = response.json()
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, vuln_data)
                return self._parse_vulnerability(vuln_data)
            elif response.status_code == 404:
                return None
            else:
                raise OSVAPIError(
                    f"OSV API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except requests.exceptions.RequestException as e:
            raise OSVAPIError(f"Request failed: {e}")

    @staticmethod
    def get_supported_ecosystems() -> List[str]:
        """Get list of supported ecosystems.

        Returns:
            List of supported ecosystem names.
        """
        return list(OSVClient.ECOSYSTEM_MAP.keys())


@dataclass
class MergedVulnerability:
    """Merged vulnerability data from NVD and OSV.

    Attributes:
        cve_id: CVE identifier (primary key).
        osv_ids: List of OSV identifiers.
        description: Description (OSV summary preferred, NVD fallback).
        cvss_score: CVSS score (NVD preferred).
        cvss_severity: Severity level.
        affected_packages: List of affected package info.
        fixed_versions: List of fixed versions (from OSV).
        references: Combined reference URLs.
        published_date: Publication date.
        last_modified: Last modification date.
        source: Primary data source ('nvd', 'osv', 'merged').
    """

    cve_id: str
    osv_ids: List[str] = field(default_factory=list)
    description: str = ""
    cvss_score: Optional[float] = None
    cvss_severity: Optional[str] = None
    affected_packages: List[Dict[str, Any]] = field(default_factory=list)
    fixed_versions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    published_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    source: str = "osv"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cve_id": self.cve_id,
            "osv_ids": self.osv_ids,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "cvss_severity": self.cvss_severity,
            "affected_packages": self.affected_packages,
            "fixed_versions": self.fixed_versions,
            "references": self.references,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "source": self.source,
        }


def merge_nvd_osv_data(
    osv_vulns: List[OSVVulnerability],
    nvd_client: Optional[Any] = None,
) -> List[MergedVulnerability]:
    """Merge OSV vulnerabilities with NVD data.

    OSV data is preferred for:
    - Fixed versions
    - Package-specific affected info

    NVD data is preferred for:
    - CVSS scores (more authoritative)
    - Detailed descriptions

    Args:
        osv_vulns: List of OSV vulnerabilities.
        nvd_client: Optional NVD client for fetching additional data.

    Returns:
        List of merged vulnerability records.
    """
    merged: Dict[str, MergedVulnerability] = {}

    for osv_vuln in osv_vulns:
        cve_ids = osv_vuln.get_cve_ids()

        if cve_ids:
            # Has CVE ID(s) - use first CVE as primary key
            primary_cve = cve_ids[0]

            if primary_cve in merged:
                # Merge with existing entry
                existing = merged[primary_cve]
                if osv_vuln.id not in existing.osv_ids:
                    existing.osv_ids.append(osv_vuln.id)
                existing.fixed_versions = list(
                    set(existing.fixed_versions + osv_vuln.fixed_versions)
                )
                existing.references = list(set(existing.references + osv_vuln.references))
            else:
                # Create new merged entry
                merged[primary_cve] = MergedVulnerability(
                    cve_id=primary_cve,
                    osv_ids=[osv_vuln.id],
                    description=osv_vuln.summary or osv_vuln.details,
                    cvss_score=osv_vuln.get_cvss_score(),
                    cvss_severity=osv_vuln.get_cvss_severity(),
                    affected_packages=osv_vuln.affected,
                    fixed_versions=osv_vuln.fixed_versions,
                    references=osv_vuln.references,
                    published_date=osv_vuln.published,
                    last_modified=osv_vuln.modified,
                    source="osv",
                )
        else:
            # No CVE ID - use OSV ID as key
            merged[osv_vuln.id] = MergedVulnerability(
                cve_id=osv_vuln.id,  # Use OSV ID as identifier
                osv_ids=[osv_vuln.id],
                description=osv_vuln.summary or osv_vuln.details,
                cvss_score=osv_vuln.get_cvss_score(),
                cvss_severity=osv_vuln.get_cvss_severity(),
                affected_packages=osv_vuln.affected,
                fixed_versions=osv_vuln.fixed_versions,
                references=osv_vuln.references,
                published_date=osv_vuln.published,
                last_modified=osv_vuln.modified,
                source="osv",
            )

    # Optionally enrich with NVD data
    if nvd_client:
        for cve_id, merged_vuln in merged.items():
            if cve_id.startswith("CVE-"):
                try:
                    nvd_data = nvd_client.get_cve(cve_id)
                    if nvd_data:
                        # Prefer NVD CVSS score
                        if nvd_data.cvss_score is not None:
                            merged_vuln.cvss_score = nvd_data.cvss_score
                            merged_vuln.cvss_severity = nvd_data.cvss_severity

                        # Use NVD description if OSV is empty
                        if not merged_vuln.description and nvd_data.description:
                            merged_vuln.description = nvd_data.description

                        # Merge references
                        merged_vuln.references = list(
                            set(merged_vuln.references + nvd_data.references)
                        )

                        merged_vuln.source = "merged"
                except Exception as e:
                    logger.warning(f"Failed to fetch NVD data for {cve_id}: {e}")

    return list(merged.values())
