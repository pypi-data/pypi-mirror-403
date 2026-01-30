"""
Shared HTTP client for BLM ArcGIS REST API queries.

Provides common identify/query operations against BLM MapServer endpoints.
"""

from typing import Any

import httpx


class BLMAPIError(Exception):
    """Error communicating with BLM ArcGIS services."""

    pass


class BLMClient:
    """Async HTTP client for BLM ArcGIS REST services."""

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout

    async def identify(
        self,
        base_url: str,
        latitude: float,
        longitude: float,
        layers: str,
        tolerance: int = 1,
        return_geometry: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Perform an identify operation on a MapServer.

        Args:
            base_url: MapServer URL (e.g., https://gis.blm.gov/.../MapServer)
            latitude: WGS84 latitude
            longitude: WGS84 longitude
            layers: Layer specification (e.g., "all:1,2" or "visible:0")
            tolerance: Pixel tolerance for hit detection
            return_geometry: Whether to include geometry in response

        Returns:
            List of result dictionaries with layerId and attributes

        Raises:
            BLMAPIError: If the API request fails
        """
        params = {
            "f": "json",
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "sr": "4326",
            "layers": layers,
            "tolerance": str(tolerance),
            "mapExtent": f"{longitude - 1},{latitude - 1},{longitude + 1},{latitude + 1}",
            "imageDisplay": "100,100,96",
            "returnGeometry": "true" if return_geometry else "false",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{base_url}/identify", params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            raise BLMAPIError("BLM API request timed out. The service may be slow or unavailable.")
        except httpx.HTTPStatusError as e:
            raise BLMAPIError(f"BLM API returned error {e.response.status_code}")
        except httpx.RequestError as e:
            raise BLMAPIError(f"Failed to connect to BLM API: {e}")

        # Check for ArcGIS error response
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            raise BLMAPIError(f"BLM API error: {error_msg}")

        return data.get("results", [])

    async def query(
        self,
        base_url: str,
        layer_id: int,
        where: str = "1=1",
        geometry: dict | None = None,
        out_fields: str = "*",
        return_geometry: bool = False,
        result_offset: int = 0,
        result_record_count: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Perform a query operation on a specific layer.

        Args:
            base_url: MapServer URL
            layer_id: Layer ID to query
            where: SQL WHERE clause
            geometry: Optional geometry filter (point, envelope, etc.)
            out_fields: Fields to return (* for all)
            return_geometry: Whether to include geometry
            result_offset: Pagination offset
            result_record_count: Max records to return

        Returns:
            List of feature attribute dictionaries

        Raises:
            BLMAPIError: If the API request fails
        """
        params = {
            "f": "json",
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            "resultOffset": str(result_offset),
            "resultRecordCount": str(result_record_count),
        }

        if geometry:
            params["geometry"] = str(geometry)
            params["geometryType"] = geometry.get("type", "esriGeometryPoint")
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{base_url}/{layer_id}/query", params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            raise BLMAPIError("BLM API request timed out. The service may be slow or unavailable.")
        except httpx.HTTPStatusError as e:
            raise BLMAPIError(f"BLM API returned error {e.response.status_code}")
        except httpx.RequestError as e:
            raise BLMAPIError(f"Failed to connect to BLM API: {e}")

        # Check for ArcGIS error response
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            raise BLMAPIError(f"BLM API error: {error_msg}")

        features = data.get("features", [])
        return [f.get("attributes", {}) for f in features]


# Shared client instance
blm_client = BLMClient(timeout=60.0)
