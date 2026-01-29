"""NVD package matcher for filtering CVEs by ecosystem and package name.

This module provides functionality to verify if a CVE from NVD keyword search
actually applies to a specific package in a given ecosystem (npm, pypi, etc.).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from cve_sentinel.fetchers.nvd import CVEData, NVDClient

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level for CVE-package match."""

    HIGH = "high"  # CPE matches + ecosystem indicator
    MEDIUM = "medium"  # CPE matches package name, no ecosystem indicator
    LOW = "low"  # Keyword match only, needs manual review
    EXCLUDED = "excluded"  # Clear mismatch (hardware, different product)


@dataclass
class CVEMatchResult:
    """Result of CVE-package matching."""

    cve_id: str
    confidence: ConfidenceLevel
    matched_cpes: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    cve_data: Optional[CVEData] = None


# Ecosystem to target_sw mapping
ECOSYSTEM_TARGET_SW: Dict[str, Set[str]] = {
    "npm": {"node.js", "nodejs", "node"},
    "pypi": {"python", "python3", "pip"},
    "go": {"go", "golang"},
    "maven": {"java", "maven", "spring"},
    "rubygems": {"ruby", "rails"},
    "crates.io": {"rust", "cargo"},
    "packagist": {"php", "composer"},
}

# Keywords that indicate a hardware/non-software CVE
HARDWARE_INDICATORS = {
    "firmware",
    "chip",
    "chipset",
    "wireless",
    "bluetooth",
    "wifi",
    "hardware",
    "device",
    "driver",
    "kernel",
    "iot",
    "embedded",
    "router",
    "switch",
    "controller",
    "printer",
    "scanner",
    "semiconductor",
    "microcontroller",
    "soc",
    "fpga",
    "asic",
    "broadcom",
    "qualcomm",
    "intel",
    "amd",
    "arm",
    "mips",
}

# Known hardware vendors that should be excluded
HARDWARE_VENDORS = {
    "cypress_semiconductor",
    "cypress",
    "broadcom",
    "qualcomm",
    "intel",
    "amd",
    "nvidia",
    "texas_instruments",
    "microchip",
    "infineon",
    "nxp",
    "stmicroelectronics",
    "analog_devices",
    "maxim_integrated",
    "silicon_labs",
    "renesas",
    "mediatek",
    "realtek",
    "marvell",
    "xilinx",
    "lattice_semiconductor",
}

# Known false positive patterns: package_name -> set of vendor/product patterns to exclude
FALSE_POSITIVE_PATTERNS: Dict[str, Set[str]] = {
    "cypress": {
        "cypress_semiconductor",
        "broadcom",
        "google:android",
        "cypress_wireless",
        "cypress_bluetooth",
        "cyw",
    },
    "vite": {
        "vitec",
        "vitess",
        "vitemoneycoin",
        "vita",
        "vitero",
    },
    "passport": {
        "passport220",
        "dedos-web",
        "gamerpolls",
    },
    "express": {
        "expressvpn",
        "express_gateway",
        "american_express",
    },
}

# Known vendor mappings for popular packages
KNOWN_VENDOR_MAPPINGS: Dict[str, Set[str]] = {
    "vite": {"vitejs"},
    "vue": {"vuejs"},
    "react": {"facebook", "reactjs"},
    "angular": {"angular", "google"},
    "express": {"expressjs", "express"},
    "lodash": {"lodash"},
    "axios": {"axios"},
    "passport": {"passport_project", "jaredhanson"},
    "eslint": {"eslint", "eslint-utils_project"},
    "webpack": {"webpack", "webpack-contrib"},
    "babel": {"babel", "babeljs"},
    "typescript": {"microsoft", "typescriptlang"},
    "jest": {"facebook", "jestjs"},
    "cypress": {"cypress-io", "cypress"},
    "mocha": {"mochajs"},
}


