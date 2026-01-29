"""Pytest fixtures for CVE Sentinel tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_nvd_response() -> Dict[str, Any]:
    """Sample NVD API response for testing."""
    return {
        "resultsPerPage": 1,
        "startIndex": 0,
        "totalResults": 1,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-15T10:00:00.000",
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2021-44228",
                    "sourceIdentifier": "security@apache.org",
                    "published": "2021-12-10T10:15:09.143",
                    "lastModified": "2023-11-07T03:39:36.750",
                    "vulnStatus": "Analyzed",
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "Apache Log4j2 2.0-beta9 through 2.15.0 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints.",
                        }
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "source": "nvd@nist.gov",
                                "type": "Primary",
                                "cvssData": {
                                    "version": "3.1",
                                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                                    "attackVector": "NETWORK",
                                    "attackComplexity": "LOW",
                                    "privilegesRequired": "NONE",
                                    "userInteraction": "NONE",
                                    "scope": "CHANGED",
                                    "confidentialityImpact": "HIGH",
                                    "integrityImpact": "HIGH",
                                    "availabilityImpact": "HIGH",
                                    "baseScore": 10.0,
                                    "baseSeverity": "CRITICAL",
                                },
                                "exploitabilityScore": 3.9,
                                "impactScore": 6.0,
                            }
                        ]
                    },
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "operator": "OR",
                                    "negate": False,
                                    "cpeMatch": [
                                        {
                                            "vulnerable": True,
                                            "criteria": "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*",
                                            "versionStartIncluding": "2.0",
                                            "versionEndExcluding": "2.15.0",
                                            "matchCriteriaId": "TEST-ID",
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                    "references": [
                        {
                            "url": "https://logging.apache.org/log4j/2.x/security.html",
                            "source": "security@apache.org",
                        },
                        {
                            "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
                            "source": "nvd@nist.gov",
                        },
                    ],
                }
            }
        ],
    }


@pytest.fixture
def sample_empty_nvd_response() -> Dict[str, Any]:
    """Empty NVD API response for testing."""
    return {
        "resultsPerPage": 0,
        "startIndex": 0,
        "totalResults": 0,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-15T10:00:00.000",
        "vulnerabilities": [],
    }
