"""Tests for NPM dependency analyzer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cve_sentinel.analyzers.npm import NpmAnalyzer


class TestNpmAnalyzer:
    """Tests for NpmAnalyzer class."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer(analysis_level=2)

    def test_ecosystem(self, analyzer: NpmAnalyzer) -> None:
        """Test ecosystem property."""
        assert analyzer.ecosystem == "npm"

    def test_manifest_patterns(self, analyzer: NpmAnalyzer) -> None:
        """Test manifest patterns."""
        assert "package.json" in analyzer.manifest_patterns

    def test_lock_patterns(self, analyzer: NpmAnalyzer) -> None:
        """Test lock file patterns."""
        patterns = analyzer.lock_patterns
        assert "package-lock.json" in patterns
        assert "yarn.lock" in patterns
        assert "pnpm-lock.yaml" in patterns


class TestPackageJsonParser:
    """Tests for package.json parsing."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer()

    def test_parse_dependencies(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing dependencies from package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "dependencies": {"express": "^4.18.0", "lodash": "~4.17.21"},
                }
            )
        )

        packages = analyzer.parse(package_json)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "express" in names
        assert "lodash" in names

        express_pkg = next(p for p in packages if p.name == "express")
        assert express_pkg.version == "4.18.0"
        assert express_pkg.is_direct is True
        assert express_pkg.ecosystem == "npm"

    def test_parse_dev_dependencies(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing devDependencies from package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "devDependencies": {"jest": "^29.0.0", "typescript": "^5.0.0"},
                }
            )
        )

        packages = analyzer.parse(package_json)

        assert len(packages) == 2
        assert all(p.is_direct for p in packages)

    def test_parse_scoped_packages(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing scoped packages (@org/package)."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "dependencies": {"@types/node": "^20.0.0", "@babel/core": "^7.22.0"},
                }
            )
        )

        packages = analyzer.parse(package_json)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "@types/node" in names
        assert "@babel/core" in names

    def test_parse_empty_package_json(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing package.json without dependencies."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"name": "test-project"}))

        packages = analyzer.parse(package_json)
        assert len(packages) == 0

    def test_parse_version_specifiers(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing various version specifiers."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "dependencies": {
                        "caret": "^1.2.3",
                        "tilde": "~1.2.3",
                        "exact": "1.2.3",
                        "gte": ">=1.2.3",
                        "range": "1.0.0 - 2.0.0",
                    },
                }
            )
        )

        packages = analyzer.parse(package_json)

        versions = {p.name: p.version for p in packages}
        assert versions["caret"] == "1.2.3"
        assert versions["tilde"] == "1.2.3"
        assert versions["exact"] == "1.2.3"
        assert versions["gte"] == "1.2.3"
        assert versions["range"] == "1.0.0"

    def test_line_numbers(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test that line numbers are captured."""
        package_json = tmp_path / "package.json"
        content = """{
  "name": "test-project",
  "dependencies": {
    "express": "^4.18.0"
  }
}"""
        package_json.write_text(content)

        packages = analyzer.parse(package_json)

        assert len(packages) == 1
        assert packages[0].source_line is not None
        assert packages[0].source_line == 4


