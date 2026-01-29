"""Tests for Python dependency analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cve_sentinel.analyzers.python import PythonAnalyzer


class TestPythonAnalyzer:
    """Tests for PythonAnalyzer class."""

    def test_ecosystem(self) -> None:
        """Test ecosystem property."""
        analyzer = PythonAnalyzer()
        assert analyzer.ecosystem == "pypi"

    def test_manifest_patterns(self) -> None:
        """Test manifest patterns."""
        analyzer = PythonAnalyzer()
        patterns = analyzer.manifest_patterns
        assert "requirements.txt" in patterns
        assert "pyproject.toml" in patterns
        assert "Pipfile" in patterns

    def test_lock_patterns(self) -> None:
        """Test lock file patterns."""
        analyzer = PythonAnalyzer()
        patterns = analyzer.lock_patterns
        assert "poetry.lock" in patterns
        assert "Pipfile.lock" in patterns


class TestRequirementsTxtParser:
    """Tests for requirements.txt parsing."""

    def test_parse_simple_requirements(self) -> None:
        """Test parsing simple requirements."""
        content = """
requests==2.28.0
flask>=2.0.0
django~=4.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert len(packages) == 3
        names = [p.name for p in packages]
        assert "requests" in names
        assert "flask" in names
        assert "django" in names

        # Check versions
        pkg_dict = {p.name: p for p in packages}
        assert pkg_dict["requests"].version == "2.28.0"
        assert pkg_dict["flask"].version == "2.0.0"
        assert pkg_dict["django"].version == "4.0"

    def test_parse_with_comments(self) -> None:
        """Test parsing with comments."""
        content = """
# This is a comment
requests==2.28.0  # inline comment
# Another comment
flask>=2.0.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert len(packages) == 2

    def test_parse_with_extras(self) -> None:
        """Test parsing packages with extras."""
        content = """
requests[security]==2.28.0
uvicorn[standard]>=0.18.0
celery[redis,sqs]==5.2.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert len(packages) == 3
        names = [p.name for p in packages]
        assert "requests" in names
        assert "uvicorn" in names
        assert "celery" in names

    def test_parse_with_environment_markers(self) -> None:
        """Test parsing with environment markers."""
        content = """
pywin32>=300; sys_platform == 'win32'
requests==2.28.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert len(packages) == 2

    def test_parse_recursive_include(self) -> None:
        """Test parsing with -r includes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create base requirements
            base = tmp_path / "requirements-base.txt"
            base.write_text("requests==2.28.0\n")

            # Create main requirements with include
            main = tmp_path / "requirements.txt"
            main.write_text("-r requirements-base.txt\nflask>=2.0.0\n")

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(main)

            assert len(packages) == 2
            names = [p.name for p in packages]
            assert "requests" in names
            assert "flask" in names

    def test_parse_line_numbers(self) -> None:
        """Test that line numbers are captured."""
        content = """requests==2.28.0
flask>=2.0.0
django~=4.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        lines = [p.source_line for p in packages]
        assert 1 in lines
        assert 2 in lines
        assert 3 in lines

    def test_parse_package_without_version(self) -> None:
        """Test parsing package without version."""
        content = "requests\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert len(packages) == 1
        assert packages[0].name == "requests"
        assert packages[0].version == "*"

    def test_packages_are_direct(self) -> None:
        """Test that requirements.txt packages are marked as direct."""
        content = "requests==2.28.0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert all(p.is_direct for p in packages)


class TestPyprojectTomlParser:
    """Tests for pyproject.toml parsing."""

    def test_parse_pep621_dependencies(self) -> None:
        """Test parsing PEP 621 style dependencies."""
        content = """
[project]
name = "test-project"
dependencies = [
    "requests>=2.28.0",
    "flask>=2.0.0",
]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            # Rename to pyproject.toml for detection
            new_path = path.parent / "pyproject.toml"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 2
        names = [p.name for p in packages]
        assert "requests" in names
        assert "flask" in names

    def test_parse_pep621_optional_dependencies(self) -> None:
        """Test parsing PEP 621 optional dependencies."""
        content = """
[project]
name = "test-project"
dependencies = ["requests>=2.28.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "ruff>=0.1.0"]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "pyproject.toml"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3
        names = [p.name for p in packages]
        assert "requests" in names
        assert "pytest" in names
        assert "ruff" in names

    def test_parse_poetry_dependencies(self) -> None:
        """Test parsing Poetry style dependencies."""
        content = """
[tool.poetry]
name = "test-project"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
flask = {version = "^2.0.0", optional = true}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "pyproject.toml"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        # Should exclude python
        assert len(packages) == 2
        names = [p.name for p in packages]
        assert "requests" in names
        assert "flask" in names
        assert "python" not in names

    def test_parse_poetry_dev_dependencies(self) -> None:
        """Test parsing Poetry dev-dependencies."""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "pyproject.toml"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 2
        names = [p.name for p in packages]
        assert "requests" in names
        assert "pytest" in names

    def test_parse_poetry_group_dependencies(self) -> None:
        """Test parsing Poetry 1.2+ group dependencies."""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"

[tool.poetry.group.test.dependencies]
coverage = "^6.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "pyproject.toml"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3
        names = [p.name for p in packages]
        assert "requests" in names
        assert "pytest" in names
        assert "coverage" in names


