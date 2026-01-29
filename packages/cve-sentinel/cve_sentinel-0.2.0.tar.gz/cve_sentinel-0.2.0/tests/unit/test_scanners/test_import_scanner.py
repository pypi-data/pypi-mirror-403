"""Tests for import statement scanners."""

from __future__ import annotations

from pathlib import Path

import pytest

from cve_sentinel.scanners.import_scanner import (
    GoScanner,
    ImportReference,
    ImportScanner,
    JavaScanner,
    JavaScriptScanner,
    PHPScanner,
    PythonScanner,
    RubyScanner,
    RustScanner,
    get_scanner_for_ecosystem,
)


class TestImportReference:
    """Tests for ImportReference dataclass."""

    def test_create_import_reference(self, temp_dir: Path) -> None:
        """Test creating an ImportReference."""
        ref = ImportReference(
            package_name="lodash",
            file_path=temp_dir / "test.js",
            line_number=1,
            import_statement="import lodash from 'lodash';",
            ecosystem="npm",
        )

        assert ref.package_name == "lodash"
        assert ref.line_number == 1
        assert ref.ecosystem == "npm"

    def test_to_dict(self, temp_dir: Path) -> None:
        """Test serialization to dictionary."""
        ref = ImportReference(
            package_name="lodash",
            file_path=temp_dir / "test.js",
            line_number=1,
            import_statement="import lodash from 'lodash';",
            ecosystem="npm",
        )

        result = ref.to_dict()

        assert result["package_name"] == "lodash"
        assert result["line_number"] == 1
        assert result["ecosystem"] == "npm"


