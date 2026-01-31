#!/bin/bash
#
# Emdash AI Installer (using uv)
# https://github.com/mendyEdri/emdash.dev
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/mendyEdri/emdash.dev/main/scripts/install.sh | bash
#
# Or with options:
#   curl -sSL ... | bash -s -- --with-graph
#   curl -sSL ... | bash -s -- --verbose
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${EMDASH_INSTALL_DIR:-$HOME/.emdash}"
BIN_DIR="${EMDASH_BIN_DIR:-$HOME/.local/bin}"
PACKAGE="emdash-ai"
MIN_PYTHON_VERSION="3.10"

# Options
WITH_GRAPH=false
REINSTALL=false
SHOW_VERSION=false
VERBOSE=false
UNINSTALL=false
FORCE=false

# Logging functions
log_step() {
    echo -e "${BLUE}→${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${DIM}  [debug] $1${NC}"
    fi
}

log_progress() {
    echo -ne "\r${BLUE}→${NC} $1"
}

log_progress_done() {
    echo -e "\r${GREEN}✓${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-graph)
            WITH_GRAPH=true
            shift
            ;;
        --reinstall)
            REINSTALL=true
            shift
            ;;
        --version|-v)
            SHOW_VERSION=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --bin-dir)
            BIN_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Emdash AI Installer"
            echo ""
            echo "Usage: curl -sSL <url> | bash -s -- [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --version, -v   Show installed version"
            echo "  --reinstall     Force reinstall (removes existing installation)"
            echo "  --uninstall     Uninstall emdash completely"
            echo "  --force, -f     Skip confirmation prompts"
            echo "  --with-graph    Install with graph database support (kuzu)"
            echo "  --verbose       Show detailed progress and debug info"
            echo "  --install-dir   Installation directory (default: ~/.emdash)"
            echo "  --bin-dir       Binary directory (default: ~/.local/bin)"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Show version only
if [[ "$SHOW_VERSION" == true ]]; then
    if [[ -f "$INSTALL_DIR/.venv/bin/python" ]]; then
        VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('emdash-ai'))" 2>/dev/null)
        if [[ -n "$VERSION" ]]; then
            echo "emdash-ai v$VERSION"
        else
            log_error "emdash-ai is not installed"
            exit 1
        fi
    else
        log_error "emdash-ai is not installed"
        exit 1
    fi
    exit 0
fi

