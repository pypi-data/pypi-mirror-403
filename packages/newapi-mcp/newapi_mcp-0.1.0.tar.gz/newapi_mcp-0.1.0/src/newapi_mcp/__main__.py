"""MCP server entry point for stdio transport."""

import sys

from .server import mcp


def main() -> int:
    """Run MCP server with stdio transport.

    This is the main entry point for the MCP server when deployed via stdio.
    It's used by Claude Desktop and other MCP clients.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        mcp.run(transport="stdio")
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
