"""
Surface Management Agency mixin for BLM MCP server.

Provides tools for determining who manages federal lands (BLM, USFS, NPS, etc.).
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Surface Management Agency MapServer
SMA_URL = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer"
LAYER_SMA = 1  # Main SMA layer with all agencies

# Agency code mappings
AGENCY_NAMES = {
    "BLM": "Bureau of Land Management",
    "NPS": "National Park Service",
    "USFS": "U.S. Forest Service",
    "FWS": "U.S. Fish and Wildlife Service",
    "USBR": "Bureau of Reclamation",
    "BIA": "Bureau of Indian Affairs",
    "DOD": "Department of Defense",
    "DOE": "Department of Energy",
    "TVA": "Tennessee Valley Authority",
    "PVT": "Private",
    "ST": "State",
    "LG": "Local Government",
    "UND": "Undetermined",
}

DEPT_NAMES = {
    "DOI": "Department of the Interior",
    "USDA": "Department of Agriculture",
    "DOD": "Department of Defense",
    "DOE": "Department of Energy",
    "PVT": "Private",
    "ST": "State",
    "LG": "Local Government",
}


class LandManager(BaseModel):
    """Surface management agency information."""

    agency_code: str = Field(..., description="Agency code (BLM, USFS, NPS, etc.)")
    agency_name: str = Field(..., description="Full agency name")
    department_code: str | None = Field(None, description="Department code (DOI, USDA, etc.)")
    department_name: str | None = Field(None, description="Full department name")
    admin_unit_name: str | None = Field(None, description="Administrative unit name")
    admin_unit_type: str | None = Field(None, description="Administrative unit type")
    state: str = Field(..., description="State abbreviation")
    is_federal: bool = Field(..., description="Whether this is federal land")
    allows_public_access: bool = Field(
        ..., description="Whether general public access is typically allowed"
    )


class SurfaceManagementResult(BaseModel):
    """Result from surface management query."""

    latitude: float
    longitude: float
    manager: LandManager | None = None
    error: str | None = None


def _parse_sma(attrs: dict) -> LandManager:
    """Parse surface management attributes."""
    agency_code = attrs.get("ADMIN_AGENCY_CODE", "UND")
    dept_code = attrs.get("ADMIN_DEPT_CODE", "")

    # Federal departments (excluding private/state/local)
    federal_depts = {"DOI", "USDA", "DOD", "DOE"}
    is_federal = dept_code in federal_depts

    # Agencies that generally allow public recreation access
    # Note: BIA (tribal) and DOD (military) are federal but restricted
    public_access_agencies = {"BLM", "USFS", "NPS", "FWS", "USBR"}
    allows_public_access = agency_code in public_access_agencies

    return LandManager(
        agency_code=agency_code,
        agency_name=AGENCY_NAMES.get(agency_code, agency_code),
        department_code=dept_code if dept_code and dept_code != "Null" else None,
        department_name=DEPT_NAMES.get(dept_code) if dept_code else None,
        admin_unit_name=(
            attrs.get("ADMIN_UNIT_NAME") if attrs.get("ADMIN_UNIT_NAME") != "Null" else None
        ),
        admin_unit_type=(
            attrs.get("ADMIN_UNIT_TYPE") if attrs.get("ADMIN_UNIT_TYPE") != "Null" else None
        ),
        state=attrs.get("ADMIN_ST", ""),
        is_federal=is_federal,
        allows_public_access=allows_public_access,
    )


class SurfaceManagementMixin(MCPMixin):
    """MCP tools for Surface Management Agency queries."""

    @mcp_tool(
        name="get_land_manager",
        description="Determine who manages the land (BLM, Forest Service, NPS, Private, etc.)",
    )
    async def get_land_manager(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> str:
        """
        Get the surface management agency for a location.

        Returns the federal agency, state agency, or private designation
        for who manages the surface rights at the given coordinates.

        Examples:
        - "Bureau of Land Management (BLM) - Department of the Interior"
        - "U.S. Forest Service (USFS) - Department of Agriculture"
        - "Private land"
        """
        result = await self._query_sma(latitude, longitude)

        if result.error:
            return f"Error: {result.error}"

        if result.manager:
            mgr = result.manager
            lines = [f"{mgr.agency_name} ({mgr.agency_code})"]

            if mgr.department_name:
                lines[0] += f" - {mgr.department_name}"

            if mgr.admin_unit_name:
                lines.append(f"Unit: {mgr.admin_unit_name}")

            lines.append(f"State: {mgr.state}")

            status = []
            if mgr.is_federal:
                status.append("Federal")
            if mgr.allows_public_access:
                status.append("Public access")
            if status:
                lines.append(f"Status: {', '.join(status)}")

            return "\n".join(lines)

        return "Unable to determine land manager."

    @mcp_tool(
        name="get_land_manager_details",
        description="Get detailed surface management data as structured object.",
    )
    async def get_land_manager_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
    ) -> SurfaceManagementResult:
        """Get full surface management details including agency codes and flags."""
        return await self._query_sma(latitude, longitude)

    async def _query_sma(self, latitude: float, longitude: float) -> SurfaceManagementResult:
        """Query BLM SMA API for location."""
        try:
            results = await blm_client.identify(SMA_URL, latitude, longitude, f"all:{LAYER_SMA}")
        except BLMAPIError as e:
            return SurfaceManagementResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return SurfaceManagementResult(
                latitude=latitude,
                longitude=longitude,
                error="No surface management data found for this location.",
            )

        # Use first result from main SMA layer
        for result in results:
            if result.get("layerId") == LAYER_SMA:
                attrs = result.get("attributes", {})
                return SurfaceManagementResult(
                    latitude=latitude,
                    longitude=longitude,
                    manager=_parse_sma(attrs),
                )

        return SurfaceManagementResult(
            latitude=latitude,
            longitude=longitude,
            error="No surface management data in response.",
        )
