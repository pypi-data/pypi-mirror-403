"""Tests for the analyzer base module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from cve_sentinel.analyzers.base import (
    AnalysisResult,
    AnalyzerRegistry,
    BaseAnalyzer,
    FileDetector,
    Package,
)


class TestPackage:
    """Tests for Package dataclass."""

    def test_package_creation(self) -> None:
        """Test creating a Package instance."""
        pkg = Package(
            name="requests",
            version="2.28.0",
            ecosystem="pypi",
            source_file=Path("requirements.txt"),
            source_line=5,
            is_direct=True,
        )
        assert pkg.name == "requests"
        assert pkg.version == "2.28.0"
        assert pkg.ecosystem == "pypi"
        assert pkg.source_file == Path("requirements.txt")
        assert pkg.source_line == 5
        assert pkg.is_direct is True

    def test_package_defaults(self) -> None:
        """Test Package default values."""
        pkg = Package(
            name="lodash",
            version="4.17.21",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        assert pkg.source_line is None
        assert pkg.is_direct is True

    def test_package_equality(self) -> None:
        """Test Package equality comparison."""
        pkg1 = Package(
            name="react",
            version="18.0.0",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        pkg2 = Package(
            name="react",
            version="18.0.0",
            ecosystem="npm",
            source_file=Path("other/package.json"),
        )
        pkg3 = Package(
            name="react",
            version="17.0.0",
            ecosystem="npm",
            source_file=Path("package.json"),
        )
        # Same name, version, ecosystem -> equal
        assert pkg1 == pkg2
        # Different version -> not equal
        assert pkg1 != pkg3

    def test_package_hash(self) -> None:
        """Test Package can be used in sets."""
        pkg1 = Package(
            name="flask",
            version="2.0.0",
            ecosystem="pypi",
            source_file=Path("requirements.txt"),
        )
        pkg2 = Package(
            name="flask",
            version="2.0.0",
            ecosystem="pypi",
            source_file=Path("setup.py"),
        )
        pkg3 = Package(
            name="django",
            version="4.0.0",
            ecosystem="pypi",
            source_file=Path("requirements.txt"),
        )
        pkg_set = {pkg1, pkg2, pkg3}
        assert len(pkg_set) == 2  # pkg1 and pkg2 are equal


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_empty_result(self) -> None:
        """Test empty AnalysisResult."""
        result = AnalysisResult()
        assert result.packages == []
        assert result.errors == []
        assert result.scanned_files == []
        assert result.package_count == 0

    def test_package_count(self) -> None:
        """Test package_count property."""
        result = AnalysisResult(
            packages=[
                Package("a", "1.0", "npm", Path("a")),
                Package("b", "2.0", "npm", Path("b")),
            ]
        )
        assert result.package_count == 2

    def test_direct_and_transitive_packages(self) -> None:
        """Test filtering direct and transitive packages."""
        direct_pkg = Package("direct", "1.0", "npm", Path("a"), is_direct=True)
        transitive_pkg = Package("trans", "1.0", "npm", Path("a"), is_direct=False)
        result = AnalysisResult(packages=[direct_pkg, transitive_pkg])

        assert result.direct_packages == [direct_pkg]
        assert result.transitive_packages == [transitive_pkg]

    def test_merge_results(self) -> None:
        """Test merging two AnalysisResults."""
        result1 = AnalysisResult(
            packages=[Package("a", "1.0", "npm", Path("a"))],
            errors=["Error 1"],
            scanned_files=[Path("file1.json")],
        )
        result2 = AnalysisResult(
            packages=[Package("b", "2.0", "npm", Path("b"))],
            errors=["Error 2"],
            scanned_files=[Path("file2.json")],
        )
        merged = result1.merge(result2)

        assert len(merged.packages) == 2
        assert len(merged.errors) == 2
        assert len(merged.scanned_files) == 2


class MockAnalyzer(BaseAnalyzer):
    """Mock analyzer for testing."""

    @property
    def ecosystem(self) -> str:
        return "mock"

    @property
    def manifest_patterns(self) -> List[str]:
        return ["mock.json"]

    @property
    def lock_patterns(self) -> List[str]:
        return ["mock.lock"]

    def detect_files(self, path: Path) -> List[Path]:
        return list(path.glob("**/mock.json"))

    def parse(self, file_path: Path) -> List[Package]:
        return [Package("mock-pkg", "1.0.0", "mock", file_path)]


class TestBaseAnalyzer:
    """Tests for BaseAnalyzer abstract class."""

    def test_analyze_method(self) -> None:
        """Test the analyze method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            mock_file = tmp_path / "mock.json"
            mock_file.write_text("{}")

            analyzer = MockAnalyzer()
            result = analyzer.analyze(tmp_path)

            assert len(result.packages) == 1
            assert result.packages[0].name == "mock-pkg"
            assert len(result.scanned_files) == 1

    def test_analyze_with_exclude_patterns(self) -> None:
        """Test analyze with exclusion patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create files in different directories
            (tmp_path / "mock.json").write_text("{}")
            excluded_dir = tmp_path / "excluded"
            excluded_dir.mkdir()
            (excluded_dir / "mock.json").write_text("{}")

            analyzer = MockAnalyzer()
            result = analyzer.analyze(tmp_path, exclude_patterns=["excluded/**"])

            assert len(result.packages) == 1


class TestAnalyzerRegistry:
    """Tests for AnalyzerRegistry."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        AnalyzerRegistry.reset()

    def test_singleton_pattern(self) -> None:
        """Test registry singleton pattern."""
        instance1 = AnalyzerRegistry.get_instance()
        instance2 = AnalyzerRegistry.get_instance()
        assert instance1 is instance2

    def test_register_and_get_all(self) -> None:
        """Test registering analyzers and getting all."""
        registry = AnalyzerRegistry.get_instance()
        analyzer = MockAnalyzer()
        registry.register(analyzer)

        all_analyzers = registry.get_all()
        assert len(all_analyzers) == 1
        assert all_analyzers[0] is analyzer

    def test_get_by_ecosystem(self) -> None:
        """Test getting analyzer by ecosystem."""
        registry = AnalyzerRegistry.get_instance()
        analyzer = MockAnalyzer()
        registry.register(analyzer)

        found = registry.get_by_ecosystem("mock")
        assert found is analyzer

        not_found = registry.get_by_ecosystem("nonexistent")
        assert not_found is None

    def test_no_duplicate_registration(self) -> None:
        """Test that duplicate ecosystems are not registered."""
        registry = AnalyzerRegistry.get_instance()
        analyzer1 = MockAnalyzer()
        analyzer2 = MockAnalyzer()
        registry.register(analyzer1)
        registry.register(analyzer2)

        assert len(registry.get_all()) == 1

    def test_clear(self) -> None:
        """Test clearing the registry."""
        registry = AnalyzerRegistry.get_instance()
        registry.register(MockAnalyzer())
        registry.clear()
        assert len(registry.get_all()) == 0

    def test_reset(self) -> None:
        """Test resetting the singleton."""
        registry1 = AnalyzerRegistry.get_instance()
        registry1.register(MockAnalyzer())
        AnalyzerRegistry.reset()
        registry2 = AnalyzerRegistry.get_instance()
        assert registry1 is not registry2
        assert len(registry2.get_all()) == 0


