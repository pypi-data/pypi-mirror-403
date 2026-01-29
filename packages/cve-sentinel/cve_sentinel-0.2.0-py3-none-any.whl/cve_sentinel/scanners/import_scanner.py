"""Import statement scanner for Level 3 analysis.

This module scans source code files to find import/require statements
and maps them to package names for vulnerability detection.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Type

logger = logging.getLogger(__name__)


@dataclass
class ImportReference:
    """Reference to an import statement in source code.

    Attributes:
        package_name: The name of the imported package.
        file_path: Path to the source file.
        line_number: Line number where the import occurs (1-indexed).
        import_statement: The full import statement text.
        ecosystem: The package ecosystem (npm, pypi, etc.).
    """

    package_name: str
    file_path: Path
    line_number: int
    import_statement: str
    ecosystem: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "package_name": self.package_name,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "import_statement": self.import_statement,
            "ecosystem": self.ecosystem,
        }


class BaseLanguageScanner(ABC):
    """Base class for language-specific import scanners."""

    # File extensions this scanner handles
    FILE_EXTENSIONS: List[str] = []

    # Ecosystem name for this scanner
    ECOSYSTEM: str = ""

    # Default exclude patterns
    DEFAULT_EXCLUDES: List[str] = [
        "node_modules",
        "vendor",
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "env",
        ".tox",
        "build",
        "dist",
        "target",
    ]

    def __init__(self, exclude_patterns: Optional[List[str]] = None) -> None:
        """Initialize the scanner.

        Args:
            exclude_patterns: Additional patterns to exclude from scanning.
        """
        self.exclude_patterns = self.DEFAULT_EXCLUDES.copy()
        if exclude_patterns:
            self.exclude_patterns.extend(exclude_patterns)

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from scanning.

        Args:
            path: Path to check.

        Returns:
            True if the path should be excluded.
        """
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False

    def scan_directory(
        self,
        directory: Path,
        max_file_size: int = 1024 * 1024,  # 1MB default
    ) -> List[ImportReference]:
        """Scan a directory for import statements.

        Args:
            directory: Directory to scan.
            max_file_size: Maximum file size in bytes to scan.

        Returns:
            List of ImportReference objects found.
        """
        references: List[ImportReference] = []

        if not directory.exists() or not directory.is_dir():
            return references

        for ext in self.FILE_EXTENSIONS:
            pattern = f"**/*{ext}"
            for file_path in directory.glob(pattern):
                if self._should_exclude(file_path):
                    continue

                if file_path.is_file():
                    # Check file size
                    try:
                        if file_path.stat().st_size > max_file_size:
                            logger.debug(f"Skipping large file: {file_path}")
                            continue
                    except OSError:
                        continue

                    file_refs = self.scan_file(file_path)
                    references.extend(file_refs)

        return references

    def scan_file(self, file_path: Path) -> List[ImportReference]:
        """Scan a single file for import statements.

        Args:
            file_path: Path to the file to scan.

        Returns:
            List of ImportReference objects found.
        """
        references: List[ImportReference] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return references

        lines = content.split("\n")
        for line_num, line in enumerate(lines, start=1):
            packages = self._extract_packages(line)
            for pkg_name, statement in packages:
                references.append(
                    ImportReference(
                        package_name=pkg_name,
                        file_path=file_path,
                        line_number=line_num,
                        import_statement=statement.strip(),
                        ecosystem=self.ECOSYSTEM,
                    )
                )

        return references

    @abstractmethod
    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from a line of code.

        Args:
            line: A single line of source code.

        Returns:
            List of tuples (package_name, import_statement).
        """
        pass


class JavaScriptScanner(BaseLanguageScanner):
    """Scanner for JavaScript/TypeScript import statements."""

    FILE_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
    ECOSYSTEM = "npm"

    # Patterns for JavaScript/TypeScript imports
    # import ... from 'package'
    IMPORT_FROM_PATTERN: Pattern = re.compile(
        r"""import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*\s+from\s+)?['"]([^'"]+)['"]"""
    )
    # require('package')
    REQUIRE_PATTERN: Pattern = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")
    # import('package') - dynamic import
    DYNAMIC_IMPORT_PATTERN: Pattern = re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""")

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from JavaScript/TypeScript import statements."""
        results: List[tuple] = []

        # Check for import ... from 'package' or import 'package'
        for match in self.IMPORT_FROM_PATTERN.finditer(line):
            pkg_path = match.group(1)
            pkg_name = self._normalize_package_name(pkg_path)
            if pkg_name:
                results.append((pkg_name, line))

        # Check for require('package')
        for match in self.REQUIRE_PATTERN.finditer(line):
            pkg_path = match.group(1)
            pkg_name = self._normalize_package_name(pkg_path)
            if pkg_name:
                results.append((pkg_name, line))

        # Check for import('package') - dynamic import
        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(line):
            pkg_path = match.group(1)
            pkg_name = self._normalize_package_name(pkg_path)
            if pkg_name:
                results.append((pkg_name, line))

        return results

    def _normalize_package_name(self, pkg_path: str) -> Optional[str]:
        """Normalize a package path to a package name.

        Handles:
        - Scoped packages: @scope/package -> @scope/package
        - Subpath imports: package/subpath -> package
        - Relative imports: ./local -> None (excluded)
        - Node built-ins: node:fs -> None (excluded)

        Args:
            pkg_path: The raw package path from the import.

        Returns:
            Normalized package name or None if it should be excluded.
        """
        # Exclude relative imports
        if pkg_path.startswith(".") or pkg_path.startswith("/"):
            return None

        # Exclude node: protocol (built-ins)
        if pkg_path.startswith("node:"):
            return None

        # Handle scoped packages (@scope/package)
        if pkg_path.startswith("@"):
            parts = pkg_path.split("/")
            if len(parts) >= 2:
                # Return @scope/package, ignore subpaths
                return f"{parts[0]}/{parts[1]}"
            return pkg_path

        # Regular package - get first part before /
        parts = pkg_path.split("/")
        return parts[0]


class PythonScanner(BaseLanguageScanner):
    """Scanner for Python import statements."""

    FILE_EXTENSIONS = [".py"]
    ECOSYSTEM = "pypi"

    # Patterns for Python imports
    # import package or import package as alias
    IMPORT_PATTERN: Pattern = re.compile(r"""^import\s+([\w.]+)""")
    # from package import ... or from package.sub import ...
    FROM_IMPORT_PATTERN: Pattern = re.compile(r"""^from\s+([\w.]+)\s+import\s+""")

    # Standard library modules to exclude
    STDLIB_MODULES: Set[str] = {
        "abc",
        "aifc",
        "argparse",
        "array",
        "ast",
        "asyncio",
        "atexit",
        "base64",
        "bdb",
        "binascii",
        "binhex",
        "bisect",
        "builtins",
        "bz2",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "cProfile",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "numbers",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "_thread",
    }

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from Python import statements."""
        results: List[tuple] = []
        line_stripped = line.strip()

        # Check for 'import package'
        match = self.IMPORT_PATTERN.match(line_stripped)
        if match:
            module_path = match.group(1)
            pkg_name = self._normalize_package_name(module_path)
            if pkg_name:
                results.append((pkg_name, line))

        # Check for 'from package import ...'
        match = self.FROM_IMPORT_PATTERN.match(line_stripped)
        if match:
            module_path = match.group(1)
            pkg_name = self._normalize_package_name(module_path)
            if pkg_name:
                results.append((pkg_name, line))

        return results

    def _normalize_package_name(self, module_path: str) -> Optional[str]:
        """Normalize a module path to a package name.

        Args:
            module_path: The module path from the import (e.g., 'package.submodule').

        Returns:
            Package name or None if it's a standard library module.
        """
        # Get the top-level package
        parts = module_path.split(".")
        top_level = parts[0]

        # Exclude standard library modules
        if top_level in self.STDLIB_MODULES:
            return None

        # Exclude relative imports (shouldn't match our pattern, but safety check)
        if top_level.startswith("_") and top_level != "_":
            return None

        return top_level


