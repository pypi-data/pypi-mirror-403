"""
PLSS (Public Land Survey System) mixin for BLM MCP server.

Provides tools for querying Section, Township, and Range from coordinates.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# BLM Cadastral MapServer
PLSS_URL = "https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer"
LAYER_TOWNSHIP = 1
LAYER_SECTION = 2


class PLSSLocation(BaseModel):
    """Public Land Survey System location."""

    section: str | None = Field(None, description="Section number (1-36)")
    township: str = Field(..., description="Township with direction (e.g., '4N')")
    range: str = Field(..., description="Range with direction (e.g., '6E')")
    principal_meridian: str = Field(..., description="Principal meridian name")
    state: str = Field(..., description="State abbreviation")
    label: str = Field(..., description="Human-readable label")
    plss_id: str = Field(..., description="Unique PLSS identifier")


class PLSSResult(BaseModel):
    """Result from PLSS coordinate query."""

    latitude: float
    longitude: float
    township: PLSSLocation | None = None
    section: PLSSLocation | None = None
    error: str | None = None


def _parse_township(attrs: dict) -> PLSSLocation:
    """Parse township attributes from API response."""
    twp_num = attrs.get("TWNSHPNO", "").lstrip("0") or "0"
    twp_dir = attrs.get("TWNSHPDIR", "")
    rng_num = attrs.get("RANGENO", "").lstrip("0") or "0"
    rng_dir = attrs.get("RANGEDIR", "")

    return PLSSLocation(
        section=None,
        township=f"{twp_num}{twp_dir}",
        range=f"{rng_num}{rng_dir}",
        principal_meridian=attrs.get("PRINMER", "Unknown"),
        state=attrs.get("STATEABBR", ""),
        label=attrs.get("TWNSHPLAB", ""),
        plss_id=attrs.get("PLSSID", ""),
    )


def _parse_section(attrs: dict, township: PLSSLocation | None) -> PLSSLocation:
    """Parse section attributes from API response."""
    sec_num = (attrs.get("First Division Number", "") or attrs.get("FRSTDIVNO", "")).lstrip(
        "0"
    ) or "0"
    div_id = attrs.get("First Division Identifier", "") or attrs.get("FRSTDIVID", "")

    if township:
        return PLSSLocation(
            section=sec_num,
            township=township.township,
            range=township.range,
            principal_meridian=township.principal_meridian,
            state=township.state,
            label=f"Section {sec_num}, {township.label}",
            plss_id=div_id,
        )

    twp_id = attrs.get("Township Identifier", "") or attrs.get("PLSSID", "")
    return PLSSLocation(
        section=sec_num,
        township="Unknown",
        range="Unknown",
        principal_meridian="Unknown",
        state=twp_id[:2] if len(twp_id) >= 2 else "",
        label=f"Section {sec_num}",
        plss_id=div_id,
    )


class PLSSMixin(MCPMixin):
    """MCP tools for Public Land Survey System queries."""

    @mcp_tool(
        name="get_plss_location",
        description="Get Section/Township/Range for coordinates (PLSS legal description).",
    )
    async def get_plss_location(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Get PLSS location for coordinates.

        Example: "Section 12, Township 4N, Range 6E, 6th Meridian"

        Coverage: 30 western/midwestern states. Not available for eastern
        seaboard states or Texas (different survey systems).
        """
        result = await self._query_plss(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if result.section:
            return (
                f"Section {result.section.section}, "
                f"Township {result.section.township}, "
                f"Range {result.section.range}, "
                f"{result.section.principal_meridian}\n"
                f"State: {result.section.state}\n"
                f"PLSS ID: {result.section.plss_id}"
            )
        elif result.township:
            return (
                f"Township {result.township.township}, "
                f"Range {result.township.range}, "
                f"{result.township.principal_meridian}\n"
                f"State: {result.township.state}\n"
                f"(Section data not available)"
            )
        return "Unable to determine PLSS location."

    @mcp_tool(
        name="get_plss_details",
        description="Get detailed PLSS data as structured object with all metadata.",
    )
    async def get_plss_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> PLSSResult:
        """Get full PLSS details including township and section objects."""
        return await self._query_plss(latitude, longitude)

    async def _query_plss(self, latitude: float, longitude: float) -> PLSSResult:
        """Query BLM PLSS API for location."""
        try:
            results = await blm_client.identify(
                PLSS_URL, latitude, longitude, f"all:{LAYER_TOWNSHIP},{LAYER_SECTION}"
            )
        except BLMAPIError as e:
            return PLSSResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return PLSSResult(
                latitude=latitude,
                longitude=longitude,
                error="No PLSS data found. Location may be outside surveyed areas.",
            )

        township_data: PLSSLocation | None = None
        section_data: PLSSLocation | None = None

        for result in results:
            layer_id = result.get("layerId")
            attrs = result.get("attributes", {})

            if layer_id == LAYER_TOWNSHIP and township_data is None:
                township_data = _parse_township(attrs)
            elif layer_id == LAYER_SECTION and section_data is None:
                section_data = _parse_section(attrs, township_data)

        return PLSSResult(
            latitude=latitude,
            longitude=longitude,
            township=township_data,
            section=section_data,
        )