def parse_cpe(cpe_uri: str) -> Dict[str, str]:
    """Parse CPE 2.3 URI into components.

    CPE 2.3 format: cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other

    Args:
        cpe_uri: CPE URI string.

    Returns:
        Dictionary with CPE components.
    """
    parts = cpe_uri.split(":")

    return {
        "part": parts[2] if len(parts) > 2 else "",  # a=application, o=os, h=hardware
        "vendor": parts[3] if len(parts) > 3 else "",
        "product": parts[4] if len(parts) > 4 else "",
        "version": parts[5] if len(parts) > 5 else "",
        "update": parts[6] if len(parts) > 6 else "",
        "edition": parts[7] if len(parts) > 7 else "",
        "language": parts[8] if len(parts) > 8 else "",
        "sw_edition": parts[9] if len(parts) > 9 else "",
        "target_sw": parts[10] if len(parts) > 10 else "",
        "target_hw": parts[11] if len(parts) > 11 else "",
    }


def normalize_name(name: str) -> str:
    """Normalize package/product name for comparison.

    Args:
        name: Name to normalize.

    Returns:
        Normalized name (lowercase, special chars removed).
    """
    # Remove scope for npm packages (@scope/name -> name)
    if name.startswith("@") and "/" in name:
        name = name.split("/", 1)[1]

    # Lowercase and remove special characters
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    return normalized


def check_ecosystem_match(cpe: Dict[str, str], ecosystem: str) -> bool:
    """Check if CPE target_sw matches the expected ecosystem.

    Args:
        cpe: Parsed CPE dictionary.
        ecosystem: Expected ecosystem (npm, pypi, etc.).

    Returns:
        True if ecosystem matches.
    """
    target_sw = cpe.get("target_sw", "").lower().replace("*", "")

    if not target_sw:
        return False

    expected_targets = ECOSYSTEM_TARGET_SW.get(ecosystem.lower(), set())
    return any(target in target_sw for target in expected_targets)


def check_name_match(cpe: Dict[str, str], package_name: str) -> Tuple[bool, str, bool]:
    """Check if CPE vendor/product matches the package name.

    Args:
        cpe: Parsed CPE dictionary.
        package_name: Package name to match.

    Returns:
        Tuple of (matches, reason, is_exact_match).
    """
    normalized_pkg = normalize_name(package_name)
    vendor = cpe.get("vendor", "").lower().replace("*", "").replace("_", "")
    product = cpe.get("product", "").lower().replace("*", "").replace("_", "")
    normalized_product = normalize_name(product)
    normalized_vendor = normalize_name(vendor)

    # Check known vendor mappings (exact match)
    known_vendors = KNOWN_VENDOR_MAPPINGS.get(package_name.lower(), set())
    vendor_clean = cpe.get("vendor", "").lower().replace("_", "-")

    if vendor_clean in known_vendors:
        return True, f"Known vendor mapping: {vendor_clean}", True

    # Exact product match (highest confidence)
    if normalized_pkg == normalized_product:
        return True, f"Exact product match: {product}", True

    # Product contains package name - but check for false positives
    # Package name must be a significant portion of the product name
    if normalized_pkg in normalized_product:
        # Avoid false positives like "vite" in "vitec" or "vitess"
        # Package name should be at least 50% of product name
        ratio = len(normalized_pkg) / len(normalized_product)
        if ratio >= 0.5:
            return True, f"Product contains package name: {product}", False
        # Also accept if product starts with package name
        if normalized_product.startswith(normalized_pkg):
            return True, f"Product starts with package name: {product}", False

    # Vendor exact match (less common but valid)
    if normalized_pkg == normalized_vendor:
        return True, f"Vendor name match: {vendor}", True

    return False, "No name match", False


def is_hardware_cve(cpe: Dict[str, str], description: str) -> bool:
    """Check if CVE is hardware-related based on CPE and description.

    Args:
        cpe: Parsed CPE dictionary.
        description: CVE description.

    Returns:
        True if likely hardware-related.
    """
    # Check CPE part
    if cpe.get("part") == "h":
        return True

    # Check if vendor is a known hardware vendor
    vendor = cpe.get("vendor", "").lower().replace("-", "_")
    if vendor in HARDWARE_VENDORS:
        return True

    # Check for hardware indicators in description
    desc_lower = description.lower()
    hardware_matches = sum(1 for ind in HARDWARE_INDICATORS if ind in desc_lower)

    # If multiple hardware indicators found, likely hardware CVE
    return hardware_matches >= 2


