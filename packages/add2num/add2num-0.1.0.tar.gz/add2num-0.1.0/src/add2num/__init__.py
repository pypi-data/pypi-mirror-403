# server.py
from mcp.server.fastmcp import FastMCP
# create a FastMCP instance
mcp = FastMCP()

@mcp.tool
def add2num(a: int, b: int) -> int:
    """
    Add two numbers together.
    """
    return a + b

@mcp.resource("greeting://{name}")
def greet(name:str) -> str:
    """
    Greet the user.
    """
    return f"Hello, {name}!"

def main() -> None:
    mcp.run(transport="stdio")