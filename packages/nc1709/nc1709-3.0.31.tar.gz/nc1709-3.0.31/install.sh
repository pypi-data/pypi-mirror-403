#!/bin/bash
#
# NC1709 Universal Installer
# Handles all Python environments automatically
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lafzusa/nc1709/main/install.sh | bash
#   OR
#   wget -qO- https://raw.githubusercontent.com/lafzusa/nc1709/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Version
NC1709_VERSION="3.0.1"

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║     NC1709 - AI Coding Assistant Installer                ║"
    echo "║     99% Tool-Calling Accuracy                             ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$ID
            OS_VERSION=$VERSION_ID
        else
            OS="linux"
            OS_VERSION="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        OS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
    else
        OS="unknown"
        OS_VERSION="unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if pip install is blocked (PEP 668)
is_externally_managed() {
    python3 -c "import sys; sys.exit(0 if any('EXTERNALLY-MANAGED' in str(p) for p in __import__('sysconfig').get_paths().values()) else 1)" 2>/dev/null
    if [ $? -eq 0 ]; then
        return 0
    fi
    # Also check by trying a dry-run install
    if pip3 install --dry-run nc1709 2>&1 | grep -q "externally-managed-environment"; then
        return 0
    fi
    return 1
}

# Install using pipx (preferred for modern systems)
install_with_pipx() {
    print_step "Installing NC1709 using pipx..."

    # Check if pipx is installed
    if ! command_exists pipx; then
        print_step "Installing pipx first..."

        if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
            sudo apt update -qq
            sudo apt install -y pipx
        elif [[ "$OS" == "fedora" ]]; then
            sudo dnf install -y pipx
        elif [[ "$OS" == "macos" ]]; then
            if command_exists brew; then
                brew install pipx
            else
                python3 -m pip install --user pipx
            fi
        else
            python3 -m pip install --user pipx 2>/dev/null || \
            pip3 install --user pipx 2>/dev/null || \
            pip install --user pipx
        fi

        # Ensure pipx path is set
        if command_exists pipx; then
            pipx ensurepath 2>/dev/null || true
        fi
    fi

    # Install NC1709 with pipx
    if command_exists pipx; then
        pipx install nc1709 --force 2>/dev/null || pipx install nc1709
        print_success "NC1709 installed successfully with pipx!"
        return 0
    else
        print_error "Failed to install pipx"
        return 1
    fi
}

# Install using virtual environment
install_with_venv() {
    print_step "Installing NC1709 in virtual environment..."

    NC1709_VENV="$HOME/.nc1709-env"

    # Create virtual environment
    if [ -d "$NC1709_VENV" ]; then
        print_warning "Existing installation found, updating..."
        rm -rf "$NC1709_VENV"
    fi

    python3 -m venv "$NC1709_VENV"

    # Install NC1709
    "$NC1709_VENV/bin/pip" install --upgrade pip
    "$NC1709_VENV/bin/pip" install nc1709

    # Create symlink or wrapper
    NC1709_BIN="$HOME/.local/bin"
    mkdir -p "$NC1709_BIN"

    # Create wrapper script
    cat > "$NC1709_BIN/nc1709" << 'WRAPPER'
#!/bin/bash
exec "$HOME/.nc1709-env/bin/nc1709" "$@"
WRAPPER
    chmod +x "$NC1709_BIN/nc1709"

    # Add to PATH if needed
    add_to_path "$NC1709_BIN"

    print_success "NC1709 installed successfully in virtual environment!"
    return 0
}

# Install using pip directly (older systems)
install_with_pip() {
    print_step "Installing NC1709 with pip..."

    # Try user install first
    if pip3 install --user nc1709 2>/dev/null; then
        print_success "NC1709 installed successfully with pip (user)!"
        return 0
    elif pip install --user nc1709 2>/dev/null; then
        print_success "NC1709 installed successfully with pip (user)!"
        return 0
    elif sudo pip3 install nc1709 2>/dev/null; then
        print_success "NC1709 installed successfully with pip (system)!"
        return 0
    else
        print_error "pip install failed"
        return 1
    fi
}