def is_false_positive(cpe: Dict[str, str], package_name: str, description: str) -> Tuple[bool, str]:
    """Check if this is a known false positive pattern.

    Args:
        cpe: Parsed CPE dictionary.
        package_name: Package name being searched.
        description: CVE description.

    Returns:
        Tuple of (is_false_positive, reason).
    """
    pkg_lower = package_name.lower()
    vendor = cpe.get("vendor", "").lower()
    product = cpe.get("product", "").lower()
    vendor_product = f"{vendor}:{product}"

    # Check known false positive patterns
    fp_patterns = FALSE_POSITIVE_PATTERNS.get(pkg_lower, set())
    for pattern in fp_patterns:
        if pattern in vendor or pattern in product or pattern in vendor_product:
            return True, f"Known false positive pattern: {pattern}"

    # Check if vendor is a hardware vendor
    if vendor.replace("-", "_") in HARDWARE_VENDORS:
        return True, f"Hardware vendor: {vendor}"

    return False, ""


def check_version_in_range(
    package_version: str,
    cpe_match: Dict[str, str],
) -> Tuple[bool, str]:
    """Check if package version falls within CPE version constraints.

    Args:
        package_version: The package version to check.
        cpe_match: CPE match data with version constraints.

    Returns:
        Tuple of (is_in_range, reason).
    """
    from packaging.version import InvalidVersion, Version

    if not package_version or package_version == "*":
        return True, "No version specified"

    # Parse package version
    try:
        # Clean version string
        version_str = package_version.strip()
        if version_str.startswith("v"):
            version_str = version_str[1:]

        pkg_ver = Version(version_str)
    except InvalidVersion:
        # Can't parse, assume affected
        return True, "Could not parse package version"

    # Get version constraints from CPE match
    version_start = cpe_match.get("versionStartIncluding", "")
    version_start_excl = cpe_match.get("versionStartExcluding", "")
    version_end = cpe_match.get("versionEndIncluding", "")
    version_end_excl = cpe_match.get("versionEndExcluding", "")

    # If no constraints, check exact version match
    cpe_version = cpe_match.get("version", "*")
    if (
        cpe_version
        and cpe_version != "*"
        and not any([version_start, version_start_excl, version_end, version_end_excl])
    ):
        try:
            cpe_ver = Version(cpe_version.replace("*", "0"))
            if pkg_ver != cpe_ver:
                return False, f"Version mismatch: {package_version} != {cpe_version}"
        except InvalidVersion:
            pass

    # Check start constraints
    if version_start:
        try:
            start_ver = Version(version_start)
            if pkg_ver < start_ver:
                return False, f"Version {package_version} < {version_start}"
        except InvalidVersion:
            pass

    if version_start_excl:
        try:
            start_ver = Version(version_start_excl)
            if pkg_ver <= start_ver:
                return False, f"Version {package_version} <= {version_start_excl}"
        except InvalidVersion:
            pass

    # Check end constraints
    if version_end:
        try:
            end_ver = Version(version_end)
            if pkg_ver > end_ver:
                return False, f"Version {package_version} > {version_end}"
        except InvalidVersion:
            pass

    if version_end_excl:
        try:
            end_ver = Version(version_end_excl)
            if pkg_ver >= end_ver:
                return False, f"Version {package_version} >= {version_end_excl}"
        except InvalidVersion:
            pass

    return True, "Version in range"


