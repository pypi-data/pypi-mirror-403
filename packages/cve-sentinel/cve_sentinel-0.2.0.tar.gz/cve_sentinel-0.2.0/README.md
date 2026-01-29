<p align="center">
  <img src="assets/icon.png" alt="CVE Sentinel" width="180" height="180">
</p>

<h1 align="center">CVE Sentinel</h1>

<p align="center">
  <strong>Your AI-Powered Vulnerability Detector</strong>
</p>

<p align="center">
  Automatically detect vulnerabilities in your dependencies before they are hacked.
</p>

<p align="center">
  <!-- CI & Coverage -->
  <a href="https://github.com/cawa102/cveSentinel/actions/workflows/ci.yml">
    <img src="https://github.com/cawa102/cveSentinel/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://codecov.io/gh/cawa102/cveSentinel">
    <img src="https://codecov.io/gh/cawa102/cveSentinel/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <!-- Package Info -->
  <a href="https://pypi.org/project/cve-sentinel/">
    <img src="https://img.shields.io/pypi/v/cve-sentinel.svg" alt="PyPI">
  </a>
  <a href="https://pypi.org/project/cve-sentinel/">
    <img src="https://img.shields.io/pypi/pyversions/cve-sentinel.svg" alt="Python Versions">
  </a>
</p>

<p align="center">
  <!-- Community -->
  <a href="https://github.com/cawa102/cveSentinel/stargazers">
    <img src="https://img.shields.io/github/stars/cawa102/cveSentinel.svg?style=social" alt="Stars">
  </a>
  <a href="https://github.com/cawa102/cveSentinel/issues">
    <img src="https://img.shields.io/github/issues/cawa102/cveSentinel.svg" alt="Issues">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  <!-- Security -->
  <a href="https://github.com/cawa102/cveSentinel/security/policy">
    <img src="https://img.shields.io/badge/Security-Policy-blue.svg" alt="Security Policy">
  </a>
</p>

---

## Demo

<p align="center">
  <img src="assets/cveSentinel.gif" alt="CVE Sentinel Demo" width="800">
</p>

<details>
<summary>📺 Watch full demo video</summary>

https://github.com/user-attachments/assets/2f68c7f1-588e-4904-be80-82407ea3361c

</details>

---

## Why CVE Sentinel?

### Built for the AI-driven Era

Traditional vulnerability scanners run periodically in CI/CD pipelines — but AI-driven development moves faster. When you're building with Claude Code, new dependencies get added in real-time. **CVE Sentinel** provides always-on protection that activates the moment you start coding, catching vulnerabilities before they ever reach your repository.

### Superior Coverage with Multi-Source Intelligence

Most scanners rely on a single vulnerability database. CVE Sentinel combines **NVD (National Vulnerability Database)** and **Google OSV (Open Source Vulnerabilities)** with intelligent filtering to deliver broader coverage without false positives:

| Source | Strength |
|--------|----------|
| **Google OSV** | High precision, ecosystem-aware queries, faster updates |
| **NVD** | Broader coverage, detailed CVSS scores, comprehensive CVE data |

#### Detection Comparison

| Method | CVEs Detected | False Positives | Assessment |
|--------|---------------|-----------------|------------|
| OSV Only | 19 | 0 | ✓ High precision, limited coverage |
| NVD Only | 115 | 98+ | ✗ Many false positives |
| **CVE Sentinel (Combined)** | **38** | **0** | ✓ **Best of both worlds** |

> *Tested on 5 popular packages: vite, express, lodash, axios, cypress*

By combining both sources with **CPE-based filtering** and **confidence scoring**, CVE Sentinel achieves **2x detection coverage** compared to OSV-only scanning while maintaining zero false positives.

### Intelligent False Positive Filtering

Raw NVD keyword searches often return irrelevant results. CVE Sentinel filters them out automatically:

