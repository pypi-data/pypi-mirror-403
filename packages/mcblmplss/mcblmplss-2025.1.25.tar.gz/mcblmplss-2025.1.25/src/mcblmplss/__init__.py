"""
mcblmplss - FastMCP server for BLM land data queries.

Query BLM data by coordinates:
- PLSS (Public Land Survey System) - Section, Township, Range
- Surface Management Agency - Who manages the land
- Mining Claims - Active and closed mining claims
"""

from mcblmplss.server import main, mcp

__all__ = ["main", "mcp"]
