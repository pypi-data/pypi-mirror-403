#!/usr/bin/env python3
"""
LangProtect MCP Gateway Setup Helper
Automatically configures VS Code for global MCP gateway usage
"""

import os
import json
import sys
from pathlib import Path


def get_vscode_settings_path():
    """Get the VS Code user settings path based on OS"""
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / "Library/Application Support/Code/User/settings.json"
    elif sys.platform == "win32":  # Windows
        return home / "AppData/Roaming/Code/User/settings.json"
    else:  # Linux
        return home / ".config/Code/User/settings.json"


def create_wrapper_script():
    """Create the global wrapper script"""
    wrapper_dir = Path.home() / ".local/bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    
    wrapper_path = wrapper_dir / "langprotect-mcp-wrapper.sh"
    
    wrapper_content = """#!/bin/bash
# LangProtect MCP Gateway Wrapper
# This wrapper allows global configuration for all VS Code workspaces

# Configure these environment variables with your LangProtect credentials
export LANGPROTECT_URL="${LANGPROTECT_URL:-http://localhost:8000}"
export LANGPROTECT_EMAIL="${LANGPROTECT_EMAIL:-your.email@company.com}"
export LANGPROTECT_PASSWORD="${LANGPROTECT_PASSWORD:-your-password}"
export MCP_SERVER_COMMAND="${MCP_SERVER_COMMAND:-npx}"
export MCP_SERVER_ARGS="${MCP_SERVER_ARGS:--y,@modelcontextprotocol/server-filesystem,.}"

exec langprotect-gateway "$@"
"""
    
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)
    
    return wrapper_path


def update_vscode_settings(wrapper_path):
    """Update VS Code settings to use the wrapper"""
    settings_path = get_vscode_settings_path()
    
    # Create directory if it doesn't exist
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing settings or create new
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
    else:
        settings = {}
    
    # Add MCP configuration
    if "chat.mcp.servers" not in settings:
        settings["chat.mcp.servers"] = {}
    
    settings["chat.mcp.servers"]["langprotect-gateway"] = {
        "type": "stdio",
        "command": str(wrapper_path),
        "args": []
    }
    
    # Enable auto-start
    settings["chat.mcp.autostart"] = "newAndOutdated"
    
    # Write back
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    
    return settings_path


def setup():
    """Main setup function"""
    print("🚀 Setting up LangProtect MCP Gateway...")
    print()
    
    # Create wrapper script
    print("📝 Creating global wrapper script...")
    wrapper_path = create_wrapper_script()
    print(f"   ✅ Created: {wrapper_path}")
    print()
    
    # Update VS Code settings
    print("⚙️  Configuring VS Code...")
    try:
        settings_path = update_vscode_settings(wrapper_path)
        print(f"   ✅ Updated: {settings_path}")
        print()
    except Exception as e:
        print(f"   ⚠️  Could not update VS Code settings: {e}")
        print(f"   You can manually add the configuration later.")
        print()
    
    # Print next steps
    print("✅ Setup complete!")
    print()
    print("📋 Next steps:")
    print()
    print("1. Configure your credentials:")
    print(f"   Edit: {wrapper_path}")
    print("   Set LANGPROTECT_URL, LANGPROTECT_EMAIL, and LANGPROTECT_PASSWORD")
    print()
    print("2. Reload VS Code:")
    print("   Press Ctrl+Shift+P → 'Developer: Reload Window'")
    print()
    print("3. Verify it's working:")
    print("   Press Ctrl+Shift+P → 'MCP: List Servers'")
    print("   You should see 'langprotect-gateway' listed")
    print()
    print("🎉 LangProtect will now protect ALL your VS Code workspaces!")
    print()
    print("💡 Tip: You can also set credentials via environment variables:")
    print("   export LANGPROTECT_URL=http://localhost:8000")
    print("   export LANGPROTECT_EMAIL=your.email@company.com")
    print("   export LANGPROTECT_PASSWORD=your-password")
    print()


if __name__ == "__main__":
    setup()
