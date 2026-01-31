"""STDIO transport entry point for MCP Agent Mail server."""

from __future__ import annotations

from .app import build_mcp_server


def main() -> None:
    """Run the MCP server over stdio transport."""
    # Create MCP server instance
    mcp_server = build_mcp_server()

    # Run with stdio transport
    mcp_server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()