# LangProtect MCP Gateway

🛡️ **Security gateway for Model Context Protocol (MCP)** - Protect your AI tool interactions from security threats.

[![PyPI version](https://badge.fury.io/py/langprotect-mcp-gateway.svg)](https://pypi.org/project/langprotect-mcp-gateway/)

## Features

✅ **Automatic Threat Detection** - Scans all MCP requests for security risks  
✅ **Access Control** - Whitelist/blacklist MCP servers and tools  
✅ **Full Audit Trail** - Logs all AI interactions for compliance  
✅ **IDE Support** - Works with VS Code, Cursor, and all MCP-compatible IDEs  
✅ **Easy Setup** - 30-second installation
✅ **Fail-Open Design** - Won't block your workflow if backend is unavailable

## Quick Start

### Installation

The gateway runs as a global CLI tool. Choose your platform:

#### Linux (Debian/Ubuntu) - Recommended: pipx

```bash
# Install pipx (one time)
sudo apt install pipx -y
pipx ensurepath

# Install the gateway
pipx install langprotect-mcp-gateway
```

#### macOS - Recommended: pipx

```bash
# Install pipx via Homebrew
brew install pipx
pipx ensurepath

# Install the gateway
pipx install langprotect-mcp-gateway
```

#### Windows

```bash
# Option 1: pipx (recommended)
pip install pipx
pipx install langprotect-mcp-gateway

# Option 2: User install
pip install --user langprotect-mcp-gateway
```

#### Verify Installation

```bash
which langprotect-gateway   # Should show: ~/.local/bin/langprotect-gateway
langprotect-gateway --help  # Should show usage info
```

### VS Code Setup (Recommended - No Wrapper Script!)

Just add this to your `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "langprotect-gateway": {
      "command": "langprotect-gateway",
      "args": ["--mcp-json-path", "${workspaceFolder}/.vscode/mcp.json"],
      "env": {
        "LANGPROTECT_URL": "http://localhost:8000",
        "LANGPROTECT_EMAIL": "your.email@company.com",
        "LANGPROTECT_PASSWORD": "your-password"
      },
      "servers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
      }
    }
  }
}
```

That's it! VS Code will:
1. Start the gateway with your credentials
2. Gateway reads the `servers` section and proxies those MCP servers
3. All tool calls get logged to LangProtect

### Alternative: Wrapper Script Setup

If you prefer using a wrapper script (useful for shared configs):

1. Create a wrapper script (e.g., `langprotect-wrapper.sh`):

```bash
#!/bin/bash
export LANGPROTECT_URL="http://localhost:8000"  # Your LangProtect backend
export LANGPROTECT_EMAIL="your.email@company.com"
export LANGPROTECT_PASSWORD="your-password"
export MCP_SERVER_COMMAND="npx"
export MCP_SERVER_ARGS="-y,@modelcontextprotocol/server-filesystem,/path/to/allowed/dir"

exec langprotect-gateway "$@"
```

2. Make it executable: `chmod +x langprotect-wrapper.sh`

3. Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "langprotect-filesystem": {
      "type": "stdio",
      "command": "/path/to/langprotect-wrapper.sh",
      "args": []
    }
  }
}
```

4. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

5. Start the server: `Ctrl+Shift+P` → "MCP: List Servers" → Click "Start"

### Cursor Setup

```json
{
  "mcpServers": {
    "langprotect-gateway": {
      "command": "langprotect-gateway",
      "args": ["--mcp-json-path", "~/.cursor/mcp.json"],
      "env": {
        "LANGPROTECT_URL": "http://localhost:8000",
        "LANGPROTECT_EMAIL": "your.email@company.com",
        "LANGPROTECT_PASSWORD": "your-password"
      },
      "servers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
      }
    }
  }
}
```

### Claude Desktop Setup

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "langprotect-gateway": {
      "command": "langprotect-gateway",
      "args": ["--mcp-json-path", "~/Library/Application Support/Claude/claude_desktop_config.json"],
      "env": {
        "LANGPROTECT_URL": "http://localhost:8000",
        "LANGPROTECT_EMAIL": "your.email@company.com",
        "LANGPROTECT_PASSWORD": "your-password"
      },
      "servers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
      }
    }
  }
}
```

## How It Works

```
┌─────────────┐     ┌────────────────────┐     ┌──────────────────┐
│   VS Code   │────▶│ LangProtect Gateway│────▶│  Filesystem MCP  │
│  (Copilot)  │     │   (Security Scan)  │     │    Server        │
└─────────────┘     └────────────────────┘     └──────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ LangProtect Backend│
                    │  (Policy Check)    │
                    └────────────────────┘
```

1. **Intercepts** all MCP tool calls from your AI assistant
2. **Sends** each request to LangProtect backend for security scanning
3. **Blocks** requests that violate your security policies
4. **Forwards** allowed requests to the actual MCP server
5. **Logs** everything for audit trail
         ↓
LangProtect Gateway (this package)
         ↓
    [Security Scan]
         ↓
MCP Servers (filesystem, github, etc.)
```

Every request is:
1. Intercepted by the gateway
2. Scanned for security threats
3. Logged to LangProtect backend
4. Forwarded to actual MCP server (if safe)
5. Response returned to AI

## Dashboard

Monitor all activity at your LangProtect dashboard:
- View all AI interactions
- See security threats blocked
- Track IDE usage
- Generate compliance reports

## Security

The gateway protects against:
- 🚫 Sensitive file access (`.env`, SSH keys, etc.)
- 🚫 Dangerous commands (`rm -rf`, data exfiltration)
- 🚫 SQL injection patterns
- 🚫 Hardcoded credentials in suggestions
- 🚫 Prompt injection attacks

## Troubleshooting

**"externally-managed-environment" error on Linux:**
- Modern Linux systems protect system Python. Use `pipx` instead:
  ```bash
  sudo apt install pipx -y
  pipx install langprotect-mcp-gateway
  ```

**Authentication failed:**
- Check `LANGPROTECT_URL`, `LANGPROTECT_EMAIL`, `LANGPROTECT_PASSWORD` are correct
- Ensure LangProtect backend is accessible

**Gateway not starting:**
- Check Python version: `python3 --version` (need 3.8+)
- Check package installed: `pipx list | grep langprotect`
- Verify path: `which langprotect-gateway`

**Tools not working:**
- Check MCP servers are configured under `"servers"` section
- Restart IDE completely

**Command not found after install:**
- Run `pipx ensurepath` and restart your terminal
- Or add `~/.local/bin` to your PATH manually

## For Team Leads

### Quick Team Rollout:

1. **Share credentials** with each team member:
   ```
   Email: user@company.com
   Password: secure-password
   Server: http://langprotect.company.com:8000
   ```

2. **Team members install:**
   ```bash
   # Linux/macOS
   sudo apt install pipx -y  # or: brew install pipx
   pipx install langprotect-mcp-gateway
   
   # Configure mcp.json with credentials
   # Restart IDE
   ```

3. **Monitor dashboard:** See all team activity in real-time

## Updates

```bash
# Upgrade with pipx
pipx upgrade langprotect-mcp-gateway

# Or reinstall specific version
pipx install langprotect-mcp-gateway==1.1.0 --force
```

## Support

- **Documentation:** https://docs.langprotect.com
- **Issues:** https://github.com/langprotect/mcp-gateway/issues
- **Security:** security@langprotect.com

## License

MIT License - see LICENSE file for details

## Links

- **Homepage:** https://langprotect.com
- **GitHub:** https://github.com/langprotect/mcp-gateway
- **Documentation:** https://docs.langprotect.com