class TestPackageLockParser:
    """Tests for package-lock.json parsing."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer()

    def test_parse_v2_format(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing package-lock.json v2/v3 format."""
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "lockfileVersion": 3,
                    "packages": {
                        "": {"name": "test-project", "dependencies": {"express": "^4.18.0"}},
                        "node_modules/express": {
                            "version": "4.18.2",
                            "resolved": "https://registry.npmjs.org/express/-/express-4.18.2.tgz",
                        },
                        "node_modules/accepts": {"version": "1.3.8"},
                    },
                }
            )
        )

        packages = analyzer.parse(lock_file)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "express" in names
        assert "accepts" in names
        assert all(p.is_direct is False for p in packages)

    def test_parse_scoped_packages_in_lock(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing scoped packages in package-lock.json."""
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "lockfileVersion": 3,
                    "packages": {
                        "": {"name": "test-project"},
                        "node_modules/@types/node": {"version": "20.4.5"},
                        "node_modules/@babel/core": {"version": "7.22.9"},
                    },
                }
            )
        )

        packages = analyzer.parse(lock_file)

        names = {p.name for p in packages}
        assert "@types/node" in names
        assert "@babel/core" in names

    def test_skip_link_protocol(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test that link: protocol packages are skipped."""
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "lockfileVersion": 3,
                    "packages": {
                        "": {"name": "test-project"},
                        "node_modules/local-pkg": {"link": True},
                        "node_modules/express": {"version": "4.18.2"},
                    },
                }
            )
        )

        packages = analyzer.parse(lock_file)

        names = {p.name for p in packages}
        assert "local-pkg" not in names
        assert "express" in names

    def test_parse_v1_format(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing package-lock.json v1 format."""
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "lockfileVersion": 1,
                    "dependencies": {
                        "express": {
                            "version": "4.18.2",
                            "dependencies": {"accepts": {"version": "1.3.8"}},
                        }
                    },
                }
            )
        )

        packages = analyzer.parse(lock_file)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "express" in names
        assert "accepts" in names


class TestYarnLockParser:
    """Tests for yarn.lock parsing."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer()

    def test_parse_yarn_lock(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing yarn.lock file."""
        yarn_lock = tmp_path / "yarn.lock"
        yarn_lock.write_text("""# THIS IS AN AUTOGENERATED FILE. DO NOT EDIT THIS FILE DIRECTLY.
# yarn lockfile v1

express@^4.18.0:
  version "4.18.2"
  resolved "https://registry.yarnpkg.com/express/-/express-4.18.2.tgz"

lodash@^4.17.21:
  version "4.17.21"
  resolved "https://registry.yarnpkg.com/lodash/-/lodash-4.17.21.tgz"
""")

        packages = analyzer.parse(yarn_lock)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "express" in names
        assert "lodash" in names

        express_pkg = next(p for p in packages if p.name == "express")
        assert express_pkg.version == "4.18.2"

    def test_parse_scoped_packages_yarn(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing scoped packages in yarn.lock."""
        yarn_lock = tmp_path / "yarn.lock"
        yarn_lock.write_text("""# yarn lockfile v1

"@types/node@^20.0.0":
  version "20.4.5"
  resolved "https://registry.yarnpkg.com/@types/node/-/node-20.4.5.tgz"

"@babel/core@^7.22.0":
  version "7.22.9"
  resolved "https://registry.yarnpkg.com/@babel/core/-/core-7.22.9.tgz"
""")

        packages = analyzer.parse(yarn_lock)

        names = {p.name for p in packages}
        assert "@types/node" in names
        assert "@babel/core" in names

    def test_parse_multiple_version_specifiers(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing packages with multiple version specifiers."""
        yarn_lock = tmp_path / "yarn.lock"
        yarn_lock.write_text("""# yarn lockfile v1

"lodash@^4.17.0", "lodash@^4.17.21":
  version "4.17.21"
  resolved "https://registry.yarnpkg.com/lodash/-/lodash-4.17.21.tgz"
""")

        packages = analyzer.parse(yarn_lock)

        # Should only have one lodash entry (deduplicated)
        lodash_pkgs = [p for p in packages if p.name == "lodash"]
        assert len(lodash_pkgs) == 1
        assert lodash_pkgs[0].version == "4.17.21"


class TestPnpmLockParser:
    """Tests for pnpm-lock.yaml parsing."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer()

    def test_parse_pnpm_lock(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing pnpm-lock.yaml file."""
        pnpm_lock = tmp_path / "pnpm-lock.yaml"
        pnpm_lock.write_text("""lockfileVersion: '6.0'

packages:
  /express@4.18.2:
    resolution: {integrity: sha512-xxx}
    engines: {node: '>= 0.10.0'}
    dependencies:
      accepts: 1.3.8

  /accepts@1.3.8:
    resolution: {integrity: sha512-yyy}
""")

        packages = analyzer.parse(pnpm_lock)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "express" in names
        assert "accepts" in names

    def test_parse_scoped_packages_pnpm(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing scoped packages in pnpm-lock.yaml."""
        pnpm_lock = tmp_path / "pnpm-lock.yaml"
        pnpm_lock.write_text("""lockfileVersion: '6.0'

packages:
  /@types/node@20.4.5:
    resolution: {integrity: sha512-xxx}

  /@babel/core@7.22.9:
    resolution: {integrity: sha512-yyy}
""")

        packages = analyzer.parse(pnpm_lock)

        names = {p.name for p in packages}
        assert "@types/node" in names
        assert "@babel/core" in names

    def test_parse_older_pnpm_format(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test parsing older pnpm-lock.yaml format with dependencies at root."""
        pnpm_lock = tmp_path / "pnpm-lock.yaml"
        pnpm_lock.write_text("""lockfileVersion: 5.4

dependencies:
  express: 4.18.2
  lodash:
    version: 4.17.21
""")

        packages = analyzer.parse(pnpm_lock)

        names = {p.name for p in packages}
        assert "express" in names
        assert "lodash" in names


class TestFileDetection:
    """Tests for dependency file detection."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer(analysis_level=2)

    def test_detect_package_json(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test detecting package.json files."""
        (tmp_path / "package.json").write_text('{"name": "test"}')

        files = analyzer.detect_files(tmp_path)

        assert len(files) == 1
        assert files[0].name == "package.json"

    def test_detect_all_lock_files(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test detecting all types of lock files."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "package-lock.json").write_text("{}")
        (tmp_path / "yarn.lock").write_text("")
        (tmp_path / "pnpm-lock.yaml").write_text("")

        files = analyzer.detect_files(tmp_path)

        names = {f.name for f in files}
        assert "package.json" in names
        assert "package-lock.json" in names
        assert "yarn.lock" in names
        assert "pnpm-lock.yaml" in names

    def test_level_1_only_manifest(self, tmp_path: Path) -> None:
        """Test that level 1 only detects manifest files."""
        analyzer = NpmAnalyzer(analysis_level=1)

        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "package-lock.json").write_text("{}")

        files = analyzer.detect_files(tmp_path)

        assert len(files) == 1
        assert files[0].name == "package.json"

    def test_exclude_node_modules(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test that node_modules directory is excluded."""
        (tmp_path / "package.json").write_text('{"name": "root"}')
        node_modules = tmp_path / "node_modules" / "some-pkg"
        node_modules.mkdir(parents=True)
        (node_modules / "package.json").write_text('{"name": "some-pkg"}')

        files = analyzer.detect_files(tmp_path)

        # Should only find root package.json, not the one in node_modules
        assert len(files) == 1
        assert files[0].parent == tmp_path


class TestAnalyze:
    """Tests for full analysis workflow."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer(analysis_level=2)

    def test_analyze_project(self, analyzer: NpmAnalyzer, tmp_path: Path) -> None:
        """Test full project analysis."""
        # Create package.json
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "test-project", "dependencies": {"express": "^4.18.0"}})
        )

        # Create package-lock.json
        (tmp_path / "package-lock.json").write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "lockfileVersion": 3,
                    "packages": {
                        "": {"name": "test-project"},
                        "node_modules/express": {"version": "4.18.2"},
                        "node_modules/accepts": {"version": "1.3.8"},
                    },
                }
            )
        )

        result = analyzer.analyze(tmp_path)

        assert result.package_count >= 3
        assert len(result.scanned_files) == 2
        assert len(result.errors) == 0

        # Check we have both direct and transitive packages
        assert len(result.direct_packages) >= 1
        assert len(result.transitive_packages) >= 2


class TestVersionNormalization:
    """Tests for version string normalization."""

    @pytest.fixture
    def analyzer(self) -> NpmAnalyzer:
        """Create NpmAnalyzer instance."""
        return NpmAnalyzer()

    def test_caret_version(self, analyzer: NpmAnalyzer) -> None:
        """Test caret version normalization."""
        assert analyzer._normalize_version("^1.2.3") == "1.2.3"

    def test_tilde_version(self, analyzer: NpmAnalyzer) -> None:
        """Test tilde version normalization."""
        assert analyzer._normalize_version("~1.2.3") == "1.2.3"

    def test_gte_version(self, analyzer: NpmAnalyzer) -> None:
        """Test >= version normalization."""
        assert analyzer._normalize_version(">=1.2.3") == "1.2.3"

    def test_range_version(self, analyzer: NpmAnalyzer) -> None:
        """Test range version normalization."""
        assert analyzer._normalize_version("1.0.0 - 2.0.0") == "1.0.0"

    def test_or_version(self, analyzer: NpmAnalyzer) -> None:
        """Test OR version normalization."""
        assert analyzer._normalize_version("^1.0.0 || ^2.0.0") == "1.0.0"

    def test_special_protocols(self, analyzer: NpmAnalyzer) -> None:
        """Test special protocol versions are preserved."""
        assert analyzer._normalize_version("file:../local") == "file:../local"
        assert analyzer._normalize_version("link:../local") == "link:../local"
        assert analyzer._normalize_version("workspace:*") == "workspace:*"

    def test_npm_alias(self, analyzer: NpmAnalyzer) -> None:
        """Test npm alias version extraction."""
        assert analyzer._normalize_version("npm:@scope/pkg@1.0.0") == "1.0.0"
