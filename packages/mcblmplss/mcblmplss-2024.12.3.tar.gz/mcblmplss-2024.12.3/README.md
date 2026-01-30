# mcblmplss

[![PyPI version](https://img.shields.io/pypi/v/mcblmplss.svg)](https://pypi.org/project/mcblmplss/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcblmplss.svg)](https://pypi.org/project/mcblmplss/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MCP server for querying U.S. public land data by coordinates.**

Drop a pin anywhere in the western U.S. and instantly get:
- **PLSS location** — Section 12, Township 4N, Range 6E
- **Land manager** — BLM, Forest Service, National Park, Private, etc.
- **Mining claims** — Active lode/placer claims with serial numbers

## When would I use this?

| Use Case | What you get |
|----------|--------------|
| **Dispersed camping** | Check if land is BLM/Forest Service before setting up camp |
| **Land research** | Get legal descriptions for title searches or due diligence |
| **Prospecting** | Find existing mining claims before staking your own |
| **Navigation** | Convert GPS coordinates to the township/range system used on paper maps |
| **GIS workflows** | Programmatic access to BLM cadastral data |

## Installation

```bash
pip install mcblmplss
```

Or run directly without installing:

```bash
uvx mcblmplss
```

### Add to Claude Code

```bash
claude mcp add blm "uvx mcblmplss"
```

## Tools

### `get_plss_location`

Convert coordinates to Section/Township/Range.

```
> get_plss_location(latitude=40.0, longitude=-105.0)

Section 9, Township 1N, Range 68W, 6th Meridian
State: CO
PLSS ID: CO060010S0680W0SN090
```

### `get_land_manager`

Find out who manages the land (and whether you can access it).

```
> get_land_manager(latitude=38.5, longitude=-110.5)

Bureau of Land Management (BLM) - Department of the Interior
Unit: Bureau of Land Management
State: UT
Status: Federal, Public access
```

```
> get_land_manager(latitude=40.0, longitude=-105.0)

Private (PVT)
State: CO
```

### `get_mining_claims`

Find active mining claims at a location.

```
> get_mining_claims(latitude=39.5, longitude=-117.0)

Found 42 mining claim(s):

MAGA #6
  Serial: NV105221817
  Type: Lode Claim
  Status: Active
  Acres: 20.66

MS 2
  Serial: NV105223666
  Type: Lode Claim
  Status: Active
  Acres: 20.66
...
```

## Coverage

Data is available for **30 states** where the Public Land Survey System was used:

![PLSS Coverage](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Public_Land_Survey_System.png/800px-Public_Land_Survey_System.png)

**Not covered:** Eastern seaboard states (use metes-and-bounds), Texas (independent surveys), Hawaii.

## Error Handling

The server returns clear error messages when:

- **Outside PLSS coverage**: "No PLSS data found. Location may be outside surveyed areas."
- **API timeout**: "BLM API request timed out. The service may be slow or unavailable."
- **No mining claims**: "No mining claims found at this location."

## Data Sources

All data comes from official BLM ArcGIS REST services:

| Data | Source | Update Frequency |
|------|--------|------------------|
| PLSS | [BLM National PLSS CadNSDI](https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer) | Quarterly |
| Surface Management | [BLM SMA](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer) | Annual |
| Mining Claims | [BLM MLRS](https://gis.blm.gov/nlsdb/rest/services/Mining_Claims/MiningClaims/MapServer) | Weekly |

**Disclaimer:** This data is for informational purposes only. For legal land descriptions, consult official BLM records or a licensed surveyor.

## Development

```bash
git clone https://git.supported.systems/MCP/mcblmplss.git
cd mcblmplss
uv sync
uv run mcblmplss
```

## License

MIT
