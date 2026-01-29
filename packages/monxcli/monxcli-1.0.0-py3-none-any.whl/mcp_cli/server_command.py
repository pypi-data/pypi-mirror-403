import asyncio
from monxcli.mcp_bridge import server, monx_tool

@monx_tool(desc="Starts the MCP server.")
def start(port: int = 8000):
    """Starts the MCP server to listen for client connections."""
    print(f"Starting MCP server on port {port}...")
    server.run(transport="streamable-http")

