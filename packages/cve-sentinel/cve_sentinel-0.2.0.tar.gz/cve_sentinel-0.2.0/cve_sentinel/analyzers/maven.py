"""Maven/Gradle dependency analyzer for Java projects."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from cve_sentinel.analyzers.base import (
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class MavenAnalyzer(BaseAnalyzer):
    """Analyzer for Maven pom.xml files.

    Supports:
    - pom.xml (Level 1: direct dependencies)
    """

    # Maven POM namespace
    POM_NS = "{http://maven.apache.org/POM/4.0.0}"

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "maven"

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["pom.xml"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns: List[str] = []  # Maven doesn't have a standard lock file
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 1,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize Maven analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Maven dependency files."""
        return self._file_detector.find_files(path, self.manifest_patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Maven pom.xml file."""
        if file_path.name == "pom.xml":
            return self._parse_pom_xml(file_path)
        return []

    def _parse_pom_xml(self, file_path: Path) -> List[Package]:
        """Parse pom.xml file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")

        try:
            # Try parsing with namespace
            root = ET.fromstring(content)
        except ET.ParseError:
            return packages

        # Detect namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Extract properties for variable substitution
        properties = self._extract_properties(root, ns)

        # Find dependencies section
        deps_section = root.find(f"{ns}dependencies")
        if deps_section is None:
            return packages

        for dep in deps_section.findall(f"{ns}dependency"):
            group_id = self._get_text(dep, f"{ns}groupId")
            artifact_id = self._get_text(dep, f"{ns}artifactId")
            version = self._get_text(dep, f"{ns}version")
            scope = self._get_text(dep, f"{ns}scope")

            if not group_id or not artifact_id:
                continue

            # Resolve property references
            if version:
                version = self._resolve_properties(version, properties)
            else:
                version = "*"  # Version might be managed by parent POM

            # Skip test scope by default
            if scope == "test":
                continue

            # Format as groupId:artifactId
            name = f"{group_id}:{artifact_id}"

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

        return packages

    def _extract_properties(self, root: ET.Element, ns: str) -> Dict[str, str]:
        """Extract properties from POM."""
        properties: Dict[str, str] = {}
        props_section = root.find(f"{ns}properties")
        if props_section is not None:
            for prop in props_section:
                # Remove namespace from tag
                tag = prop.tag.replace(ns, "")
                if prop.text:
                    properties[tag] = prop.text
        return properties

    def _resolve_properties(self, value: str, properties: Dict[str, str]) -> str:
        """Resolve ${property} references in value."""
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, value)
        for match in matches:
            if match in properties:
                value = value.replace(f"${{{match}}}", properties[match])
        return value

    def _get_text(self, element: ET.Element, path: str) -> Optional[str]:
        """Get text content of a child element."""
        child = element.find(path)
        if child is not None and child.text:
            return child.text.strip()
        return None


class GradleAnalyzer(BaseAnalyzer):
    """Analyzer for Gradle build files.

    Supports:
    - build.gradle (Level 1: direct dependencies)
    - build.gradle.kts (Level 1: Kotlin DSL)
    """

    @property
    def ecosystem(self) -> str:
        """Return the ecosystem name."""
        return "maven"  # Gradle uses Maven repositories

    @property
    def manifest_patterns(self) -> List[str]:
        """Return glob patterns for manifest files."""
        default_patterns = ["build.gradle", "build.gradle.kts"]
        custom = self._custom_patterns.get("manifests", [])
        return default_patterns + custom

    @property
    def lock_patterns(self) -> List[str]:
        """Return glob patterns for lock files."""
        default_patterns: List[str] = []
        custom = self._custom_patterns.get("locks", [])
        return default_patterns + custom

    def __init__(
        self,
        analysis_level: int = 1,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize Gradle analyzer.

        Args:
            analysis_level: Analysis depth (1=manifest only)
            custom_patterns: Optional custom file patterns {"manifests": [...], "locks": [...]}
        """
        self.analysis_level = analysis_level
        self._custom_patterns = custom_patterns or {}
        self._file_detector = FileDetector()

    def detect_files(self, path: Path) -> List[Path]:
        """Detect Gradle build files."""
        return self._file_detector.find_files(path, self.manifest_patterns)

    def parse(self, file_path: Path) -> List[Package]:
        """Parse a Gradle build file."""
        if file_path.name in ("build.gradle", "build.gradle.kts"):
            return self._parse_build_gradle(file_path)
        return []

    def _parse_build_gradle(self, file_path: Path) -> List[Package]:
        """Parse build.gradle or build.gradle.kts file."""
        packages: List[Package] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        in_dependencies = False
        brace_count = 0

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track dependencies block
            if re.match(r"dependencies\s*\{", stripped):
                in_dependencies = True
                brace_count = 1
                continue

            if in_dependencies:
                brace_count += stripped.count("{") - stripped.count("}")
                if brace_count <= 0:
                    in_dependencies = False
                    continue

                # Parse dependency declarations
                # Groovy: implementation 'group:artifact:version'
                # Kotlin: implementation("group:artifact:version")
                patterns = [
                    # Groovy string
                    r"(implementation|api|compile|compileOnly|runtimeOnly|testImplementation|testCompile)\s+['\"]([^'\"]+)['\"]",
                    # Kotlin function
                    r"(implementation|api|compile|compileOnly|runtimeOnly|testImplementation|testCompile)\s*\(\s*['\"]([^'\"]+)['\"]",
                    # Groovy map style
                    r"(implementation|api|compile)\s+group:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*version:\s*['\"]([^'\"]+)['\"]",
                ]

                for pattern in patterns:
                    match = re.search(pattern, stripped)
                    if match:
                        groups = match.groups()
                        config_type = groups[0]

                        # Skip test dependencies
                        if "test" in config_type.lower():
                            continue

                        if len(groups) == 4:
                            # Map style: group, name, version
                            name = f"{groups[1]}:{groups[2]}"
                            version = groups[3]
                        else:
                            # String style: group:artifact:version
                            dep_str = groups[1]
                            parts = dep_str.split(":")
                            if len(parts) >= 2:
                                name = f"{parts[0]}:{parts[1]}"
                                version = parts[2] if len(parts) > 2 else "*"
                            else:
                                continue

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
                        break

        return packages


def register() -> None:
    """Register Maven and Gradle analyzers."""
    registry = AnalyzerRegistry.get_instance()
    registry.register(MavenAnalyzer())
    registry.register(GradleAnalyzer())
