"""Vulnerability matcher for correlating packages with CVEs."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from packaging.version import InvalidVersion, Version

from cve_sentinel.analyzers.base import Package
from cve_sentinel.fetchers.nvd import CVEData, NVDClient
from cve_sentinel.fetchers.osv import OSVClient, OSVVulnerability

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityMatch:
    """Represents a matched vulnerability for a package."""

    cve_id: str
    package: Package
    severity: str
    cvss_score: Optional[float]
    description: str
    fix_version: Optional[str]
    fix_command: Optional[str]
    affected_files: List[Dict] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    osv_id: Optional[str] = None

    def __hash__(self) -> int:
        return hash((self.cve_id, self.package.name, self.package.ecosystem))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VulnerabilityMatch):
            return False
        return (
            self.cve_id == other.cve_id
            and self.package.name == other.package.name
            and self.package.ecosystem == other.package.ecosystem
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "cve_id": self.cve_id,
            "osv_id": self.osv_id,
            "package": {
                "name": self.package.name,
                "version": self.package.version,
                "ecosystem": self.package.ecosystem,
            },
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "description": self.description,
            "fix_version": self.fix_version,
            "fix_command": self.fix_command,
            "affected_files": self.affected_files,
            "references": self.references,
        }


class VersionMatcher:
    """Utility class for version comparison and matching."""

    @staticmethod
    def parse_version(version_str: str) -> Optional[Version]:
        """Parse a version string into a Version object.

        Args:
            version_str: Version string to parse.

        Returns:
            Version object if parseable, None otherwise.
        """
        if not version_str or version_str == "*":
            return None

        # Clean up version string
        version_str = version_str.strip()
        # Remove leading 'v' if present
        if version_str.startswith("v"):
            version_str = version_str[1:]

        try:
            return Version(version_str)
        except InvalidVersion:
            # Try to extract a valid version
            match = re.match(r"^(\d+(?:\.\d+)*)", version_str)
            if match:
                try:
                    return Version(match.group(1))
                except InvalidVersion:
                    pass
            logger.debug(f"Could not parse version: {version_str}")
            return None

    @staticmethod
    def is_version_affected(
        version: str,
        affected_ranges: List[Dict],
    ) -> Tuple[bool, Optional[str]]:
        """Check if a version is affected by the vulnerability.

        Args:
            version: The version to check.
            affected_ranges: List of affected version ranges from OSV.

        Returns:
            Tuple of (is_affected, fix_version).
        """
        parsed_version = VersionMatcher.parse_version(version)
        if parsed_version is None:
            # Can't determine, assume affected
            return True, None

        fix_version: Optional[str] = None

        for affected in affected_ranges:
            ranges = affected.get("ranges", [])
            versions = affected.get("versions", [])

            # Check explicit version list
            if versions:
                if version in versions:
                    # Find fix version from ranges
                    for r in ranges:
                        events = r.get("events", [])
                        for event in events:
                            if "fixed" in event:
                                fix_version = event["fixed"]
                    return True, fix_version

            # Check version ranges
            for r in ranges:
                range_type = r.get("type", "")
                events = r.get("events", [])

                introduced: Optional[str] = None
                fixed: Optional[str] = None

                for event in events:
                    if "introduced" in event:
                        introduced = event["introduced"]
                    if "fixed" in event:
                        fixed = event["fixed"]

                # Check if version falls within range
                if VersionMatcher._is_in_range(parsed_version, introduced, fixed, range_type):
                    return True, fixed

        return False, None

    @staticmethod
    def _is_in_range(
        version: Version,
        introduced: Optional[str],
        fixed: Optional[str],
        range_type: str,
    ) -> bool:
        """Check if version is within the affected range.

        Args:
            version: Parsed version to check.
            introduced: Version where vulnerability was introduced.
            fixed: Version where vulnerability was fixed.
            range_type: Type of range (SEMVER, ECOSYSTEM, GIT).

        Returns:
            True if version is in the affected range.
        """
        # Parse introduced version
        if introduced and introduced != "0":
            introduced_ver = VersionMatcher.parse_version(introduced)
            if introduced_ver and version < introduced_ver:
                return False

        # Parse fixed version
        if fixed:
            fixed_ver = VersionMatcher.parse_version(fixed)
            if fixed_ver and version >= fixed_ver:
                return False

        return True

    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version.
            v2: Second version.

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.
        """
        parsed_v1 = VersionMatcher.parse_version(v1)
        parsed_v2 = VersionMatcher.parse_version(v2)

        if parsed_v1 is None or parsed_v2 is None:
            return 0

        if parsed_v1 < parsed_v2:
            return -1
        elif parsed_v1 > parsed_v2:
            return 1
        return 0