| Package | False Match | Reason | Result |
|---------|-------------|--------|--------|
| `cypress` | Cypress Semiconductor chips | Hardware vendor | ❌ Filtered |
| `vite` | VITEC video encoders | Different product | ❌ Filtered |
| `express` | ExpressVPN | Different product | ❌ Filtered |

**How it works:**
- 🔍 **CPE Matching** - Validates vendor/product names against known mappings
- 🏭 **Hardware Exclusion** - Blocks 20+ hardware vendors (Intel, Broadcom, etc.)
- 📊 **Confidence Scoring** - HIGH / MEDIUM / LOW ratings for each match
- 🔢 **Version Validation** - Checks if your version is actually affected

### Key Features

- **Always-On Detection** - Automatically scans when you start Claude Code sessions
- **Multi-Source Intelligence** - NVD + Google OSV for maximum coverage
- **Smart Filtering** - Eliminates false positives with CPE-based validation
- **7+ Languages** - JavaScript, Python, Go, Java, Ruby, Rust, PHP and more
- **3 Analysis Levels** - From quick manifest scans to deep source code analysis
- **Actionable Fixes** - Get specific upgrade commands, not just vulnerability reports

---

## Quick Start

### Installation

```bash
# Install from PyPI
pip install cve-sentinel

# Or install from GitHub (latest development version)
pip install git+https://github.com/cawa102/cveSentinel.git
```

### Scan Your Project

```bash
# Scan current directory
cve-sentinel scan

# Scan a specific directory
cve-sentinel scan /path/to/project

# Scan with options
cve-sentinel scan /path/to/project --level 2 --exclude node_modules --exclude .venv
```

No configuration file required - just run and scan!

### Auto-scan with Claude Code (Optional)

