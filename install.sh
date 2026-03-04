#!/bin/bash
#
# JARVIS USB Installer
# Run this on the target system to install JARVIS
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "============================================"
echo "   JARVIS USB Installation Script"
echo "============================================"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Please run as root: sudo $0${NC}"
    exit 1
fi

echo -e "${GREEN}Installing JARVIS AI Assistant...${NC}"

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Installing Ollama...${NC}"
    curl -fsSL https://ollama.ai/install.sh | sh
    export PATH="$PATH:/usr/local/bin"
fi

# Create JARVIS directory
echo -e "${YELLOW}Creating JARVIS directories...${NC}"
mkdir -p /opt/jarvis/{bin,config,logs,models}

# Copy files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r $SCRIPT_DIR/bin/* /opt/jarvis/bin/
cp -r $SCRIPT_DIR/config/* /opt/jarvis/config/

chmod +x /opt/jarvis/bin/*

# Create symlink
ln -sf /opt/jarvis/bin/jarvis /usr/local/bin/jarvis

# Enable Ollama service
echo -e "${YELLOW}Setting up Ollama service...${NC}"
systemctl enable ollama 2>/dev/null || true
systemctl start ollama 2>/dev/null || true

# Load JARVIS model
echo -e "${YELLOW}Loading JARVIS model...${NC}"
if [ -f /opt/jarvis/config/Modelfile ]; then
    ollama create jarvis -f /opt/jarvis/config/Modelfile 2>/dev/null || echo "Using llama3.1"
fi

echo ""
echo -e "${GREEN}============================================"
echo "   JARVIS Installation Complete!"
echo "============================================${NC}"
echo ""
echo "Commands:"
echo "  jarvis chat     - Start chatting with JARVIS"
echo "  jarvis status  - Check system health"
echo "  jarvis monitor - Run continuous monitoring"
echo ""
echo "Note: First run may take time to load the model."