# Uninstall mode
if [[ "$UNINSTALL" == true ]]; then
    echo -e "${RED}"
    echo "  _____ __  __ ____    _    ____  _   _ "
    echo " | ____|  \/  |  _ \  / \  / ___|| | | |"
    echo " |  _| | |\/| | | | |/ _ \ \___ \| |_| |"
    echo " | |___| |  | | |_| / ___ \ ___) |  _  |"
    echo " |_____|_|  |_|____/_/   \_\____/|_| |_|"
    echo -e "${NC}"
    echo "            Uninstaller"
    echo ""

    # Check if emdash is installed
    FOUND_INSTALL=false
    FOUND_COMMANDS=false
    FOUND_UV=false
    ACTUAL_EM_PATH=""

    # Check default install location (new .venv location)
    if [[ -d "$INSTALL_DIR/.venv" ]]; then
        FOUND_INSTALL=true
        VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('emdash-ai'))" 2>/dev/null || echo "unknown")
        echo -e "  Found installation: ${YELLOW}$INSTALL_DIR${NC} (v$VERSION)"
    # Check old venv location for backwards compatibility
    elif [[ -d "$INSTALL_DIR/venv" ]]; then
        FOUND_INSTALL=true
        VERSION=$("$INSTALL_DIR/venv/bin/pip" show emdash-ai 2>/dev/null | grep "^Version:" | cut -d' ' -f2 || echo "unknown")
        echo -e "  Found installation: ${YELLOW}$INSTALL_DIR${NC} (v$VERSION)"
    fi

    # Check default bin location
    if [[ -f "$BIN_DIR/em" ]] || [[ -f "$BIN_DIR/emdash" ]] || [[ -f "$BIN_DIR/co" ]]; then
        FOUND_COMMANDS=true
        echo -e "  Found commands in: ${YELLOW}$BIN_DIR${NC}"
    fi

    # Check if em is in PATH somewhere else
    if [[ "$FOUND_COMMANDS" == false ]]; then
        ACTUAL_EM_PATH=$(command -v em 2>/dev/null || true)
        if [[ -n "$ACTUAL_EM_PATH" ]]; then
            FOUND_COMMANDS=true
            echo -e "  Found em command: ${YELLOW}$ACTUAL_EM_PATH${NC}"
        fi
    fi

    # Check if installed via uv globally
    if [[ "$FOUND_INSTALL" == false ]] && command -v uv &> /dev/null; then
        if uv pip show emdash-ai &>/dev/null 2>&1; then
            FOUND_UV=true
            UV_VERSION=$(uv pip show emdash-ai 2>/dev/null | grep "^Version:" | cut -d' ' -f2 || echo "unknown")
            echo -e "  Found uv installation: ${YELLOW}emdash-ai v$UV_VERSION${NC}"
        fi
    fi

    if [[ "$FOUND_INSTALL" == false ]] && [[ "$FOUND_COMMANDS" == false ]] && [[ "$FOUND_UV" == false ]]; then
        log_warn "Emdash AI does not appear to be installed"
        echo ""
        echo "  Checked locations:"
        echo "    - $INSTALL_DIR"
        echo "    - $BIN_DIR/em"
        echo "    - $BIN_DIR/emdash"
        echo "    - $BIN_DIR/co"
        echo "    - uv global packages"
        echo "    - PATH (via 'which em')"
        echo ""
        exit 0
    fi

    echo ""

    # Confirmation
    if [[ "$FORCE" == false ]]; then
        echo -e "${YELLOW}This will remove:${NC}"
        [[ "$FOUND_INSTALL" == true ]] && echo "  - $INSTALL_DIR (entire directory)"
        if [[ "$FOUND_COMMANDS" == true ]]; then
            [[ -f "$BIN_DIR/em" ]] && echo "  - $BIN_DIR/em"
            [[ -f "$BIN_DIR/emdash" ]] && echo "  - $BIN_DIR/emdash"
            [[ -f "$BIN_DIR/co" ]] && echo "  - $BIN_DIR/co"
            [[ -n "$ACTUAL_EM_PATH" ]] && echo "  - $ACTUAL_EM_PATH (and related emdash/co commands)"
        fi
        [[ "$FOUND_UV" == true ]] && echo "  - uv package: emdash-ai"
        echo ""
        read -p "Continue with uninstall? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            log_warn "Uninstall cancelled"
            exit 0
        fi
        echo ""
    fi

    # Remove installation directory
    if [[ "$FOUND_INSTALL" == true ]]; then
        log_step "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
        log_success "Removed $INSTALL_DIR"
    fi

    # Remove command wrappers from default location
    if [[ -f "$BIN_DIR/em" ]] || [[ -f "$BIN_DIR/emdash" ]] || [[ -f "$BIN_DIR/co" ]]; then
        log_step "Removing command shortcuts from $BIN_DIR..."
        [[ -f "$BIN_DIR/em" ]] && rm -f "$BIN_DIR/em"
        [[ -f "$BIN_DIR/emdash" ]] && rm -f "$BIN_DIR/emdash"
        [[ -f "$BIN_DIR/co" ]] && rm -f "$BIN_DIR/co"
        log_success "Removed em, emdash, and co commands"
    fi

    # Remove em command found via PATH (if different location)
    if [[ -n "$ACTUAL_EM_PATH" ]] && [[ "$ACTUAL_EM_PATH" != "$BIN_DIR/em" ]]; then
        log_step "Removing em command from $ACTUAL_EM_PATH..."
        ACTUAL_BIN_DIR=$(dirname "$ACTUAL_EM_PATH")
        rm -f "$ACTUAL_EM_PATH"
        [[ -f "$ACTUAL_BIN_DIR/emdash" ]] && rm -f "$ACTUAL_BIN_DIR/emdash"
        [[ -f "$ACTUAL_BIN_DIR/co" ]] && rm -f "$ACTUAL_BIN_DIR/co"
        log_success "Removed em command from PATH location"
    fi

    # Uninstall uv package if found
    if [[ "$FOUND_UV" == true ]]; then
        log_step "Uninstalling uv package..."
        if uv pip uninstall emdash-ai -y &>/dev/null 2>&1; then
            log_success "Uninstalled emdash-ai via uv"
        else
            log_warn "Could not uninstall uv package automatically"
            echo "  Run manually: uv pip uninstall emdash-ai"
        fi
    fi

    # Done!
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✓ Emdash AI has been uninstalled${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Note: PATH entry in your shell config was not removed."
    echo "  You may optionally remove this line from your shell config:"
    echo ""
    echo "    export PATH=\"$BIN_DIR:\$PATH\""
    echo ""
    echo "  To reinstall later:"
    echo "    curl -sSL <install-url> | bash"
    echo ""
    exit 0
fi

# Force reinstall if requested
if [[ "$REINSTALL" == true ]] && [[ -d "$INSTALL_DIR/.venv" ]]; then
    log_step "Removing existing installation..."
    log_debug "rm -rf $INSTALL_DIR/.venv"
    rm -rf "$INSTALL_DIR/.venv"
    log_success "Removed existing installation"
fi

echo -e "${BLUE}"
echo "  _____ __  __ ____    _    ____  _   _ "
echo " | ____|  \/  |  _ \  / \  / ___|| | | |"
echo " |  _| | |\/| | | | |/ _ \ \___ \| |_| |"
echo " | |___| |  | | |_| / ___ \ ___) |  _  |"
echo " |_____|_|  |_|____/_/   \_\____/|_| |_|"
echo -e "${NC}"
echo "         AI Code Assistant Installer"
echo ""

log_debug "Install directory: $INSTALL_DIR"
log_debug "Binary directory: $BIN_DIR"
log_debug "With graph: $WITH_GRAPH"

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="linux";;
        Darwin*)    OS="macos";;
        MINGW*|MSYS*|CYGWIN*) OS="windows";;
        *)          OS="unknown";;
    esac
    echo "$OS"
}

