#!/usr/bin/env python3
"""MCP CLI command handlers for socialia."""

import sys


def cmd_mcp(args) -> int:
    """Handle MCP command."""
    from .._branding import get_env_var_name

    if args.mcp_command == "start":
        import asyncio
        from ..mcp_server import main as mcp_main, HAS_MCP

        if not HAS_MCP:
            print(
                "Error: MCP package not installed. Run: pip install socialia[mcp]",
                file=sys.stderr,
            )
            return 1
        asyncio.run(mcp_main())
        return 0

    elif args.mcp_command == "doctor":
        from ..mcp_server import HAS_MCP

        print("Socialia MCP Server - Health Check")
        print("=" * 40)
        print()
        # Check MCP package
        if HAS_MCP:
            print("✅ MCP package installed")
        else:
            print("❌ MCP package not installed")
            print("   Run: pip install socialia[mcp]")
        # Check platform credentials
        from .._branding import get_env

        platforms = {
            "Twitter": ["X_CONSUMER_KEY", "X_ACCESSTOKEN"],
            "LinkedIn": ["LINKEDIN_ACCESS_TOKEN"],
            "Reddit": ["REDDIT_CLIENT_ID", "REDDIT_USERNAME"],
            "YouTube": ["YOUTUBE_CLIENT_SECRETS_FILE"],
            "Analytics": ["GOOGLE_ANALYTICS_MEASUREMENT_ID"],
        }
        print()
        for platform, keys in platforms.items():
            configured = all(get_env(k) for k in keys)
            status = "✅" if configured else "⚪"
            print(f"{status} {platform}")
        return 0

    elif args.mcp_command == "list-tools":
        print("Available MCP Tools:")
        print("─" * 40)
        tools = [
            ("social_post", "Post to social media platform"),
            ("social_delete", "Delete a post"),
            ("social_feed", "Get recent posts"),
            ("social_mentions", "Get mentions"),
            ("analytics_track", "Track an event"),
            ("analytics_realtime", "Get realtime users"),
            ("analytics_pageviews", "Get page views"),
            ("analytics_sources", "Get traffic sources"),
        ]
        for name, desc in tools:
            print(f"  {name:20} {desc}")
        return 0

    elif args.mcp_command == "installation":
        print("Claude Desktop Configuration")
        print("=" * 40)
        print()
        print("Add to your Claude Desktop config:")
        print()
        config = f'''{{
  "mcpServers": {{
    "socialia": {{
      "command": "socialia",
      "args": ["mcp", "start"],
      "env": {{
        "{get_env_var_name("X_CONSUMER_KEY")}": "...",
        "{get_env_var_name("X_CONSUMER_KEY_SECRET")}": "...",
        "{get_env_var_name("X_ACCESSTOKEN")}": "...",
        "{get_env_var_name("X_ACCESSTOKEN_SECRET")}": "..."
      }}
    }}
  }}
}}'''
        print(config)
        return 0

    else:
        print(
            "Usage: socialia mcp {start|doctor|list-tools|installation}",
            file=sys.stderr,
        )
        return 1
