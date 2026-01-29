"""CVE Sentinel CLI with subcommand support."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from cve_sentinel.config import ConfigError, load_config
from cve_sentinel.scanner import CVESentinelScanner, __version__, setup_logging

logger = logging.getLogger(__name__)

# Default configuration template
CONFIG_TEMPLATE = """\
# CVE Sentinel Configuration
# See: https://github.com/xxx/cve-sentinel#configuration

# Target directory to scan (relative to this config file)
target_path: "."

# Paths to exclude from scanning (glob patterns)
exclude:
  - "node_modules/"
  - "vendor/"
  - ".git/"
  - "__pycache__/"
  - "venv/"
  - ".venv/"
  - "dist/"
  - "build/"

# Analysis level:
#   1: Direct dependencies from manifest files only
#   2: Include transitive dependencies from lock files
#   3: Include import statement scanning in source code
analysis_level: 2

# Automatically scan when Claude Code session starts
auto_scan_on_startup: true

# Cache time-to-live in hours (CVE data cache)
cache_ttl_hours: 24

# NVD API key (recommended for better rate limits)
# Get your key at: https://nvd.nist.gov/developers/request-an-api-key
# Best practice: Set via environment variable CVE_SENTINEL_NVD_API_KEY
# nvd_api_key: "your-api-key-here"

# Custom file patterns for dependency detection (optional)
# Use this to scan non-standard dependency files
# Valid ecosystems: javascript, python, go, java, ruby, rust, php
# custom_patterns:
#   python:
#     manifests:
#       - "deps/*.txt"
#       - "custom-requirements.txt"
#     locks:
#       - "custom.lock"
#   javascript:
#     manifests:
#       - "dependencies.json"

# Data sources configuration
# OSV: High precision, package-aware queries
# NVD: Broader coverage with CPE-based filtering
datasources:
  osv_enabled: true
  nvd_enabled: true
  # Minimum confidence for NVD-only results: high, medium, low
  nvd_min_confidence: medium
  # Prefer OSV data when same CVE found in both sources
  prefer_osv: true
"""

# CLAUDE.md addition template
CLAUDE_MD_ADDITION = """\

## CVE Sentinel Integration

This project uses CVE Sentinel for automatic vulnerability detection.

### Automatic Scanning
CVE Sentinel automatically scans dependencies when a Claude Code session starts.
Check `.cve-sentinel/status.json` for scan status and `.cve-sentinel/results.json` for results.

### Manual Commands
```bash
# Scan current directory (no config file needed)
cve-sentinel scan

# Scan specific path
cve-sentinel scan /path/to/project

# With options
cve-sentinel scan --level 2 --exclude "test/*" --verbose
```

### Configuration (Optional)
For persistent settings, create `.cve-sentinel.yaml`. CLI options override config file settings.
"""


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute the scan command."""
    setup_logging(verbose=args.verbose)

    target_path = args.path.resolve()

    try:
        # Build CLI overrides
        cli_overrides: dict = {}
        if args.level is not None:
            cli_overrides["analysis_level"] = args.level
        if args.exclude:
            cli_overrides["exclude"] = args.exclude

        config = load_config(
            base_path=target_path,
            validate=True,
            require_api_key=False,
            cli_overrides=cli_overrides,
        )

        scanner = CVESentinelScanner(config)
        result = scanner.scan(target_path)

        if not result.success:
            logger.error("Scan failed with errors")
            for error in result.errors:
                logger.error(f"  - {error}")
            return 2

        # Determine exit code based on vulnerabilities
        if result.has_vulnerabilities:
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            threshold_index = severity_order.index(args.fail_on)

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