class TestFileDetector:
    """Tests for FileDetector."""

    def test_find_files_basic(self) -> None:
        """Test basic file finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            (tmp_path / "other.txt").write_text("")

            detector = FileDetector()
            found = detector.find_files(tmp_path, ["package.json"])

            assert len(found) == 1
            assert found[0].name == "package.json"

    def test_find_files_recursive(self) -> None:
        """Test recursive file finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            subdir = tmp_path / "subproject"
            subdir.mkdir()
            (subdir / "package.json").write_text("{}")

            detector = FileDetector()
            found = detector.find_files(tmp_path, ["package.json"])

            assert len(found) == 2

    def test_find_files_with_max_depth(self) -> None:
        """Test file finding with max depth."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            deep = tmp_path / "level1" / "level2"
            deep.mkdir(parents=True)
            (deep / "package.json").write_text("{}")

            detector = FileDetector(max_depth=1)
            found = detector.find_files(tmp_path, ["package.json"])

            assert len(found) == 1  # Only root level

    def test_default_excludes(self) -> None:
        """Test that default directories are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            node_modules = tmp_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.json").write_text("{}")

            detector = FileDetector()
            found = detector.find_files(tmp_path, ["package.json"])

            assert len(found) == 1
            assert "node_modules" not in str(found[0])

    def test_custom_exclude_patterns(self) -> None:
        """Test custom exclusion patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            vendor = tmp_path / "vendor"
            vendor.mkdir()
            (vendor / "package.json").write_text("{}")

            detector = FileDetector(exclude_patterns=["vendor/**"])
            found = detector.find_files(tmp_path, ["package.json"])

            assert len(found) == 1
            assert "vendor" not in str(found[0])

    def test_find_files_non_existent_directory(self) -> None:
        """Test finding files in non-existent directory."""
        detector = FileDetector()
        found = detector.find_files(Path("/nonexistent/path"), ["*.json"])
        assert found == []

    def test_find_files_multiple_patterns(self) -> None:
        """Test finding files with multiple patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text("{}")
            (tmp_path / "requirements.txt").write_text("")
            (tmp_path / "other.txt").write_text("")

            detector = FileDetector()
            found = detector.find_files(tmp_path, ["package.json", "requirements.txt"])

            assert len(found) == 2
