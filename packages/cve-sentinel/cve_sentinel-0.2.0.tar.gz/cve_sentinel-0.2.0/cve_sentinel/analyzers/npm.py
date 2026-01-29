"""NPM/Yarn/PNPM dependency analyzer for JavaScript/TypeScript projects."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from cve_sentinel.analyzers.base import (
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class NpmAnalyzer(BaseAnalyzer):
    """Analyzer for npm, yarn, and pnpm package managers.

    Supports:
    - package.json (Level 1: direct dependencies)
    - package-lock.json (Level 2: transitive dependencies)
    - yarn.lock (Level 2: transitive dependencies)
    - pnpm-lock.yaml (Level 2: transitive dependencies)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "npm"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["package.json"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 2,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize NPM analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only, 2=include lock files)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect npm dependency files in the given path.

        Args:
            path: Directory to search

        Returns:
            List of found dependency files
        """
        patterns = self.manifest_patterns.copy()
        if self.analysis_level >= 2:
            patterns.extend(self.lock_patterns)

        return self._file_detector.find_files(path, patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a dependency file and return list of packages.

        Args:
            file_path: Path to the dependency file

        Returns:
            List of Package objects
        """
        file_name = file_path.name

        if file_name == "package.json":
            return self._parse_package_json(file_path)
        elif file_name == "package-lock.json":
            return self._parse_package_lock(file_path)
        elif file_name == "yarn.lock":
            return self._parse_yarn_lock(file_path)
        elif file_name == "pnpm-lock.yaml":
            return self._parse_pnpm_lock(file_path)

        return []

    def _parse_package_json(self, file_path: Path) -> List[Package]:
        """Parse package.json file.

        Args:
            file_path: Path to package.json

        Returns:
            List of direct dependency packages
        """
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return packages

        # Parse dependencies
        deps = data.get("dependencies", {})
        for name, version_spec in deps.items():
            version = self._normalize_version(version_spec)
            line_num = self._find_line_number(content, name, "dependencies")
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

        # Parse devDependencies
        dev_deps = data.get("devDependencies", {})
        for name, version_spec in dev_deps.items():
            version = self._normalize_version(version_spec)
            line_num = self._find_line_number(content, name, "devDependencies")
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

    def _parse_package_lock(self, file_path: Path) -> List[Package]:
        """Parse package-lock.json file (v2/v3 format).

        Args:
            file_path: Path to package-lock.json

        Returns:
            List of transitive dependency packages
        """
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return packages

        # Get root package name to skip it
        root_name = data.get("name", "")

        # Handle v2/v3 format with "packages" key
        packages_data = data.get("packages", {})
        if packages_data:
            for pkg_path, pkg_info in packages_data.items():
                # Skip root package (empty path)
                if not pkg_path:
                    continue

                # Skip link: protocol packages
                if pkg_info.get("link"):
                    continue

                # Extract package name from path (e.g., "node_modules/@scope/pkg" -> "@scope/pkg")
                name = self._extract_package_name_from_path(pkg_path)
                if not name or name == root_name:
                    continue

                version = pkg_info.get("version", "")
                if not version:
                    continue

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
        else:
            # Handle v1 format with "dependencies" key
            deps = data.get("dependencies", {})
            self._parse_lock_v1_deps(deps, file_path, packages, root_name)

        return packages

    def _parse_lock_v1_deps(
        self,
        deps: Dict[str, Any],
        file_path: Path,
        packages: List[Package],
        root_name: str,
    ) -> None:
        """Recursively parse v1 lock file dependencies.

        Args:
            deps: Dependencies dict
            file_path: Source file path
            packages: List to append packages to
            root_name: Root package name to skip
        """
        for name, info in deps.items():
            if name == root_name:
                continue

            version = info.get("version", "")
            if version:
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

            # Recursively parse nested dependencies
            nested_deps = info.get("dependencies", {})
            if nested_deps:
                self._parse_lock_v1_deps(nested_deps, file_path, packages, root_name)

    def _parse_yarn_lock(self, file_path: Path) -> List[Package]:
        """Parse yarn.lock file.

        Args:
            file_path: Path to yarn.lock

        Returns:
            List of transitive dependency packages
        """
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        # Yarn.lock format:
        # "package@^version", "package@~version":
        #   version "x.y.z"
        #   resolved "..."
        #   ...

        # Match package blocks - handle both yarn v1 and berry formats
        # Pattern for package name line (can have multiple specifiers)
        current_names: List[str] = []
        current_version: Optional[str] = None

        lines = content.split("\n")
        seen_packages: set = set()

        for line in lines:
            # Skip comments and empty lines
            if line.startswith("#") or not line.strip():
                continue

            # Check if this is a package header line
            if not line.startswith(" ") and not line.startswith("\t"):
                # If we have a previous package, save it
                if current_names and current_version:
                    for name in current_names:
                        pkg_key = (name, current_version)
                        if pkg_key not in seen_packages:
                            seen_packages.add(pkg_key)
                            packages.append(
                                Package(
                                    name=name,
                                    version=current_version,
                                    ecosystem=self.ecosystem,
                                    source_file=file_path,
                                    source_line=None,
                                    is_direct=False,
                                )
                            )

                # Parse new package header
                current_names = self._parse_yarn_header(line)
                current_version = None

            elif line.strip().startswith("version"):
                # Extract version
                match = re.match(r'\s+version\s+"?([^"]+)"?', line)
                if match:
                    current_version = match.group(1)

        # Don't forget the last package
        if current_names and current_version:
            for name in current_names:
                pkg_key = (name, current_version)
                if pkg_key not in seen_packages:
                    seen_packages.add(pkg_key)
                    packages.append(
                        Package(
                            name=name,
                            version=current_version,
                            ecosystem=self.ecosystem,
                            source_file=file_path,
                            source_line=None,
                            is_direct=False,
                        )
                    )

        return packages

    def _parse_yarn_header(self, line: str) -> List[str]:
        """Parse yarn.lock package header line.

        Args:
            line: Header line (e.g., '"@scope/pkg@^1.0.0", "@scope/pkg@~1.0.0":')

        Returns:
            List of package names
        """
        names: List[str] = []

        # Remove trailing colon
        line = line.rstrip(":")

        # Split by comma for multiple version specifiers
        specs = re.split(r'",\s*"?', line)

        for spec in specs:
            # Clean up the spec
            spec = spec.strip().strip('"').strip("'")
            if not spec:
                continue

            # Extract package name from specifier (before @ version)
            # Handle scoped packages: @scope/name@version
            name = self._extract_package_name_from_spec(spec)
            if name and name not in names:
                names.append(name)

        return names

    def _parse_pnpm_lock(self, file_path: Path) -> List[Package]:
        """Parse pnpm-lock.yaml file.

        Args:
            file_path: Path to pnpm-lock.yaml

        Returns:
            List of transitive dependency packages
        """
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            return packages

        if not data:
            return packages

        # Handle pnpm lockfile v6+ format
        pkgs = data.get("packages", {})
        for pkg_spec, pkg_info in pkgs.items():
            name, version = self._parse_pnpm_package_spec(pkg_spec)
            if not name or not version:
                continue

            # Skip peer dependencies and dev meta
            if isinstance(pkg_info, dict) and pkg_info.get("dev") is True:
                continue

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

        # Handle older pnpm format with dependencies at root level
        dependencies = data.get("dependencies", {})
        for name, version_info in dependencies.items():
            if isinstance(version_info, str):
                version = self._normalize_version(version_info)
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
            else:
                continue

            if version:
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

    def _parse_pnpm_package_spec(self, spec: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse pnpm package specifier.

        Args:
            spec: Package specifier (e.g., "/@scope/pkg@1.0.0" or "/pkg@1.0.0")

        Returns:
            Tuple of (name, version) or (None, None) if parsing fails
        """
        # Remove leading slash
        spec = spec.lstrip("/")

        # Handle scoped packages: @scope/name@version
        if spec.startswith("@"):
            # @scope/name@version
            match = re.match(r"(@[^/]+/[^@]+)@(.+)", spec)
            if match:
                return match.group(1), match.group(2)
        else:
            # name@version
            match = re.match(r"([^@]+)@(.+)", spec)
            if match:
                return match.group(1), match.group(2)

        return None, None

    def _normalize_version(self, version_spec: str) -> str:
        """Normalize version specifier to a clean version string.

        Handles npm version specifiers: ^, ~, >=, <=, >, <, =, x, *, ||, etc.

        Args:
            version_spec: Version specifier (e.g., "^1.2.3", "~1.0.0", ">=2.0.0")

        Returns:
            Normalized version string
        """
        if not version_spec:
            return ""

        # Handle special protocols
        if any(
            version_spec.startswith(p)
            for p in ["file:", "link:", "workspace:", "git:", "git+", "http:", "https:"]
        ):
            return version_spec

        # Handle npm: prefix
        if version_spec.startswith("npm:"):
            # npm:@scope/pkg@version -> extract version
            parts = version_spec.split("@")
            if len(parts) >= 2:
                return parts[-1]

        # Remove common prefixes
        version = re.sub(r"^[\^~>=<]+", "", version_spec)

        # Handle range: take first version from "x.y.z - a.b.c"
        if " - " in version:
            version = version.split(" - ")[0].strip()

        # Handle OR: take first version from "x.y.z || a.b.c"
        if " || " in version:
            version = version.split(" || ")[0].strip()
            version = re.sub(r"^[\^~>=<]+", "", version)

        # Handle space-separated (AND): take first
        if " " in version:
            version = version.split()[0].strip()
            version = re.sub(r"^[\^~>=<]+", "", version)

        return version.strip()

    def _extract_package_name_from_path(self, pkg_path: str) -> Optional[str]:
        """Extract package name from node_modules path.

        Args:
            pkg_path: Path like "node_modules/@scope/pkg" or "node_modules/pkg"

        Returns:
            Package name or None
        """
        # Handle nested node_modules (e.g., node_modules/a/node_modules/b)
        parts = pkg_path.split("node_modules/")
        if len(parts) < 2:
            return None

        # Get the last segment after node_modules/
        last_part = parts[-1]

        # Handle scoped packages
        if last_part.startswith("@"):
            # @scope/name
            segments = last_part.split("/")
            if len(segments) >= 2:
                return f"{segments[0]}/{segments[1]}"
        else:
            # Regular package - just get the first directory name
            return last_part.split("/")[0]

        return None

    def _extract_package_name_from_spec(self, spec: str) -> Optional[str]:
        """Extract package name from version specifier.

        Args:
            spec: Specifier like "@scope/pkg@^1.0.0" or "pkg@~2.0.0"

        Returns:
            Package name or None
        """
        # Handle scoped packages
        if spec.startswith("@"):
            # @scope/name@version - find the second @
            match = re.match(r"(@[^/]+/[^@]+)@", spec)
            if match:
                return match.group(1)
            # Might be just @scope/name without version
            if "/" in spec and "@" not in spec[1:]:
                return spec
        else:
            # name@version
            at_idx = spec.find("@")
            if at_idx > 0:
                return spec[:at_idx]
            # Might be just name without version
            return spec if spec else None

        return None

    def _find_line_number(self, content: str, package_name: str, section: str) -> Optional[int]:
        """Find line number of a package in package.json.

        Args:
            content: File content
            package_name: Package name to find
            section: Section name (dependencies, devDependencies)

        Returns:
            Line number (1-indexed) or None
        """
        lines = content.split("\n")
        in_section = False

        # Escape special regex characters in package name
        escaped_name = re.escape(package_name)

        for i, line in enumerate(lines, start=1):
            if f'"{section}"' in line or f"'{section}'" in line:
                in_section = True
            elif in_section:
                # Check if we've exited the section (closing brace at same indent or less)
                if re.match(r"^\s*\}", line):
                    in_section = False
                elif re.search(rf'["\']({escaped_name})["\']', line):
                    return i

        return None


# Register the analyzer
def register() -> None:
    """Register the NPM analyzer."""
    AnalyzerRegistry.get_instance().register(NpmAnalyzer())
