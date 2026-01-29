"""Base analyzer class and common data models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class Package:
    """Represents a detected package dependency."""

    name: str
    version: str
    ecosystem: str  # npm, pypi, go, maven, rubygems, crates.io, packagist
    source_file: Path
    source_line: Optional[int] = None
    is_direct: bool = True  # True for direct dependency, False for transitive

    def __hash__(self) -> int:
        return hash((self.name, self.version, self.ecosystem))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Package):
            return False
        return (
            self.name == other.name
            and self.version == other.version
            and self.ecosystem == other.ecosystem
        )


@dataclass
class AnalysisResult:
    """Result of dependency analysis."""

    packages: List[Package] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scanned_files: List[Path] = field(default_factory=list)

    @property
    def package_count(self) -> int:
        """Return total number of packages found."""
        return len(self.packages)

    @property
    def direct_packages(self) -> List[Package]:
        """Return only direct dependencies."""
        return [p for p in self.packages if p.is_direct]

    @property
    def transitive_packages(self) -> List[Package]:
        """Return only transitive dependencies."""
        return [p for p in self.packages if not p.is_direct]

    def merge(self, other: AnalysisResult) -> AnalysisResult:
        """Merge another result into this one."""
        return AnalysisResult(
            packages=self.packages + other.packages,
            errors=self.errors + other.errors,
            scanned_files=self.scanned_files + other.scanned_files,
        )


class BaseAnalyzer(ABC):
    """Abstract base class for dependency analyzers."""

    @property
    @abstractmethod
    def ecosystem(self) -> str:
        """Return the ecosystem name (npm, pypi, etc.)."""
        ...

    @property
    @abstractmethod
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files (e.g., package.json)."""
        ...

    @property
    @abstractmethod
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files (e.g., package-lock.json)."""
        ...

    @abstractmethod
    def detect_files(self, path: Path) -> List[Path]:
        """Detect dependency files in the given path."""
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> List[Package]:
        """Parse a dependency file and return list of packages."""
        ...

    def analyze(self, path: Path, exclude_patterns: Optional[List[str]] = None) -> AnalysisResult:
        """Analyze dependencies in the given path.

        Args:
            path: Directory to analyze
            exclude_patterns: Glob patterns to exclude from scanning

        Returns:
            AnalysisResult with found packages and any errors
        """
        result = AnalysisResult()
        try:
            files = self.detect_files(path)
            # Filter excluded paths
            if exclude_patterns:
                files = [f for f in files if not _matches_any_pattern(f, exclude_patterns)]

            for file_path in files:
                result.scanned_files.append(file_path)
                try:
                    packages = self.parse(file_path)
                    result.packages.extend(packages)
                except Exception as e:
                    result.errors.append(f"Error parsing {file_path}: {e}")
        except Exception as e:
            result.errors.append(f"Error detecting files: {e}")

        return result


def _matches_any_pattern(path: Path, patterns: List[str]) -> bool:
    """Check if path matches any of the given glob patterns."""
    path_str = str(path)
    for pattern in patterns:
        # Support common patterns like node_modules/**, .git/**, etc.
        if pattern.endswith("/**"):
            dir_pattern = pattern[:-3]
            if dir_pattern in path_str:
                return True
        elif pattern in path_str:
            return True
    return False


class AnalyzerRegistry:
    """Registry for managing dependency analyzers."""

    _instance: Optional[AnalyzerRegistry] = None
    _analyzers: List[BaseAnalyzer]

    def __init__(self) -> None:
        self._analyzers = []

    @classmethod
    def get_instance(cls) -> AnalyzerRegistry:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = AnalyzerRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (mainly for testing)."""
        cls._instance = None

    def register(self, analyzer: BaseAnalyzer) -> None:
        """Register an analyzer."""
        # Avoid duplicate registration
        for existing in self._analyzers:
            if existing.ecosystem == analyzer.ecosystem:
                return
        self._analyzers.append(analyzer)

    def get_all(self) -> List[BaseAnalyzer]:
        """Get all registered analyzers."""
        return self._analyzers.copy()

    def get_by_ecosystem(self, ecosystem: str) -> Optional[BaseAnalyzer]:
        """Get analyzer by ecosystem name."""
        for analyzer in self._analyzers:
            if analyzer.ecosystem == ecosystem:
                return analyzer
        return None

    def clear(self) -> None:
        """Clear all registered analyzers."""
        self._analyzers = []


class FileDetector:
    """Utility for detecting dependency files in a directory."""

    def __init__(
        self,
        exclude_patterns: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
    ) -> None:
        """Initialize file detector.

        Args:
            exclude_patterns: Glob patterns to exclude (e.g., node_modules/**)
            max_depth: Maximum directory depth to search (None for unlimited)
        """
        self.exclude_patterns = exclude_patterns or []
        self.max_depth = max_depth
        # Default exclusions
        self._default_excludes: Set[str] = {
            "node_modules",
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            ".venv",
            "venv",
            ".env",
            "dist",
            "build",
            ".eggs",
        }

    def find_files(
        self,
        root: Path,
        patterns: List[str],
        include_default_excludes: bool = True,
    ) -> List[Path]:
        """Find files matching patterns in the given root directory.

        Args:
            root: Root directory to search
            patterns: Glob patterns to match (e.g., ["package.json", "*/package.json"])
            include_default_excludes: Whether to exclude common directories

        Returns:
            List of matching file paths
        """
        if not root.is_dir():
            return []

        found_files: List[Path] = []
        exclude_dirs = self._default_excludes if include_default_excludes else set()

        # Add user-specified exclusions
        for pattern in self.exclude_patterns:
            if pattern.endswith("/**"):
                exclude_dirs.add(pattern[:-3])

        self._search_recursive(root, patterns, found_files, exclude_dirs, 0)
        return sorted(found_files)

    def _search_recursive(
        self,
        current: Path,
        patterns: List[str],
        found: List[Path],
        exclude_dirs: Set[str],
        depth: int,
    ) -> None:
        """Recursively search for files."""
        if self.max_depth is not None and depth > self.max_depth:
            return

        try:
            for item in current.iterdir():
                if item.is_dir():
                    if item.name not in exclude_dirs:
                        self._search_recursive(item, patterns, found, exclude_dirs, depth + 1)
                elif item.is_file():
                    for pattern in patterns:
                        if item.match(pattern):
                            found.append(item)
                            break
        except PermissionError:
            pass  # Skip directories we can't access
