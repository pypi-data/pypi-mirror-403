#!/bin/bash
# CVE Sentinel - Claude Code SessionStart Hook
# This script is triggered when Claude Code starts a new session.
# It initializes CVE scanning in the background to avoid blocking the session.

set -e

# Configuration
OUTPUT_DIR=".cve-sentinel"
STATUS_FILE="$OUTPUT_DIR/status.json"
LOG_FILE="$OUTPUT_DIR/scanner.log"
CONFIG_FILE=".cve-sentinel.yaml"
ALT_CONFIG_FILE=".cve-sentinel.yml"

# Check if auto_scan_on_startup is disabled in config
check_auto_scan_enabled() {
    local config_file=""

    if [ -f "$CONFIG_FILE" ]; then
        config_file="$CONFIG_FILE"
    elif [ -f "$ALT_CONFIG_FILE" ]; then
        config_file="$ALT_CONFIG_FILE"
    else
        # No config file, use default (enabled)
        return 0
    fi

    # Check if auto_scan_on_startup is explicitly set to false
    if grep -q "auto_scan_on_startup:\s*false" "$config_file" 2>/dev/null; then
        return 1
    fi

    return 0
}

# Get current timestamp in ISO 8601 format
get_timestamp() {
    if date --version >/dev/null 2>&1; then
        # GNU date (Linux)
        date -u +%Y-%m-%dT%H:%M:%SZ
    else
        # BSD date (macOS)
        date -u +%Y-%m-%dT%H:%M:%SZ
    fi
}

# Write status JSON file
write_status() {
    local status="$1"
    local error_message="${2:-}"
    local timestamp
    timestamp=$(get_timestamp)

    if [ -n "$error_message" ]; then
        cat > "$STATUS_FILE" << EOF
{
    "status": "$status",
    "started_at": "$timestamp",
    "error": "$error_message"
}
EOF
    else
        cat > "$STATUS_FILE" << EOF
{
    "status": "$status",
    "started_at": "$timestamp"
}
EOF
    fi
}

# Main execution
main() {
    # Check if auto scan is enabled
    if ! check_auto_scan_enabled; then
        echo "CVE Sentinel: Auto-scan disabled in configuration"
        exit 0
    fi

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    # Initialize status.json with "scanning" state
    write_status "scanning"

    # Check if Python and cve_sentinel module are available
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        write_status "error" "Python not found"
        exit 0  # Exit 0 to not block Claude Code
    fi

    # Determine Python command
    PYTHON_CMD="python3"
    if ! command -v python3 &> /dev/null; then
        PYTHON_CMD="python"
    fi

    # Check if cve_sentinel module is installed
    if ! $PYTHON_CMD -c "import cve_sentinel" 2>/dev/null; then
        write_status "error" "cve_sentinel module not installed"
        exit 0  # Exit 0 to not block Claude Code
    fi

    # Start the scanner in background
    # Using nohup to ensure the process continues after this script exits
    nohup $PYTHON_CMD -m cve_sentinel --path . > "$LOG_FILE" 2>&1 &

    # Store the background process PID
    echo $! > "$OUTPUT_DIR/scanner.pid"

    # Exit immediately (Hook timeout avoidance)
    # The background process will update status.json when complete
    exit 0
}

main "$@"
