# mcblmplss

[![PyPI version](https://img.shields.io/pypi/v/mcblmplss.svg)](https://pypi.org/project/mcblmplss/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcblmplss.svg)](https://pypi.org/project/mcblmplss/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MCP server for querying U.S. public land data by coordinates.**

Drop a pin anywhere in the western U.S. and get comprehensive land data:

| Category | What you get |
|----------|--------------|
| **PLSS Location** | Section 12, Township 4N, Range 6E, Principal Meridian |
| **Land Manager** | BLM, Forest Service, NPS, Private, State, Tribal |
| **Mining Claims** | Active lode/placer claims with serial numbers |
| **Grazing Allotments** | Livestock grazing permits and acreage |
| **Wild Horses** | Herd Management Areas with population data |
| **Recreation Sites** | Campgrounds, trailheads, boat launches |
| **Wilderness Areas** | Designated Wilderness & Study Areas (WSAs) |
| **Wild Rivers** | Wild & Scenic River segments |
| **ACECs** | Areas of Critical Environmental Concern |

## When would I use this?

| Use Case | Tools to use |
|----------|--------------|
| **Dispersed camping** | `get_land_manager` — Check if it's BLM/USFS public land |
| **Trip planning** | `get_recreation_sites` — Find nearby campgrounds and trailheads |
| **Land research** | `get_plss_location` — Get legal descriptions for title searches |
| **Prospecting** | `get_mining_claims` — Check existing claims before staking |
| **Ranching** | `get_grazing_allotment` — Research grazing permit areas |
| **Wildlife viewing** | `get_wild_horse_herd` — Find wild horse/burro areas |
| **Backcountry planning** | `get_wilderness_area` — Identify wilderness regulations |
| **River trips** | `get_wild_river` — Check Wild & Scenic River status |
| **Conservation research** | `get_acec` — Find protected environmental areas |

## Installation

```bash
pip install mcblmplss
```

Or run directly:

```bash
uvx mcblmplss
```

### Add to Claude Code

```bash
claude mcp add blm "uvx mcblmplss"
```

## Tools (18 total)

Each data type has two tools: a human-readable version and a `_details` version returning structured data.

### PLSS — Public Land Survey System

```
> get_plss_location(40.0, -105.0)

Section 9, Township 1N, Range 68W, 6th Meridian
State: CO
PLSS ID: CO060010S0680W0SN090
```

### Land Manager — Surface Management Agency

```
> get_land_manager(38.5, -110.5)

Bureau of Land Management (BLM) - Department of the Interior
Unit: Bureau of Land Management
State: UT
Status: Federal, Public access
```

### Mining Claims

```
> get_mining_claims(39.5, -117.0)

Found 42 mining claim(s):

MAGA #6
  Serial: NV105221817
  Type: Lode Claim
  Status: Active
  Acres: 20.66
```

### Grazing Allotments

```
> get_grazing_allotment(40.0, -117.0)

AUSTIN (#10004)
State: Nevada
Admin Unit: MOUNT LEWIS FIELD OFFICE
Acres: 245,420
Managing Number: NV10004
```

### Wild Horses & Burros

```
> get_wild_horse_herd(40.0, -117.5)

Augusta Mountains (NV0311)
State: Nevada
Type: Horse
Acres: 177,570
Horse AML: 185-308
Estimated Population: 475 (154% of AML)
Last Inventory: 2015-01-01
```

### Recreation Sites

```
> get_recreation_sites(38.9, -111.2)

Found 3 recreation site(s):

Rochester Panel
  Type: Facility
  Reservable: No
  Phone: 435-636-3600
  https://www.blm.gov/visit/search-details/257016/1
```

### Wilderness & WSAs

```
> get_wilderness_area(38.4, -110.9)

Middle Wild Horse Mesa
  Status: Designated Wilderness
  State: Utah
  NLCS ID: NLCS000885
  Designated: 3/12/2019
```

### Wild & Scenic Rivers

```
> get_wild_river(42.5, -123.5)

Rogue River
  Classification: Recreational
  State: Oregon
  NLCS ID: NLCS000836
```

### ACECs — Areas of Critical Environmental Concern

```
> get_acec(35.0, -117.0)

Superior-Cronese
  State: California
  Protected Values: Natural Process, Natural System, Wildlife
  Acres: 518,461
  Land Use Plan: CDCA Plan, as amended by DRECP
  Designated: 9/14/2016
```

## Coverage

Data is available for **30 states** where the Public Land Survey System was used:

![PLSS Coverage](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Public_Land_Survey_System.png/800px-Public_Land_Survey_System.png)

**Not covered:** Eastern seaboard states (metes-and-bounds), Texas (independent surveys), Hawaii.

## Data Sources

All data comes from official BLM ArcGIS REST services:

| Data | Source | Typical Update |
|------|--------|----------------|
| PLSS | [BLM National PLSS CadNSDI](https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer) | Quarterly |
| Surface Management | [BLM SMA](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer) | Annual |
| Mining Claims | [BLM MLRS](https://gis.blm.gov/nlsdb/rest/services/Mining_Claims/MiningClaims/MapServer) | Weekly |
| Grazing | [BLM Grazing Allotment](https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_Grazing_Allotment/MapServer) | Annual |
| Wild Horses | [BLM WHB](https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB_Geocortex/MapServer) | Annual |
| Recreation | [BLM RIDB](https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation_Sites_Facilities/MapServer) | Nightly |
| Wilderness | [BLM NLCS WLD/WSA](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer) | As designated |
| Wild Rivers | [BLM NLCS WSR](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WSR/MapServer) | As designated |
| ACEC | [BLM ACEC](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_ACEC/MapServer) | As designated |

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
