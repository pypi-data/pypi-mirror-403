"""
FastMCP server for querying BLM land data.

Provides tools for:
- PLSS (Public Land Survey System) - Section, Township, Range
- Surface Management Agency - Who manages the land
- Mining Claims - Active and closed mining claims
- Grazing Allotments - Livestock grazing areas
- Wild Horses & Burros - Herd Management Areas
- Recreation Sites - Campgrounds, trailheads, facilities
- Wilderness & WSAs - Protected wilderness areas
- Wild & Scenic Rivers - Designated river segments
- ACECs - Areas of Critical Environmental Concern

All data is queried from official BLM ArcGIS REST services.
"""

from fastmcp import FastMCP

from mcblmplss.mixins import (
    ACECMixin,
    GrazingMixin,
    MiningClaimsMixin,
    PLSSMixin,
    RecreationMixin,
    SurfaceManagementMixin,
    WildernessMixin,
    WildHorseMixin,
    WildRiversMixin,
)

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

    **Grazing Allotments**
    BLM-managed areas for livestock grazing permits.

    **Wild Horses & Burros**
    Herd Management Areas (HMAs) with population data and AML targets.

    **Recreation Sites**
    Campgrounds, trailheads, day use areas, boat launches, and facilities.

    **Wilderness & WSAs**
    Designated Wilderness Areas and Wilderness Study Areas (WSAs).

    **Wild & Scenic Rivers**
    Federally designated Wild, Scenic, or Recreational river segments.

    **ACECs (Areas of Critical Environmental Concern)**
    BLM areas requiring special management for natural, cultural, or scenic values.

    Coverage: 30 western/midwestern states. Eastern seaboard and Texas
    use different survey systems.
    """,
)

# Create mixin instances
plss_mixin = PLSSMixin()
sma_mixin = SurfaceManagementMixin()
mining_mixin = MiningClaimsMixin()
grazing_mixin = GrazingMixin()
wild_horse_mixin = WildHorseMixin()
recreation_mixin = RecreationMixin()
wilderness_mixin = WildernessMixin()
wild_rivers_mixin = WildRiversMixin()
acec_mixin = ACECMixin()

# Register all mixin tools with the server
plss_mixin.register_all(mcp)
sma_mixin.register_all(mcp)
mining_mixin.register_all(mcp)
grazing_mixin.register_all(mcp)
wild_horse_mixin.register_all(mcp)
recreation_mixin.register_all(mcp)
wilderness_mixin.register_all(mcp)
wild_rivers_mixin.register_all(mcp)
acec_mixin.register_all(mcp)


def main():
    """Entry point for the mcblmplss MCP server."""
    try:
        from importlib.metadata import version

        package_version = version("mcblmplss")
    except Exception:
        package_version = "dev"

    print(f"🗺️  mcblmplss v{package_version} - BLM Land Data Server")
    print("📍 PLSS | 🏛️  Land Manager | ⛏️  Mining | 🐄 Grazing")
    print("🐴 Wild Horses | ⛺ Recreation | 🏔️  Wilderness | 🏞️  Rivers | 🌿 ACEC")
    mcp.run()


if __name__ == "__main__":
    main()