class TestPipfileParser:
    """Tests for Pipfile parsing."""

    def test_parse_pipfile_packages(self) -> None:
        """Test parsing Pipfile packages section."""
        content = """
[packages]
requests = "==2.28.0"
flask = ">=2.0.0"
django = "*"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "Pipfile"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3
        pkg_dict = {p.name: p for p in packages}
        assert pkg_dict["requests"].version == "2.28.0"
        assert pkg_dict["flask"].version == "2.0.0"
        assert pkg_dict["django"].version == "*"

    def test_parse_pipfile_dev_packages(self) -> None:
        """Test parsing Pipfile dev-packages section."""
        content = """
[packages]
requests = "==2.28.0"

[dev-packages]
pytest = ">=7.0.0"
ruff = "*"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "Pipfile"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3


class TestPoetryLockParser:
    """Tests for poetry.lock parsing."""

    def test_parse_poetry_lock(self) -> None:
        """Test parsing poetry.lock file."""
        content = """
[[package]]
name = "requests"
version = "2.28.0"
description = "Python HTTP library"

[[package]]
name = "urllib3"
version = "1.26.12"
description = "HTTP library"

[[package]]
name = "certifi"
version = "2022.9.24"
description = "Python package for Mozilla's CA Bundle"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "poetry.lock"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3
        pkg_dict = {p.name: p for p in packages}
        assert pkg_dict["requests"].version == "2.28.0"
        assert pkg_dict["urllib3"].version == "1.26.12"
        assert pkg_dict["certifi"].version == "2022.9.24"

    def test_poetry_lock_packages_are_transitive(self) -> None:
        """Test that poetry.lock packages are marked as transitive."""
        content = """
[[package]]
name = "requests"
version = "2.28.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "poetry.lock"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert all(not p.is_direct for p in packages)


class TestPipfileLockParser:
    """Tests for Pipfile.lock parsing."""

    def test_parse_pipfile_lock(self) -> None:
        """Test parsing Pipfile.lock file."""
        content = """
{
    "_meta": {
        "hash": {"sha256": "abc123"},
        "pipfile-spec": 6,
        "requires": {"python_version": "3.8"}
    },
    "default": {
        "requests": {
            "version": "==2.28.0"
        },
        "urllib3": {
            "version": "==1.26.12"
        }
    },
    "develop": {
        "pytest": {
            "version": "==7.0.0"
        }
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "Pipfile.lock"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert len(packages) == 3
        pkg_dict = {p.name: p for p in packages}
        assert pkg_dict["requests"].version == "2.28.0"
        assert pkg_dict["urllib3"].version == "1.26.12"
        assert pkg_dict["pytest"].version == "7.0.0"

    def test_pipfile_lock_packages_are_transitive(self) -> None:
        """Test that Pipfile.lock packages are marked as transitive."""
        content = """
{
    "default": {
        "requests": {"version": "==2.28.0"}
    },
    "develop": {}
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
            new_path = path.parent / "Pipfile.lock"
            path.rename(new_path)

        analyzer = PythonAnalyzer()
        packages = analyzer.parse(new_path)
        new_path.unlink()

        assert all(not p.is_direct for p in packages)


class TestPackageNameNormalization:
    """Tests for package name normalization."""

    def test_normalize_underscores(self) -> None:
        """Test normalizing underscores to hyphens."""
        content = "my_package==1.0.0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert packages[0].name == "my-package"

    def test_normalize_dots(self) -> None:
        """Test normalizing dots to hyphens."""
        content = "zope.interface==5.0.0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        assert packages[0].name == "zope-interface"

    def test_normalize_case(self) -> None:
        """Test normalizing to lowercase."""
        content = "Flask==2.0.0\nDjango==4.0.0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requirements.txt"
            path.write_text(content)

            analyzer = PythonAnalyzer()
            packages = analyzer.parse(path)

        names = [p.name for p in packages]
        assert "flask" in names
        assert "django" in names


class TestFileDetection:
    """Tests for file detection."""

    def test_detect_all_python_files(self) -> None:
        """Test detecting all Python dependency files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create various files
            (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")
            (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
            (tmp_path / "Pipfile").write_text("[packages]\n")
            (tmp_path / "poetry.lock").write_text("[[package]]\nname='x'\nversion='1'\n")
            (tmp_path / "Pipfile.lock").write_text('{"default":{},"develop":{}}\n')
            (tmp_path / "other.txt").write_text("not a dependency file\n")

            analyzer = PythonAnalyzer()
            files = analyzer.detect_files(tmp_path)

            filenames = [f.name for f in files]
            assert "requirements.txt" in filenames
            assert "pyproject.toml" in filenames
            assert "Pipfile" in filenames
            assert "poetry.lock" in filenames
            assert "Pipfile.lock" in filenames
            assert "other.txt" not in filenames

    def test_detect_nested_files(self) -> None:
        """Test detecting files in nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create nested structure
            (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")
            subdir = tmp_path / "subproject"
            subdir.mkdir()
            (subdir / "requirements.txt").write_text("flask>=2.0.0\n")

            analyzer = PythonAnalyzer()
            files = analyzer.detect_files(tmp_path)

            assert len(files) == 2
