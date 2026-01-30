"""
ACEC (Areas of Critical Environmental Concern) mixin for BLM MCP server.

Provides tools for querying BLM-designated areas requiring special management
to protect important natural, cultural, or scenic values.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# ACEC MapServer
ACEC_URL = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_ACEC/MapServer"
LAYER_ACEC = 0  # ACEC Designated Polygons

# Relevance field mappings
RELEVANCE_FIELDS = {
    "ACEC Cultural Designation Relevance": "Cultural",
    "ACEC Wildlife Resource Designation Relevance": "Wildlife",
    "ACEC Scenic Designation Relevance": "Scenic",
    "ACEC Natural System Designation Relevance": "Natural System",
}

RELEVANCE_POSITIVE = "Yes - Affirmative or Present"


class ACEC(BaseModel):
    """Individual ACEC record."""

    name: str = Field(..., description="ACEC name")
    land_use_plan: str | None = Field(None, description="Land Use Plan name")
    designation_date: str | None = Field(None, description="Record of Decision date")
    acres: float | None = Field(None, description="GIS-calculated acreage")
    state: str = Field(..., description="Administrative state abbreviation")
    relevance_values: list[str] = Field(
        default_factory=list,
        description="Protected values (Cultural, Wildlife, Scenic, Natural System)",
    )


class ACECResult(BaseModel):
    """Result from ACEC query."""

    latitude: float
    longitude: float
    acecs: list[ACEC] = Field(default_factory=list)
    error: str | None = None


def _parse_acec(attrs: dict) -> ACEC:
    """Parse ACEC attributes from API response."""
    # Extract relevance values where designation is affirmative
    relevance_values = []
    for field_name, value_name in RELEVANCE_FIELDS.items():
        if attrs.get(field_name) == RELEVANCE_POSITIVE:
            relevance_values.append(value_name)

    # Parse acres
    acres_val = attrs.get("GIS_ACRES")
    try:
        acres = float(acres_val) if acres_val is not None else None
    except (ValueError, TypeError):
        acres = None

    return ACEC(
        name=attrs.get("ACEC_NAME", "Unnamed ACEC"),
        land_use_plan=attrs.get("LUP_NAME") if attrs.get("LUP_NAME") else None,
        designation_date=attrs.get("ROD_DATE") if attrs.get("ROD_DATE") else None,
        acres=acres,
        state=attrs.get("ADMIN_ST", ""),
        relevance_values=relevance_values,
    )


class ACECMixin(MCPMixin):
    """MCP tools for ACEC (Areas of Critical Environmental Concern) queries."""

    @mcp_tool(
        name="get_acec",
        description="Find Areas of Critical Environmental Concern at coordinates.",
    )
    async def get_acec(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Get information about Areas of Critical Environmental Concern (ACEC).

        ACECs are BLM-designated areas requiring special management to protect
        important values including:
        - Cultural resources (archaeological sites, historic areas)
        - Wildlife resources (habitat, migration corridors)
        - Scenic values (viewsheds, landscapes)
        - Natural systems (unique geology, rare plants)

        Returns ACEC name, protected values, acreage, and land use plan info.
        """
        result = await self._query_acec(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if not result.acecs:
            return "No Areas of Critical Environmental Concern found at this location."

        lines = [f"Found {len(result.acecs)} ACEC(s):"]
        for acec in result.acecs:
            lines.append(f"\n{acec.name}")
            lines.append(f"  State: {acec.state}")

            if acec.relevance_values:
                lines.append(f"  Protected Values: {', '.join(acec.relevance_values)}")

            if acec.acres:
                lines.append(f"  Acres: {acec.acres:,.1f}")

            if acec.land_use_plan:
                lines.append(f"  Land Use Plan: {acec.land_use_plan}")

            if acec.designation_date:
                lines.append(f"  Designated: {acec.designation_date}")

        return "\n".join(lines)

    @mcp_tool(
        name="get_acec_details",
        description="Get detailed ACEC data as structured objects.",
    )
    async def get_acec_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> ACECResult:
        """Get full ACEC details including all designation relevance fields."""
        return await self._query_acec(latitude, longitude)

    async def _query_acec(self, latitude: float, longitude: float) -> ACECResult:
        """Query BLM ACEC API for location."""
        try:
            results = await blm_client.identify(
                ACEC_URL, latitude, longitude, f"all:{LAYER_ACEC}"
            )
        except BLMAPIError as e:
            return ACECResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return ACECResult(
                latitude=latitude,
                longitude=longitude,
                acecs=[],
            )

        acecs = []
        seen_names = set()

        for result in results:
            if result.get("layerId") == LAYER_ACEC:
                attrs = result.get("attributes", {})
                name = attrs.get("ACEC_NAME", "")

                # Dedupe by ACEC name
                if name and name not in seen_names:
                    seen_names.add(name)
                    acecs.append(_parse_acec(attrs))

        return ACECResult(
            latitude=latitude,
            longitude=longitude,
            acecs=acecs,
        )
