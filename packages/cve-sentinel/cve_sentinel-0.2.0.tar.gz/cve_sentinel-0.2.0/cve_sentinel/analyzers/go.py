"""Go dependency analyzer."""

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


class GoAnalyzer(BaseAnalyzer):
    """Analyzer for Go modules.

    Supports:
    - go.mod (Level 1: direct dependencies)
    - go.sum (Level 2: transitive dependencies)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "go"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["go.mod"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns = ["go.sum"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 2,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize Go analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only, 2=include lock files)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Go dependency files."""
        patterns = self.manifest_patterns.copy()
        if self.analysis_level >= 2:
            patterns.extend(self.lock_patterns)
        return self._file_detector.find_files(path, patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Go dependency file."""
        if file_path.name == "go.mod":
            return self._parse_go_mod(file_path)
        elif file_path.name == "go.sum":
            return self._parse_go_sum(file_path)
        return []

    def _parse_go_mod(self, file_path: Path) -> List[Package]:
        """Parse go.mod file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        in_require_block = False
        line_num = 0

        for line in lines:
            line_num += 1
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("//"):
                continue

            # Check for require block start
            if stripped == "require (":
                in_require_block = True
                continue

            # Check for block end
            if stripped == ")":
                in_require_block = False
                continue

            # Parse single-line require
            if stripped.startswith("require ") and "(" not in stripped:
                match = re.match(r"require\s+(\S+)\s+(\S+)", stripped)
                if match:
                    module_path = match.group(1)
                    version = self._normalize_version(match.group(2))
                    packages.append(
                        Package(
                            name=module_path,
                            version=version,
                            ecosystem=self.ecosystem,
                            source_file=file_path,
                            source_line=line_num,
                            is_direct=True,
                        )
                    )
                continue

            # Parse require block entries
            if in_require_block:
                # Format: module/path v1.2.3 [// indirect]
                match = re.match(r"(\S+)\s+(\S+)(?:\s+//\s*indirect)?", stripped)
                if match:
                    module_path = match.group(1)
                    version = self._normalize_version(match.group(2))
                    is_indirect = "// indirect" in stripped
                    packages.append(
                        Package(
                            name=module_path,
                            version=version,
                            ecosystem=self.ecosystem,
                            source_file=file_path,
                            source_line=line_num,
                            is_direct=not is_indirect,
                        )
                    )

        return packages

    def _parse_go_sum(self, file_path: Path) -> List[Package]:
        """Parse go.sum file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")
        seen: set = set()

        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Format: module/path v1.2.3 h1:hash=
            # or: module/path v1.2.3/go.mod h1:hash=
            match = re.match(r"(\S+)\s+(\S+?)(?:/go\.mod)?\s+", stripped)
            if match:
                module_path = match.group(1)
                version = self._normalize_version(match.group(2))

                pkg_key = (module_path, version)
                if pkg_key not in seen:
                    seen.add(pkg_key)
                    packages.append(
                        Package(
                            name=module_path,
                            version=version,
                            ecosystem=self.ecosystem,
                            source_file=file_path,
                            source_line=None,
                            is_direct=False,
                        )
                    )

        return packages

    def _normalize_version(self, version: str) -> str:
        """Normalize Go version string."""
        # Remove v prefix if present
        if version.startswith("v"):
            version = version[1:]
        # Handle +incompatible suffix
        version = version.replace("+incompatible", "")
        return version


def register() -> None:
    """Register the Go analyzer."""
    AnalyzerRegistry.get_instance().register(GoAnalyzer())
