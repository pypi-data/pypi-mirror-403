#!/bin/bash

# React Native Godot MCP Server Installation Script

echo "================================================"
echo "React Native Godot MCP Server Installation"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    
    # Check if version is 3.8+
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        echo -e "${GREEN}✓ Python version is compatible${NC}"
    else
        echo -e "${RED}✗ Python 3.8+ is required${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    echo "You may need to run: pip3 install -r requirements.txt manually"
    exit 1
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x react_native_godot_mcp.py
chmod +x test_mcp_server.py
echo -e "${GREEN}✓ Scripts are now executable${NC}"

# Test the installation
echo ""
echo "Testing MCP server..."
python3 -c "
try:
    from react_native_godot_mcp import mcp
    print('✓ MCP server module loaded successfully')
except Exception as e:
    print(f'✗ Failed to load MCP server: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MCP server is ready${NC}"
else
    echo -e "${RED}✗ MCP server test failed${NC}"
    exit 1
fi

echo ""
echo "================================================"
echo -e "${GREEN}Installation complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Run the test suite: python3 test_mcp_server.py"
echo "2. Start the server: python3 react_native_godot_mcp.py"
echo "3. Or use MCP Inspector: npx @modelcontextprotocol/inspector python3 react_native_godot_mcp.py"
echo ""
echo "To integrate with Claude Desktop, add the following to your config:"
echo "Location: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "react-native-godot": {'
echo '      "command": "python3",'
echo "      \"args\": [\"$(pwd)/react_native_godot_mcp.py\"]"
echo '    }'
echo '  }'
echo '}'
echo ""
