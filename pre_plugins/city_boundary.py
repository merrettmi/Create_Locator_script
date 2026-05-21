#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
city_boundary.py - ArcGIS Geocoding Locator Service Builder


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = '2026-03-21 21:56:13'
###############################################################################

from core import DatasetConfig, create_locator_for_dataset, Context
from utils.arcpy_utils import (
    giveArcpyResults,
)
import traceback
from utils.MyLogging import logger

from pprint import pformat

# logger.tracez('loading up city_boundary')

def register(register_fn, ctx:Context):
    cfg = DatasetConfig(
        name="city_boundary",
        sde="ng911",
        tbl="IncorporatedMunicipalityBoundary",
        local_name="IncorporatedMunicipalityBoundary_GDB",
        role="City",
        field_mapping_templates=[
            'City.CITY {tblName}.City',
            'City.REGION {tblName}.Prov',
            'City.REGION_ABBR {tblName}.Prov_Abbriviation',
            'City.COUNTRY {tblName}.CountryCode',
        ],
        add_fields=[     {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 2}},
            {"name": "Prov", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "City", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "CountryCode", "type": "TEXT", "args": {"field_length": 3}},
      ],
        update_logic=lambda row: (
            {            
                "Prov_Abbriviation": None,
                "Prov": None,
                "City": None,
                "CountryCode": None,
            }
            if "__fields__" in row else
            {                
                "Prov_Abbriviation": "YT",
                "Prov": "Yukon Territory",
                "City": "City of Whitehorse",
                "CountryCode": "CAN"

            }
        ),
        locator_func=create_locator_for_dataset,
    )
    register_fn(cfg)



# # -----------------------------------------------------------------
# def register(register_fn):
#     cfg = DatasetConfig(
#         name="city_boundary",
#         sde="ng911",
#         tbl="IncorporatedMunicipalityBoundary",
#         local_name="IncorporatedMunicipalityBoundary_GDB",
#         role="AdministrativeArea",
#         field_mapping_templates=[
#             'AdministrativeArea.AreaName {tblName}.Inc_Muni',
#             'AdministrativeArea.Region {tblName}.Prov',
#             'AdministrativeArea.RegionAbbr {tblName}.State',
#             'AdministrativeArea.AreaType {tblName}.AreaType',

#             # 'AdministrativeArea.Country {tblName}.Country',
#             # 'City.SUBREGION {tblName}.OBJECTID',
#         ],
#         add_fields=[
#             {"name": "Prov", "type": "TEXT", "args": {"field_length": 50}},
#             {"name": "AreaType", "type": "TEXT", "args": {"field_length": 50}},
#         ],
#         update_logic=lambda row: (
#             {"Prov": None}
#             if "__fields__" in row else
#             {"Prov": "Yukon Territory",
#                 "AreaType": "City",
#                 # "Country": "CAN"
#             }
#         ),
#         locator_func=create_locator_for_dataset,
#     )
#     register_fn(cfg)



#     Role NameUse ForPointAddressAddress pointsStreetAddressRoad centerlinesParcelParcel polygonsPOIPoints of interestCityCity boundariesRegionState/province boundariesNeighborhoodNeighborhood/community boundariesPostalCodePostal code zones