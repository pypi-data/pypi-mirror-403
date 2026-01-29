## MCP Configuration

Add the following to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "semantic-retrieval": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Rakhil-Hyperworks/Semantic-layer.git",
        "semantic-retrieval",
        "YOUR_USERNAME_HERE"
      ]
    }
  }
}
```

Replace `YOUR_USERNAME_HERE` with your actual username.

After adding the configuration, restart Claude Desktop.
