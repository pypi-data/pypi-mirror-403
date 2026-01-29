#!/bin/bash
# CVE Sentinel Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/xxx/cve-sentinel/main/scripts/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         CVE Sentinel Installer             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get Python command (python3 or python)
get_python_cmd() {
    if command_exists python3; then
        echo "python3"
    elif command_exists python; then
        echo "python"
    else
        echo ""
    fi
}

# Check Python version
check_python_version() {
    local python_cmd=$1
    local version_output=$($python_cmd --version 2>&1)
    local version=$(echo "$version_output" | grep -oE '[0-9]+\.[0-9]+' | head -1)
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
        return 0
    else
        return 1
    fi
}

# Get pip command
get_pip_cmd() {
    local python_cmd=$1
    if $python_cmd -m pip --version >/dev/null 2>&1; then
        echo "$python_cmd -m pip"
    elif command_exists pip3; then
        echo "pip3"
    elif command_exists pip; then
        echo "pip"
    else
        echo ""
    fi
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    local python_cmd=$(get_python_cmd)
    if [ -z "$python_cmd" ]; then
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    if ! check_python_version "$python_cmd"; then
        print_error "Python 3.8 or higher is required. Current version: $($python_cmd --version)"
        exit 1
    fi
    print_success "Python: $($python_cmd --version)"

    # Check pip
    local pip_cmd=$(get_pip_cmd "$python_cmd")
    if [ -z "$pip_cmd" ]; then
        print_error "pip is not installed. Please install pip."
        exit 1
    fi
    print_success "pip: $($pip_cmd --version | head -1)"

    # Check curl or wget (for future use)
    if command_exists curl; then
        print_success "curl: available"
    elif command_exists wget; then
        print_success "wget: available"
    else
        print_warning "Neither curl nor wget found. May need for future updates."
    fi

    echo "$python_cmd|$pip_cmd"
}

# Install CVE Sentinel
install_package() {
    local pip_cmd=$1

    print_info "Installing CVE Sentinel..."

    # Install from PyPI (or local for development)
    if [ -f "pyproject.toml" ]; then
        # Development install
        print_info "Development mode detected. Installing in editable mode..."
        $pip_cmd install -e ".[dev]"
    else
        # Production install
        $pip_cmd install cve-sentinel
    fi

    print_success "CVE Sentinel package installed"
}

# Setup Claude Code hooks directory
setup_hooks_dir() {
    local hooks_dir="$HOME/.claude/hooks"

    print_info "Setting up hooks directory..."

    mkdir -p "$hooks_dir"
    print_success "Hooks directory created: $hooks_dir"
}

# Create hook script
create_hook_script() {
    local hooks_dir="$HOME/.claude/hooks"
    local hook_script="$hooks_dir/cve-sentinel-scan.sh"
    local python_cmd=$1

    print_info "Creating hook script..."

    cat > "$hook_script" << 'HOOK_SCRIPT'
#!/bin/bash
# CVE Sentinel SessionStart Hook
# This script is called when a Claude Code session starts

# Get the project directory from argument or current directory
PROJECT_DIR="${1:-.}"

# Check if .cve-sentinel.yaml exists or if there are dependency files
should_scan() {
    if [ -f "$PROJECT_DIR/.cve-sentinel.yaml" ]; then
        return 0
    fi

    # Check for common dependency files
    for file in package.json requirements.txt pyproject.toml Gemfile Cargo.toml go.mod composer.json pom.xml build.gradle; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            return 0
        fi
    done

    return 1
}

# Run scan if applicable
if should_scan; then
    # Run in background to not block Claude Code startup
    nohup cve-sentinel scan --path "$PROJECT_DIR" > /dev/null 2>&1 &
fi
HOOK_SCRIPT

    chmod +x "$hook_script"
    print_success "Hook script created: $hook_script"
}

# Update Claude Code settings
update_claude_settings() {
    local settings_dir="$HOME/.claude"
    local settings_file="$settings_dir/settings.json"
    local python_cmd=$1

    print_info "Updating Claude Code settings..."

    mkdir -p "$settings_dir"

    # Use Python to update JSON (more reliable than shell parsing)
    $python_cmd << PYTHON_SCRIPT
import json
import os

settings_file = "$settings_file"
hooks_dir = os.path.expanduser("~/.claude/hooks")
hook_script = os.path.join(hooks_dir, "cve-sentinel-scan.sh")

# Load existing settings or create new
settings = {}
if os.path.exists(settings_file):
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

# Ensure hooks section exists
if 'hooks' not in settings:
    settings['hooks'] = {}

if 'sessionStart' not in settings['hooks']:
    settings['hooks']['sessionStart'] = []

# Add CVE Sentinel hook if not already present
hook_entry = {
    "name": "cve-sentinel",
    "command": hook_script,
    "args": ["\${projectPath}"],
    "enabled": True
}

# Check if hook already exists
hook_exists = False
for hook in settings['hooks']['sessionStart']:
    if isinstance(hook, dict) and hook.get('name') == 'cve-sentinel':
        hook_exists = True
        break

if not hook_exists:
    settings['hooks']['sessionStart'].append(hook_entry)

# Write settings
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("Settings updated successfully")
PYTHON_SCRIPT

    print_success "Claude Code settings updated"
}

# Print post-installation instructions
print_instructions() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     Installation completed successfully!   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    echo "1. Get an NVD API Key (recommended for better rate limits):"
    echo "   https://nvd.nist.gov/developers/request-an-api-key"
    echo ""
    echo "2. Set the API key as an environment variable:"
    echo "   export CVE_SENTINEL_NVD_API_KEY=your_api_key_here"
    echo ""
    echo "   Add to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "   echo 'export CVE_SENTINEL_NVD_API_KEY=your_api_key_here' >> ~/.zshrc"
    echo ""
    echo "3. Initialize CVE Sentinel in your project:"
    echo "   cd /path/to/your/project"
    echo "   cve-sentinel init"
    echo ""
    echo "4. Run a manual scan:"
    echo "   cve-sentinel scan"
    echo ""
    echo -e "${BLUE}Other commands:${NC}"
    echo "   cve-sentinel --help      Show all available commands"
    echo "   cve-sentinel update      Update CVE Sentinel"
    echo "   cve-sentinel uninstall   Uninstall CVE Sentinel"
    echo ""
}

# Main installation flow
main() {
    print_header

    # Check prerequisites and get commands
    local result=$(check_prerequisites)
    local python_cmd=$(echo "$result" | cut -d'|' -f1)
    local pip_cmd=$(echo "$result" | cut -d'|' -f2)

    echo ""

    # Install package
    install_package "$pip_cmd"

    # Setup hooks
    setup_hooks_dir
    create_hook_script "$python_cmd"
    update_claude_settings "$python_cmd"

    # Print instructions
    print_instructions
}

# Run main
main "$@"
