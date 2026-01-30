"""
Wild and Scenic Rivers mixin for BLM MCP server.

Provides tools for querying designated Wild and Scenic Rivers from BLM's NLCS database.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Wild and Scenic Rivers MapServer
WSR_URL = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WSR/MapServer"
LAYER_WSR = 0  # Wild and Scenic Rivers layer


class WildRiver(BaseModel):
    """Individual wild and scenic river segment."""

    nlcs_id: str = Field(..., description="NLCS unique identifier")
    name: str = Field(..., description="River/segment name")
    category: str = Field(..., description="Full designation category")
    classification: str = Field(
        ..., description="River classification (Wild, Scenic, or Recreational)"
    )
    state: str = Field(..., description="Administrative state code")
    segment_number: str | None = Field(None, description="WSR segment number")


class WildRiverResult(BaseModel):
    """Result from wild and scenic rivers query."""

    latitude: float
    longitude: float
    rivers: list[WildRiver] = Field(default_factory=list)
    error: str | None = None


def _parse_river(attrs: dict) -> WildRiver:
    """Parse wild river attributes from API response."""
    category = attrs.get("Category", "")

    # Extract classification from category string
    # e.g., "Designated - Recreational" -> "Recreational"
    classification = "Unknown"
    if category:
        category_lower = category.lower()
        if "wild" in category_lower:
            classification = "Wild"
        elif "scenic" in category_lower:
            classification = "Scenic"
        elif "recreational" in category_lower:
            classification = "Recreational"

    segment_num = attrs.get("WSR Segment Number")
    if segment_num and segment_num == "Null":
        segment_num = None

    return WildRiver(
        nlcs_id=attrs.get("NLCS_ID", ""),
        name=attrs.get("NLCS Name", "Unknown"),
        category=category,
        classification=classification,
        state=attrs.get("Administrative State Code", ""),
        segment_number=segment_num,
    )


class WildRiversMixin(MCPMixin):
    """MCP tools for Wild and Scenic Rivers queries."""

    @mcp_tool(
        name="get_wild_river",
        description="Find Wild and Scenic Rivers near coordinates.",
    )
    async def get_wild_river(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Find Wild and Scenic River segments near a location.

        The National Wild and Scenic Rivers System preserves rivers with
        outstanding natural, cultural, or recreational values in a free-flowing
        condition. Rivers are classified as:

        - Wild: Primitive, undeveloped watersheds, no road access
        - Scenic: Largely undeveloped but accessible by road
        - Recreational: Readily accessible with some development

        Uses tolerance=50 for linear river features.
        """
        result = await self._query_rivers(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if not result.rivers:
            return "No Wild and Scenic Rivers found near this location."

        lines = [f"Found {len(result.rivers)} Wild and Scenic River segment(s):"]
        for river in result.rivers:
            lines.append(f"\n{river.name}")
            lines.append(f"  Classification: {river.classification}")
            lines.append(f"  Category: {river.category}")
            lines.append(f"  State: {river.state}")
            if river.segment_number:
                lines.append(f"  Segment: {river.segment_number}")
            lines.append(f"  NLCS ID: {river.nlcs_id}")

        return "\n".join(lines)

    @mcp_tool(
        name="get_wild_river_details",
        description="Get detailed Wild and Scenic Rivers data as structured objects.",
    )
    async def get_wild_river_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> WildRiverResult:
        """Get full Wild and Scenic Rivers data including NLCS identifiers."""
        return await self._query_rivers(latitude, longitude)

    async def _query_rivers(
        self,
        latitude: float,
        longitude: float,
    ) -> WildRiverResult:
        """Query BLM Wild and Scenic Rivers API."""
        try:
            results = await blm_client.identify(
                WSR_URL, latitude, longitude, f"all:{LAYER_WSR}", tolerance=50
            )
        except BLMAPIError as e:
            return WildRiverResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return WildRiverResult(
                latitude=latitude,
                longitude=longitude,
                rivers=[],
            )

        rivers = []
        seen_ids = set()

        for result in results:
            if result.get("layerId") == LAYER_WSR:
                attrs = result.get("attributes", {})

                # Dedupe by NLCS ID
                nlcs_id = attrs.get("NLCS_ID", "")
                if nlcs_id and nlcs_id not in seen_ids:
                    seen_ids.add(nlcs_id)
                    rivers.append(_parse_river(attrs))

        return WildRiverResult(
            latitude=latitude,
            longitude=longitude,
            rivers=rivers,
        )