OS=$(detect_os)
log_debug "Detected uname: $(uname -s)"

if [[ "$OS" == "unknown" ]]; then
    log_error "Unsupported operating system"
    echo "This installer supports macOS and Linux."
    echo "For Windows, please use: uv pip install emdash-ai"
    exit 1
fi

if [[ "$OS" == "windows" ]]; then
    log_warn "Windows detected. Please use PowerShell installer or uv:"
    echo "  uv pip install emdash-ai"
    exit 1
fi

log_success "Detected OS: $OS"

# Check for uv and install if needed
log_step "Checking for uv..."
if ! command -v uv &> /dev/null; then
    log_warn "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the new PATH
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv &> /dev/null; then
        log_success "uv installed"
    else
        log_error "Failed to install uv"
        echo "Please install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
else
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    log_success "Found uv $UV_VERSION"
fi

# Check for cmake (required for kuzu graph database)
log_step "Checking for cmake..."
if ! command -v cmake &> /dev/null; then
    log_warn "cmake not found (required for graph database)"

    if [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            log_step "Installing cmake via Homebrew..."
            brew install cmake
            if command -v cmake &> /dev/null; then
                log_success "cmake installed"
            else
                log_error "Failed to install cmake"
                echo "Please install manually: brew install cmake"
                exit 1
            fi
        else
            log_error "Homebrew not found. Please install cmake manually:"
            echo "  brew install cmake"
            echo "  Or: https://cmake.org/download/"
            exit 1
        fi
    else
        # Linux
        log_step "Installing cmake..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y cmake
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y cmake
        elif command -v yum &> /dev/null; then
            sudo yum install -y cmake
        else
            log_error "Could not install cmake automatically"
            echo "Please install cmake manually for your distribution"
            exit 1
        fi

        if command -v cmake &> /dev/null; then
            log_success "cmake installed"
        else
            log_error "Failed to install cmake"
            exit 1
        fi
    fi
else
    CMAKE_VERSION=$(cmake --version | head -1 | cut -d' ' -f3)
    log_success "Found cmake $CMAKE_VERSION"
fi

# Check if already installed - auto-update if so
if [[ -d "$INSTALL_DIR/.venv" ]] && [[ -f "$INSTALL_DIR/.venv/bin/python" ]]; then
    # Get current version
    OLD_VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('emdash-ai'))" 2>/dev/null || echo "unknown")
    log_step "Existing installation found: ${YELLOW}v$OLD_VERSION${NC}"
    log_step "Checking for updates from PyPI..."
    log_debug "Running: uv pip install --upgrade $PACKAGE"

    # Update using uv
    if [[ "$WITH_GRAPH" == true ]]; then
        if [[ "$VERBOSE" == true ]]; then
            uv pip install --python "$INSTALL_DIR/.venv/bin/python" --upgrade "$PACKAGE[graph]"
        else
            uv pip install --python "$INSTALL_DIR/.venv/bin/python" --upgrade "$PACKAGE[graph]" 2>&1 | while read -r line; do
                log_progress "Updating... $line"
            done
            echo ""
        fi
    else
        if [[ "$VERBOSE" == true ]]; then
            uv pip install --python "$INSTALL_DIR/.venv/bin/python" --upgrade "$PACKAGE"
        else
            uv pip install --python "$INSTALL_DIR/.venv/bin/python" --upgrade "$PACKAGE" 2>&1 | while read -r line; do
                log_progress "Updating... $line"
            done
            echo ""
        fi
    fi

    # Get new version
    NEW_VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('emdash-ai'))" 2>/dev/null)

    if [[ "$OLD_VERSION" == "$NEW_VERSION" ]]; then
        log_success "Already up to date: ${GREEN}v$NEW_VERSION${NC}"
    else
        log_success "Updated: ${YELLOW}v$OLD_VERSION${NC} → ${GREEN}v$NEW_VERSION${NC}"
    fi

    # Verify commands exist and have correct permissions
    log_debug "Verifying wrapper scripts..."
    if [[ -f "$BIN_DIR/em" ]]; then
        log_debug "em script exists at $BIN_DIR/em"
        if [[ -x "$BIN_DIR/em" ]]; then
            log_debug "em script is executable"
        else
            log_warn "em script is not executable, fixing..."
            chmod +x "$BIN_DIR/em"
            log_success "Fixed em permissions"
        fi
    fi

    exit 0
