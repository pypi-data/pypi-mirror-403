"""Combined vulnerability matcher using both OSV and NVD data sources.

This module provides a matcher that:
1. Uses OSV as the primary source (high precision, package-aware)
2. Supplements with NVD keyword search (broader coverage, filtered for accuracy)
3. Deduplicates and merges results with confidence scoring
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from cve_sentinel.analyzers.base import Package
from cve_sentinel.fetchers.nvd import NVDClient
from cve_sentinel.fetchers.nvd_package_matcher import (
    ConfidenceLevel,
    CVEMatchResult,
    NVDPackageMatcher,
)
from cve_sentinel.fetchers.osv import OSVClient, OSVVulnerability
from cve_sentinel.matcher import VersionMatcher, VulnerabilityMatch

logger = logging.getLogger(__name__)


@dataclass
class CombinedVulnerabilityMatch(VulnerabilityMatch):
    """Extended vulnerability match with source tracking."""

    source: str = "unknown"  # "osv", "nvd", "both"
    confidence: str = "high"  # "high", "medium", "low"
    nvd_verified: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        base = super().to_dict()
        base["source"] = self.source
        base["confidence"] = self.confidence
        base["nvd_verified"] = self.nvd_verified
        return base


class CombinedVulnerabilityMatcher:
    """Matches packages against both OSV and NVD databases.

    Strategy:
    1. Query OSV for each package (high precision)
    2. Query NVD with keyword search and filter results (broader coverage)
    3. Merge results, preferring OSV data when available
    4. Assign confidence scores based on data source agreement
    """

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
        nvd_min_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ) -> None:
        """Initialize combined matcher.

        Args:
            nvd_client: NVD API client.
            osv_client: OSV API client.
            nvd_min_confidence: Minimum confidence level for NVD-only results.
        """
        self.nvd_client = nvd_client
        self.osv_client = osv_client
        self.nvd_min_confidence = nvd_min_confidence

        self._nvd_matcher: Optional[NVDPackageMatcher] = None
        if nvd_client:
            self._nvd_matcher = NVDPackageMatcher(nvd_client)

        self._seen_vulns: Set[str] = set()

    def match(self, packages: List[Package]) -> List[CombinedVulnerabilityMatch]:
        """Match packages against both OSV and NVD.

        Args:
            packages: List of packages to check.

        Returns:
            List of combined vulnerability matches.
        """
        self._seen_vulns.clear()
        all_matches: Dict[str, CombinedVulnerabilityMatch] = {}

        # Group packages by ecosystem
        packages_by_ecosystem: Dict[str, List[Package]] = {}
        for pkg in packages:
            if pkg.ecosystem not in packages_by_ecosystem:
                packages_by_ecosystem[pkg.ecosystem] = []
            packages_by_ecosystem[pkg.ecosystem].append(pkg)

        for _ecosystem, eco_packages in packages_by_ecosystem.items():
            for pkg in eco_packages:
                # Step 1: Query OSV (primary source)
                osv_matches = self._match_osv(pkg)
                for match in osv_matches:
                    key = f"{match.cve_id}:{pkg.name}:{pkg.ecosystem}"
                    if key not in all_matches:
                        all_matches[key] = match

                # Step 2: Query NVD with filtering (supplementary)
                if self._nvd_matcher:
                    nvd_matches = self._match_nvd(pkg)
                    for match in nvd_matches:
                        key = f"{match.cve_id}:{pkg.name}:{pkg.ecosystem}"
                        if key in all_matches:
                            # Already found by OSV - mark as verified by both sources
                            existing = all_matches[key]
                            existing.source = "both"
                            existing.nvd_verified = True
                            existing.confidence = "high"
                            # Update CVSS if NVD has better data
                            if match.cvss_score and (not existing.cvss_score):
                                existing.cvss_score = match.cvss_score
                                existing.severity = match.severity
                        else:
                            # New from NVD only
                            all_matches[key] = match

        return list(all_matches.values())

    def _match_osv(self, package: Package) -> List[CombinedVulnerabilityMatch]:
        """Match package against OSV database.

        Args:
            package: Package to check.

        Returns:
            List of vulnerability matches from OSV.
        """
        if not self.osv_client:
            return []

        matches: List[CombinedVulnerabilityMatch] = []

        try:
            vulns = self.osv_client.query(
                package_name=package.name,
                ecosystem=package.ecosystem,
                version=package.version if package.version != "*" else None,
            )

            for osv_vuln in vulns:
                match = self._process_osv_vulnerability(package, osv_vuln)
                if match:
                    matches.append(match)

        except Exception as e:
            logger.warning(f"Error querying OSV for {package.name}: {e}")

        return matches

    def _process_osv_vulnerability(
        self,
        package: Package,
        osv_vuln: OSVVulnerability,
    ) -> Optional[CombinedVulnerabilityMatch]:
        """Process an OSV vulnerability into a match.

        Args:
            package: The affected package.
            osv_vuln: OSV vulnerability data.

        Returns:
            CombinedVulnerabilityMatch if affected, None otherwise.
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

        # Skip duplicates
        if primary_id in self._seen_vulns:
            return None
        self._seen_vulns.add(primary_id)

        # Get severity info
        cvss_score = osv_vuln.get_cvss_score()
        severity = osv_vuln.get_cvss_severity() or "UNKNOWN"
        description = osv_vuln.summary or osv_vuln.details

        # Use fix version from OSV
        if not fix_version and osv_vuln.fixed_versions:
            fix_version = osv_vuln.fixed_versions[0]

        # Generate fix command
        fix_command = None
        if fix_version:
            fix_command = self._generate_fix_command(package, fix_version)

        # Build affected files info
        affected_files = []
        if package.source_file:
            affected_files.append(
                {
                    "file": str(package.source_file),
                    "line": package.source_line,
                }
            )

        return CombinedVulnerabilityMatch(
            cve_id=primary_id,
            osv_id=osv_vuln.id if osv_vuln.id != primary_id else None,
            package=package,
            severity=severity,
            cvss_score=cvss_score,
            description=description[:500] if description else "",
            fix_version=fix_version,
            fix_command=fix_command,
            affected_files=affected_files,
            references=osv_vuln.references[:5],
            source="osv",
            confidence="high",
            nvd_verified=False,
        )

    def _match_nvd(self, package: Package) -> List[CombinedVulnerabilityMatch]:
        """Match package against NVD database with filtering.

        Args:
            package: Package to check.

        Returns:
            List of vulnerability matches from NVD.
        """
        if not self._nvd_matcher:
            return []

        matches: List[CombinedVulnerabilityMatch] = []

        try:
            # Search NVD and filter by confidence
            nvd_results = self._nvd_matcher.search_and_filter(
                package_name=package.name,
                ecosystem=package.ecosystem,
                package_version=package.version,
                min_confidence=self.nvd_min_confidence,
            )

            for result in nvd_results:
                if result.cve_id in self._seen_vulns:
                    continue

                match = self._process_nvd_result(package, result)
                if match:
                    matches.append(match)
                    self._seen_vulns.add(result.cve_id)

        except Exception as e:
            logger.warning(f"Error querying NVD for {package.name}: {e}")

        return matches

    def _process_nvd_result(
        self,
        package: Package,
        result: CVEMatchResult,
    ) -> Optional[CombinedVulnerabilityMatch]:
        """Process an NVD match result into a vulnerability match.

        Args:
            package: The affected package.
            result: NVD match result.

        Returns:
            CombinedVulnerabilityMatch if valid, None otherwise.
        """
        if not result.cve_data:
            return None

        cve = result.cve_data

        # Map confidence level
        confidence_map = {
            ConfidenceLevel.HIGH: "high",
            ConfidenceLevel.MEDIUM: "medium",
            ConfidenceLevel.LOW: "low",
        }
        confidence = confidence_map.get(result.confidence, "low")

        # Build affected files info
        affected_files = []
        if package.source_file:
            affected_files.append(
                {
                    "file": str(package.source_file),
                    "line": package.source_line,
                }
            )

        return CombinedVulnerabilityMatch(
            cve_id=cve.cve_id,
            osv_id=None,
            package=package,
            severity=cve.cvss_severity or "UNKNOWN",
            cvss_score=cve.cvss_score,
            description=cve.description[:500] if cve.description else "",
            fix_version=None,  # NVD doesn't provide this
            fix_command=None,
            affected_files=affected_files,
            references=cve.references[:5],
            source="nvd",
            confidence=confidence,
            nvd_verified=True,
        )

    def _generate_fix_command(
        self,
        package: Package,
        fix_version: str,
    ) -> Optional[str]:
        """Generate fix command for a package.

        Args:
            package: The package to fix.
            fix_version: The version to upgrade to.

        Returns:
            Fix command string or None.
        """
        template = self.FIX_COMMANDS.get(package.ecosystem)
        if template:
            return template.format(package=package.name, version=fix_version)
        return None

    def get_statistics(
        self,
        matches: List[CombinedVulnerabilityMatch],
    ) -> Dict:
        """Get statistics about the matches.

        Args:
            matches: List of vulnerability matches.

        Returns:
            Dictionary with statistics.
        """
        stats = {
            "total": len(matches),
            "by_source": {
                "osv_only": sum(1 for m in matches if m.source == "osv"),
                "nvd_only": sum(1 for m in matches if m.source == "nvd"),
                "both": sum(1 for m in matches if m.source == "both"),
            },
            "by_confidence": {
                "high": sum(1 for m in matches if m.confidence == "high"),
                "medium": sum(1 for m in matches if m.confidence == "medium"),
                "low": sum(1 for m in matches if m.confidence == "low"),
            },
            "by_severity": {
                "CRITICAL": sum(1 for m in matches if m.severity == "CRITICAL"),
                "HIGH": sum(1 for m in matches if m.severity == "HIGH"),
                "MEDIUM": sum(1 for m in matches if m.severity == "MEDIUM"),
                "LOW": sum(1 for m in matches if m.severity == "LOW"),
                "UNKNOWN": sum(1 for m in matches if m.severity in ("UNKNOWN", None)),
            },
        }
        return stats
