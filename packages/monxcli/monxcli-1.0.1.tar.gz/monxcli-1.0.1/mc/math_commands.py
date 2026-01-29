from monxcli.mcp_bridge import monx_tool


@monx_tool(desc="Add two numbers together.")
@staticmethod
def add(x: int, y: int):
    """Adds two numbers."""
    print(f"The result of {x} + {y} is {x + y}")

@monx_tool(desc="subtract two numbers.")
@staticmethod
def subtract(x: int, y: int):
    """Subtracts two numbers."""
    print(f"The result of {x} - {y} is {x - y}")

@monx_tool(desc="Multiply two numbers.")
@staticmethod
def multiply(a: int, b: int):
    return a * b