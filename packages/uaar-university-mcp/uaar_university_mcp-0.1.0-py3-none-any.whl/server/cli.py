"""MCP server CLI entry point for stdio transport (Claude Code CLI)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.tools import register_all_tools
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("university_mcp", instructions="Tools for university information access and management.")
register_all_tools(mcp)

if __name__ == "__main__":
    import sys
    mcp.run(transport="stdio")