fi

# Create installation directory
log_step "Creating installation directory..."
log_debug "mkdir -p $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
log_debug "Directory created: $(ls -la "$INSTALL_DIR" 2>/dev/null | head -1)"
log_success "Created $INSTALL_DIR"

# Create virtual environment using uv
log_step "Creating virtual environment (this may take a moment)..."
log_debug "Running: uv venv $INSTALL_DIR/.venv --python $MIN_PYTHON_VERSION"
uv venv "$INSTALL_DIR/.venv" --python "$MIN_PYTHON_VERSION"
log_debug "Venv created, checking python..."
if [[ -f "$INSTALL_DIR/.venv/bin/python" ]]; then
    log_success "Virtual environment created"
    PYTHON_VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_debug "Python version: $PYTHON_VERSION"
else
    log_error "Failed to create virtual environment - python not found"
    log_debug "Contents of $INSTALL_DIR/.venv/bin/:"
    ls -la "$INSTALL_DIR/.venv/bin/" 2>/dev/null || echo "  Directory not found"
    exit 1
fi

# Install package using uv
log_step "Installing emdash-ai from PyPI (this may take 1-2 minutes)..."
log_debug "Running: uv pip install $PACKAGE"
if [[ "$WITH_GRAPH" == true ]]; then
    if [[ "$VERBOSE" == true ]]; then
        uv pip install --python "$INSTALL_DIR/.venv/bin/python" "$PACKAGE[graph]"
    else
        uv pip install --python "$INSTALL_DIR/.venv/bin/python" "$PACKAGE[graph]" 2>&1 | while read -r line; do
            # Show abbreviated progress
            if [[ "$line" == *"Resolved"* ]] || [[ "$line" == *"Installed"* ]] || [[ "$line" == *"packages"* ]]; then
                echo -e "  ${DIM}$line${NC}"
            fi
        done
    fi
    log_success "Installed with graph support"
else
    if [[ "$VERBOSE" == true ]]; then
        uv pip install --python "$INSTALL_DIR/.venv/bin/python" "$PACKAGE"
    else
        uv pip install --python "$INSTALL_DIR/.venv/bin/python" "$PACKAGE" 2>&1 | while read -r line; do
            # Show abbreviated progress
            if [[ "$line" == *"Resolved"* ]] || [[ "$line" == *"Installed"* ]] || [[ "$line" == *"packages"* ]]; then
                echo -e "  ${DIM}$line${NC}"
            fi
        done
    fi
    log_success "Installed (without graph support)"
    echo -e "   ${YELLOW}Tip:${NC} For graph features, reinstall with: --with-graph"
fi

# Verify installation
log_debug "Verifying emdash-ai installation..."
if "$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; importlib.metadata.version('emdash-ai')" &>/dev/null; then
    log_debug "emdash-ai package found"
else
    log_error "emdash-ai package not found after installation"
    exit 1
fi

# Create bin directory
log_step "Creating command shortcuts..."
log_debug "mkdir -p $BIN_DIR"
mkdir -p "$BIN_DIR"

