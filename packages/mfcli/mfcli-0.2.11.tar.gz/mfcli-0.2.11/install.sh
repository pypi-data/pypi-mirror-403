#!/bin/bash
# mfcli Installation Script for Linux/macOS
# This script installs mfcli using pipx for isolated dependency management

set -e

echo ""
echo "======================================================================"
echo "  MFCLI INSTALLATION FOR LINUX/MACOS"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${CYAN}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}Found: Python $PYTHON_VERSION${NC}"
    
    # Extract major and minor version
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" != "3" ] || [ "$MINOR" != "12" ]; then
        echo -e "  ${YELLOW}Warning: Python 3.12.x is recommended (you have $MAJOR.$MINOR)${NC}"
        read -p "  Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "  ${RED}Installation cancelled.${NC}"
            exit 1
        fi
    fi
else
    echo -e "  ${RED}Error: Python 3 not found!${NC}"
    echo -e "  ${YELLOW}Please install Python 3.12 from https://www.python.org/downloads/${NC}"
    exit 1
fi

# Determine OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "  Detected OS: ${MACHINE}"

# Check if pipx is installed
echo ""
echo -e "${CYAN}Checking pipx installation...${NC}"
if command -v pipx &> /dev/null; then
    echo -e "  ${GREEN}pipx already installed${NC}"
else
    echo -e "  ${YELLOW}pipx not found. Installing pipx...${NC}"
    
    if [ "$MACHINE" = "Mac" ]; then
        # Try homebrew first on macOS
        if command -v brew &> /dev/null; then
            echo -e "  ${YELLOW}Installing via Homebrew...${NC}"
            brew install pipx
            pipx ensurepath
        else
            echo -e "  ${YELLOW}Installing via pip...${NC}"
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
    elif [ "$MACHINE" = "Linux" ]; then
        # Try apt-get on Debian/Ubuntu
        if command -v apt-get &> /dev/null; then
            echo -e "  ${YELLOW}Installing via apt-get...${NC}"
            sudo apt-get update && sudo apt-get install -y pipx
            pipx ensurepath
        else
            echo -e "  ${YELLOW}Installing via pip...${NC}"
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
    else
        echo -e "  ${YELLOW}Installing via pip...${NC}"
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
    
    echo -e "  ${GREEN}pipx installed successfully!${NC}"
    echo -e "  ${YELLOW}Note: You may need to restart your terminal for PATH changes to take effect.${NC}"
    
    # Add pipx to current session PATH
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install mfcli
echo ""
echo -e "${CYAN}Installing mfcli...${NC}"

# Determine installation source
if [ "$MFCLI_INSTALL_SOURCE" = "pypi" ]; then
    echo -e "  ${YELLOW}Installing from PyPI...${NC}"
    pipx install mfcli
else
    echo -e "  ${YELLOW}Installing from GitHub...${NC}"
    pipx install git+https://github.com/MultifactorAI/multifactor-adk-backend.git
fi

echo -e "  ${GREEN}mfcli installed successfully!${NC}"

# Create Multifactor directory structure
echo ""
echo -e "${CYAN}Setting up configuration directory...${NC}"

MULTIFACTOR_DIR="$HOME/Multifactor"
if [ ! -d "$MULTIFACTOR_DIR" ]; then
    mkdir -p "$MULTIFACTOR_DIR"
    echo -e "  ${GREEN}Created: $MULTIFACTOR_DIR${NC}"
else
    echo -e "  ${GREEN}Directory already exists: $MULTIFACTOR_DIR${NC}"
fi

# Check if .env file exists
ENV_FILE="$MULTIFACTOR_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "  ${YELLOW}.env file will be created when you run 'mfcli configure'${NC}"
else
    echo -e "  ${GREEN}.env file already exists${NC}"
fi

# Verify installation
echo ""
echo -e "${CYAN}Verifying installation...${NC}"

if command -v mfcli &> /dev/null; then
    echo -e "  ${GREEN}mfcli command: OK${NC}"
else
    echo -e "  ${YELLOW}Warning: mfcli command not found in PATH${NC}"
    echo -e "  ${YELLOW}You may need to restart your terminal or run: source ~/.bashrc${NC}"
fi

if command -v mfcli-mcp &> /dev/null; then
    echo -e "  ${GREEN}mfcli-mcp command: OK${NC}"
else
    echo -e "  ${YELLOW}Warning: mfcli-mcp command not found in PATH${NC}"
    echo -e "  ${YELLOW}You may need to restart your terminal or run: source ~/.bashrc${NC}"
fi

# Success message
echo ""
echo "======================================================================"
echo "  INSTALLATION COMPLETE!"
echo "======================================================================"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo ""
echo -e "  ${NC}1. Configure API keys:${NC}"
echo -e "       ${CYAN}mfcli configure${NC}"
echo ""
echo -e "  ${NC}2. Navigate to your hardware project directory:${NC}"
echo -e "       ${CYAN}cd /path/to/your/project${NC}"
echo ""
echo -e "  ${NC}3. Initialize the project:${NC}"
echo -e "       ${CYAN}mfcli init${NC}"
echo ""
echo -e "  ${NC}4. Run the pipeline:${NC}"
echo -e "       ${CYAN}mfcli run${NC}"
echo ""
echo -e "  ${NC}5. (Optional) Setup MCP server for AI coding assistants:${NC}"
echo -e "       ${CYAN}mfcli setup-mcp${NC}"
echo ""
echo -e "${GREEN}For help and documentation:${NC}"
echo -e "  ${CYAN}https://github.com/MultifactorAI/multifactor-adk-backend${NC}"
echo ""
echo -e "${GREEN}To verify your installation:${NC}"
echo -e "  ${CYAN}mfcli doctor${NC}"
echo ""
echo -e "${YELLOW}Note: If commands are not found, restart your terminal or run:${NC}"
echo -e "  ${CYAN}source ~/.bashrc${NC}  ${NC}(or ~/.zshrc for Zsh)${NC}"
echo ""
