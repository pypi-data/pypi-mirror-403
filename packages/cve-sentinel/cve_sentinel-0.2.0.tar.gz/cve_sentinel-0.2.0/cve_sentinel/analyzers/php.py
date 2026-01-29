"""PHP Composer dependency analyzer."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from cve_sentinel.analyzers.base import (
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class PhpAnalyzer(BaseAnalyzer):
    """Analyzer for PHP Composer.

    Supports:
    - composer.json (Level 1: direct dependencies)
    - composer.lock (Level 2: transitive dependencies)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "packagist"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["composer.json"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns = ["composer.lock"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 2,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize PHP analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only, 2=include lock files)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect PHP dependency files."""
        patterns = self.manifest_patterns.copy()
        if self.analysis_level >= 2:
            patterns.extend(self.lock_patterns)
        return self._file_detector.find_files(path, patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a PHP dependency file."""
        if file_path.name == "composer.json":
            return self._parse_composer_json(file_path)
        elif file_path.name == "composer.lock":
            return self._parse_composer_lock(file_path)
        return []

    def _parse_composer_json(self, file_path: Path) -> List[Package]:
        """Parse composer.json file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return packages

        # Parse require section
        require = data.get("require", {})
        for name, version_spec in require.items():
            # Skip PHP version constraints and extensions
            if name == "php" or name.startswith("ext-"):
                continue

            version = self._normalize_version(version_spec)
            line_num = self._find_line_number(content, name, "require")

            packages.append(
                Package(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=line_num,
                    is_direct=True,
                )
            )

        # Parse require-dev section
        require_dev = data.get("require-dev", {})
        for name, version_spec in require_dev.items():
            if name == "php" or name.startswith("ext-"):
                continue

            version = self._normalize_version(version_spec)
            line_num = self._find_line_number(content, name, "require-dev")

            packages.append(
                Package(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=line_num,
                    is_direct=True,
                )
            )

        return packages

    def _parse_composer_lock(self, file_path: Path) -> List[Package]:
        """Parse composer.lock file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return packages

        # Parse packages section
        pkg_list = data.get("packages", [])
        for pkg in pkg_list:
            name = pkg.get("name", "")
            version = pkg.get("version", "")

            if not name or not version:
                continue

            # Normalize version (remove 'v' prefix)
            if version.startswith("v"):
                version = version[1:]

            packages.append(
                Package(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=False,
                )
            )

        # Parse packages-dev section
        pkg_dev_list = data.get("packages-dev", [])
        for pkg in pkg_dev_list:
            name = pkg.get("name", "")
            version = pkg.get("version", "")

            if not name or not version:
                continue

            if version.startswith("v"):
                version = version[1:]

            packages.append(
                Package(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=False,
                )
            )

        return packages

    def _normalize_version(self, version_spec: str) -> str:
        """Normalize Composer version specifier."""
        if not version_spec:
            return "*"

        # Handle dev versions
        if version_spec.startswith("dev-"):
            return version_spec

        # Remove operators: ^, ~, >=, <=, >, <, =, ||
        version = re.sub(r"^[\^~>=<|]+\s*", "", version_spec)

        # Handle OR: take first version
        if "|" in version:
            version = version.split("|")[0].strip()
            version = re.sub(r"^[\^~>=<]+\s*", "", version)

        # Handle range with space: ">1.0 <2.0" -> take first
        if " " in version:
            version = version.split()[0].strip()
            version = re.sub(r"^[\^~>=<]+\s*", "", version)

        # Remove 'v' prefix
        if version.startswith("v"):
            version = version[1:]

        # Handle wildcard: 1.* -> 1.0
        version = re.sub(r"\.\*$", ".0", version)

        return version.strip() or "*"

    def _find_line_number(self, content: str, package_name: str, section: str) -> int | None:
        """Find line number of a package in composer.json."""
        lines = content.split("\n")
        in_section = False
        escaped_name = re.escape(package_name)

        for i, line in enumerate(lines, start=1):
            if f'"{section}"' in line:
                in_section = True
            elif in_section:
                if re.match(r"^\s*\}", line):
                    in_section = False
                elif re.search(rf'"{escaped_name}"', line):
                    return i

        return None


def register() -> None:
    """Register the PHP analyzer."""
    AnalyzerRegistry.get_instance().register(PhpAnalyzer())
