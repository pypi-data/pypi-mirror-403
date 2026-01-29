"""Main scanner module for CVE Sentinel."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from cve_sentinel.analyzers.base import AnalysisResult, AnalyzerRegistry, Package
from cve_sentinel.config import Config, ConfigError, load_config
from cve_sentinel.fetchers.nvd import NVDClient
from cve_sentinel.fetchers.nvd_package_matcher import ConfidenceLevel
from cve_sentinel.fetchers.osv import OSVClient
from cve_sentinel.matcher import VulnerabilityMatch, VulnerabilityMatcher
from cve_sentinel.matcher_combined import CombinedVulnerabilityMatcher
from cve_sentinel.reporter import Reporter, create_reporter

# Type alias for matcher (either VulnerabilityMatcher or CombinedVulnerabilityMatcher)
MatcherType = Union[VulnerabilityMatcher, CombinedVulnerabilityMatcher]

logger = logging.getLogger(__name__)

__version__ = "0.2.0"


@dataclass
class ScanResult:
    """Result of a CVE scan.

    Attributes:
        success: Whether the scan completed successfully.
        packages_scanned: Number of packages scanned.
        vulnerabilities: List of detected vulnerabilities.
        errors: List of error messages encountered during scan.
        scan_duration: Duration of the scan in seconds.
    """

    success: bool
    packages_scanned: int
    vulnerabilities: List[VulnerabilityMatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scan_duration: float = 0.0

    @property
    def has_vulnerabilities(self) -> bool:
        """Check if any vulnerabilities were found."""
        return len(self.vulnerabilities) > 0

    @property
    def critical_count(self) -> int:
        """Count of critical severity vulnerabilities."""
        return sum(1 for v in self.vulnerabilities if (v.severity or "").upper() == "CRITICAL")

    @property
    def high_count(self) -> int:
        """Count of high severity vulnerabilities."""
        return sum(1 for v in self.vulnerabilities if (v.severity or "").upper() == "HIGH")


class CVESentinelScanner:
    """Main scanner class that orchestrates the CVE detection process.

    This class coordinates the dependency analysis, vulnerability matching,
    and result reporting for CVE Sentinel.
    """

    def __init__(
        self,
        config: Config,
        nvd_client: Optional[NVDClient] = None,
        osv_client: Optional[OSVClient] = None,
    ) -> None:
        """Initialize the scanner with configuration.

        Args:
            config: Configuration object with scan settings.
            nvd_client: Optional pre-configured NVD client.
            osv_client: Optional pre-configured OSV client.
        """
        self.config = config
        self._nvd_client = nvd_client
        self._osv_client = osv_client
        self._reporter: Optional[Reporter] = None
        self._matcher: Optional[MatcherType] = None
        self._initialized = False

    def _initialize_components(self, target_path: Path) -> None:
        """Initialize scanner components.

        Args:
            target_path: Path to the project being scanned.
        """
        if self._initialized:
            return

        # Set up cache directory
        cache_dir = target_path / ".cve-sentinel" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Get datasources config
        ds_config = self.config.datasources

        # Initialize NVD client if enabled and not provided
        if self._nvd_client is None and ds_config.nvd_enabled and self.config.nvd_api_key:
            self._nvd_client = NVDClient(
                api_key=self.config.nvd_api_key,
                cache_dir=cache_dir,
                cache_ttl_hours=self.config.cache_ttl_hours,
            )

        # Initialize OSV client if enabled and not provided
        if self._osv_client is None and ds_config.osv_enabled:
            self._osv_client = OSVClient(
                cache_dir=cache_dir,
                cache_ttl_hours=self.config.cache_ttl_hours,
            )

        # Map confidence level string to enum
        confidence_map = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
        }
        nvd_min_confidence = confidence_map.get(
            ds_config.nvd_min_confidence.lower(),
            ConfidenceLevel.MEDIUM,
        )

        # Initialize matcher based on datasources configuration
        if ds_config.nvd_enabled and self._nvd_client:
            # Use combined matcher for broader coverage
            self._matcher = CombinedVulnerabilityMatcher(
                nvd_client=self._nvd_client,
                osv_client=self._osv_client if ds_config.osv_enabled else None,
                nvd_min_confidence=nvd_min_confidence,
            )
            logger.info(
                f"Using combined matcher (OSV: {ds_config.osv_enabled}, "
                f"NVD: {ds_config.nvd_enabled}, min_confidence: {ds_config.nvd_min_confidence})"
            )
        else:
            # Use original matcher (OSV only or with NVD details)
            self._matcher = VulnerabilityMatcher(
                nvd_client=self._nvd_client,
                osv_client=self._osv_client,
                fetch_nvd_details=self._nvd_client is not None,
            )
            logger.info(f"Using OSV matcher (NVD details: {self._nvd_client is not None})")

        # Initialize reporter
        self._reporter = create_reporter(target_path)

        # Register analyzers
        self._register_analyzers()

        self._initialized = True

    def _register_analyzers(self) -> None:
        """Register all available dependency analyzers."""
        # Import and register analyzers
        from cve_sentinel.analyzers.go import GoAnalyzer
        from cve_sentinel.analyzers.maven import GradleAnalyzer, MavenAnalyzer
        from cve_sentinel.analyzers.npm import NpmAnalyzer
        from cve_sentinel.analyzers.php import PhpAnalyzer
        from cve_sentinel.analyzers.python import PythonAnalyzer
        from cve_sentinel.analyzers.ruby import RubyAnalyzer
        from cve_sentinel.analyzers.rust import RustAnalyzer

        registry = AnalyzerRegistry.get_instance()
        registry.clear()

        analysis_level = self.config.analysis_level
        custom_patterns = self.config.custom_patterns or {}

        # Map ecosystem names to their aliases for custom_patterns lookup
        # Users can use either the common name or the ecosystem name
        ecosystem_aliases = {
            "npm": ["javascript", "npm"],
            "pypi": ["python", "pypi"],
            "go": ["go"],
            "maven": ["java", "maven", "gradle"],
            "rubygems": ["ruby", "rubygems"],
            "crates.io": ["rust", "crates.io"],
            "packagist": ["php", "packagist"],
        }

        def get_custom_patterns_for(ecosystem: str) -> Optional[dict]:
            """Get custom patterns for an ecosystem, checking aliases."""
            for alias in ecosystem_aliases.get(ecosystem, []):
                if alias in custom_patterns:
                    return custom_patterns[alias]
            return None

        # Register analyzers with appropriate analysis level and custom patterns
        # Note: PythonAnalyzer uses exclude_patterns instead of analysis_level
        registry.register(
            NpmAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("npm"),
            )
        )
        registry.register(PythonAnalyzer(custom_patterns=get_custom_patterns_for("pypi")))
        registry.register(
            GoAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("go"),
            )
        )
        registry.register(
            MavenAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("maven"),
            )
        )
        registry.register(
            GradleAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("maven"),
            )
        )
        registry.register(
            RubyAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("rubygems"),
            )
        )
        registry.register(
            RustAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("crates.io"),
            )
        )
        registry.register(
            PhpAnalyzer(
                analysis_level=analysis_level,
                custom_patterns=get_custom_patterns_for("packagist"),
            )
        )

    def scan(self, target_path: Path) -> ScanResult:
        """Perform a CVE scan on the target path.

        Executes the 10-step scan flow:
        1. Update status.json to "scanning"
        2. Load configuration
        3. Validate target path
        4. Detect dependency files
        5. Parse packages (Level 1-2)
        6. Import statement scanning (Level 3, if enabled)
        7. CVE matching
        8. Aggregate results
        9. Write results.json
        10. Update status.json to "completed"

        Args:
            target_path: Path to the project directory to scan.

        Returns:
            ScanResult with scan outcome and vulnerabilities.
        """
        start_time = time.time()
        errors: List[str] = []
        packages: List[Package] = []
        vulnerabilities: List[VulnerabilityMatch] = []

        try:
            # Step 3: Validate target path BEFORE initialization
            if not target_path.exists():
                raise ConfigError(f"Target path does not exist: {target_path}")
            if not target_path.is_dir():
                raise ConfigError(f"Target path is not a directory: {target_path}")

            # Step 1: Initialize components and update status
            self._initialize_components(target_path)
            if self._reporter:
                self._reporter.update_status("scanning")

            logger.info(f"Starting CVE scan for: {target_path}")

            # Step 4-5: Detect and parse dependency files
            registry = AnalyzerRegistry.get_instance()
            analyzers = registry.get_all()

            if not analyzers:
                logger.warning("No analyzers registered")
                errors.append("No analyzers registered")

            combined_result = AnalysisResult()

            for analyzer in analyzers:
                logger.debug(f"Running {analyzer.ecosystem} analyzer")
                try:
                    result = analyzer.analyze(
                        target_path,
                        exclude_patterns=self.config.exclude,
                    )
                    combined_result = combined_result.merge(result)
                    logger.debug(
                        f"{analyzer.ecosystem}: found {result.package_count} packages "
                        f"in {len(result.scanned_files)} files"
                    )
                except Exception as e:
                    error_msg = f"Error in {analyzer.ecosystem} analyzer: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            # Deduplicate packages
            packages = self._deduplicate_packages(combined_result.packages)
            errors.extend(combined_result.errors)

            logger.info(f"Found {len(packages)} unique packages")

            # Step 6: Import statement scanning (Level 3)
            # Note: Level 3 scanning is handled within individual analyzers
            # when analysis_level >= 3

            # Step 7: CVE matching
            if packages and self._matcher:
                logger.info("Matching packages against vulnerability databases...")
                try:
                    vulnerabilities = self._matcher.match(packages)  # type: ignore[assignment]
                    logger.info(f"Found {len(vulnerabilities)} vulnerabilities")
                except Exception as e:
                    error_msg = f"Error during vulnerability matching: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Step 8-9: Aggregate and write results
            if self._reporter:
                self._reporter.write_results(
                    project_path=target_path,
                    packages_scanned=len(packages),
                    vulnerabilities=vulnerabilities,
                )

                # Print summary to terminal
                self._reporter.print_summary(len(packages), vulnerabilities)

            # Step 10: Update status to completed
            if self._reporter:
                self._reporter.update_status("completed")

            scan_duration = time.time() - start_time
            logger.info(f"Scan completed in {scan_duration:.2f}s")

            return ScanResult(
                success=True,
                packages_scanned=len(packages),
                vulnerabilities=vulnerabilities,
                errors=errors,
                scan_duration=scan_duration,
            )

        except Exception as e:
            # Error handling
            scan_duration = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Scan failed: {error_msg}")
            errors.append(error_msg)

            # Update status to error
            if self._reporter:
                self._reporter.update_status("error", error_message=error_msg)

            return ScanResult(
                success=False,
                packages_scanned=len(packages),
                vulnerabilities=vulnerabilities,
                errors=errors,
                scan_duration=scan_duration,
            )

    def _deduplicate_packages(self, packages: List[Package]) -> List[Package]:
        """Remove duplicate packages, preferring direct dependencies.

        Args:
            packages: List of packages possibly with duplicates.

        Returns:
            Deduplicated list of packages.
        """
        seen: dict[tuple[str, str, str], Package] = {}

        for pkg in packages:
            key = (pkg.name, pkg.version, pkg.ecosystem)
            if key not in seen:
                seen[key] = pkg
            elif pkg.is_direct and not seen[key].is_direct:
                # Prefer direct dependency
                seen[key] = pkg

        return list(seen.values())


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable debug logging.
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="cve-sentinel",
        description="Scan project dependencies for known CVE vulnerabilities",
    )

    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("."),
        help="Path to the project directory to scan (default: current directory)",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to configuration file (default: .cve-sentinel.yaml in project)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (debug) output",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Exit with error code if vulnerabilities at or above this severity are found (default: HIGH)",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format to stdout",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for CVE Sentinel CLI.

    Args:
        args: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0: success, 1: vulnerabilities found, 2: error).
    """
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)

    # Set up logging
    setup_logging(verbose=parsed_args.verbose)

    # Resolve target path
    target_path = parsed_args.path.resolve()

    try:
        # Load configuration
        config = load_config(
            base_path=target_path,
            validate=True,
            require_api_key=False,  # Allow scanning without NVD API key
        )

        # Create scanner
        scanner = CVESentinelScanner(config)

        # Run scan
        result = scanner.scan(target_path)

        if not result.success:
            logger.error("Scan failed with errors")
            for error in result.errors:
                logger.error(f"  - {error}")
            return 2

        # Determine exit code based on vulnerabilities
        if result.has_vulnerabilities:
            # Check severity threshold
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            threshold_index = severity_order.index(parsed_args.fail_on)

            for vuln in result.vulnerabilities:
                severity = (vuln.severity or "UNKNOWN").upper()
                if severity in severity_order:
                    if severity_order.index(severity) <= threshold_index:
                        return 1

        return 0

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 2
    except KeyboardInterrupt:
        logger.info("Scan cancelled by user")
        return 2
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