class GoScanner(BaseLanguageScanner):
    """Scanner for Go import statements."""

    FILE_EXTENSIONS = [".go"]
    ECOSYSTEM = "go"

    # Patterns for Go imports
    # import "package"
    SINGLE_IMPORT_PATTERN: Pattern = re.compile(r"""^\s*import\s+(?:\w+\s+)?["']([^"']+)["']""")
    # import ( "package" ) - inside block
    BLOCK_IMPORT_PATTERN: Pattern = re.compile(r"""^\s*(?:\w+\s+)?["']([^"']+)["']""")

    # Standard library prefixes to exclude
    STDLIB_PREFIXES: List[str] = [
        "archive/",
        "bufio",
        "bytes",
        "compress/",
        "container/",
        "context",
        "crypto/",
        "database/",
        "debug/",
        "embed",
        "encoding/",
        "errors",
        "expvar",
        "flag",
        "fmt",
        "go/",
        "hash/",
        "html/",
        "image/",
        "index/",
        "io",
        "log/",
        "math/",
        "mime/",
        "net/",
        "os",
        "path/",
        "plugin",
        "reflect",
        "regexp",
        "runtime",
        "sort",
        "strconv",
        "strings",
        "sync",
        "syscall",
        "testing",
        "text/",
        "time",
        "unicode",
        "unsafe",
    ]

    def __init__(self, exclude_patterns: Optional[List[str]] = None) -> None:
        super().__init__(exclude_patterns)
        self._in_import_block = False

    def scan_file(self, file_path: Path) -> List[ImportReference]:
        """Override to handle import blocks."""
        references: List[ImportReference] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return references

        lines = content.split("\n")
        in_import_block = False

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Check for start of import block
            if stripped.startswith("import ("):
                in_import_block = True
                continue

            # Check for end of import block
            if in_import_block and stripped == ")":
                in_import_block = False
                continue

            # Process imports
            if in_import_block:
                # Inside import block
                match = self.BLOCK_IMPORT_PATTERN.match(line)
                if match:
                    pkg_path = match.group(1)
                    pkg_name = self._normalize_package_name(pkg_path)
                    if pkg_name:
                        references.append(
                            ImportReference(
                                package_name=pkg_name,
                                file_path=file_path,
                                line_number=line_num,
                                import_statement=line.strip(),
                                ecosystem=self.ECOSYSTEM,
                            )
                        )
            else:
                # Single import
                match = self.SINGLE_IMPORT_PATTERN.match(line)
                if match:
                    pkg_path = match.group(1)
                    pkg_name = self._normalize_package_name(pkg_path)
                    if pkg_name:
                        references.append(
                            ImportReference(
                                package_name=pkg_name,
                                file_path=file_path,
                                line_number=line_num,
                                import_statement=line.strip(),
                                ecosystem=self.ECOSYSTEM,
                            )
                        )

        return references

    def _extract_packages(self, line: str) -> List[tuple]:
        """Not used for Go - overridden scan_file instead."""
        return []

    def _normalize_package_name(self, pkg_path: str) -> Optional[str]:
        """Normalize a Go import path to a package identifier.

        Args:
            pkg_path: The import path (e.g., 'github.com/user/repo/pkg').

        Returns:
            The module path or None if it's a standard library package.
        """
        # Exclude standard library
        for prefix in self.STDLIB_PREFIXES:
            if pkg_path == prefix.rstrip("/") or pkg_path.startswith(prefix):
                return None

        # For external packages, return the full module path
        # Go modules typically use the first 3 parts: host/user/repo
        if "/" in pkg_path:
            parts = pkg_path.split("/")
            if len(parts) >= 3:
                return "/".join(parts[:3])
            return pkg_path

        return None


