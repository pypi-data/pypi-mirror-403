# Test version for local testing without real Entra ID credentials
from fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

mcp = FastMCP("azure_user_mcp_server")


@mcp.tool()
def get_user_name() -> str:
    """this is a tool to get my user name from the Entra ID."""
    # For testing purposes, return a mock user name
    return "Test User (Mock)"


if __name__ == "__main__":
    logger.info("Starting MCP server (test version)...")
    mcp.run(transport="stdio")


def main():
    """Main entry point for the MCP server (test version)."""
    logger.info("Starting MCP server (test version)...")
    mcp.run(transport="stdio")