def cmd_init(args: argparse.Namespace) -> int:
    """Execute the init command."""
    setup_logging(verbose=args.verbose)

    target_path = args.path.resolve()

    print(f"Initializing CVE Sentinel in: {target_path}")

    # Create .cve-sentinel.yaml
    config_file = target_path / ".cve-sentinel.yaml"
    if config_file.exists() and not args.force:
        print(f"Configuration file already exists: {config_file}")
        print("Use --force to overwrite.")
    else:
        config_file.write_text(CONFIG_TEMPLATE)
        print(f"Created: {config_file}")

    # Create .cve-sentinel directory
    sentinel_dir = target_path / ".cve-sentinel"
    sentinel_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created: {sentinel_dir}/")

    # Add to .gitignore if it exists
    gitignore = target_path / ".gitignore"
    gitignore_entries = [".cve-sentinel/"]

    if gitignore.exists():
        content = gitignore.read_text()
        lines_to_add = [entry for entry in gitignore_entries if entry not in content]
        if lines_to_add:
            with open(gitignore, "a") as f:
                f.write("\n# CVE Sentinel\n")
                for entry in lines_to_add:
                    f.write(f"{entry}\n")
            print(f"Updated: {gitignore}")
    else:
        with open(gitignore, "w") as f:
            f.write("# CVE Sentinel\n")
            for entry in gitignore_entries:
                f.write(f"{entry}\n")
        print(f"Created: {gitignore}")

    # Show CLAUDE.md addition suggestion
    print("\n" + "=" * 50)
    print("Consider adding the following to your CLAUDE.md:")
    print("=" * 50)
    print(CLAUDE_MD_ADDITION)
    print("=" * 50)

    print("\nCVE Sentinel initialized successfully!")
    print("\nNext steps:")
    print("  1. Run: cve-sentinel scan")
    print("  2. (Optional) Customize .cve-sentinel.yaml for persistent settings")

    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Execute the uninstall command."""
    setup_logging(verbose=args.verbose)

    print("Uninstalling CVE Sentinel...")

    # Confirm uninstall
    if not args.yes:
        response = input("Are you sure you want to uninstall CVE Sentinel? [y/N] ")
        if response.lower() not in ("y", "yes"):
            print("Uninstall cancelled.")
            return 0

    errors = []

    # Remove Claude Code hook settings
    settings_file = Path.home() / ".claude" / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file) as f:
                settings = json.load(f)

            # Remove CVE Sentinel hook
            if "hooks" in settings and "sessionStart" in settings["hooks"]:
                settings["hooks"]["sessionStart"] = [
                    h
                    for h in settings["hooks"]["sessionStart"]
                    if not (isinstance(h, dict) and h.get("name") == "cve-sentinel")
                ]

                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=2)
                print("Removed Claude Code hook settings")

        except Exception as e:
            errors.append(f"Failed to update Claude Code settings: {e}")

    # Remove hook script
    hook_script = Path.home() / ".claude" / "hooks" / "cve-sentinel-scan.sh"
    if hook_script.exists():
        try:
            hook_script.unlink()
            print(f"Removed: {hook_script}")
        except Exception as e:
            errors.append(f"Failed to remove hook script: {e}")

    # Remove cache (optional)
    if args.remove_cache:
        cache_dir = Path.home() / ".cve-sentinel"
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"Removed cache: {cache_dir}")
            except Exception as e:
                errors.append(f"Failed to remove cache: {e}")

    # Uninstall pip package
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "cve-sentinel"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Uninstalled CVE Sentinel package")
        else:
            errors.append(f"pip uninstall failed: {result.stderr}")
    except Exception as e:
        errors.append(f"Failed to uninstall package: {e}")

    if errors:
        print("\nCompleted with errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nCVE Sentinel has been uninstalled.")
    print("\nNote: Project-level .cve-sentinel.yaml and .cve-sentinel/ directories")
    print("have not been removed. Delete them manually if desired.")

    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Execute the update command."""
    setup_logging(verbose=args.verbose)

    print("Updating CVE Sentinel...")

    # Update pip package
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "cve-sentinel"]
        if args.verbose:
            result = subprocess.run(cmd, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("CVE Sentinel package updated successfully")
        else:
            if result.stderr:
                print(f"Update failed: {result.stderr}")
            return 1

    except Exception as e:
        print(f"Failed to update package: {e}")
        return 1

    # Update hook script
    hooks_dir = Path.home() / ".claude" / "hooks"
    hook_script = hooks_dir / "cve-sentinel-scan.sh"

    if hooks_dir.exists():
        hook_content = """\
#!/bin/bash
# CVE Sentinel SessionStart Hook
# This script is called when a Claude Code session starts

# Get the project directory from argument or current directory
PROJECT_DIR="${1:-.}"

# Check if .cve-sentinel.yaml exists or if there are dependency files
should_scan() {
    if [ -f "$PROJECT_DIR/.cve-sentinel.yaml" ]; then
        return 0
    fi

    # Check for common dependency files
    for file in package.json requirements.txt pyproject.toml Gemfile Cargo.toml go.mod composer.json pom.xml build.gradle; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            return 0
        fi
    done

    return 1
}

# Run scan if applicable
if should_scan; then
    # Run in background to not block Claude Code startup
    nohup cve-sentinel scan --path "$PROJECT_DIR" > /dev/null 2>&1 &
fi
"""
        try:
            hook_script.write_text(hook_content)
            hook_script.chmod(0o755)
            print(f"Updated hook script: {hook_script}")
        except Exception as e:
            print(f"Warning: Failed to update hook script: {e}")

    print("\nCVE Sentinel has been updated to the latest version.")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="cve-sentinel",
        description="CVE auto-detection and remediation for project dependencies",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="Available commands",
    )

    # Scan command (default behavior)
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan project for CVE vulnerabilities",
        description="Scan project dependencies for known CVE vulnerabilities",
    )
    scan_parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Path to the project directory (default: current directory)",
    )
    scan_parser.add_argument(
        "--level",
        "-l",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Analysis level: 1=manifest only, 2=include lock files, 3=include import scanning",
    )
    scan_parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        help="Path patterns to exclude (can be specified multiple times)",
    )
    scan_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    scan_parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Exit with error if vulnerabilities at or above this severity (default: HIGH)",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize CVE Sentinel in a project",
        description="Create configuration files for CVE Sentinel in the project",
    )
    init_parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("."),
        help="Path to the project directory (default: current directory)",
    )
    init_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing configuration",
    )
    init_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    init_parser.set_defaults(func=cmd_init)

    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall CVE Sentinel",
        description="Remove CVE Sentinel and its configuration",
    )
    uninstall_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    uninstall_parser.add_argument(
        "--remove-cache",
        action="store_true",
        help="Also remove cached CVE data",
    )
    uninstall_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)

    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update CVE Sentinel to the latest version",
        description="Update CVE Sentinel package and hook scripts",
    )
    update_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    update_parser.set_defaults(func=cmd_update)

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for CVE Sentinel CLI."""
    parser = create_parser()

    # Handle shorthand: if first arg is not a known command, treat as path for scan
    known_commands = {"scan", "init", "uninstall", "update"}
    if args and args[0] not in known_commands and not args[0].startswith("-"):
        # First arg looks like a path, prepend "scan"
        args = ["scan", *args]

    parsed_args = parser.parse_args(args)

    # Default to scan if no command specified
    if parsed_args.command is None:
        # No arguments at all - run scan on current directory
        scan_args = ["scan"]
        parsed_args = parser.parse_args(scan_args)

    # Execute command
    if hasattr(parsed_args, "func"):
        return parsed_args.func(parsed_args)

    parser.print_help()
    return 0