# Main 'em' command
log_debug "Creating $BIN_DIR/em wrapper script"
cat > "$BIN_DIR/em" << EOF
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/em" "\$@"
EOF

log_debug "Setting execute permission on $BIN_DIR/em"
chmod +x "$BIN_DIR/em"
if [[ -x "$BIN_DIR/em" ]]; then
    log_debug "em script is now executable"
else
    log_error "Failed to set execute permission on em script"
    log_debug "File permissions: $(ls -la "$BIN_DIR/em")"
fi

# 'emdash' command
log_debug "Creating $BIN_DIR/emdash wrapper script"
cat > "$BIN_DIR/emdash" << EOF
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/emdash" "\$@"
EOF

log_debug "Setting execute permission on $BIN_DIR/emdash"
chmod +x "$BIN_DIR/emdash"
if [[ -x "$BIN_DIR/emdash" ]]; then
    log_debug "emdash script is now executable"
else
    log_error "Failed to set execute permission on emdash script"
    log_debug "File permissions: $(ls -la "$BIN_DIR/emdash")"
fi

# 'co' command (CoworkerAgent - non-coding assistant)
log_debug "Creating $BIN_DIR/co wrapper script"
cat > "$BIN_DIR/co" << EOF
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/co" "\$@"
EOF

log_debug "Setting execute permission on $BIN_DIR/co"
chmod +x "$BIN_DIR/co"
if [[ -x "$BIN_DIR/co" ]]; then
    log_debug "co script is now executable"
else
    log_error "Failed to set execute permission on co script"
    log_debug "File permissions: $(ls -la "$BIN_DIR/co")"
fi

log_success "Created commands: em, emdash, co"
log_debug "Wrapper scripts:"
log_debug "  $(ls -la "$BIN_DIR/em" 2>/dev/null)"
log_debug "  $(ls -la "$BIN_DIR/emdash" 2>/dev/null)"
log_debug "  $(ls -la "$BIN_DIR/co" 2>/dev/null)"

# Check if bin dir is in PATH
add_to_path() {
    local shell_config=""
    local shell_name=""

    log_debug "Current shell: $SHELL"

    case "$SHELL" in
        */zsh)
            shell_config="$HOME/.zshrc"
            shell_name="zsh"
            ;;
        */bash)
            if [[ "$OS" == "macos" ]]; then
                shell_config="$HOME/.bash_profile"
            else
                shell_config="$HOME/.bashrc"
            fi
            shell_name="bash"
            ;;
        */fish)
            shell_config="$HOME/.config/fish/config.fish"
            shell_name="fish"
            ;;
        *)
            shell_config="$HOME/.profile"
            shell_name="sh"
            ;;
    esac

    log_debug "Shell config file: $shell_config"

    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo ""
        log_warn "$BIN_DIR is not in your PATH"
        echo ""

        if [[ "$shell_name" == "fish" ]]; then
            path_line="set -gx PATH \"$BIN_DIR\" \$PATH"
        else
            path_line="export PATH=\"$BIN_DIR:\$PATH\""
        fi

        read -p "  Add to $shell_config? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            log_debug "Adding PATH to $shell_config"
            echo "" >> "$shell_config"
            echo "# Emdash AI" >> "$shell_config"
            echo "$path_line" >> "$shell_config"
            log_success "Added to $shell_config"
            echo -e "   ${YELLOW}Run:${NC} source $shell_config"
        else
            echo ""
            echo "  Add this to your shell config manually:"
            echo "    $path_line"
        fi
    else
        log_debug "$BIN_DIR is already in PATH"
    fi
}

add_to_path

# Get installed version
VERSION=$("$INSTALL_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('emdash-ai'))")

# Done!
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Emdash AI v$VERSION installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Get started:"
echo "    em              # Start coding assistant"
echo "    co              # Start coworker (non-coding) assistant"
echo "    em --help       # Show all options"
echo ""
echo "  Locations:"
echo "    Install:  $INSTALL_DIR"
echo "    Commands: $BIN_DIR/em"
echo ""
echo "  Update:"
echo "    emdash update"
echo ""
echo "  Troubleshoot:"
echo "    # If 'permission denied', run:"
echo "    chmod +x $BIN_DIR/em $BIN_DIR/emdash $BIN_DIR/co"
echo ""
echo "  Uninstall:"
echo "    curl -sSL <install-url> | bash -s -- --uninstall"
echo ""
