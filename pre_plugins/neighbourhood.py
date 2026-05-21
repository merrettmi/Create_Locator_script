from core import DatasetConfig, create_locator_for_dataset, Context#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
neighbourhood.py.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\neighbourhood.py




"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = '2026-03-21 21:56:19'
###############################################################################

from core import DatasetConfig, create_locator_for_dataset
from utils.arcpy_utils import (
    giveArcpyResults,
)
import traceback
from utils.MyLogging import logger

from pprint import pformat

def register(register_fn, ctx:Context):
    cfg = DatasetConfig(
        name="neighbourhood",
        sde="ng911",
        tbl="NeighborhoodCommunityBoundary",
        local_name="NeighborhoodCommunityBoundary_GDB",
        role="Neighborhood",  # ✅ Changed from AdministrativeArea to City
        field_mapping_templates=[
            'Neighborhood.CITY {tblName}.City',
            'Neighborhood.REGION {tblName}.Prov',
            'Neighborhood.REGION_ABBR {tblName}.Prov_Abbriviation',
            'Neighborhood.COUNTRY  {tblName}.CountryCode',

            'Neighborhood.NEIGHBORHOOD {tblName}.Nbrhd_Comm',
        ],
        add_fields=[
                {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 2}},
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
                "CountryCode": "CAN",
            }        
        ),
        locator_func=create_locator_for_dataset,
    )
    register_fn(cfg)



            # 'Neighborhood.NEIGHBORHOOD {tblName}.Nbrhd_Comm',
            # 'Neighborhood.CITY {tblName}.Inc_Muni',
            # 'Neighborhood.REGION {tblName}.State',
            # 'Neighborhood.COUNTRY {tblName}.Country'