"""
Wild Horse and Burro mixin for BLM MCP server.

Provides tools for querying Herd Management Areas (HMA) and Herd Areas (HA)
from BLM's Wild Horse and Burro program.
"""

from datetime import datetime

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Wild Horse and Burro MapServer
WHB_URL = "https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB_Geocortex/MapServer"
LAYER_HMA = 8  # Herd Management Area
LAYER_HA = 9  # Herd Area


class HerdManagementArea(BaseModel):
    """Herd Management Area information."""

    name: str = Field(..., description="Herd Management Area name")
    hma_id: str | None = Field(None, description="HMA identifier")
    herd_type: str | None = Field(None, description="Type of animals (Horse, Burro, or both)")
    acres: float | None = Field(None, description="Total acres in HMA")
    state: str | None = Field(None, description="Administrative state code")
    horse_aml_low: int | None = Field(None, description="Horse AML (low)")
    horse_aml_high: int | None = Field(None, description="Horse AML (high)")
    horse_population: int | None = Field(None, description="Estimated horse population")
    burro_aml_low: int | None = Field(None, description="Burro AML (low)")
    burro_aml_high: int | None = Field(None, description="Burro AML (high)")
    burro_population: int | None = Field(None, description="Estimated burro population")
    inventory_date: str | None = Field(None, description="Population inventory date")
    website: str | None = Field(None, description="HMA website link")


class WildHorseResult(BaseModel):
    """Result from wild horse/burro herd query."""

    latitude: float
    longitude: float
    hma: HerdManagementArea | None = None
    error: str | None = None


def _parse_nullable(value: str | int | float | None) -> str | None:
    """Convert 'Null' strings and empty values to None."""
    if value is None or value == "Null" or value == "":
        return None
    return str(value)


def _parse_int(value: str | int | float | None) -> int | None:
    """Parse integer from API, handling 'Null' strings."""
    if value is None or value == "Null" or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _parse_float(value: str | int | float | None) -> float | None:
    """Parse float from API, handling 'Null' strings."""
    if value is None or value == "Null" or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value: str | int | None) -> str | None:
    """Parse date from API (may be epoch ms or string)."""
    if value is None or value == "Null" or value == "":
        return None
    try:
        # ArcGIS often returns epoch milliseconds
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            epoch_ms = int(value)
            return datetime.fromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d")
        return str(value)
    except (ValueError, TypeError, OSError):
        return str(value) if value else None


def _parse_hma(attrs: dict) -> HerdManagementArea:
    """Parse HMA attributes from API response."""
    # Note: BLM has a typo in their field name - "Mangement" instead of "Management"
    name = (
        attrs.get("Herd Mangement Area Name")
        or attrs.get("Herd Management Area Name", "Unknown")
    )

    return HerdManagementArea(
        name=name,
        hma_id=_parse_nullable(attrs.get("Herd Management Area Identifier")),
        herd_type=_parse_nullable(attrs.get("Herd Type")),
        acres=_parse_float(attrs.get("TOTAL_ACRES") or attrs.get("BLM Acres")),
        state=_parse_nullable(attrs.get("Administrative State Code")),
        horse_aml_low=_parse_int(attrs.get("HORSE_AML_LOW")),
        horse_aml_high=_parse_int(attrs.get("HORSE_AML_HIGH")),
        horse_population=_parse_int(attrs.get("EST_HORSE_POP")),
        burro_aml_low=_parse_int(attrs.get("BURRO_AML_LOW")),
        burro_aml_high=_parse_int(attrs.get("BURRO_AML_HIGH")),
        burro_population=_parse_int(attrs.get("EST_BURRO_POP")),
        inventory_date=_parse_date(attrs.get("POP_INVENTORY_DT")),
        website=_parse_nullable(attrs.get("HMA Website Link")),
    )


class WildHorseMixin(MCPMixin):
    """MCP tools for Wild Horse and Burro herd queries."""

    @mcp_tool(
        name="get_wild_horse_herd",
        description="Check if a location is within a Wild Horse or Burro Herd Management Area.",
    )
    async def get_wild_horse_herd(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Get wild horse and burro herd management information for a location.

        Returns details about the Herd Management Area (HMA) including:
        - HMA name and herd type (horses, burros, or both)
        - Appropriate Management Level (AML) population targets
        - Current estimated populations
        - Total acreage

        HMAs are areas managed by BLM for wild horse and burro populations
        under the Wild Free-Roaming Horses and Burros Act of 1971.
        """
        result = await self._query_hma(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if result.hma:
            hma = result.hma
            lines = [f"Herd Management Area: {hma.name}"]

            if hma.herd_type:
                lines.append(f"Herd Type: {hma.herd_type}")

            if hma.state:
                lines.append(f"State: {hma.state}")

            if hma.acres:
                lines.append(f"Total Acres: {hma.acres:,.0f}")

            # Horse population info
            if hma.horse_aml_low is not None or hma.horse_aml_high is not None:
                aml_range = f"{hma.horse_aml_low or 0}-{hma.horse_aml_high or '?'}"
                lines.append(f"Horse AML Range: {aml_range}")
            if hma.horse_population is not None:
                lines.append(f"Estimated Horse Population: {hma.horse_population:,}")

            # Burro population info
            if hma.burro_aml_low is not None or hma.burro_aml_high is not None:
                aml_range = f"{hma.burro_aml_low or 0}-{hma.burro_aml_high or '?'}"
                lines.append(f"Burro AML Range: {aml_range}")
            if hma.burro_population is not None:
                lines.append(f"Estimated Burro Population: {hma.burro_population:,}")

            if hma.inventory_date:
                lines.append(f"Population Inventory Date: {hma.inventory_date}")

            if hma.website:
                lines.append(f"More Info: {hma.website}")

            return "\n".join(lines)

        return "This location is not within a Wild Horse or Burro Herd Management Area."

    @mcp_tool(
        name="get_wild_horse_herd_details",
        description="Get detailed Wild Horse/Burro HMA data as structured object.",
    )
    async def get_wild_horse_herd_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> WildHorseResult:
        """Get full HMA details including all population metrics."""
        return await self._query_hma(latitude, longitude)

    async def _query_hma(self, latitude: float, longitude: float) -> WildHorseResult:
        """Query BLM Wild Horse/Burro API for HMA at location."""
        try:
            # Query HMA layer (layer 8)
            results = await blm_client.identify(WHB_URL, latitude, longitude, f"all:{LAYER_HMA}")
        except BLMAPIError as e:
            return WildHorseResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return WildHorseResult(
                latitude=latitude,
                longitude=longitude,
                hma=None,
            )

        # Use first result from HMA layer
        for result in results:
            if result.get("layerId") == LAYER_HMA:
                attrs = result.get("attributes", {})
                return WildHorseResult(
                    latitude=latitude,
                    longitude=longitude,
                    hma=_parse_hma(attrs),
                )

        return WildHorseResult(
            latitude=latitude,
            longitude=longitude,
            hma=None,
        )
