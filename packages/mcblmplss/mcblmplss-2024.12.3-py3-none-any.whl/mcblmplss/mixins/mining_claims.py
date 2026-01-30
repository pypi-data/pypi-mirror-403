"""
Mining Claims mixin for BLM MCP server.

Provides tools for querying active and closed mining claims from BLM's MLRS database.
"""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pydantic import BaseModel, Field

from mcblmplss.client import BLMAPIError, blm_client

# Mining Claims MapServer (separate server from main BLM arcgis)
MINING_URL = "https://gis.blm.gov/nlsdb/rest/services/Mining_Claims/MiningClaims/MapServer"
LAYER_ACTIVE = 1
LAYER_CLOSED = 2

# Claim type codes
CLAIM_TYPES = {
    "384101": "Lode Claim",
    "384102": "Placer Claim",
    "384103": "Mill Site",
    "384104": "Tunnel Site",
}


class MiningClaim(BaseModel):
    """Individual mining claim record."""

    claim_name: str = Field(..., description="Geographic/claim name")
    serial_number: str = Field(..., description="BLM case serial number")
    claim_type: str = Field(..., description="Type of claim (Lode, Placer, Mill Site, etc.)")
    status: str = Field(..., description="Case disposition (Active, Closed)")
    acres: float | None = Field(None, description="Claim acreage")
    legal_description: str | None = Field(None, description="PLSS legal description")


class MiningClaimsResult(BaseModel):
    """Result from mining claims query."""

    latitude: float
    longitude: float
    claims: list[MiningClaim] = Field(default_factory=list)
    total_found: int = 0
    error: str | None = None


def _parse_claim(attrs: dict, status: str) -> MiningClaim:
    """Parse mining claim attributes from API response."""
    # API returns human-readable field names
    claim_type_code = attrs.get("BLM Product Code", "")
    claim_type = attrs.get("BLM Product", "") or CLAIM_TYPES.get(claim_type_code, "Unknown")

    acres_str = attrs.get("Case Acres", "")
    try:
        acres = float(acres_str) if acres_str else None
    except (ValueError, TypeError):
        acres = None

    return MiningClaim(
        claim_name=attrs.get("Geographic Name", "Unnamed"),
        serial_number=attrs.get("Case Serial Number", ""),
        claim_type=claim_type,
        status=status,
        acres=acres,
        legal_description=attrs.get("Case Metadata"),
    )


class MiningClaimsMixin(MCPMixin):
    """MCP tools for mining claims queries."""

    @mcp_tool(
        name="get_mining_claims",
        description="Find active mining claims at or near coordinates.",
    )
    async def get_mining_claims(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
        include_closed: bool = Field(
            default=False, description="Include closed/void claims in results"
        ),
        tolerance: int = Field(
            default=10, description="Search radius in pixels (larger = wider search)"
        ),
    ) -> str:
        """
        Find mining claims at a location.

        Mining claims include:
        - Lode Claims: Hard rock mineral deposits (veins, ledges)
        - Placer Claims: Loose mineral deposits (gold in streams)
        - Mill Sites: Processing facilities
        - Tunnel Sites: Underground access

        Returns claim names, BLM serial numbers, and acreage.
        """
        result = await self._query_claims(latitude, longitude, include_closed, tolerance)

        if result.error:
            return f"Error: {result.error}"

        if not result.claims:
            return "No mining claims found at this location."

        lines = [f"Found {result.total_found} mining claim(s):"]
        for claim in result.claims[:20]:  # Limit display to 20
            lines.append(f"\n{claim.claim_name}")
            lines.append(f"  Serial: {claim.serial_number}")
            lines.append(f"  Type: {claim.claim_type}")
            lines.append(f"  Status: {claim.status}")
            if claim.acres:
                lines.append(f"  Acres: {claim.acres:.2f}")

        if result.total_found > 20:
            lines.append(f"\n... and {result.total_found - 20} more claims")

        return "\n".join(lines)

    @mcp_tool(
        name="get_mining_claims_details",
        description="Get detailed mining claims data as structured objects.",
    )
    async def get_mining_claims_details(
        self,
        latitude: float = Field(description="Latitude in decimal degrees (WGS84)"),
        longitude: float = Field(description="Longitude in decimal degrees (WGS84)"),
        include_closed: bool = Field(default=False, description="Include closed/void claims"),
        tolerance: int = Field(default=10, description="Search radius in pixels"),
    ) -> MiningClaimsResult:
        """Get full mining claims data including legal descriptions."""
        return await self._query_claims(latitude, longitude, include_closed, tolerance)

    async def _query_claims(
        self,
        latitude: float,
        longitude: float,
        include_closed: bool,
        tolerance: int,
    ) -> MiningClaimsResult:
        """Query BLM Mining Claims API."""
        layers = f"all:{LAYER_ACTIVE}"
        if include_closed:
            layers = f"all:{LAYER_ACTIVE},{LAYER_CLOSED}"

        try:
            results = await blm_client.identify(
                MINING_URL, latitude, longitude, layers, tolerance=tolerance
            )
        except BLMAPIError as e:
            return MiningClaimsResult(
                latitude=latitude,
                longitude=longitude,
                error=str(e),
            )

        if not results:
            return MiningClaimsResult(
                latitude=latitude,
                longitude=longitude,
                claims=[],
                total_found=0,
            )

        claims = []
        seen_serials = set()

        for result in results:
            layer_id = result.get("layerId")
            attrs = result.get("attributes", {})

            # Determine status from layer
            status = "Active" if layer_id == LAYER_ACTIVE else "Closed"

            # Dedupe by serial number
            serial = attrs.get("Case Serial Number", "")
            if serial and serial not in seen_serials:
                seen_serials.add(serial)
                claims.append(_parse_claim(attrs, status))

        return MiningClaimsResult(
            latitude=latitude,
            longitude=longitude,
            claims=claims,
            total_found=len(claims),
        )
