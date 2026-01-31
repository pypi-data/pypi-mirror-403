# MCP Server Configuration Examples

## Claude Desktop Configuration

### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "react-native-godot": {
      "command": "python3",
      "args": ["/absolute/path/to/react_native_godot_mcp.py"],
      "env": {}
    }
  }
}
```

### Windows
Location: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "react-native-godot": {
      "command": "python",
      "args": ["C:\\path\\to\\react_native_godot_mcp.py"],
      "env": {}
    }
  }
}
```

### Linux
Location: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "react-native-godot": {
      "command": "python3",
      "args": ["/home/user/path/to/react_native_godot_mcp.py"],
      "env": {}
    }
  }
}
```

## MCP Inspector Testing

Use the MCP Inspector to test the server interactively:

```bash
npx @modelcontextprotocol/inspector python3 react_native_godot_mcp.py
```

This opens a web interface where you can:
- View all available tools
- Test each tool with different parameters
- See the responses in real-time

## Python Client Integration

```python
import asyncio
from mcp import Client

async def use_mcp_server():
    # Initialize client
    client = Client()
    
    # Connect to the server via stdio
    await client.connect_stdio(["python3", "react_native_godot_mcp.py"])
    
    # List available tools
    tools = await client.list_tools()
    print("Available tools:", [tool.name for tool in tools])
    
    # Call a tool
    result = await client.call_tool(
        "get_documentation",
        {
            "section": "initialization",
            "format": "markdown",
            "detail": "detailed"
        }
    )
    
    print("Result:", result)
    
    # Clean up
    await client.disconnect()

# Run the client
asyncio.run(use_mcp_server())
```

## TypeScript/Node.js Client

```typescript
import { Client } from '@modelcontextprotocol/sdk';

async function useMCPServer() {
    // Initialize client
    const client = new Client();
    
    // Connect to the server
    await client.connect({
        command: 'python3',
        args: ['react_native_godot_mcp.py'],
        transport: 'stdio'
    });
    
    // Call a tool
    const result = await client.callTool({
        name: 'search_documentation',
        arguments: {
            query: 'worklets',
            max_results: 5,
            format: 'markdown'
        }
    });
    
    console.log('Search results:', result);
    
    // Disconnect
    await client.disconnect();
}

useMCPServer().catch(console.error);
```

## Docker Configuration

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server
COPY react_native_godot_mcp.py .

# Run the server
CMD ["python", "react_native_godot_mcp.py"]
```

Build and run:
```bash
docker build -t react-native-godot-mcp .
docker run -it react-native-godot-mcp
```

## Environment Variables

You can customize the server behavior with environment variables:

```bash
# Set custom GitHub branch
export RNG_GITHUB_BRANCH=develop

# Set custom timeout
export RNG_REQUEST_TIMEOUT=60

# Set character limit
export RNG_CHAR_LIMIT=50000

python3 react_native_godot_mcp.py
```

## Systemd Service (Linux)

Create `/etc/systemd/system/react-native-godot-mcp.service`:

```ini
[Unit]
Description=React Native Godot MCP Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/server
ExecStart=/usr/bin/python3 /path/to/react_native_godot_mcp.py
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable react-native-godot-mcp
sudo systemctl start react-native-godot-mcp
sudo systemctl status react-native-godot-mcp
```

## Logging Configuration

Add logging to the server by modifying the Python script:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## Multiple Server Configuration

Run multiple MCP servers together in Claude:

```json
{
  "mcpServers": {
    "react-native-godot": {
      "command": "python3",
      "args": ["/path/to/react_native_godot_mcp.py"]
    },
    "another-server": {
      "command": "node",
      "args": ["/path/to/another-server.js"]
    }
  }
}
```

## Troubleshooting

### Server won't start
- Check Python version: `python3 --version` (needs 3.8+)
- Verify dependencies: `pip3 list | grep -E "mcp|fastmcp|httpx|pydantic"`
- Check file permissions: `ls -la react_native_godot_mcp.py`

### Connection issues
- Test with MCP Inspector first
- Check the server is running: `ps aux | grep react_native_godot_mcp`
- Verify path in config is absolute, not relative

### Tool errors
- Check network connection for GitHub access
- Verify the repository is accessible
- Check error messages in server output

## Performance Tuning

For better performance with multiple concurrent requests:

```python
# In react_native_godot_mcp.py, adjust these values:
CHARACTER_LIMIT = 50000  # Increase for more content
REQUEST_TIMEOUT = 60     # Increase for slow connections
MAX_CONCURRENT = 10      # Limit concurrent requests
```

## Security Considerations

- The server only reads from public GitHub repositories
- No authentication is stored or transmitted
- Consider running in a containerized environment for isolation
- Use read-only file system mounts where possible