class JavaScanner(BaseLanguageScanner):
    """Scanner for Java import statements."""

    FILE_EXTENSIONS = [".java"]
    ECOSYSTEM = "maven"

    # Pattern for Java imports
    # import package.Class; or import package.*;
    IMPORT_PATTERN: Pattern = re.compile(r"""^\s*import\s+(?:static\s+)?([\w.]+)(?:\.\*)?;""")

    # Java standard library and common internal packages to exclude
    STDLIB_PACKAGES: List[str] = [
        "java.",
        "javax.",
        "sun.",
        "com.sun.",
        "jdk.",
    ]

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from Java import statements."""
        results: List[tuple] = []

        match = self.IMPORT_PATTERN.match(line.strip())
        if match:
            import_path = match.group(1)
            pkg_name = self._normalize_package_name(import_path)
            if pkg_name:
                results.append((pkg_name, line))

        return results

    def _normalize_package_name(self, import_path: str) -> Optional[str]:
        """Normalize a Java import path to a package identifier.

        Args:
            import_path: The import path (e.g., 'org.apache.commons.lang3.StringUtils').

        Returns:
            Group:Artifact format or None if standard library.
        """
        # Exclude standard library packages
        for prefix in self.STDLIB_PACKAGES:
            if import_path.startswith(prefix):
                return None

        # Java package naming convention typically uses reversed domain
        # We return the first 2-3 parts as package identifier
        parts = import_path.split(".")
        if len(parts) >= 2:
            # Common pattern: org.groupid.artifactid or com.groupid.artifactid
            return ".".join(parts[: min(3, len(parts))])

        return None


class RubyScanner(BaseLanguageScanner):
    """Scanner for Ruby require statements."""

    FILE_EXTENSIONS = [".rb"]
    ECOSYSTEM = "rubygems"

    # Patterns for Ruby requires
    # require 'package' or require "package"
    REQUIRE_PATTERN: Pattern = re.compile(r"""^\s*require\s+['"]([^'"]+)['"]""")
    # require_relative should be excluded
    REQUIRE_RELATIVE_PATTERN: Pattern = re.compile(r"""^\s*require_relative\s+""")

    # Ruby standard library modules to exclude
    STDLIB_MODULES: Set[str] = {
        "abbrev",
        "base64",
        "benchmark",
        "bigdecimal",
        "cgi",
        "cmath",
        "coverage",
        "csv",
        "date",
        "dbm",
        "debug",
        "delegate",
        "digest",
        "drb",
        "english",
        "erb",
        "etc",
        "extmk",
        "fcntl",
        "fiddle",
        "fileutils",
        "find",
        "forwardable",
        "gdbm",
        "getoptlong",
        "io",
        "ipaddr",
        "irb",
        "json",
        "logger",
        "matrix",
        "minitest",
        "mkmf",
        "monitor",
        "mutex_m",
        "net",
        "nkf",
        "objspace",
        "observer",
        "open-uri",
        "open3",
        "openssl",
        "optparse",
        "ostruct",
        "pathname",
        "pp",
        "prettyprint",
        "prime",
        "pstore",
        "psych",
        "pty",
        "racc",
        "rake",
        "rdoc",
        "readline",
        "reline",
        "resolv",
        "resolv-replace",
        "rexml",
        "rinda",
        "ripper",
        "rss",
        "rubygems",
        "scanf",
        "sdbm",
        "securerandom",
        "set",
        "shellwords",
        "singleton",
        "socket",
        "stringio",
        "strscan",
        "syslog",
        "tempfile",
        "thwait",
        "time",
        "timeout",
        "tmpdir",
        "tracer",
        "tsort",
        "un",
        "unicode_normalize",
        "uri",
        "weakref",
        "webrick",
        "yaml",
        "zlib",
    }

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from Ruby require statements."""
        results: List[tuple] = []
        stripped = line.strip()

        # Skip require_relative
        if self.REQUIRE_RELATIVE_PATTERN.match(stripped):
            return results

        match = self.REQUIRE_PATTERN.match(stripped)
        if match:
            gem_path = match.group(1)
            pkg_name = self._normalize_package_name(gem_path)
            if pkg_name:
                results.append((pkg_name, line))

        return results

    def _normalize_package_name(self, gem_path: str) -> Optional[str]:
        """Normalize a gem path to a package name.

        Args:
            gem_path: The required path (e.g., 'rails' or 'active_support/core_ext').

        Returns:
            Gem name or None if it's a standard library module.
        """
        # Get the top-level gem name
        parts = gem_path.split("/")
        gem_name = parts[0]

        # Exclude standard library
        if gem_name in self.STDLIB_MODULES:
            return None

        return gem_name


