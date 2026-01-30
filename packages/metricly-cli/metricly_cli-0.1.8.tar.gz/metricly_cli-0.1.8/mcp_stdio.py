#!/usr/bin/env python3
"""Metricly MCP Server - Local stdio transport for Claude Code.

This is a wrapper that runs the MCP server in stdio mode for local
Claude Code integration. It uses the CLI's authentication system
(credentials stored in ~/.metricly/).

Usage:
    # First login via CLI
    metricly login

    # Then add to Claude Code settings (see below)

    # Or use dev mode with emulators (no login required)
    METRICLY_DEV_MODE=1 python mcp_stdio.py

Claude Code Integration:
    Add to ~/.claude/settings.json or project's .claude/settings.local.json:

    {
      "mcpServers": {
        "metricly": {
          "command": "uv",
          "args": ["run", "--project", "/path/to/metricly/backend", "python", "mcp_stdio.py"],
          "env": {
            "FIRESTORE_EMULATOR_HOST": "localhost:8081"  # Optional: for local dev
          }
        }
      }
    }

    For dev mode with emulators:
    {
      "mcpServers": {
        "metricly": {
          "command": "uv",
          "args": ["run", "--project", "/path/to/metricly/backend", "python", "mcp_stdio.py"],
          "env": {
            "FIRESTORE_EMULATOR_HOST": "localhost:8081",
            "METRICLY_DEV_MODE": "1"
          }
        }
      }
    }
"""

import asyncio
import sys
import os

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import _init_firebase
from services.auth import UserContext


def get_dev_user() -> UserContext:
    """Get a dev user for local emulator testing."""
    return UserContext(
        uid="dev-user",
        email="dev@metricly.xyz",
        org_id="local-dev",
        role="owner",
    )


async def get_cli_user() -> UserContext:
    """Get user from CLI credentials."""
    from cli.auth import CLIAuthManager, AuthenticationError

    auth = CLIAuthManager()

    if not auth.is_logged_in():
        raise AuthenticationError("Not logged in. Run 'metricly login' first.")

    return await auth.get_user()


def main():
    """Run MCP server in stdio mode with CLI authentication."""
    # Initialize Firebase
    _init_firebase()

    # Check for dev mode (uses mock user, no login required)
    dev_mode = os.environ.get("METRICLY_DEV_MODE", "").lower() in ("1", "true", "yes")

    if dev_mode:
        user = get_dev_user()
        print(f"Dev mode: using mock user {user.email}", file=sys.stderr)
    else:
        try:
            user = asyncio.run(get_cli_user())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Set stdio user before importing mcp_server (bypasses OAuth)
    from mcp_server import set_stdio_user, mcp
    set_stdio_user(user)

    # Run in stdio mode (synchronous)
    print(f"Starting Metricly MCP (stdio) as {user.email}...", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
