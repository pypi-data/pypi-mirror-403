The BLM's ArcGIS services are surprisingly comprehensive - there's a lot more we could
  tap into:
  ┌─────────────────────────────────────────────────┬─────────────────────────────────────────────────┐
  │           Potential Future Additions            │                   Data Source                   │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Grazing allotments                              │ range/BLM_Natl_Grazing_Allotment                │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Wild horse/burro areas                          │ range/BLM_Natl_WHB_Geocortex                    │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Recreation sites & campgrounds                  │ recreation/BLM_Natl_Recreation_Sites_Facilities │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Wilderness & WSAs                               │ lands/BLM_Natl_NLCS_WLD_WSA                     │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Wild & Scenic Rivers                            │ lands/BLM_Natl_NLCS_WSR                         │
  ├─────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ ACECs (Areas of Critical Environmental Concern) │ lands/BLM_Natl_ACEC                             │
  └─────────────────────────────────────────────────┴─────────────────────────────────────────────────┘
  The mixin pattern makes adding these trivial - just create a new file in mixins/, define the tools, and register it in
   server.py.