class TestJavaScriptScanner:
    """Tests for JavaScript/TypeScript import scanner."""

    @pytest.fixture
    def scanner(self) -> JavaScriptScanner:
        """Create a JavaScript scanner."""
        return JavaScriptScanner()

    def test_import_from_pattern(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test import ... from 'package' pattern."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import lodash from 'lodash';
import { map } from 'lodash';
import * as _ from 'lodash';
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 3
        assert all(ref.package_name == "lodash" for ref in refs)

    def test_require_pattern(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test require('package') pattern."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
const lodash = require('lodash');
const express = require('express');
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "lodash"
        assert refs[1].package_name == "express"

    def test_dynamic_import_pattern(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test import('package') dynamic import pattern."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
const module = await import('lodash');
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "lodash"

    def test_scoped_packages(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test scoped packages (@scope/package)."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import { something } from '@angular/core';
const pkg = require('@babel/core');
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "@angular/core"
        assert refs[1].package_name == "@babel/core"

    def test_subpath_imports(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test subpath imports return base package."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import { something } from 'lodash/map';
import util from '@angular/core/testing';
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "lodash"
        assert refs[1].package_name == "@angular/core"

    def test_excludes_relative_imports(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test relative imports are excluded."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import something from './local';
import other from '../parent';
import lodash from 'lodash';
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "lodash"

    def test_excludes_node_builtins(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test node: protocol built-ins are excluded."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import fs from 'node:fs';
import path from 'node:path';
import lodash from 'lodash';
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "lodash"

    def test_typescript_extensions(self, scanner: JavaScriptScanner, temp_dir: Path) -> None:
        """Test TypeScript file extensions are supported."""
        for ext in [".ts", ".tsx", ".mjs", ".cjs"]:
            test_file = temp_dir / f"test{ext}"
            test_file.write_text("import lodash from 'lodash';")

            refs = scanner.scan_file(test_file)

            assert len(refs) == 1
            assert refs[0].package_name == "lodash"


class TestPythonScanner:
    """Tests for Python import scanner."""

    @pytest.fixture
    def scanner(self) -> PythonScanner:
        """Create a Python scanner."""
        return PythonScanner()

    def test_import_pattern(self, scanner: PythonScanner, temp_dir: Path) -> None:
        """Test import package pattern."""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
import requests
import numpy
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "requests"
        assert refs[1].package_name == "numpy"

    def test_from_import_pattern(self, scanner: PythonScanner, temp_dir: Path) -> None:
        """Test from package import ... pattern."""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
from requests import Session
from numpy import array
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "requests"
        assert refs[1].package_name == "numpy"

    def test_from_submodule_import(self, scanner: PythonScanner, temp_dir: Path) -> None:
        """Test from package.submodule import ... pattern."""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
from requests.auth import HTTPBasicAuth
from numpy.random import randint
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "requests"
        assert refs[1].package_name == "numpy"

    def test_excludes_stdlib(self, scanner: PythonScanner, temp_dir: Path) -> None:
        """Test standard library imports are excluded."""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
import os
import sys
import json
from pathlib import Path
from collections import defaultdict
import requests
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "requests"

    def test_import_with_alias(self, scanner: PythonScanner, temp_dir: Path) -> None:
        """Test import with alias."""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
import numpy as np
import pandas as pd
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "numpy"
        assert refs[1].package_name == "pandas"


class TestGoScanner:
    """Tests for Go import scanner."""

    @pytest.fixture
    def scanner(self) -> GoScanner:
        """Create a Go scanner."""
        return GoScanner()

    def test_single_import(self, scanner: GoScanner, temp_dir: Path) -> None:
        """Test single import statement."""
        test_file = temp_dir / "test.go"
        test_file.write_text("""
package main

import "github.com/gin-gonic/gin"
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "github.com/gin-gonic/gin"

    def test_import_block(self, scanner: GoScanner, temp_dir: Path) -> None:
        """Test import block with multiple packages."""
        test_file = temp_dir / "test.go"
        test_file.write_text("""
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/spf13/cobra"
)
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "github.com/gin-gonic/gin"
        assert refs[1].package_name == "github.com/spf13/cobra"

    def test_excludes_stdlib(self, scanner: GoScanner, temp_dir: Path) -> None:
        """Test standard library imports are excluded."""
        test_file = temp_dir / "test.go"
        test_file.write_text("""
package main

import (
    "fmt"
    "net/http"
    "github.com/gin-gonic/gin"
)
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "github.com/gin-gonic/gin"

    def test_aliased_import(self, scanner: GoScanner, temp_dir: Path) -> None:
        """Test aliased import."""
        test_file = temp_dir / "test.go"
        test_file.write_text("""
package main

import (
    mux "github.com/gorilla/mux"
)
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "github.com/gorilla/mux"


class TestJavaScanner:
    """Tests for Java import scanner."""

    @pytest.fixture
    def scanner(self) -> JavaScanner:
        """Create a Java scanner."""
        return JavaScanner()

    def test_class_import(self, scanner: JavaScanner, temp_dir: Path) -> None:
        """Test class import statement."""
        test_file = temp_dir / "Test.java"
        test_file.write_text("""
package com.example;

import org.apache.commons.lang3.StringUtils;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "org.apache.commons"

    def test_wildcard_import(self, scanner: JavaScanner, temp_dir: Path) -> None:
        """Test wildcard import statement."""
        test_file = temp_dir / "Test.java"
        test_file.write_text("""
package com.example;

import org.springframework.web.*;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "org.springframework.web"

    def test_static_import(self, scanner: JavaScanner, temp_dir: Path) -> None:
        """Test static import statement."""
        test_file = temp_dir / "Test.java"
        test_file.write_text("""
package com.example;

import static org.junit.Assert.assertEquals;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "org.junit.Assert"

    def test_excludes_stdlib(self, scanner: JavaScanner, temp_dir: Path) -> None:
        """Test Java standard library imports are excluded."""
        test_file = temp_dir / "Test.java"
        test_file.write_text("""
package com.example;

import java.util.List;
import javax.servlet.http.HttpServlet;
import org.apache.commons.lang3.StringUtils;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "org.apache.commons"


class TestRubyScanner:
    """Tests for Ruby require scanner."""

    @pytest.fixture
    def scanner(self) -> RubyScanner:
        """Create a Ruby scanner."""
        return RubyScanner()

    def test_require_pattern(self, scanner: RubyScanner, temp_dir: Path) -> None:
        """Test require 'gem' pattern."""
        test_file = temp_dir / "test.rb"
        test_file.write_text("""
require 'rails'
require 'sinatra'
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "rails"
        assert refs[1].package_name == "sinatra"

    def test_require_double_quotes(self, scanner: RubyScanner, temp_dir: Path) -> None:
        """Test require with double quotes."""
        test_file = temp_dir / "test.rb"
        test_file.write_text("""
require "rails"
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "rails"

    def test_require_with_subpath(self, scanner: RubyScanner, temp_dir: Path) -> None:
        """Test require with subpath returns base gem."""
        test_file = temp_dir / "test.rb"
        test_file.write_text("""
require 'active_support/core_ext'
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "active_support"

    def test_excludes_require_relative(self, scanner: RubyScanner, temp_dir: Path) -> None:
        """Test require_relative is excluded."""
        test_file = temp_dir / "test.rb"
        test_file.write_text("""
require_relative 'local_file'
require 'rails'
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "rails"

    def test_excludes_stdlib(self, scanner: RubyScanner, temp_dir: Path) -> None:
        """Test Ruby standard library is excluded."""
        test_file = temp_dir / "test.rb"
        test_file.write_text("""
require 'json'
require 'yaml'
require 'rails'
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "rails"


class TestRustScanner:
    """Tests for Rust use scanner."""

    @pytest.fixture
    def scanner(self) -> RustScanner:
        """Create a Rust scanner."""
        return RustScanner()

    def test_use_pattern(self, scanner: RustScanner, temp_dir: Path) -> None:
        """Test use crate::... pattern."""
        test_file = temp_dir / "test.rs"
        test_file.write_text("""
use serde::Serialize;
use tokio::runtime;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "serde"
        assert refs[1].package_name == "tokio"

    def test_extern_crate_pattern(self, scanner: RustScanner, temp_dir: Path) -> None:
        """Test extern crate pattern."""
        test_file = temp_dir / "test.rs"
        test_file.write_text("""
extern crate serde;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "serde"

    def test_excludes_stdlib(self, scanner: RustScanner, temp_dir: Path) -> None:
        """Test std library is excluded."""
        test_file = temp_dir / "test.rs"
        test_file.write_text("""
use std::collections::HashMap;
use core::mem;
use serde::Serialize;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "serde"

    def test_excludes_self_crate(self, scanner: RustScanner, temp_dir: Path) -> None:
        """Test crate/self/super are excluded."""
        test_file = temp_dir / "test.rs"
        test_file.write_text("""
use crate::module;
use self::submodule;
use super::parent;
use serde::Serialize;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "serde"


class TestPHPScanner:
    """Tests for PHP use scanner."""

    @pytest.fixture
    def scanner(self) -> PHPScanner:
        """Create a PHP scanner."""
        return PHPScanner()

    def test_use_pattern(self, scanner: PHPScanner, temp_dir: Path) -> None:
        """Test use Namespace\\Class pattern."""
        test_file = temp_dir / "test.php"
        test_file.write_text("""<?php
use Symfony\\Component\\HttpFoundation\\Request;
use Laravel\\Framework\\Support;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 2
        assert refs[0].package_name == "symfony/component"
        assert refs[1].package_name == "laravel/framework"

    def test_excludes_internal(self, scanner: PHPScanner, temp_dir: Path) -> None:
        """Test PHP internal classes are excluded."""
        test_file = temp_dir / "test.php"
        test_file.write_text("""<?php
use Exception;
use DateTime;
use Symfony\\Component\\HttpFoundation\\Request;
""")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "symfony/component"


class TestImportScanner:
    """Tests for the main ImportScanner class."""

    @pytest.fixture
    def scanner(self) -> ImportScanner:
        """Create an ImportScanner."""
        return ImportScanner()

    def test_scan_directory_all_languages(self, scanner: ImportScanner, temp_dir: Path) -> None:
        """Test scanning directory with multiple languages."""
        # Create test files
        (temp_dir / "test.js").write_text("import lodash from 'lodash';")
        (temp_dir / "test.py").write_text("import requests")

        results = scanner.scan_directory(temp_dir)

        assert "npm" in results
        assert "pypi" in results
        assert len(results["npm"]) == 1
        assert len(results["pypi"]) == 1

    def test_scan_specific_ecosystems(self, temp_dir: Path) -> None:
        """Test scanning with specific ecosystems."""
        scanner = ImportScanner(ecosystems=["npm"])

        (temp_dir / "test.js").write_text("import lodash from 'lodash';")
        (temp_dir / "test.py").write_text("import requests")

        results = scanner.scan_directory(temp_dir)

        assert "npm" in results
        assert "pypi" not in results

    def test_scan_file(self, scanner: ImportScanner, temp_dir: Path) -> None:
        """Test scanning a single file."""
        test_file = temp_dir / "test.js"
        test_file.write_text("import lodash from 'lodash';")

        refs = scanner.scan_file(test_file)

        assert len(refs) == 1
        assert refs[0].package_name == "lodash"

    def test_get_imports_for_package(self, scanner: ImportScanner, temp_dir: Path) -> None:
        """Test filtering imports for a specific package."""
        test_file = temp_dir / "test.js"
        test_file.write_text("""
import lodash from 'lodash';
import express from 'express';
import { map } from 'lodash';
""")

        refs = scanner.scan_file(test_file)
        lodash_refs = scanner.get_imports_for_package("lodash", refs)

        assert len(lodash_refs) == 2
        assert all(ref.package_name == "lodash" for ref in lodash_refs)

    def test_get_supported_extensions(self) -> None:
        """Test getting supported file extensions."""
        extensions = ImportScanner.get_supported_extensions()

        assert ".js" in extensions
        assert ".py" in extensions
        assert ".go" in extensions
        assert ".java" in extensions
        assert ".rb" in extensions
        assert ".rs" in extensions
        assert ".php" in extensions

    def test_get_supported_ecosystems(self) -> None:
        """Test getting supported ecosystems."""
        ecosystems = ImportScanner.get_supported_ecosystems()

        assert "npm" in ecosystems
        assert "pypi" in ecosystems
        assert "go" in ecosystems
        assert "maven" in ecosystems
        assert "rubygems" in ecosystems
        assert "crates.io" in ecosystems
        assert "packagist" in ecosystems

    def test_excludes_node_modules(self, scanner: ImportScanner, temp_dir: Path) -> None:
        """Test node_modules directory is excluded."""
        # Create files in node_modules
        node_modules = temp_dir / "node_modules" / "lodash"
        node_modules.mkdir(parents=True)
        (node_modules / "index.js").write_text("import something from 'something';")

        # Create file outside node_modules
        (temp_dir / "test.js").write_text("import lodash from 'lodash';")

        results = scanner.scan_directory(temp_dir)

        assert len(results.get("npm", [])) == 1
        assert results["npm"][0].package_name == "lodash"


class TestGetScannerForEcosystem:
    """Tests for get_scanner_for_ecosystem function."""

    def test_get_npm_scanner(self) -> None:
        """Test getting npm scanner."""
        scanner = get_scanner_for_ecosystem("npm")

        assert scanner is not None
        assert isinstance(scanner, JavaScriptScanner)

    def test_get_pypi_scanner(self) -> None:
        """Test getting pypi scanner."""
        scanner = get_scanner_for_ecosystem("pypi")

        assert scanner is not None
        assert isinstance(scanner, PythonScanner)

    def test_get_unknown_scanner(self) -> None:
        """Test getting scanner for unknown ecosystem."""
        scanner = get_scanner_for_ecosystem("unknown")

        assert scanner is None
