"""Python dependency analyzer for pip, poetry, and pipenv."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from cve_sentinel.analyzers.base import BaseAnalyzer, FileDetector, Package


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python dependencies (pip, poetry, pipenv)."""

    @property
    def ecosystem(self) -> str:
        return "pypi"

    @property
    def manifest_patterns(self) -> List[str]:
        default_patterns = ["requirements.txt", "requirements*.txt", "pyproject.toml", "Pipfile"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        default_patterns = ["poetry.lock", "Pipfile.lock"]
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        exclude_patterns: Optional[List[str]] = None,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize the analyzer.

        Args:
            exclude_patterns: Glob patterns to exclude from file detection
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector(exclude_patterns=exclude_patterns)

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Python dependency files in the given path."""
        all_patterns = self.manifest_patterns + self.lock_patterns
        return self._file_detector.find_files(path, all_patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Python dependency file and return packages."""
        filename = file_path.name.lower()

        if filename == "requirements.txt" or filename.startswith("requirements"):
            if filename.endswith(".txt"):
                return self._parse_requirements_txt(file_path)
        elif filename == "pyproject.toml":
            return self._parse_pyproject_toml(file_path)
        elif filename == "pipfile":
            return self._parse_pipfile(file_path)
        elif filename == "poetry.lock":
            return self._parse_poetry_lock(file_path)
        elif filename == "pipfile.lock":
            return self._parse_pipfile_lock(file_path)

        return []

    def _parse_requirements_txt(
        self, file_path: Path, visited: Optional[set] = None
    ) -> List[Package]:
        """Parse requirements.txt file.

        Supports:
        - package==version
        - package>=version
        - package[extra]==version
        - Comments (#)
        - -r includes
        """
        if visited is None:
            visited = set()

        # Prevent infinite recursion
        abs_path = file_path.resolve()
        if abs_path in visited:
            return []
        visited.add(abs_path)

        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        for line_num, line in enumerate(content.splitlines(), start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Handle -r includes
            if line.startswith("-r ") or line.startswith("--requirement "):
                include_path = line.split(None, 1)[1].strip()
                include_file = file_path.parent / include_path
                if include_file.exists():
                    packages.extend(self._parse_requirements_txt(include_file, visited))
                continue

            # Skip other flags
            if line.startswith("-"):
                continue

            # Parse package specification
            parsed = self._parse_requirement_line(line)
            if parsed:
                name, version = parsed
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

    def _parse_requirement_line(self, line: str) -> Optional[Tuple[str, str]]:
        """Parse a single requirement line.

        Returns:
            Tuple of (package_name, version) or None if unparseable
        """
        # Remove inline comments
        if " #" in line:
            line = line.split(" #")[0].strip()

        # Remove environment markers
        if ";" in line:
            line = line.split(";")[0].strip()

        # Handle extras: package[extra1,extra2]==version
        extras_match = re.match(r"^([a-zA-Z0-9_.-]+)\[([^\]]+)\](.*)$", line)
        if extras_match:
            name = extras_match.group(1)
            rest = extras_match.group(3).strip()
            # Parse version from rest (e.g., "==2.28.0")
            version_only_pattern = r"^(==|>=|<=|~=|!=|>|<)\s*([a-zA-Z0-9_.*+-]+)"
            version_match = re.match(version_only_pattern, rest)
            if version_match:
                version = version_match.group(2)
                return self._normalize_package_name(name), version
            elif not rest:
                return self._normalize_package_name(name), "*"
            return None

        # Match version specifiers
        # Patterns: ==, >=, <=, ~=, !=, >, <
        version_pattern = r"^([a-zA-Z0-9_.-]+)\s*(==|>=|<=|~=|!=|>|<)\s*([a-zA-Z0-9_.*+-]+)"
        match = re.match(version_pattern, line)

        if match:
            pkg_name = match.group(1)
            version = match.group(3)
            return self._normalize_package_name(pkg_name), version

        # Package without version
        simple_match = re.match(r"^([a-zA-Z0-9_.-]+)\s*$", line)
        if simple_match:
            pkg_name = simple_match.group(1)
            return self._normalize_package_name(pkg_name), "*"

        return None

    def _parse_pyproject_toml(self, file_path: Path) -> List[Package]:
        """Parse pyproject.toml for dependencies.

        Supports:
        - [project.dependencies] (PEP 621)
        - [project.optional-dependencies]
        - [tool.poetry.dependencies]
        - [tool.poetry.dev-dependencies]
        """
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except Exception:
            return []

        # PEP 621 style: [project.dependencies]
        project = data.get("project", {})
        deps = project.get("dependencies", [])
        for dep in deps:
            parsed = self._parse_requirement_line(dep)
            if parsed:
                name, version = parsed
                packages.append(
                    Package(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        source_file=file_path,
                        source_line=None,
                        is_direct=True,
                    )
                )

        # PEP 621 optional dependencies
        optional_deps = project.get("optional-dependencies", {})
        for _group, deps_list in optional_deps.items():
            for dep in deps_list:
                parsed = self._parse_requirement_line(dep)
                if parsed:
                    name, version = parsed
                    packages.append(
                        Package(
                            name=name,
                            version=version,
                            ecosystem=self.ecosystem,
                            source_file=file_path,
                            source_line=None,
                            is_direct=True,
                        )
                    )

        # Poetry style: [tool.poetry.dependencies]
        tool = data.get("tool", {})
        poetry = tool.get("poetry", {})
        poetry_deps = poetry.get("dependencies", {})
        for name, spec in poetry_deps.items():
            if name.lower() == "python":
                continue
            version = self._extract_poetry_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=True,
                )
            )

        # Poetry dev dependencies
        dev_deps = poetry.get("dev-dependencies", {})
        for name, spec in dev_deps.items():
            version = self._extract_poetry_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=True,
                )
            )

        # Poetry group dependencies (poetry 1.2+)
        groups = poetry.get("group", {})
        for _group_name, group_data in groups.items():
            group_deps = group_data.get("dependencies", {})
            for name, spec in group_deps.items():
                version = self._extract_poetry_version(spec)
                packages.append(
                    Package(
                        name=self._normalize_package_name(name),
                        version=version,
                        ecosystem=self.ecosystem,
                        source_file=file_path,
                        source_line=None,
                        is_direct=True,
                    )
                )

        return packages

    def _extract_poetry_version(self, spec: Any) -> str:
        """Extract version from Poetry dependency specification."""
        if isinstance(spec, str):
            # Simple version string: "^1.0.0" or ">=1.0,<2.0"
            return spec.lstrip("^~")
        elif isinstance(spec, dict):
            # Complex specification: {version = "^1.0.0", optional = true}
            version = spec.get("version", "*")
            return version.lstrip("^~") if isinstance(version, str) else "*"
        return "*"

    def _parse_pipfile(self, file_path: Path) -> List[Package]:
        """Parse Pipfile for dependencies."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except Exception:
            return []

        # Parse [packages] section
        pkgs = data.get("packages", {})
        for name, spec in pkgs.items():
            version = self._extract_pipfile_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=True,
                )
            )

        # Parse [dev-packages] section
        dev_pkgs = data.get("dev-packages", {})
        for name, spec in dev_pkgs.items():
            version = self._extract_pipfile_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=True,
                )
            )

        return packages

    def _extract_pipfile_version(self, spec: Any) -> str:
        """Extract version from Pipfile dependency specification."""
        if isinstance(spec, str):
            if spec == "*":
                return "*"
            # Remove operators
            return re.sub(r"^[=<>~!]+", "", spec)
        elif isinstance(spec, dict):
            version = spec.get("version", "*")
            if version == "*":
                return "*"
            return re.sub(r"^[=<>~!]+", "", version)
        return "*"

    def _parse_poetry_lock(self, file_path: Path) -> List[Package]:
        """Parse poetry.lock for transitive dependencies."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except Exception:
            return []

        # Parse [[package]] entries
        pkg_list = data.get("package", [])
        for pkg in pkg_list:
            name = pkg.get("name", "")
            version = pkg.get("version", "*")
            if name:
                packages.append(
                    Package(
                        name=self._normalize_package_name(name),
                        version=version,
                        ecosystem=self.ecosystem,
                        source_file=file_path,
                        source_line=None,
                        is_direct=False,  # Lock file = transitive dependencies
                    )
                )

        return packages

    def _parse_pipfile_lock(self, file_path: Path) -> List[Package]:
        """Parse Pipfile.lock for transitive dependencies."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        # Parse "default" section (production dependencies)
        default = data.get("default", {})
        for name, spec in default.items():
            version = self._extract_pipfile_lock_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=False,
                )
            )

        # Parse "develop" section (dev dependencies)
        develop = data.get("develop", {})
        for name, spec in develop.items():
            version = self._extract_pipfile_lock_version(spec)
            packages.append(
                Package(
                    name=self._normalize_package_name(name),
                    version=version,
                    ecosystem=self.ecosystem,
                    source_file=file_path,
                    source_line=None,
                    is_direct=False,
                )
            )

        return packages

    def _extract_pipfile_lock_version(self, spec: Dict) -> str:
        """Extract version from Pipfile.lock entry."""
        version = spec.get("version", "*")
        if version.startswith("=="):
            return version[2:]
        return version

    def _normalize_package_name(self, name: str) -> str:
        """Normalize Python package name (PEP 503)."""
        return re.sub(r"[-_.]+", "-", name).lower()
