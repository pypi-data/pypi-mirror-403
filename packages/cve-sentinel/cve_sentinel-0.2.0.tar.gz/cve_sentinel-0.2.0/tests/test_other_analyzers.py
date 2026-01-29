"""Tests for Go, Maven, Gradle, Ruby, Rust, and PHP analyzers."""

from __future__ import annotations

from pathlib import Path

import pytest

from cve_sentinel.analyzers.go import GoAnalyzer
from cve_sentinel.analyzers.maven import GradleAnalyzer, MavenAnalyzer
from cve_sentinel.analyzers.php import PhpAnalyzer
from cve_sentinel.analyzers.ruby import RubyAnalyzer
from cve_sentinel.analyzers.rust import RustAnalyzer

# =============================================================================
# Go Analyzer Tests
# =============================================================================


class TestGoAnalyzer:
    """Tests for GoAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> GoAnalyzer:
        return GoAnalyzer()

    def test_ecosystem(self, analyzer: GoAnalyzer) -> None:
        assert analyzer.ecosystem == "go"

    def test_parse_go_mod(self, analyzer: GoAnalyzer, tmp_path: Path) -> None:
        """Test parsing go.mod file."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("""module example.com/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/stretchr/testify v1.8.4 // indirect
)

require github.com/pkg/errors v0.9.1
""")
        packages = analyzer.parse(go_mod)

        assert len(packages) == 3
        names = {p.name for p in packages}
        assert "github.com/gin-gonic/gin" in names
        assert "github.com/stretchr/testify" in names
        assert "github.com/pkg/errors" in names

        # Check direct vs indirect
        gin_pkg = next(p for p in packages if "gin" in p.name)
        assert gin_pkg.is_direct is True

        testify_pkg = next(p for p in packages if "testify" in p.name)
        assert testify_pkg.is_direct is False  # marked as indirect

    def test_parse_go_sum(self, analyzer: GoAnalyzer, tmp_path: Path) -> None:
        """Test parsing go.sum file."""
        go_sum = tmp_path / "go.sum"
        go_sum.write_text("""github.com/gin-gonic/gin v1.9.1 h1:abc123=
github.com/gin-gonic/gin v1.9.1/go.mod h1:def456=
github.com/pkg/errors v0.9.1 h1:xyz789=
""")
        packages = analyzer.parse(go_sum)

        # Should deduplicate entries
        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "github.com/gin-gonic/gin" in names
        assert "github.com/pkg/errors" in names

    def test_version_normalization(self, analyzer: GoAnalyzer) -> None:
        """Test Go version normalization."""
        assert analyzer._normalize_version("v1.2.3") == "1.2.3"
        assert analyzer._normalize_version("v0.0.0-20210101+incompatible") == "0.0.0-20210101"


# =============================================================================
# Maven Analyzer Tests
# =============================================================================


class TestMavenAnalyzer:
    """Tests for MavenAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> MavenAnalyzer:
        return MavenAnalyzer()

    def test_ecosystem(self, analyzer: MavenAnalyzer) -> None:
        assert analyzer.ecosystem == "maven"

    def test_parse_pom_xml(self, analyzer: MavenAnalyzer, tmp_path: Path) -> None:
        """Test parsing pom.xml file."""
        pom = tmp_path / "pom.xml"
        pom.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>myproject</artifactId>
    <version>1.0.0</version>

    <properties>
        <spring.version>5.3.20</spring.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>${spring.version}</version>
        </dependency>
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>31.1-jre</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
""")
        packages = analyzer.parse(pom)

        # Should have 2 packages (junit is test scope, skipped)
        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "org.springframework:spring-core" in names
        assert "com.google.guava:guava" in names

        # Check property resolution
        spring_pkg = next(p for p in packages if "spring" in p.name)
        assert spring_pkg.version == "5.3.20"

    def test_parse_pom_without_namespace(self, analyzer: MavenAnalyzer, tmp_path: Path) -> None:
        """Test parsing pom.xml without namespace."""
        pom = tmp_path / "pom.xml"
        pom.write_text("""<?xml version="1.0"?>
<project>
    <dependencies>
        <dependency>
            <groupId>org.example</groupId>
            <artifactId>lib</artifactId>
            <version>1.0.0</version>
        </dependency>
    </dependencies>
