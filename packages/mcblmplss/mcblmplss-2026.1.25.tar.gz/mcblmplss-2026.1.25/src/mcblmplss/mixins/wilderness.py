"""
Wilderness Area mixin for BLM MCP server.

Provides tools for querying Wilderness Areas and Wilderness Study Areas (WSAs)
from BLM's National Landscape Conservation System (NLCS).
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Wilderness Areas and WSAs MapServer
WILDERNESS_URL = (
    "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer"
)
LAYER_WILDERNESS = 0  # Designated Wilderness Areas
LAYER_WSA = 1  # Wilderness Study Areas


class WildernessArea(BaseModel):
    """Individual wilderness or wilderness study area record."""

    nlcs_id: str = Field(..., description="NLCS identifier")
    name: str = Field(..., description="Wilderness or WSA name")
    state: str = Field(..., description="Administrative state code")
    designation_date: str | None = Field(None, description="Date of designation")
    casefile: str | None = Field(None, description="Casefile number")
    is_designated: bool = Field(
        ..., description="True if designated wilderness, False if WSA"
    )


class WildernessResult(BaseModel):
    """Result from wilderness query."""

    latitude: float
    longitude: float
    areas: list[WildernessArea] = Field(default_factory=list)
    error: str | None = None


def _parse_wilderness(attrs: dict, layer_id: int) -> WildernessArea:
    """Parse wilderness attributes from API response."""
    is_designated = layer_id == LAYER_WILDERNESS

    # Handle null/empty values
    desig_date = attrs.get("DESIG_DATE")
    if desig_date and desig_date != "Null":
        desig_date = str(desig_date)
    else:
        desig_date = None

    casefile = attrs.get("Casefile Number")
    if casefile and casefile != "Null":
        casefile = str(casefile)
    else:
        casefile = None

    return WildernessArea(
        nlcs_id=attrs.get("NLCS_ID", ""),
        name=attrs.get("NLCS Name", "Unnamed"),
        state=attrs.get("Administrative State Code", ""),
        designation_date=desig_date,
        casefile=casefile,
        is_designated=is_designated,
    )


class WildernessMixin(MCPMixin):
    """MCP tools for wilderness area queries."""

    @mcp_tool(
        name="get_wilderness_area",
        description="Check if a location is in a Wilderness Area or Wilderness Study Area (WSA).",
    )
    async def get_wilderness_area(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Determine if coordinates fall within a Wilderness Area or WSA.

        Wilderness Areas are congressionally designated lands with the highest
        level of protection. WSAs are areas under study for potential designation.

        Returns wilderness/WSA name and designation status.
        """
        result = await self._query_wilderness(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if not result.areas:
            return "This location is not within a Wilderness Area or Wilderness Study Area."

        lines = []
        for area in result.areas:
            status = "Designated Wilderness" if area.is_designated else "WSA"
            lines.append(f"{area.name}")
            lines.append(f"  Status: {status}")
            lines.append(f"  State: {area.state}")
            lines.append(f"  NLCS ID: {area.nlcs_id}")
            if area.designation_date:
                lines.append(f"  Designated: {area.designation_date}")
            if area.casefile:
                lines.append(f"  Casefile: {area.casefile}")
            lines.append("")

        return "\n".join(lines).strip()

    @mcp_tool(
        name="get_wilderness_area_details",
        description="Get detailed wilderness/WSA data as structured objects.",
    )
    async def get_wilderness_area_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> WildernessResult:
        """Get full wilderness area data including NLCS IDs and designation status."""
        return await self._query_wilderness(latitude, longitude)

    async def _query_wilderness(
        self, latitude: float, longitude: float
    ) -> WildernessResult:
        """Query BLM Wilderness/WSA API for location."""
        layers = f"all:{LAYER_WILDERNESS},{LAYER_WSA}"

        try:
            results = await blm_client.identify(
                WILDERNESS_URL, latitude, longitude, layers
            )
        except BLMAPIError as e:
            return WildernessResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return WildernessResult(
                latitude=latitude,
                longitude=longitude,
                areas=[],
            )

        areas = []
        seen_ids = set()

        for result in results:
            layer_id = result.get("layerId")
            attrs = result.get("attributes", {})

            # Dedupe by NLCS ID
            nlcs_id = attrs.get("NLCS_ID", "")
            if nlcs_id and nlcs_id not in seen_ids:
                seen_ids.add(nlcs_id)
                areas.append(_parse_wilderness(attrs, layer_id))

        return WildernessResult(
            latitude=latitude,
            longitude=longitude,
            areas=areas,
        )