# Add directory to PATH
add_to_path() {
    local dir="$1"
    local shell_rc=""

    # Determine shell config file
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
        shell_rc="$HOME/.bashrc"
    else
        shell_rc="$HOME/.profile"
    fi

    # Check if already in PATH
    if [[ ":$PATH:" != *":$dir:"* ]]; then
        echo "" >> "$shell_rc"
        echo "# NC1709 PATH" >> "$shell_rc"
        echo "export PATH=\"$dir:\$PATH\"" >> "$shell_rc"
        export PATH="$dir:$PATH"
        print_step "Added $dir to PATH in $shell_rc"
    fi
}

# Verify installation
verify_installation() {
    print_step "Verifying installation..."

    # Source shell config to get updated PATH
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc" 2>/dev/null || true
    fi
    if [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc" 2>/dev/null || true
    fi

    # Refresh PATH for pipx
    if command_exists pipx; then
        eval "$(pipx ensurepath 2>/dev/null)" || true
    fi

    # Try to find nc1709
    if command_exists nc1709; then
        local version=$(nc1709 --version 2>/dev/null || echo "installed")
        print_success "NC1709 is ready! Version: $version"
        return 0
    fi

    # Check common locations
    local locations=(
        "$HOME/.local/bin/nc1709"
        "$HOME/.nc1709-env/bin/nc1709"
        "/usr/local/bin/nc1709"
        "$HOME/.local/pipx/venvs/nc1709/bin/nc1709"
    )

    for loc in "${locations[@]}"; do
        if [ -x "$loc" ]; then
            print_success "NC1709 installed at: $loc"
            print_warning "You may need to restart your terminal or run: source ~/.bashrc"
            return 0
        fi
    done

    print_warning "NC1709 installed but not in PATH. Restart your terminal."
    return 0
}

# Print post-install instructions
print_instructions() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  NC1709 Installation Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}Quick Start:${NC}"
    echo ""
    echo "    1. Get your API key: support@lafzusa.com"
    echo ""
    echo "    2. Set your API key:"
    echo -e "       ${YELLOW}export NC1709_API_KEY=\"your-api-key\"${NC}"
    echo ""
    echo "    3. Start using NC1709:"
    echo -e "       ${YELLOW}nc1709 \"create a Python web server\"${NC}"
    echo ""
    echo -e "  ${CYAN}Test with demo key:${NC}"
    echo -e "       ${YELLOW}export NC1709_API_KEY=\"nc1709_production_key\"${NC}"
    echo -e "       ${YELLOW}nc1709 \"hello world\"${NC}"
    echo ""
    echo -e "  ${CYAN}Documentation:${NC} https://docs.lafzusa.com/nc1709"
    echo -e "  ${CYAN}Support:${NC} support@lafzusa.com"
    echo ""

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "  ${YELLOW}NOTE: Restart your terminal or run:${NC}"
        echo -e "       ${YELLOW}source ~/.bashrc${NC}"
        echo ""
    fi
}

# Main installation logic
main() {
    print_banner

    detect_os
    print_step "Detected OS: $OS $OS_VERSION"

    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed."
        print_step "Install Python 3 first:"
        if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
            echo "  sudo apt install python3 python3-pip python3-venv"
        elif [[ "$OS" == "fedora" ]]; then
            echo "  sudo dnf install python3 python3-pip"
        elif [[ "$OS" == "macos" ]]; then
            echo "  brew install python3"
        fi
        exit 1
    fi

    print_step "Python version: $(python3 --version)"

    # Determine installation method
    local installed=false

    # Check if system has PEP 668 restrictions
    if is_externally_managed; then
        print_step "Modern Python environment detected (PEP 668)"

        # Try pipx first (cleanest solution)
        if install_with_pipx; then
            installed=true
        # Fallback to venv
        elif install_with_venv; then
            installed=true
        fi
    else
        print_step "Traditional Python environment detected"

        # Try direct pip install
        if install_with_pip; then
            installed=true
        # Fallback to venv
        elif install_with_venv; then
            installed=true
        fi
    fi

    if [ "$installed" = true ]; then
        verify_installation
        print_instructions
        exit 0
    else
        print_error "Installation failed. Please try manual installation:"
        echo ""
        echo "  Option 1: pipx install nc1709"
        echo "  Option 2: python3 -m venv ~/.nc1709-env && ~/.nc1709-env/bin/pip install nc1709"
        echo ""
        echo "  For help: support@lafzusa.com"
        exit 1
    fi
}

# Run main
main "$@"