</project>
""")
        packages = analyzer.parse(pom)
        assert len(packages) == 1
        assert packages[0].name == "org.example:lib"


# =============================================================================
# Gradle Analyzer Tests
# =============================================================================


class TestGradleAnalyzer:
    """Tests for GradleAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> GradleAnalyzer:
        return GradleAnalyzer()

    def test_ecosystem(self, analyzer: GradleAnalyzer) -> None:
        assert analyzer.ecosystem == "maven"

    def test_parse_build_gradle(self, analyzer: GradleAnalyzer, tmp_path: Path) -> None:
        """Test parsing build.gradle file."""
        gradle = tmp_path / "build.gradle"
        gradle.write_text("""plugins {
    id 'java'
}

dependencies {
    implementation 'org.springframework:spring-core:5.3.20'
    api 'com.google.guava:guava:31.1-jre'
    testImplementation 'junit:junit:4.13.2'
}
""")
        packages = analyzer.parse(gradle)

        # testImplementation should be skipped
        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "org.springframework:spring-core" in names
        assert "com.google.guava:guava" in names

    def test_parse_build_gradle_kts(self, analyzer: GradleAnalyzer, tmp_path: Path) -> None:
        """Test parsing build.gradle.kts file."""
        gradle = tmp_path / "build.gradle.kts"
        gradle.write_text("""plugins {
    kotlin("jvm")
}

dependencies {
    implementation("org.jetbrains.kotlin:kotlin-stdlib:1.8.0")
    api("com.squareup.okhttp3:okhttp:4.10.0")
}
""")
        packages = analyzer.parse(gradle)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "org.jetbrains.kotlin:kotlin-stdlib" in names


# =============================================================================
# Ruby Analyzer Tests
# =============================================================================


class TestRubyAnalyzer:
    """Tests for RubyAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> RubyAnalyzer:
        return RubyAnalyzer()

    def test_ecosystem(self, analyzer: RubyAnalyzer) -> None:
        assert analyzer.ecosystem == "rubygems"

    def test_parse_gemfile(self, analyzer: RubyAnalyzer, tmp_path: Path) -> None:
        """Test parsing Gemfile."""
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text("""source 'https://rubygems.org'

gem 'rails', '~> 7.0.0'
gem 'pg', '>= 1.1'
gem 'puma'

# Comment
gem 'bootsnap', require: false
""")
        packages = analyzer.parse(gemfile)

        assert len(packages) == 4
        names = {p.name for p in packages}
        assert "rails" in names
        assert "pg" in names
        assert "puma" in names
        assert "bootsnap" in names

        rails_pkg = next(p for p in packages if p.name == "rails")
        assert rails_pkg.version == "7.0.0"

    def test_parse_gemfile_lock(self, analyzer: RubyAnalyzer, tmp_path: Path) -> None:
        """Test parsing Gemfile.lock."""
        lock = tmp_path / "Gemfile.lock"
        lock.write_text("""GEM
  remote: https://rubygems.org/
  specs:
    actioncable (7.0.4)
      actionpack (= 7.0.4)
    actionpack (7.0.4)
      rack (~> 2.2, >= 2.2.0)
    rack (2.2.5)

PLATFORMS
  ruby

DEPENDENCIES
  rails (~> 7.0.0)
""")
        packages = analyzer.parse(lock)

        assert len(packages) == 3
        names = {p.name for p in packages}
        assert "actioncable" in names
        assert "actionpack" in names
        assert "rack" in names


# =============================================================================
# Rust Analyzer Tests
# =============================================================================


class TestRustAnalyzer:
    """Tests for RustAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> RustAnalyzer:
        return RustAnalyzer()

    def test_ecosystem(self, analyzer: RustAnalyzer) -> None:
        assert analyzer.ecosystem == "crates.io"

    def test_parse_cargo_toml(self, analyzer: RustAnalyzer, tmp_path: Path) -> None:
        """Test parsing Cargo.toml file."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("""[package]
name = "myproject"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = { version = "1.28", features = ["full"] }
local-dep = { path = "../local" }

[dev-dependencies]
criterion = "0.4"
""")
        packages = analyzer.parse(cargo)

        # local-dep should be skipped (path dependency)
        assert len(packages) == 3
        names = {p.name for p in packages}
        assert "serde" in names
        assert "tokio" in names
        assert "criterion" in names
        assert "local-dep" not in names

    def test_parse_cargo_lock(self, analyzer: RustAnalyzer, tmp_path: Path) -> None:
        """Test parsing Cargo.lock file."""
        lock = tmp_path / "Cargo.lock"
        lock.write_text("""# This file is automatically @generated by Cargo.
