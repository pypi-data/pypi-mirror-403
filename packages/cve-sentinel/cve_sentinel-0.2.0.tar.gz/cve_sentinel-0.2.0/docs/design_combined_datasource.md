# Combined Data Source Design for CVE Sentinel

## Overview

This document describes the design for combining OSV and NVD data sources to achieve both **accuracy** and **comprehensive coverage** in vulnerability detection.

## Problem Statement

- **OSV Only**: High precision but may miss some vulnerabilities not yet in OSV
- **NVD Only**: Broader coverage but keyword search produces many false positives (e.g., "vite" matches "VITEC", "cypress" matches Cypress chips)
- **Goal**: Combine both sources to maximize coverage while maintaining accuracy

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CombinedVulnerabilityMatcher                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. OSV Query (Primary Source)                                  │
│     - Package name + ecosystem + version                        │
│     - High precision, provides fix versions                     │
│     - Results marked as "osv" source, "high" confidence         │
│                                                                 │
│  2. NVD Query + Filtering (Supplementary Source)                │
│     - Keyword search by package name                            │
│     - CPE-based filtering:                                      │
│       ├── Exact product match → HIGH confidence                 │
│       ├── Product contains name + ecosystem match → MEDIUM      │
│       ├── Partial match only → LOW (excluded by default)        │
│       └── Hardware/OS CPE → EXCLUDED                            │
│     - Results marked as "nvd" source with confidence level      │
│                                                                 │
│  3. Deduplication & Merge                                       │
│     - Same CVE from both sources → "both" source, verified      │
│     - OSV data preferred for fix versions                       │
│     - NVD data preferred for CVSS scores                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | CPE exact match + ecosystem indicator (node.js, python, etc.) | Include |
| **MEDIUM** | CPE exact match OR (partial match + ecosystem indicator) | Include with review flag |
| **LOW** | Partial keyword match only | Exclude by default |
| **EXCLUDED** | Hardware CPE, OS CPE, or clear product mismatch | Exclude |

## CPE Filtering Logic

```python
def check_name_match(cpe, package_name):
    # 1. Known vendor mapping (highest priority)
    if cpe.vendor in KNOWN_VENDOR_MAPPINGS[package_name]:
        return True, "exact", "Known vendor mapping"

    # 2. Exact product match
    if normalize(package_name) == normalize(cpe.product):
        return True, "exact", "Exact product match"

    # 3. Product contains package name (with ratio check)
    if package_name in cpe.product:
        ratio = len(package_name) / len(cpe.product)
        if ratio >= 0.5:  # Avoid "vite" in "vitec"
            return True, "partial", "Product contains package"

    return False, None, "No match"
```

## Ecosystem Detection

```python
ECOSYSTEM_TARGET_SW = {
    "npm": {"node.js", "nodejs", "node"},
    "pypi": {"python", "python3", "pip"},
    "go": {"go", "golang"},
    "maven": {"java", "maven", "spring"},
    "rubygems": {"ruby", "rails"},
    "crates.io": {"rust", "cargo"},
    "packagist": {"php", "composer"},
}
```

## Hardware/False Positive Exclusion

```python
HARDWARE_INDICATORS = {
    "firmware", "chip", "chipset", "wireless", "bluetooth",
    "wifi", "hardware", "device", "driver", "kernel", "iot",
    "router", "switch", "controller", "printer", "scanner"
}

def is_hardware_cve(cpe, description):
    # Exclude if CPE part is hardware
    if cpe.part == "h":
        return True

    # Exclude if description has multiple hardware indicators
    hardware_matches = count_matches(description, HARDWARE_INDICATORS)
    return hardware_matches >= 2
```

## Output Format

```json
{
  "cve_id": "CVE-2024-12345",
  "package": {
    "name": "vite",
    "version": "4.2.1",
    "ecosystem": "npm"
  },
  "severity": "HIGH",
  "cvss_score": 7.5,
  "source": "both",       // "osv", "nvd", or "both"
  "confidence": "high",   // "high", "medium", or "low"
  "nvd_verified": true,   // Verified by NVD CPE match
  "fix_version": "4.5.3",
  "fix_command": "npm install vite@4.5.3"
}
```

## Test Results

### Coverage Comparison (Sample: 25 packages)

| Method | CVEs Found | Additional |
|--------|-----------|------------|
| OSV Only | 17 | - |
| Combined (OSV + Filtered NVD) | 42 | +25 (+147%) |

### Confidence Distribution

| Confidence | Count | Percentage |
|------------|-------|------------|
| High | 21 | 50% |
| Medium | 21 | 50% |
| Low | 0 | 0% (filtered) |

## Implementation Files

- `cve_sentinel/fetchers/nvd_package_matcher.py` - NVD filtering logic
- `cve_sentinel/matcher_combined.py` - Combined matcher implementation

## Implemented Improvements

1. **Version Range Validation**: Cross-check NVD CPE version ranges with package version ✓
2. **False Positive Filtering**: Hardware vendor blacklist and known false positive patterns ✓
3. **Confidence Tuning**: Users can configure minimum confidence level via config ✓
4. **Datasource Configuration**: Enable/disable OSV/NVD independently ✓

## Future Improvements

1. **Description NLP**: Use keyword extraction to improve product matching
2. **Caching Strategy**: Cache NVD results per package to reduce API calls
3. **Manual Review Queue**: Flag medium-confidence results for manual review

## Configuration

```yaml
# .cve-sentinel.yaml

# NVD API key (recommended for better rate limits)
# Best practice: Set via environment variable CVE_SENTINEL_NVD_API_KEY
# nvd_api_key: "your-api-key-here"

# Data sources configuration
datasources:
  # Enable/disable OSV (high precision, package-aware queries)
  osv_enabled: true

  # Enable/disable NVD (broader coverage with CPE-based filtering)
  nvd_enabled: true

  # Minimum confidence for NVD-only results: high, medium, low
  # - high: Only exact CPE matches with ecosystem indicator
  # - medium: Exact CPE matches OR partial matches with ecosystem (default)
  # - low: Include keyword-only matches (may have false positives)
  nvd_min_confidence: medium

  # Prefer OSV data when same CVE found in both sources
  prefer_osv: true
```

## False Positive Prevention

### Hardware Vendor Blacklist

The following vendors are automatically excluded as they are known hardware manufacturers:

- cypress_semiconductor, broadcom, qualcomm
- intel, amd, nvidia, texas_instruments
- microchip, infineon, nxp, stmicroelectronics
- And many more...

### Package-Specific False Positive Patterns

Known false positive patterns for common packages:

```python
FALSE_POSITIVE_PATTERNS = {
    "cypress": {"cypress_semiconductor", "broadcom", "google:android", ...},
    "vite": {"vitec", "vitess", "vitemoneycoin", ...},
    "passport": {"passport220", "dedos-web", ...},
    "express": {"expressvpn", "express_gateway", ...},
}
```

## Version Range Validation

NVD CPE version constraints are validated:

- `versionStartIncluding`: Package version must be >= this version
- `versionStartExcluding`: Package version must be > this version
- `versionEndIncluding`: Package version must be <= this version
- `versionEndExcluding`: Package version must be < this version

If a package version falls outside the affected range, the CVE is excluded.
