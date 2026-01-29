# monxcli/mcp_bridge.py

from mcp.server import FastMCP
from monxcli.commands import commands as monx_cli_commands

# Shared MCP server instance
server = FastMCP("monxcli-mcp", stateless_http=True, host="0.0.0.0", port=1919)


def monx_tool(func=None, *, name=None, desc=None):
    """
    Use this decorator ONCE on a function.
    It becomes:
        - a MonxCLI command
        - an MCP tool

    Example:
        @monx_tool(desc="Adds two numbers")
        def add(a: int, b: int):
            return a + b
    """

    if func is None:
        return lambda f: monx_tool(f, name=name, desc=desc)

    # Register for MonxCLI
    monx_wrapped = monx_cli_commands.command()(func)

    # Register for MCP
    tool_name = name or func.__name__
    server.tool(name=tool_name, description=desc)(func)

    return monx_wrapped
