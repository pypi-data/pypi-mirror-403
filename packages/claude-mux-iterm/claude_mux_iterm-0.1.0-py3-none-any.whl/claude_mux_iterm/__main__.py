"""Entry point for Claude Mux iTerm MCP server."""

from .server import mcp


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