class NVDPackageMatcher:
    """Matcher for verifying CVE applicability to packages."""

    def __init__(self, nvd_client: NVDClient) -> None:
        """Initialize matcher with NVD client.

        Args:
            nvd_client: NVD API client for fetching CVE details.
        """
        self.nvd_client = nvd_client

    def match_cve_to_package(
        self,
        cve_id: str,
        package_name: str,
        ecosystem: str,
        package_version: Optional[str] = None,
    ) -> CVEMatchResult:
        """Verify if a CVE applies to a specific package.

        Args:
            cve_id: CVE identifier.
            package_name: Package name.
            ecosystem: Package ecosystem (npm, pypi, etc.).
            package_version: Optional package version for version range check.

        Returns:
            CVEMatchResult with confidence level and reasons.
        """
        cve_data = self.nvd_client.get_cve(cve_id)

        if not cve_data:
            return CVEMatchResult(
                cve_id=cve_id,
                confidence=ConfidenceLevel.EXCLUDED,
                reasons=["CVE not found in NVD"],
            )

        result = CVEMatchResult(
            cve_id=cve_id,
            confidence=ConfidenceLevel.LOW,  # Default
            cve_data=cve_data,
        )

        # No CPEs - can only rely on keyword match
        if not cve_data.affected_cpes:
            result.confidence = ConfidenceLevel.LOW
            result.reasons.append("No CPE information available - keyword match only")
            return result

        # Analyze each CPE
        has_ecosystem_match = False
        has_name_match = False
        has_exact_match = False
        is_hardware = False
        is_false_pos = False

        for cpe_uri in cve_data.affected_cpes:
            cpe = parse_cpe(cpe_uri)

            # Check for hardware CVE
            if is_hardware_cve(cpe, cve_data.description):
                is_hardware = True
                continue

            # Check for known false positive patterns
            fp_check, fp_reason = is_false_positive(cpe, package_name, cve_data.description)
            if fp_check:
                is_false_pos = True
                result.reasons.append(fp_reason)
                continue

            # Check name match
            name_matches, name_reason, is_exact = check_name_match(cpe, package_name)
            if name_matches:
                has_name_match = True
                if is_exact:
                    has_exact_match = True
                result.matched_cpes.append(cpe_uri)
                result.reasons.append(name_reason)

                # Check ecosystem match
                if check_ecosystem_match(cpe, ecosystem):
                    has_ecosystem_match = True
                    result.reasons.append(f"Ecosystem match: target_sw={cpe.get('target_sw')}")

                # Check version range if provided
                if package_version:
                    version_in_range, version_reason = check_version_in_range(
                        package_version,
                        {
                            "version": cpe.get("version", "*"),
                            # Note: Full version constraints would come from NVD API configurations
                        },
                    )
                    if version_in_range:
                        result.reasons.append(version_reason)
                    else:
                        result.reasons.append(f"Version not affected: {version_reason}")

        # Determine confidence level
        if is_false_pos and not has_exact_match:
            result.confidence = ConfidenceLevel.EXCLUDED
            result.reasons.append("Known false positive pattern detected")
        elif is_hardware and not has_exact_match:
            result.confidence = ConfidenceLevel.EXCLUDED
            result.reasons.append("Hardware-related CVE, not applicable to software package")
        elif has_exact_match and has_ecosystem_match:
            result.confidence = ConfidenceLevel.HIGH
        elif has_exact_match:
            result.confidence = ConfidenceLevel.MEDIUM
        elif has_name_match and has_ecosystem_match:
            # Partial match with ecosystem - medium confidence
            result.confidence = ConfidenceLevel.MEDIUM
        elif has_name_match:
            # Partial match only - low confidence, needs review
            result.confidence = ConfidenceLevel.LOW
        else:
            result.confidence = ConfidenceLevel.EXCLUDED
            result.reasons.append("No CPE matches package name")

        return result

    def search_and_filter(
        self,
        package_name: str,
        ecosystem: str,
        package_version: Optional[str] = None,
        min_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ) -> List[CVEMatchResult]:
        """Search NVD for package and filter results by confidence.

        Args:
            package_name: Package name to search.
            ecosystem: Package ecosystem.
            package_version: Optional package version.
            min_confidence: Minimum confidence level to include.

        Returns:
            List of CVEMatchResult objects that meet the confidence threshold.
        """
        # Search NVD by keyword
        cves = self.nvd_client.search_by_keyword(
            keyword=package_name,
            results_per_page=100,
        )

        results: List[CVEMatchResult] = []
        confidence_order = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        min_index = confidence_order.index(min_confidence)

        for cve in cves:
            match_result = self.match_cve_to_package(
                cve_id=cve.cve_id,
                package_name=package_name,
                ecosystem=ecosystem,
                package_version=package_version,
            )

            # Filter by confidence
            if match_result.confidence in confidence_order[: min_index + 1]:
                results.append(match_result)

        return results