Want CVE Sentinel to automatically scan every time you start Claude Code? See [How to Work with Claude Code](#how-to-work-with-claude-code) for setup instructions.

---

## NVD API Key (Recommended)

For faster scanning, get a free API key from [NVD](https://nvd.nist.gov/developers/request-an-api-key):

```bash
export NVD_API_KEY=your-api-key-here
```

Without an API key, requests are rate-limited to 5 per 30 seconds.


---

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Your Project   │────▶│  CVE Sentinel   │────▶│  Security Report│
│                 │     │                 │     │                 │
│ package.json    │     │ ┌─────────────┐ │     │ 3 Critical      │
│ requirements.txt│     │ │ NVD API 2.0 │ │     │ 5 High          │
│ go.mod          │     │ └─────────────┘ │     │ 2 Medium        │
│ Cargo.toml      │     │ ┌─────────────┐ │     │                 │
│ ...             │     │ │ Google OSV  │ │     │ + Fix Commands  │
│                 │     │ └─────────────┘ │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Supported Languages (Default)

| Language | Package Managers | Files Analyzed |
|:--------:|:-----------------|:---------------|
| **JavaScript** | npm, yarn, pnpm | `package.json`, `package-lock.json`, `yarn.lock` |
| **Python** | pip, poetry, pipenv | `requirements.txt`, `pyproject.toml`, `Pipfile` |
| **Go** | go mod | `go.mod`, `go.sum` |
| **Java** | Maven, Gradle | `pom.xml`, `build.gradle` |
| **Ruby** | Bundler | `Gemfile`, `Gemfile.lock` |
| **Rust** | Cargo | `Cargo.toml`, `Cargo.lock` |
| **PHP** | Composer | `composer.json`, `composer.lock` |

---

## Analysis Levels

Choose the depth of analysis that fits your needs:

| Level | What It Scans | Best For |
|:-----:|:--------------|:---------|
| **1** | Manifest files only | Quick CI checks |
| **2** | + Lock files (transitive deps) | Regular development (default) |
| **3** | + Source code imports | Pre-release audits |

```bash
# Quick scan - manifest files only (Level 1)
cve-sentinel scan --level 1

# Standard scan - includes lock files (Level 2, default)
cve-sentinel scan

# Deep scan - includes source code analysis (Level 3)
cve-sentinel scan --level 3

# Scan specific directory with level
cve-sentinel scan /path/to/project --level 3
```

---

## Usage

```bash
cve-sentinel scan [PATH] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `PATH` | Target directory to scan (default: current directory) |
| `--level`, `-l` | Analysis level: 1, 2, or 3 (default: 2) |
| `--exclude`, `-e` | Paths to exclude (can be specified multiple times) |
| `--verbose`, `-v` | Enable verbose output |
| `--fail-on` | Exit with error if vulnerabilities at or above this severity (default: HIGH) |

### Examples

```bash
# Basic scan
cve-sentinel scan

# Scan with exclusions
cve-sentinel scan --exclude node_modules --exclude dist

# CI/CD usage - fail on critical vulnerabilities only
cve-sentinel scan --fail-on CRITICAL

# Verbose deep scan
cve-sentinel scan /path/to/project --level 3 --verbose
```

---

## Configuration (Optional)

For persistent settings, create `.cve-sentinel.yaml` in your project root:

```yaml
# Scan settings
analysis_level: 2

# Exclude paths (e.g., test fixtures)
exclude:
  - node_modules/
  - vendor/
  - .venv/

# Cache settings
cache_ttl_hours: 24

# Auto-scan on Claude Code startup
auto_scan_on_startup: true

# Data sources configuration
datasources:
  osv_enabled: true       # High precision, ecosystem-aware
  nvd_enabled: true       # Broader coverage with filtering
  nvd_min_confidence: medium  # high, medium, or low
  prefer_osv: true        # Prefer OSV data when available from both
```

### Confidence Levels

| Level | Criteria | Included by Default |
|-------|----------|---------------------|
| **HIGH** | Exact CPE match + ecosystem verified | ✓ Yes |
| **MEDIUM** | CPE match or partial match + ecosystem | ✓ Yes |
| **LOW** | Keyword match only | ✗ No |

CLI options override configuration file settings.

---

## Custom File Patterns

Your unique projects sometimes use non-standard file names for their dependencies. CVE Sentinel lets you specify additional file patterns to scan:

```yaml
# .cve-sentinel.yaml
custom_patterns:
  python:
    manifests:
      - "deps/*.txt"
      - "requirements-*.txt"
    locks:
      - "custom.lock"
  javascript:
    manifests:
      - "dependencies.json"
```

### Supported Ecosystems

| Config Key | Aliases | Default Files |
|:-----------|:--------|:--------------|
| `javascript` | `npm` | `package.json`, `package-lock.json`, `yarn.lock` |
| `python` | `pypi` | `requirements.txt`, `pyproject.toml`, `Pipfile` |
| `go` | - | `go.mod`, `go.sum` |
| `java` | `maven`, `gradle` | `pom.xml`, `build.gradle` |
| `ruby` | `rubygems` | `Gemfile`, `Gemfile.lock` |
| `rust` | `crates.io` | `Cargo.toml`, `Cargo.lock` |
| `php` | `packagist` | `composer.json`, `composer.lock` |

Custom patterns **extend** the defaults - your standard files are always scanned.

---

## How to Work with Claude Code

CVE Sentinel integrates with [Claude Code](https://claude.ai/code) as a **SessionStart Hook**. Once configured, it automatically scans your project for vulnerabilities every time you launch Claude Code.

### Quick Setup (Recommended)

Run the install script to set up everything automatically:

```bash
# Clone the repository
git clone https://github.com/cawa102/cveSentinel.git
cd cveSentinel

# Run the installer
./scripts/install.sh
```

This script:
- Installs the `cve-sentinel` package
- Creates the hook script at `~/.claude/hooks/cve-sentinel-scan.sh`
- Configures Claude Code's `~/.claude/settings.json`

### Manual Setup

If you prefer manual configuration or already have `cve-sentinel` installed via pip:

#### Step 1: Create the hook script

Create `~/.claude/hooks/cve-sentinel-scan.sh`:

```bash
#!/bin/bash
PROJECT_DIR="${1:-.}"

should_scan() {
    if [ -f "$PROJECT_DIR/.cve-sentinel.yaml" ]; then
        return 0
    fi
    for file in package.json requirements.txt pyproject.toml Gemfile Cargo.toml go.mod composer.json pom.xml build.gradle; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            return 0
        fi
    done
    return 1
}

if should_scan; then
    nohup cve-sentinel scan --path "$PROJECT_DIR" > /dev/null 2>&1 &
fi
```

Make it executable:

```bash
chmod +x ~/.claude/hooks/cve-sentinel-scan.sh
```

#### Step 2: Configure Claude Code settings

Add the hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "sessionStart": [
      {
        "name": "cve-sentinel",
        "command": "~/.claude/hooks/cve-sentinel-scan.sh",
        "args": ["${projectPath}"],
        "enabled": true
      }
    ]
  }
}
```

### Project Configuration (Optional)

For project-specific settings, run in your project directory:

```bash
cve-sentinel init
```

This creates:
- `.cve-sentinel.yaml` - Configuration file for custom settings
- `.cve-sentinel/` - Directory for scan results and cache

### How It Works with Claude Code

Once configured:

1. **Session Start** - Hook triggers automatically when you launch Claude Code
2. **Background Scan** - CVE Sentinel scans dependencies without blocking your session
3. **Results Available** - Check `.cve-sentinel/results.json` for vulnerability details
4. **Claude Assistance** - Ask Claude to review results and help implement fixes

---

## Sample Output

```
⚠ CVE Scan Complete: 73 vulnerabilities found

[CVE-2025-xxxxx] (Description)
Severity: 
Description: 
Affected Files: '/path/where/this/vuln/exists'
Fix:
...
```

---

## Troubleshooting

#### API Rate Limiting

```
Error querying OSV for npm: OSV API bad request: {"code":3,"message":"Too many queries."}
```

**Cause:** Too many requests to OSV API in a short period.

**Solution:** The tool automatically retries with exponential backoff. For large projects, the scan may take longer. If errors persist, wait a few minutes and try again.

---

#### CVSS Score Parsing Error

```
could not convert string to float: 'CVSS:3.1/AV:N/AC:L/...'
```

**Cause:** Older version of CVE Sentinel. This was fixed in recent updates.

**Solution:** Update to the latest version:
```bash
pip install --upgrade cve-sentinel
```

---

#### Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `analysis_level must be between 1 and 3` | Invalid analysis level | Use `--level 1`, `2`, or `3` |
| `target_path does not exist` | Invalid scan path | Check the path exists |
| `Failed to parse YAML config file` | Invalid YAML syntax | Check `.cve-sentinel.yaml` syntax |

---

#### NVD API Errors

```
NVD API rate limit exceeded
```

**Cause:** NVD API has strict rate limits without an API key (5 requests per 30 seconds).

**Solution:** Get a free API key from [NVD](https://nvd.nist.gov/developers/request-an-api-key) and set it:
```bash
export CVE_SENTINEL_NVD_API_KEY=your-api-key-here
```

---

#### Python Version Error

```
Package 'cve-sentinel' requires a different Python: 3.8.x not in '>=3.9'
```

**Cause:** Python version is too old.

**Solution:** Use Python 3.9 or later:
```bash
python3.9 -m pip install cve-sentinel
```

---

## Development

```bash
# Clone and install
git clone https://github.com/cawa102/cveSentinel.git
cd cveSentinel
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
```

---

## Contributing

Contributions are welcome! Whether it's:
- Adding support for new languages
- Improving vulnerability detection
- Enhancing the user experience

Please feel free to submit a Pull Request.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with security in mind. Powered by Claude Code.</sub>
</p>
