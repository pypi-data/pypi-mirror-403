"""Rust dependency analyzer."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from cve_sentinel.analyzers.base import (
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class RustAnalyzer(BaseAnalyzer):
    """Analyzer for Rust Cargo.

    Supports:
    - Cargo.toml (Level 1: direct dependencies)
    - Cargo.lock (Level 2: transitive dependencies)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "crates.io"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["Cargo.toml"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns = ["Cargo.lock"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 2,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize Rust analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only, 2=include lock files)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Rust dependency files."""
        patterns = self.manifest_patterns.copy()
        if self.analysis_level >= 2:
            patterns.extend(self.lock_patterns)
        return self._file_detector.find_files(path, patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Rust dependency file."""
        if file_path.name == "Cargo.toml":
            return self._parse_cargo_toml(file_path)
        elif file_path.name == "Cargo.lock":
            return self._parse_cargo_lock(file_path)
        return []

    def _parse_cargo_toml(self, file_path: Path) -> List[Package]:
        """Parse Cargo.toml file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except Exception:
            return packages

        # Get package name to skip self-references
        pkg_name = data.get("package", {}).get("name", "")

        # Parse dependencies
        deps = data.get("dependencies", {})
        packages.extend(self._parse_deps_section(deps, file_path, pkg_name, True))

        # Parse dev-dependencies
        dev_deps = data.get("dev-dependencies", {})
        packages.extend(self._parse_deps_section(dev_deps, file_path, pkg_name, True))

        # Parse build-dependencies
        build_deps = data.get("build-dependencies", {})
        packages.extend(self._parse_deps_section(build_deps, file_path, pkg_name, True))

        return packages

    def _parse_deps_section(
        self,
        deps: Dict[str, Any],
        file_path: Path,
        skip_name: str,
        is_direct: bool,
    ) -> List[Package]:
        """Parse a dependencies section."""
        packages: List[Package] = []

        for name, spec in deps.items():
            if name == skip_name:
                continue

            version = self._extract_version(spec)
            if not version:
                continue

            packages.append(
                Package(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=is_direct,
                )
            )

        return packages

    def _extract_version(self, spec: Any) -> Optional[str]:
        """Extract version from dependency specification."""
        if isinstance(spec, str):
            return self._normalize_version(spec)
        elif isinstance(spec, dict):
            version = spec.get("version")
            if version:
                return self._normalize_version(version)
            # Git or path dependencies don't have versions
            if spec.get("git") or spec.get("path"):
                return None
        return None

    def _normalize_version(self, version: str) -> str:
        """Normalize Cargo version specifier."""
        # Remove operators: ^, ~, >=, <=, >, <, =
        version = re.sub(r"^[\^~>=<]+\s*", "", version.strip())
        # Handle wildcard: 1.* -> 1.0
        version = re.sub(r"\.\*$", ".0", version)
        return version

    def _parse_cargo_lock(self, file_path: Path) -> List[Package]:
        """Parse Cargo.lock file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except Exception:
            return packages

        # Parse [[package]] entries
        pkg_list = data.get("package", [])
        seen: set = set()

        for pkg in pkg_list:
            name = pkg.get("name", "")
            version = pkg.get("version", "")

            if not name or not version:
                continue

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
    """Register the Rust analyzer."""
    AnalyzerRegistry.get_instance().register(RustAnalyzer())