version = 3

[[package]]
name = "serde"
version = "1.0.160"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "serde_json"
version = "1.0.96"
dependencies = [
 "serde",
]
""")
        packages = analyzer.parse(lock)

        assert len(packages) == 2
        names = {p.name for p in packages}
        assert "serde" in names
        assert "serde_json" in names


# =============================================================================
# PHP Analyzer Tests
# =============================================================================


class TestPhpAnalyzer:
    """Tests for PhpAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> PhpAnalyzer:
        return PhpAnalyzer()

    def test_ecosystem(self, analyzer: PhpAnalyzer) -> None:
        assert analyzer.ecosystem == "packagist"

    def test_parse_composer_json(self, analyzer: PhpAnalyzer, tmp_path: Path) -> None:
        """Test parsing composer.json file."""
        composer = tmp_path / "composer.json"
        composer.write_text("""{
    "name": "vendor/myproject",
    "require": {
        "php": ">=8.0",
        "laravel/framework": "^9.0",
        "guzzlehttp/guzzle": "^7.5"
    },
    "require-dev": {
        "phpunit/phpunit": "^9.5"
    }
}
""")
        packages = analyzer.parse(composer)

        # php requirement should be skipped
        assert len(packages) == 3
        names = {p.name for p in packages}
        assert "laravel/framework" in names
        assert "guzzlehttp/guzzle" in names
        assert "phpunit/phpunit" in names

        laravel_pkg = next(p for p in packages if "laravel" in p.name)
        assert laravel_pkg.version == "9.0"

    def test_parse_composer_lock(self, analyzer: PhpAnalyzer, tmp_path: Path) -> None:
        """Test parsing composer.lock file."""
        lock = tmp_path / "composer.lock"
        lock.write_text("""{
    "packages": [
        {
            "name": "laravel/framework",
            "version": "v9.52.0"
        },
        {
            "name": "guzzlehttp/guzzle",
            "version": "7.5.0"
        }
    ],
    "packages-dev": [
        {
            "name": "phpunit/phpunit",
            "version": "v9.6.0"
        }
    ]
}
""")
        packages = analyzer.parse(lock)

        assert len(packages) == 3

        # Version should have 'v' prefix removed
        laravel_pkg = next(p for p in packages if "laravel" in p.name)
        assert laravel_pkg.version == "9.52.0"


# =============================================================================
# File Detection Tests
# =============================================================================


class TestFileDetection:
    """Tests for file detection across all analyzers."""

    def test_go_detect_files(self, tmp_path: Path) -> None:
        """Test Go file detection."""
        (tmp_path / "go.mod").write_text("module test")
        (tmp_path / "go.sum").write_text("")

        analyzer = GoAnalyzer()
        files = analyzer.detect_files(tmp_path)

        names = {f.name for f in files}
        assert "go.mod" in names
        assert "go.sum" in names

    def test_maven_detect_files(self, tmp_path: Path) -> None:
        """Test Maven file detection."""
        (tmp_path / "pom.xml").write_text("<project></project>")

        analyzer = MavenAnalyzer()
        files = analyzer.detect_files(tmp_path)

        assert len(files) == 1
        assert files[0].name == "pom.xml"

    def test_ruby_detect_files(self, tmp_path: Path) -> None:
        """Test Ruby file detection."""
        (tmp_path / "Gemfile").write_text("")
        (tmp_path / "Gemfile.lock").write_text("")

        analyzer = RubyAnalyzer()
        files = analyzer.detect_files(tmp_path)

        names = {f.name for f in files}
        assert "Gemfile" in names
        assert "Gemfile.lock" in names

    def test_rust_detect_files(self, tmp_path: Path) -> None:
        """Test Rust file detection."""
        (tmp_path / "Cargo.toml").write_text("[package]")
        (tmp_path / "Cargo.lock").write_text("")

        analyzer = RustAnalyzer()
        files = analyzer.detect_files(tmp_path)

        names = {f.name for f in files}
        assert "Cargo.toml" in names
        assert "Cargo.lock" in names

    def test_php_detect_files(self, tmp_path: Path) -> None:
        """Test PHP file detection."""
        (tmp_path / "composer.json").write_text("{}")
        (tmp_path / "composer.lock").write_text("{}")

        analyzer = PhpAnalyzer()
        files = analyzer.detect_files(tmp_path)

        names = {f.name for f in files}
        assert "composer.json" in names
        assert "composer.lock" in names
