# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CVE Sentinel - A Claude Code plugin that automatically detects CVE vulnerabilities in project dependencies and proposes remediation actions.

### Core Functionality
- **CVE Detection**: Fetches vulnerability data from NVD API 2.0 and Google OSV
- **Dependency Analysis**: Parses package manifests and lock files across multiple languages
- **Vulnerability Matching**: Correlates detected packages with known CVEs using CPE matching
- **Remediation Proposals**: Suggests fix versions and upgrade commands

### Plugin Architecture
- Runs as a Claude Code Hook (SessionStart trigger)
- Uses background processing with status/result JSON files for async communication
- CLAUDE.md instructions guide Claude to monitor `.cve-sentinel/status.json` and report results

## Technology Stack

- **Implementation**: Python
- **Data Sources**: NVD API 2.0 (requires API key), Google OSV
- **CVE Fetch Strategy**: Package-specific queries (not bulk download)
- **Cache**: Per-project (`.cve-sentinel/cache/`)

## Supported Package Managers

| Language | Package Managers | Manifest Files | Lock Files |
|----------|-----------------|----------------|------------|
| JavaScript/TypeScript | npm, yarn, pnpm | package.json | package-lock.json, yarn.lock, pnpm-lock.yaml |
| Python | pip, poetry, pipenv | requirements.txt, pyproject.toml, Pipfile | poetry.lock, Pipfile.lock |
| Go | go mod | go.mod | go.sum |
| Java | Maven, Gradle | pom.xml, build.gradle | - |
| Ruby | Bundler | Gemfile | Gemfile.lock |
| Rust | Cargo | Cargo.toml | Cargo.lock |
| PHP | Composer | composer.json | composer.lock |

## Analysis Levels

- **Level 1**: Direct dependencies from manifest files
- **Level 2**: Transitive dependencies from lock files
- **Level 3**: Import statement scanning in source code (reports file:line locations)

## Key File Structure

```
.cve-sentinel/
├── status.json      # Scan state (scanning|completed|error)
├── results.json     # Scan results with vulnerabilities
└── cache/           # CVE data cache

.cve-sentinel.yaml   # Project configuration (optional)
```

## Usage

```bash
# Scan current directory (no config file needed)
cve-sentinel scan

# Scan specific path
cve-sentinel scan /path/to/project

# With options (override config file settings)
cve-sentinel scan --level 2 --exclude "test/*" --verbose
```

## Configuration (Optional)

Configuration via `.cve-sentinel.yaml` for persistent settings:
- `target_path`: Scan target directory
- `exclude`: Paths to exclude
- `analysis_level`: 1-3
- `auto_scan_on_startup`: Enable/disable automatic scanning
- `cache_ttl_hours`: Cache expiration

**Priority order (later overrides earlier):**
1. Default values
2. `.cve-sentinel.yaml` config file
3. Environment variables
4. CLI arguments (highest priority)

## NVD API Key

Required. Store in environment variable for security.

## Documentation

Refer to `/docs` directory for detailed specifications:
- `requirement.md` - Full requirements specification (in Japanese)
- `tickets/README.md` - Development ticket management and progress tracking
- `tickets/T001_*.md` - Individual ticket details with tasks and acceptance criteria

## Development Workflow

### Ticket Management
Each ticket in `/docs/tickets/` contains:
- **状態 (Status)**: TODO | IN_PROGRESS | DONE
- **チェックリスト**: Detailed task breakdown with checkboxes

### Checklist Usage
1. Before starting a ticket, update its status to `IN_PROGRESS`
2. As you complete each task, mark it with `[x]`:
   ```markdown
   - [x] Completed task
   - [ ] Pending task
   ```
3. When all checklist items are done, update status to `DONE`
4. Update `tickets/README.md` status column accordingly

### Example Workflow
```bash
# 1. Read the ticket
# 2. Update status: TODO → IN_PROGRESS
# 3. Implement tasks, checking off items as completed
# 4. Update status: IN_PROGRESS → DONE
# 5. Update README.md ticket table
```
