# Description: Entry point for running the quantum MCP server.
# Description: Allows running the server via python -m quantum_mcp.
"""Entry point for the quantum MCP server."""

from quantum_mcp.server import create_server


def main() -> None:
    """Run the MCP server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
