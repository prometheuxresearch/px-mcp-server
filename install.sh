#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Prometheux MCP Server - Installation Script             ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Darwin*)    OS_TYPE="macOS";;
    Linux*)     OS_TYPE="Linux";;
    *)          OS_TYPE="UNKNOWN";;
esac

if [ "$OS_TYPE" = "UNKNOWN" ]; then
    echo -e "${RED}Error: Unsupported operating system${NC}"
    echo "This script only works on macOS and Linux."
    echo "For Windows, please follow the manual installation instructions."
    exit 1
fi

echo -e "${GREEN}✓${NC} Detected OS: $OS_TYPE"
echo ""

# Step 1: Check/Install pipx
echo -e "${BLUE}[Step 1/5]${NC} Checking for pipx..."

if command -v pipx &> /dev/null; then
    echo -e "${GREEN}✓${NC} pipx is already installed"
else
    echo -e "${YELLOW}⚠${NC} pipx not found. Installing pipx..."
    
    if [ "$OS_TYPE" = "macOS" ]; then
        if command -v brew &> /dev/null; then
            brew install pipx
            pipx ensurepath
        else
            echo -e "${YELLOW}Homebrew not found. Installing pipx via pip...${NC}"
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
    else
        # Linux
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
    
    echo -e "${GREEN}✓${NC} pipx installed successfully"
fi

# Ensure pipx path is available
export PATH="$HOME/.local/bin:$PATH"

echo ""

# Step 2: Install prometheux-mcp
echo -e "${BLUE}[Step 2/5]${NC} Installing prometheux-mcp package..."

# Check if already installed
if pipx list | grep -q prometheux-mcp; then
    echo -e "${YELLOW}⚠${NC} prometheux-mcp is already installed. Upgrading..."
    pipx upgrade prometheux-mcp || pipx install prometheux-mcp --force
else
    pipx install prometheux-mcp
fi

echo -e "${GREEN}✓${NC} prometheux-mcp installed successfully"
echo ""

# Step 3: Collect credentials
echo -e "${BLUE}[Step 3/5]${NC} Please provide your Prometheux credentials..."
echo ""

read -p "Prometheux API URL (press Enter for default: https://api.prometheux.ai): " PROMETHEUX_URL
PROMETHEUX_URL=${PROMETHEUX_URL:-https://api.prometheux.ai}

read -p "Username: " PROMETHEUX_USERNAME
while [ -z "$PROMETHEUX_USERNAME" ]; do
    echo -e "${RED}Username is required${NC}"
    read -p "Username: " PROMETHEUX_USERNAME
done

read -p "Organization: " PROMETHEUX_ORGANIZATION
while [ -z "$PROMETHEUX_ORGANIZATION" ]; do
    echo -e "${RED}Organization is required${NC}"
    read -p "Organization: " PROMETHEUX_ORGANIZATION
done

read -sp "Authentication Token: " PROMETHEUX_TOKEN
echo ""
while [ -z "$PROMETHEUX_TOKEN" ]; do
    echo -e "${RED}Token is required${NC}"
    read -sp "Authentication Token: " PROMETHEUX_TOKEN
    echo ""
done

echo ""
echo -e "${GREEN}✓${NC} Credentials collected"
echo ""

# Step 4: Configure Claude Desktop
echo -e "${BLUE}[Step 4/5]${NC} Configuring Claude Desktop..."

# Determine config file location
if [ "$OS_TYPE" = "macOS" ]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
else
    CONFIG_DIR="$HOME/.config/Claude"
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

# Create directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Get the full path to prometheux-mcp
PROMETHEUX_MCP_PATH=$(which prometheux-mcp)

if [ -z "$PROMETHEUX_MCP_PATH" ]; then
    PROMETHEUX_MCP_PATH="$HOME/.local/bin/prometheux-mcp"
fi

# Create or update config file
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} Config file already exists. Creating backup..."
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Check if the config already has mcpServers
    if grep -q '"mcpServers"' "$CONFIG_FILE"; then
        # Config has mcpServers, we need to add/update prometheux entry
        # For simplicity, we'll use python to manipulate JSON
        python3 << EOF
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['prometheux'] = {
    'command': '$PROMETHEUX_MCP_PATH',
    'args': ['--url', '$PROMETHEUX_URL'],
    'env': {
        'PROMETHEUX_TOKEN': '$PROMETHEUX_TOKEN',
        'PROMETHEUX_USERNAME': '$PROMETHEUX_USERNAME',
        'PROMETHEUX_ORGANIZATION': '$PROMETHEUX_ORGANIZATION'
    }
}

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)

print('${GREEN}✓${NC} Configuration updated')
EOF
    else
        # No mcpServers in config, create new structure
        python3 << EOF
import json

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
except:
    config = {}

config['mcpServers'] = {
    'prometheux': {
        'command': '$PROMETHEUX_MCP_PATH',
        'args': ['--url', '$PROMETHEUX_URL'],
        'env': {
            'PROMETHEUX_TOKEN': '$PROMETHEUX_TOKEN',
            'PROMETHEUX_USERNAME': '$PROMETHEUX_USERNAME',
            'PROMETHEUX_ORGANIZATION': '$PROMETHEUX_ORGANIZATION'
        }
    }
}

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)

print('${GREEN}✓${NC} Configuration updated')
EOF
    fi
else
    # Create new config file
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "prometheux": {
      "command": "$PROMETHEUX_MCP_PATH",
      "args": ["--url", "$PROMETHEUX_URL"],
      "env": {
        "PROMETHEUX_TOKEN": "$PROMETHEUX_TOKEN",
        "PROMETHEUX_USERNAME": "$PROMETHEUX_USERNAME",
        "PROMETHEUX_ORGANIZATION": "$PROMETHEUX_ORGANIZATION"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✓${NC} Configuration file created"
fi

echo ""

# Step 5: Final instructions
echo -e "${BLUE}[Step 5/5]${NC} Installation complete!"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 Installation Successful! 🎉                ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "  1. Restart Claude Desktop completely (Quit with Cmd+Q, then reopen)"
echo "  2. Look for the 🔨 (hammer) icon in Claude Desktop"
echo "  3. Verify 'Prometheux Knowledge Graph' appears in the tools list"
echo "  4. Test by asking Claude: 'List my Prometheux concepts'"
echo ""
echo -e "${BLUE}Configuration saved to:${NC}"
echo "  $CONFIG_FILE"
echo ""
echo -e "${BLUE}Backup created:${NC}"
LATEST_BACKUP=$(ls -t "$CONFIG_FILE.backup."* 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "  $LATEST_BACKUP"
else
    echo "  (no backup needed - new installation)"
fi
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "  • If tools don't appear, check Claude Desktop logs"
echo "  • macOS logs: ~/Library/Logs/Claude/"
echo "  • Linux logs: ~/.config/Claude/logs/"
echo ""
echo -e "${GREEN}For support:${NC} davben@prometheux.co.uk, teodoro.baldazzi@prometheux.co.uk, support@prometheux.co.uk"
echo ""
