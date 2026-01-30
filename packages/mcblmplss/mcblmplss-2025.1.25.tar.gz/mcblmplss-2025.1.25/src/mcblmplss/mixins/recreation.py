"""
Recreation Sites and Facilities mixin for BLM MCP server.

Provides tools for querying BLM recreation sites including campgrounds,
trailheads, boat ramps, and other public facilities.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Recreation Sites and Facilities MapServer
RECREATION_URL = "https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation_Sites_Facilities/MapServer"
LAYER_FACILITIES = 0
LAYER_SITES = 1


class RecreationSite(BaseModel):
    """Recreation site or facility record."""

    facility_id: str = Field(..., description="BLM facility identifier")
    name: str = Field(..., description="Facility or site name")
    description: str | None = Field(None, description="Facility description")
    site_type: str | None = Field(None, description="Type of recreation facility")
    directions: str | None = Field(None, description="Directions to the facility")
    phone: str | None = Field(None, description="Contact phone number")
    email: str | None = Field(None, description="Contact email address")
    url: str | None = Field(None, description="Website URL for more information")
    state: str | None = Field(None, description="State abbreviation")
    reservable: bool = Field(False, description="Whether reservations are accepted")


class RecreationResult(BaseModel):
    """Result from recreation sites query."""

    latitude: float
    longitude: float
    sites: list[RecreationSite] = Field(default_factory=list)
    total_found: int = 0
    error: str | None = None


def _parse_site(attrs: dict) -> RecreationSite:
    """Parse recreation site attributes from API response."""

    def clean_string(value: str | None) -> str | None:
        """Convert empty strings and null markers to None."""
        if value is None or value == "" or value == "Null":
            return None
        return value

    # Convert Reservable: 0 = False, -1 = True (typical ArcGIS boolean)
    reservable_val = attrs.get("Reservable", 0)
    reservable = reservable_val == -1 or reservable_val == 1

    return RecreationSite(
        facility_id=attrs.get("FacilityID", ""),
        name=attrs.get("FacilityName", "Unnamed"),
        description=clean_string(attrs.get("FacilityDescription")),
        site_type=clean_string(attrs.get("FacilityTypeDescription")),
        directions=clean_string(attrs.get("FacilityDirections")),
        phone=clean_string(attrs.get("FacilityPhone")),
        email=clean_string(attrs.get("FacilityEmail")),
        url=clean_string(attrs.get("URL")),
        state=clean_string(attrs.get("State")),
        reservable=reservable,
    )


class RecreationMixin(MCPMixin):
    """MCP tools for recreation sites and facilities queries."""

    @mcp_tool(
        name="get_recreation_sites",
        description="Find BLM recreation sites near coordinates (campgrounds, trailheads, etc.).",
    )
    async def get_recreation_sites(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Find recreation sites and facilities near a location.

        Recreation sites include:
        - Campgrounds and camping areas
        - Trailheads and hiking areas
        - Boat ramps and water access
        - Picnic areas
        - Visitor centers

        Returns site names, types, contact info, and reservation status.
        """
        result = await self._query_recreation(latitude, longitude, tolerance=100)

        if result.error:
            return f"Error: {result.error}"

        if not result.sites:
            return "No recreation sites found near this location."

        lines = [f"Found {result.total_found} recreation site(s):"]
        for site in result.sites[:10]:  # Limit display to 10
            lines.append(f"\n{site.name}")
            if site.site_type:
                lines.append(f"  Type: {site.site_type}")
            if site.state:
                lines.append(f"  State: {site.state}")
            if site.reservable:
                lines.append("  Reservations: Accepted")
            if site.phone:
                lines.append(f"  Phone: {site.phone}")
            if site.url:
                lines.append(f"  Website: {site.url}")

        if result.total_found > 10:
            lines.append(f"\n... and {result.total_found - 10} more sites")

        return "\n".join(lines)

    @mcp_tool(
        name="get_recreation_sites_details",
        description="Get detailed recreation site data as structured objects.",
    )
    async def get_recreation_sites_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
        tolerance: int = Field(
            default=100, description="Search radius in pixels (larger = wider search)"
        ),
    ) -> RecreationResult:
        """Get full recreation site data including descriptions and contact info."""
        return await self._query_recreation(latitude, longitude, tolerance)

    async def _query_recreation(
        self,
        latitude: float,
        longitude: float,
        tolerance: int = 100,
    ) -> RecreationResult:
        """Query BLM Recreation Sites API."""
        layers = f"all:{LAYER_FACILITIES},{LAYER_SITES}"

        try:
            results = await blm_client.identify(
                RECREATION_URL, latitude, longitude, layers, tolerance=tolerance
            )
        except BLMAPIError as e:
            return RecreationResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return RecreationResult(
                latitude=latitude,
                longitude=longitude,
                sites=[],
                total_found=0,
            )

        sites = []
        seen_ids = set()

        for result in results:
            attrs = result.get("attributes", {})

            # Dedupe by facility ID
            facility_id = attrs.get("FacilityID", "")
            if facility_id and facility_id not in seen_ids:
                seen_ids.add(facility_id)
                sites.append(_parse_site(attrs))

        return RecreationResult(
            latitude=latitude,
            longitude=longitude,
            sites=sites,
            total_found=len(sites),
        )
