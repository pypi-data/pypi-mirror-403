# CVE Sentinel Installation Guide

This guide explains how to install and configure CVE Sentinel for automatic vulnerability detection in your projects.

## Quick Install

### Using the Install Script (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/xxx/cve-sentinel/main/scripts/install.sh | bash
```

### Using pip

```bash
pip install cve-sentinel
```

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Claude Code (for automatic session scanning)

## Post-Installation Setup

### 1. Get an NVD API Key (Recommended)

While CVE Sentinel works without an API key, having one provides better rate limits and faster scans.

1. Visit: https://nvd.nist.gov/developers/request-an-api-key
2. Fill out the form to request an API key
3. Check your email for the API key

### 2. Set the Environment Variable

Add the API key to your shell profile:

**For Bash (~/.bashrc):**
```bash
echo 'export CVE_SENTINEL_NVD_API_KEY=your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

**For Zsh (~/.zshrc):**
```bash
echo 'export CVE_SENTINEL_NVD_API_KEY=your_api_key_here' >> ~/.zshrc
source ~/.zshrc
```

**For Fish (~/.config/fish/config.fish):**
```bash
echo 'set -x CVE_SENTINEL_NVD_API_KEY your_api_key_here' >> ~/.config/fish/config.fish
```

### 3. Initialize in Your Project

Navigate to your project directory and run:

```bash
cd /path/to/your/project
cve-sentinel init
```

This will:
- Create `.cve-sentinel.yaml` configuration file
- Create `.cve-sentinel/` directory for results and cache
- Update `.gitignore` to exclude CVE Sentinel files

### 4. Run Your First Scan

```bash
cve-sentinel scan
```

Or with verbose output:

```bash
cve-sentinel scan --verbose
```

## CLI Commands

### `cve-sentinel scan`

Scan project dependencies for known CVE vulnerabilities.

```bash
cve-sentinel scan [options]

Options:
  --path, -p PATH      Path to project directory (default: current directory)
  --verbose, -v        Enable verbose output
  --fail-on SEVERITY   Exit with error if vulnerabilities at or above this
                       severity (CRITICAL, HIGH, MEDIUM, LOW; default: HIGH)
```

**Examples:**
```bash
# Scan current directory
cve-sentinel scan

# Scan specific directory
cve-sentinel scan --path /path/to/project

# Fail only on critical vulnerabilities
cve-sentinel scan --fail-on CRITICAL
```

### `cve-sentinel init`

Initialize CVE Sentinel configuration in a project.

```bash
cve-sentinel init [options]

Options:
  --path, -p PATH   Path to project directory (default: current directory)
  --force, -f       Overwrite existing configuration
  --verbose, -v     Enable verbose output
```

**Examples:**
```bash
# Initialize in current directory
cve-sentinel init

# Initialize in specific directory
cve-sentinel init --path /path/to/project

# Force overwrite existing config
cve-sentinel init --force
```

### `cve-sentinel update`

Update CVE Sentinel to the latest version.

```bash
cve-sentinel update [options]

Options:
  --verbose, -v     Enable verbose output
```

### `cve-sentinel uninstall`

Remove CVE Sentinel from the system.

```bash
cve-sentinel uninstall [options]

Options:
  --yes, -y          Skip confirmation prompt
  --remove-cache     Also remove cached CVE data
  --verbose, -v      Enable verbose output
```

**Note:** This does not remove project-level `.cve-sentinel.yaml` files or `.cve-sentinel/` directories.

## Configuration

CVE Sentinel is configured via `.cve-sentinel.yaml` in your project root:

```yaml
# Target directory to scan (relative to this config file)
target_path: "."

# Paths to exclude from scanning
exclude:
  - "node_modules/"
  - "vendor/"
  - ".git/"
  - "__pycache__/"
  - "venv/"

# Analysis level:
#   1: Direct dependencies from manifest files only
#   2: Include transitive dependencies from lock files
#   3: Include import statement scanning in source code
analysis_level: 2

# Automatically scan when Claude Code session starts
auto_scan_on_startup: true

# Cache time-to-live in hours
cache_ttl_hours: 24

# NVD API key (prefer environment variable)
# nvd_api_key: "your-api-key"
```

## Claude Code Integration

When installed via the install script, CVE Sentinel automatically integrates with Claude Code:

1. A hook script is created at `~/.claude/hooks/cve-sentinel-scan.sh`
2. Claude Code settings are updated to run the hook on session start
3. Scans run in the background without blocking Claude Code startup

### Manual Hook Setup

If you need to manually configure the Claude Code hook, add this to `~/.claude/settings.json`:

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

## Output Files

CVE Sentinel creates the following files in your project:

| File | Description |
|------|-------------|
| `.cve-sentinel/status.json` | Current scan status (scanning, completed, error) |
| `.cve-sentinel/results.json` | Scan results with vulnerabilities |
| `.cve-sentinel/cache/` | Cached CVE data |

### status.json

```json
{
  "status": "completed",
  "started_at": "2024-01-01T00:00:00+00:00",
  "completed_at": "2024-01-01T00:00:05+00:00"
}
```

### results.json

```json
{
  "scan_date": "2024-01-01T00:00:05+00:00",
  "packages_scanned": 42,
  "summary": {
    "total": 3,
    "critical": 1,
    "high": 2,
    "medium": 0,
    "low": 0
  },
  "vulnerabilities": [
    {
      "cve_id": "CVE-2021-12345",
      "package_name": "example-package",
      "installed_version": "1.0.0",
      "severity": "CRITICAL",
      "fix_version": "1.0.1",
      "fix_command": "npm install example-package@1.0.1"
    }
  ]
}
```

## Troubleshooting

### "Python not found"

Ensure Python 3.8+ is installed and available in your PATH:

```bash
python3 --version
# or
python --version
```

### "NVD API rate limit exceeded"

Without an API key, NVD limits requests to 5 per 30 seconds. Get an API key for 50 requests per 30 seconds.

### "No vulnerabilities found" for packages with known CVEs

1. Check that lock files exist (package-lock.json, poetry.lock, etc.)
2. Ensure the package version in your lock file matches the vulnerable version
3. Try increasing `analysis_level` in configuration

### Hook not running in Claude Code

1. Check if the hook script exists: `ls ~/.claude/hooks/cve-sentinel-scan.sh`
2. Verify Claude Code settings: `cat ~/.claude/settings.json`
3. Ensure the hook has execute permission: `chmod +x ~/.claude/hooks/cve-sentinel-scan.sh`

### Clearing the cache

If you're getting stale results:

```bash
rm -rf .cve-sentinel/cache/
cve-sentinel scan
```

## Uninstalling

To completely remove CVE Sentinel:

```bash
cve-sentinel uninstall --yes --remove-cache
```

To remove project-level files:

```bash
rm -rf .cve-sentinel/ .cve-sentinel.yaml
```
