"""Ruby dependency analyzer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from cve_sentinel.analyzers.base import (
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class RubyAnalyzer(BaseAnalyzer):
    """Analyzer for Ruby Bundler.

    Supports:
    - Gemfile (Level 1: direct dependencies)
    - Gemfile.lock (Level 2: transitive dependencies)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "rubygems"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["Gemfile"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns = ["Gemfile.lock"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 2,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize Ruby analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only, 2=include lock files)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Ruby dependency files."""
        patterns = self.manifest_patterns.copy()
        if self.analysis_level >= 2:
            patterns.extend(self.lock_patterns)
        return self._file_detector.find_files(path, patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Ruby dependency file."""
        if file_path.name == "Gemfile":
            return self._parse_gemfile(file_path)
        elif file_path.name == "Gemfile.lock":
            return self._parse_gemfile_lock(file_path)
        return []

    def _parse_gemfile(self, file_path: Path) -> List[Package]:
        """Parse Gemfile."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                continue

            # Parse gem declarations
            # gem 'name', 'version'
            # gem 'name', '~> version'
            # gem 'name', '>= version', '< version'
            # gem 'name', version: 'x.y.z'
            match = re.match(r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*(.+))?", stripped)
            if match:
                name = match.group(1)
                version_part = match.group(2)

                version = self._extract_version(version_part) if version_part else "*"

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

    def _extract_version(self, version_str: str) -> str:
        """Extract version from Gemfile version specification."""
        if not version_str:
            return "*"

        # Handle version: 'x.y.z' syntax
        version_match = re.search(r"version:\s*['\"]([^'\"]+)['\"]", version_str)
        if version_match:
            return self._normalize_version(version_match.group(1))

        # Handle string version: '~> 1.2.3' or '>= 1.0'
        string_match = re.search(r"['\"]([^'\"]+)['\"]", version_str)
        if string_match:
            return self._normalize_version(string_match.group(1))

        return "*"

    def _normalize_version(self, version: str) -> str:
        """Normalize Ruby version specifier."""
        # Remove operators: ~>, >=, <=, >, <, =
        version = re.sub(r"^[~>=<]+\s*", "", version.strip())
        return version

    def _parse_gemfile_lock(self, file_path: Path) -> List[Package]:
        """Parse Gemfile.lock."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        in_specs = False
        seen: set = set()

        for line in lines:
            # Check for GEM section specs
            if line.strip() == "specs:":
                in_specs = True
                continue

            # End of specs section (new section or blank line after indented content)
            if in_specs and line and not line.startswith(" "):
                in_specs = False
                continue

            if in_specs:
                # Parse gem entries: "    gem_name (version)"
                # Indentation of 4 spaces indicates a direct spec
                match = re.match(r"^    (\S+)\s+\(([^)]+)\)$", line)
                if match:
                    name = match.group(1)
                    version = match.group(2)

                    pkg_key = (name, version)
                    if pkg_key not in seen:
                        seen.add(pkg_key)
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


def register() -> None:
    """Register the Ruby analyzer."""
    AnalyzerRegistry.get_instance().register(RubyAnalyzer())
