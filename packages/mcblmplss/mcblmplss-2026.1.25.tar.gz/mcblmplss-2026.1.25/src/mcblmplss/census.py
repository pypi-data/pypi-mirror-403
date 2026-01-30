"""
Census Bureau TIGERweb client for county lookups.

Provides county information via the Census Bureau's TIGERweb ArcGIS service.
This complements BLM data which doesn't include county boundaries.
"""

import httpx
from pydantic import BaseModel, Field

# Census TIGERweb MapServer
CENSUS_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer"
LAYER_COUNTY = 82


class CountyInfo(BaseModel):
    """County information from Census TIGERweb."""

    name: str = Field(..., description="County name (e.g., 'Valley County')")
    fips: str = Field(..., description="Full FIPS code: state + county (e.g., '16085')")
    county_fips: str = Field(..., description="County FIPS code only (e.g., '085')")
    state_fips: str = Field(..., description="State FIPS code (e.g., '16' for Idaho)")


class CensusAPIError(Exception):
    """Error communicating with Census TIGERweb services."""

    pass


async def get_county(latitude: float, longitude: float, timeout: float = 30.0) -> CountyInfo | None:
    """
    Get county information for coordinates.

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
        timeout: Request timeout in seconds

    Returns:
        CountyInfo if found, None if no county data available

    Raises:
        CensusAPIError: If the API request fails
    """
    params = {
        "f": "json",
        "geometry": f"{longitude},{latitude}",
        "geometryType": "esriGeometryPoint",
        "sr": "4326",
        "layers": f"all:{LAYER_COUNTY}",
        "tolerance": "1",
        "mapExtent": f"{longitude - 1},{latitude - 1},{longitude + 1},{latitude + 1}",
        "imageDisplay": "100,100,96",
        "returnGeometry": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{CENSUS_URL}/identify", params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        raise CensusAPIError("Census API request timed out.")
    except httpx.HTTPStatusError as e:
        raise CensusAPIError(f"Census API returned error {e.response.status_code}")
    except httpx.RequestError as e:
        raise CensusAPIError(f"Failed to connect to Census API: {e}")

    if "error" in data:
        error_msg = data["error"].get("message", "Unknown error")
        raise CensusAPIError(f"Census API error: {error_msg}")

    results = data.get("results", [])
    if not results:
        return None

    # Find the county layer result
    for result in results:
        if result.get("layerId") == LAYER_COUNTY:
            attrs = result.get("attributes", {})
            name = attrs.get("NAME", "")
            geoid = attrs.get("GEOID", "")
            county_fips = attrs.get("COUNTY", "")

            if geoid and len(geoid) >= 5:
                return CountyInfo(
                    name=name,
                    fips=geoid,
                    county_fips=county_fips,
                    state_fips=geoid[:2],
                )

    return None


async def get_counties_batch(
    coordinates: list[tuple[float, float]],
    timeout: float = 30.0,
) -> list[CountyInfo | None]:
    """
    Get county information for multiple coordinates in parallel.

    Args:
        coordinates: List of (latitude, longitude) tuples
        timeout: Request timeout per coordinate

    Returns:
        List of CountyInfo or None for each coordinate
    """
    import asyncio

    async def safe_get_county(lat: float, lon: float) -> CountyInfo | None:
        try:
            return await get_county(lat, lon, timeout)
        except CensusAPIError:
            return None

    tasks = [safe_get_county(lat, lon) for lat, lon in coordinates]
    return await asyncio.gather(*tasks)
