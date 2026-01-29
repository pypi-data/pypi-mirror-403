"""CVE Sentinel CLI entry point.

Allows running:
    python -m cve_sentinel [command] [args]

Commands:
    scan      - Scan project for CVE vulnerabilities (default)
    init      - Initialize CVE Sentinel in a project
    update    - Update CVE Sentinel to the latest version
    uninstall - Uninstall CVE Sentinel
"""

import sys

from cve_sentinel.cli import main

if __name__ == "__main__":
    sys.exit(main())
