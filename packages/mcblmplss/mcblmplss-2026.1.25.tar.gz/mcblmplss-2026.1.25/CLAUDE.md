# mcblmplss - BLM Land Data MCP Server

This FastMCP server provides 18 tools across 9 BLM data domains, all using the mixin pattern.

## Architecture

```
src/mcblmplss/
├── server.py          # FastMCP server, registers all mixins
├── client.py          # Shared BLMClient for ArcGIS REST API
└── mixins/
    ├── plss.py              # Section/Township/Range
    ├── surface_management.py # Who manages the land
    ├── mining_claims.py     # Active/closed mining claims
    ├── grazing.py           # Grazing allotments
    ├── wild_horses.py       # Herd Management Areas
    ├── recreation.py        # Campgrounds, trailheads
    ├── wilderness.py        # Wilderness & WSAs
    ├── wild_rivers.py       # Wild & Scenic Rivers
    └── acec.py              # Areas of Critical Environmental Concern
```

## Adding New Data Sources

The mixin pattern makes adding new BLM data sources trivial:

1. Create a new file in `mixins/`
2. Define Pydantic models for the data
3. Create a `*Mixin(MCPMixin)` class with `@mcp_tool` methods
4. Add the mixin to `mixins/__init__.py`
5. Register it in `server.py`

## BLM ArcGIS Services

All data comes from official BLM MapServer endpoints:

| Service | Endpoint |
|---------|----------|
| PLSS | `gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer` |
| Surface Management | `gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer` |
| Mining Claims | `gis.blm.gov/nlsdb/rest/services/Mining_Claims/MiningClaims/MapServer` |
| Grazing | `gis.blm.gov/arcgis/rest/services/range/BLM_Natl_Grazing_Allotment/MapServer` |
| Wild Horses | `gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB_Geocortex/MapServer` |
| Recreation | `gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation_Sites_Facilities/MapServer` |
| Wilderness | `gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer` |
| Wild Rivers | `gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WSR/MapServer` |
| ACEC | `gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_ACEC/MapServer` |

## Testing

```bash
uv run python -c "
import asyncio
from mcblmplss.mixins import PLSSMixin

async def test():
    plss = PLSSMixin()
    result = await plss.get_plss_location(40.0, -105.0)
    print(result)

asyncio.run(test())
"
```