class VulnerabilityMatcher:
    """Matches detected packages against known CVEs."""

    # Fix command templates by ecosystem
    FIX_COMMANDS = {
        "npm": "npm install {package}@{version}",
        "pypi": "pip install {package}=={version}",
        "go": "go get {package}@v{version}",
        "maven": "Update version in pom.xml to {version}",
        "rubygems": "bundle update {package}",
        "crates.io": "cargo update -p {package}",
        "packagist": "composer require {package}:{version}",
    }

    def __init__(
        self,
        nvd_client: Optional[NVDClient] = None,
        osv_client: Optional[OSVClient] = None,
        fetch_nvd_details: bool = True,
    ) -> None:
        """Initialize matcher with API clients.

        Args:
            nvd_client: NVD API client for CVE details.
            osv_client: OSV API client for vulnerability queries.
            fetch_nvd_details: Whether to fetch additional details from NVD.
        """
        self.nvd_client = nvd_client
        self.osv_client = osv_client
        self.fetch_nvd_details = fetch_nvd_details
        self._seen_vulns: Set[Tuple[str, str, str]] = set()

    def match(self, packages: List[Package]) -> List[VulnerabilityMatch]:
        """Match packages against known vulnerabilities.

        Args:
            packages: List of packages to check.

        Returns:
            List of vulnerability matches.
        """
        if not self.osv_client:
            logger.warning("No OSV client configured, skipping vulnerability matching")
            return []

        matches: List[VulnerabilityMatch] = []
        self._seen_vulns.clear()

        # Group packages by ecosystem for batch querying
        packages_by_ecosystem: Dict[str, List[Package]] = {}
        for pkg in packages:
            if pkg.ecosystem not in packages_by_ecosystem:
                packages_by_ecosystem[pkg.ecosystem] = []
            packages_by_ecosystem[pkg.ecosystem].append(pkg)

        # Process each package
        for ecosystem, eco_packages in packages_by_ecosystem.items():
            # Build batch query
            batch_packages = [
                {
                    "name": pkg.name,
                    "ecosystem": ecosystem,
                    "version": pkg.version if pkg.version != "*" else None,
                }
                for pkg in eco_packages
            ]

            try:
                # Query OSV for vulnerabilities
                results = self.osv_client.query_batch(batch_packages)

                # Process results
                for pkg in eco_packages:
                    pkg_key = f"{ecosystem}:{pkg.name}"
                    vulns = results.get(pkg_key, [])

                    for osv_vuln in vulns:
                        match = self._process_osv_vulnerability(pkg, osv_vuln)
                        if match:
                            matches.append(match)

            except Exception as e:
                logger.error(f"Error querying OSV for {ecosystem}: {e}")
                # Fall back to individual queries
                for pkg in eco_packages:
                    try:
                        vulns = self.osv_client.query(
                            pkg.name,
                            ecosystem,
                            pkg.version if pkg.version != "*" else None,
                        )
                        for osv_vuln in vulns:
                            match = self._process_osv_vulnerability(pkg, osv_vuln)
                            if match:
                                matches.append(match)
                    except Exception as e2:
                        logger.error(f"Error querying OSV for {pkg.name}: {e2}")

        return matches

    def _process_osv_vulnerability(
        self,
        package: Package,
        osv_vuln: OSVVulnerability,
    ) -> Optional[VulnerabilityMatch]:
        """Process an OSV vulnerability and create a match.

        Args:
            package: The affected package.
            osv_vuln: The OSV vulnerability data.

        Returns:
            VulnerabilityMatch if affected, None otherwise.
        """
        # Check version affectedness
        is_affected, fix_version = VersionMatcher.is_version_affected(
            package.version,
            osv_vuln.affected,
        )

        if not is_affected:
            return None

        # Get CVE ID (prefer CVE over GHSA/OSV ID)
        cve_ids = osv_vuln.get_cve_ids()
        primary_id = cve_ids[0] if cve_ids else osv_vuln.id

        # Check for duplicates
        vuln_key = (primary_id, package.name, package.ecosystem)
        if vuln_key in self._seen_vulns:
            return None
        self._seen_vulns.add(vuln_key)

        # Get CVSS score and severity from OSV
        cvss_score = osv_vuln.get_cvss_score()
        severity = osv_vuln.get_cvss_severity()
        description = osv_vuln.summary or osv_vuln.details
        references = osv_vuln.references

        # Try to get better data from NVD if we have a CVE ID
        if cve_ids and self.nvd_client and self.fetch_nvd_details:
            nvd_data = self._fetch_nvd_details(cve_ids[0])
            if nvd_data:
                if nvd_data.cvss_score is not None:
                    cvss_score = nvd_data.cvss_score
                if nvd_data.cvss_severity:
                    severity = nvd_data.cvss_severity
                if nvd_data.description:
                    description = nvd_data.description
                if nvd_data.references:
                    references = list(set(references + nvd_data.references))

        # Use fix version from OSV if not found in range check
        if not fix_version and osv_vuln.fixed_versions:
            fix_version = osv_vuln.fixed_versions[0]

        # Generate fix command
        fix_command = None
        if fix_version:
            fix_command = self.generate_fix_command(package, fix_version)

        # Build affected files info
        affected_files = []
        if package.source_file:
            affected_files.append(
                {
                    "file": str(package.source_file),
                    "line": package.source_line,
                }
            )

        return VulnerabilityMatch(
            cve_id=primary_id,
            osv_id=osv_vuln.id if osv_vuln.id != primary_id else None,
            package=package,
            severity=severity or "UNKNOWN",
            cvss_score=cvss_score,
            description=description[:500] if description else "",
            fix_version=fix_version,
            fix_command=fix_command,
            affected_files=affected_files,
            references=references[:5],  # Limit references
        )

    def _fetch_nvd_details(self, cve_id: str) -> Optional[CVEData]:
        """Fetch CVE details from NVD.

        Args:
            cve_id: CVE identifier.

        Returns:
            CVEData if found, None otherwise.
        """
        if not self.nvd_client:
            return None

        try:
            return self.nvd_client.get_cve(cve_id)
        except Exception as e:
            logger.debug(f"Could not fetch NVD data for {cve_id}: {e}")
            return None

    def generate_fix_command(
        self,
        package: Package,
        fix_version: str,
    ) -> Optional[str]:
        """Generate fix command for a package.

        Args:
            package: The package to fix.
            fix_version: The version to upgrade to.

        Returns:
            Fix command string or None if not supported.
        """
        template = self.FIX_COMMANDS.get(package.ecosystem)
        if template:
            return template.format(package=package.name, version=fix_version)
        return None

    def match_single(self, package: Package) -> List[VulnerabilityMatch]:
        """Match a single package against known vulnerabilities.

        Args:
            package: Package to check.

        Returns:
            List of vulnerability matches.
        """
        return self.match([package])

    def get_severity_counts(
        self,
        matches: List[VulnerabilityMatch],
    ) -> Dict[str, int]:
        """Get count of vulnerabilities by severity.

        Args:
            matches: List of vulnerability matches.

        Returns:
            Dictionary mapping severity to count.
        """
        counts: Dict[str, int] = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
        }
        for match in matches:
            severity = match.severity.upper() if match.severity else "UNKNOWN"
            if severity in counts:
                counts[severity] += 1
            else:
                counts["UNKNOWN"] += 1
        return counts

    def filter_by_severity(
        self,
        matches: List[VulnerabilityMatch],
        min_severity: str = "LOW",
    ) -> List[VulnerabilityMatch]:
        """Filter matches by minimum severity.

        Args:
            matches: List of vulnerability matches.
            min_severity: Minimum severity to include.

        Returns:
            Filtered list of matches.
        """
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        try:
            min_index = severity_order.index(min_severity.upper())
        except ValueError:
            min_index = len(severity_order) - 1

        return [
            m
            for m in matches
            if severity_order.index(m.severity.upper() if m.severity else "UNKNOWN") <= min_index
        ]
