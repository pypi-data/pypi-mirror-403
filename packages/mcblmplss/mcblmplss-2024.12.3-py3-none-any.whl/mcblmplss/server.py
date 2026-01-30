"""
FastMCP server for querying BLM land data.

Provides tools for:
- PLSS (Public Land Survey System) - Section, Township, Range
- Surface Management Agency - Who manages the land
- Mining Claims - Active and closed mining claims

All data is queried from official BLM ArcGIS REST services.
"""

from fastmcp import FastMCP

from mcblmplss.mixins import MiningClaimsMixin, PLSSMixin, SurfaceManagementMixin

# Initialize FastMCP server
mcp = FastMCP(
    name="mcblmplss",
    instructions="""
    Query U.S. Bureau of Land Management (BLM) land data by coordinates.

    **PLSS (Public Land Survey System)**
    The survey grid dividing western/midwestern US into:
    - Townships: 6x6 mile squares (N/S from baseline, E/W from meridian)
    - Sections: 1 square mile (640 acres), numbered 1-36
    - Principal Meridians: Reference lines for survey system

    **Surface Management Agency**
    Who manages the land surface:
    - Federal: BLM, Forest Service, NPS, Fish & Wildlife, etc.
    - State, Local, Tribal, or Private

    **Mining Claims**
    Mineral rights claims from BLM's MLRS database:
    - Lode Claims: Hard rock minerals (veins, ledges)
    - Placer Claims: Loose deposits (gold in streams)
    - Mill Sites, Tunnel Sites

    Coverage: 30 western/midwestern states. Eastern seaboard and Texas
    use different survey systems.
    """,
)

# Create mixin instances and register tools
plss_mixin = PLSSMixin()
sma_mixin = SurfaceManagementMixin()
mining_mixin = MiningClaimsMixin()

# Register all mixin tools with the server
plss_mixin.register_all(mcp)
sma_mixin.register_all(mcp)
mining_mixin.register_all(mcp)


def main():
    """Entry point for the mcblmplss MCP server."""
    try:
        from importlib.metadata import version

        package_version = version("mcblmplss")
    except Exception:
        package_version = "dev"

    print(f"🗺️  mcblmplss v{package_version} - BLM Land Data Server")
    print("📍 PLSS | 🏛️  Surface Management | ⛏️  Mining Claims")
    mcp.run()


if __name__ == "__main__":
    main()
