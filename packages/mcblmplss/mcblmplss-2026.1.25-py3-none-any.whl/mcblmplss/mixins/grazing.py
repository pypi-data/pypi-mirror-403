"""
Grazing Allotment mixin for BLM MCP server.

Provides tools for querying BLM grazing allotment information.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Grazing Allotment MapServer
GRAZING_URL = "https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_Grazing_Allotment/MapServer"
LAYER_ALLOTMENT = 12  # Grazing Allotment Polygons


class GrazingAllotment(BaseModel):
    """Grazing allotment information."""

    allotment_number: str = Field(..., description="Allotment number identifier")
    allotment_name: str = Field(..., description="Name of the grazing allotment")
    acres: float | None = Field(None, description="GIS-calculated acreage")
    state: str = Field(..., description="Administrative state code")
    admin_unit: str | None = Field(None, description="Administrative unit code")
    managing_number: str | None = Field(
        None, description="Managing state allotment number"
    )


class GrazingResult(BaseModel):
    """Result from grazing allotment query."""

    latitude: float
    longitude: float
    allotment: GrazingAllotment | None = None
    error: str | None = None


def _parse_allotment(attrs: dict) -> GrazingAllotment:
    """Parse grazing allotment attributes from API response."""
    acres_val = attrs.get("GIS Acres")
    try:
        acres = float(acres_val) if acres_val is not None else None
    except (ValueError, TypeError):
        acres = None

    return GrazingAllotment(
        allotment_number=attrs.get("Allotment Number", ""),
        allotment_name=attrs.get("Allotment Name", "Unnamed"),
        acres=acres,
        state=attrs.get("Administrative State Code", ""),
        admin_unit=attrs.get("Adminstrative Unit Code"),  # Note: BLM's typo
        managing_number=attrs.get("Managing State Allotment Number"),
    )


class GrazingMixin(MCPMixin):
    """MCP tools for grazing allotment queries."""

    @mcp_tool(
        name="get_grazing_allotment",
        description="Find BLM grazing allotment information at coordinates.",
    )
    async def get_grazing_allotment(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Get grazing allotment information for a location.

        Grazing allotments are areas of public land designated for
        livestock grazing under BLM permits. Returns the allotment
        name, number, acreage, and administrative details.
        """
        result = await self._query_grazing(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if result.allotment:
            allot = result.allotment
            lines = [f"{allot.allotment_name} (#{allot.allotment_number})"]

            if allot.acres:
                lines.append(f"Acres: {allot.acres:,.2f}")

            lines.append(f"State: {allot.state}")

            if allot.admin_unit:
                lines.append(f"Admin Unit: {allot.admin_unit}")

            if allot.managing_number:
                lines.append(f"Managing Number: {allot.managing_number}")

            return "\n".join(lines)

        return "No grazing allotment found at this location."

    @mcp_tool(
        name="get_grazing_allotment_details",
        description="Get detailed grazing allotment data as structured object.",
    )
    async def get_grazing_allotment_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> GrazingResult:
        """Get full grazing allotment details including administrative codes."""
        return await self._query_grazing(latitude, longitude)

    async def _query_grazing(
        self, latitude: float, longitude: float
    ) -> GrazingResult:
        """Query BLM Grazing Allotment API for location."""
        try:
            results = await blm_client.identify(
                GRAZING_URL, latitude, longitude, f"all:{LAYER_ALLOTMENT}"
            )
        except BLMAPIError as e:
            return GrazingResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return GrazingResult(
                latitude=latitude,
                longitude=longitude,
                error="No grazing allotment data found for this location.",
            )

        # Use first result from allotment layer
        for result in results:
            if result.get("layerId") == LAYER_ALLOTMENT:
                attrs = result.get("attributes", {})
                return GrazingResult(
                    latitude=latitude,
                    longitude=longitude,
                    allotment=_parse_allotment(attrs),
                )

        return GrazingResult(
            latitude=latitude,
            longitude=longitude,
            error="No grazing allotment data in response.",
        )