class RustScanner(BaseLanguageScanner):
    """Scanner for Rust use statements."""

    FILE_EXTENSIONS = [".rs"]
    ECOSYSTEM = "crates.io"

    # Patterns for Rust
    # use crate::...; or use package::...;
    USE_PATTERN: Pattern = re.compile(r"""^\s*use\s+([\w]+)(?:::|;)""")
    # extern crate package;
    EXTERN_CRATE_PATTERN: Pattern = re.compile(r"""^\s*extern\s+crate\s+([\w]+)""")

    # Rust standard library and internal crates to exclude
    STDLIB_CRATES: Set[str] = {
        "std",
        "core",
        "alloc",
        "proc_macro",
        "test",
        "crate",
        "self",
        "super",
    }

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract crate names from Rust use/extern statements."""
        results: List[tuple] = []
        stripped = line.strip()

        # Check for 'use crate::...'
        match = self.USE_PATTERN.match(stripped)
        if match:
            crate_name = match.group(1)
            if crate_name not in self.STDLIB_CRATES:
                results.append((crate_name, line))

        # Check for 'extern crate ...'
        match = self.EXTERN_CRATE_PATTERN.match(stripped)
        if match:
            crate_name = match.group(1)
            if crate_name not in self.STDLIB_CRATES:
                results.append((crate_name, line))

        return results

    def _normalize_package_name(self, crate_name: str) -> Optional[str]:
        """Normalize a crate name."""
        if crate_name in self.STDLIB_CRATES:
            return None
        return crate_name


class PHPScanner(BaseLanguageScanner):
    """Scanner for PHP use statements."""

    FILE_EXTENSIONS = [".php"]
    ECOSYSTEM = "packagist"

    # Patterns for PHP
    # use Namespace\Class;
    USE_PATTERN: Pattern = re.compile(r"""^\s*use\s+([\w\\]+)""")

    # PHP internal namespaces to exclude
    INTERNAL_NAMESPACES: List[str] = [
        "Exception",
        "Error",
        "Throwable",
        "Iterator",
        "Generator",
        "Closure",
        "stdClass",
        "DateTime",
        "DateTimeImmutable",
        "DateInterval",
        "DatePeriod",
        "DateTimeZone",
    ]

    def _extract_packages(self, line: str) -> List[tuple]:
        """Extract package names from PHP use statements."""
        results: List[tuple] = []
        stripped = line.strip()

        # Skip require/include statements (vendor autoload)
        if "require" in stripped or "include" in stripped:
            return results

        match = self.USE_PATTERN.match(stripped)
        if match:
            namespace = match.group(1)
            pkg_name = self._normalize_package_name(namespace)
            if pkg_name:
                results.append((pkg_name, line))

        return results

    def _normalize_package_name(self, namespace: str) -> Optional[str]:
        """Normalize a PHP namespace to a package name.

        Args:
            namespace: The use namespace (e.g., 'Symfony\\Component\\HttpFoundation').

        Returns:
            Vendor/package format or None if internal.
        """
        # Replace backslashes with forward slashes
        namespace = namespace.replace("\\", "/")
        parts = namespace.split("/")

        # Skip internal PHP classes
        if parts[0] in self.INTERNAL_NAMESPACES:
            return None

        # Packagist convention: vendor/package
        if len(parts) >= 2:
            return f"{parts[0].lower()}/{parts[1].lower()}"

        return None


class ImportScanner:
    """Main import scanner that coordinates language-specific scanners."""

    # Mapping of ecosystems to their scanners
    SCANNERS: Dict[str, Type[BaseLanguageScanner]] = {
        "npm": JavaScriptScanner,
        "pypi": PythonScanner,
        "go": GoScanner,
        "maven": JavaScanner,
        "rubygems": RubyScanner,
        "crates.io": RustScanner,
        "packagist": PHPScanner,
    }

    # File extension to ecosystem mapping
    EXTENSION_MAP: Dict[str, str] = {
        ".js": "npm",
        ".jsx": "npm",
        ".ts": "npm",
        ".tsx": "npm",
        ".mjs": "npm",
        ".cjs": "npm",
        ".py": "pypi",
        ".go": "go",
        ".java": "maven",
        ".rb": "rubygems",
        ".rs": "crates.io",
        ".php": "packagist",
    }

    def __init__(
        self,
        ecosystems: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        """Initialize the import scanner.

        Args:
            ecosystems: List of ecosystems to scan for. If None, all are enabled.
            exclude_patterns: Additional patterns to exclude from scanning.
        """
        self.exclude_patterns = exclude_patterns
        self.active_scanners: Dict[str, BaseLanguageScanner] = {}

        # Initialize scanners for requested ecosystems
        target_ecosystems = ecosystems or list(self.SCANNERS.keys())
        for eco in target_ecosystems:
            if eco in self.SCANNERS:
                self.active_scanners[eco] = self.SCANNERS[eco](exclude_patterns)

    def scan_directory(
        self,
        directory: Path,
        max_file_size: int = 1024 * 1024,
    ) -> Dict[str, List[ImportReference]]:
        """Scan a directory for import statements across all languages.

        Args:
            directory: Directory to scan.
            max_file_size: Maximum file size in bytes to scan.

        Returns:
            Dictionary mapping ecosystems to their import references.
        """
        results: Dict[str, List[ImportReference]] = {}

        for ecosystem, scanner in self.active_scanners.items():
            refs = scanner.scan_directory(directory, max_file_size)
            if refs:
                results[ecosystem] = refs

        return results

    def scan_file(self, file_path: Path) -> List[ImportReference]:
        """Scan a single file for import statements.

        Args:
            file_path: Path to the file to scan.

        Returns:
            List of ImportReference objects found.
        """
        ext = file_path.suffix.lower()
        ecosystem = self.EXTENSION_MAP.get(ext)

        if ecosystem and ecosystem in self.active_scanners:
            return self.active_scanners[ecosystem].scan_file(file_path)

        return []

    def get_imports_for_package(
        self,
        package_name: str,
        references: List[ImportReference],
    ) -> List[ImportReference]:
        """Filter import references for a specific package.

        Args:
            package_name: Package name to filter for.
            references: List of all import references.

        Returns:
            List of references for the specified package.
        """
        return [ref for ref in references if ref.package_name == package_name]

    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Get list of supported file extensions."""
        return list(ImportScanner.EXTENSION_MAP.keys())

    @staticmethod
    def get_supported_ecosystems() -> List[str]:
        """Get list of supported ecosystems."""
        return list(ImportScanner.SCANNERS.keys())


def get_scanner_for_ecosystem(ecosystem: str) -> Optional[BaseLanguageScanner]:
    """Get a scanner instance for a specific ecosystem.

    Args:
        ecosystem: The ecosystem name.

    Returns:
        Scanner instance or None if not supported.
    """
    scanner_class = ImportScanner.SCANNERS.get(ecosystem)
    if scanner_class:
        return scanner_class()
    return None
