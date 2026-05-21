#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
yukon.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\yukon.py


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-03-21 21:56:39"
###############################################################################

from core import DatasetConfig, create_locator_for_dataset, Context
from utils.arcpy_utils import (
    giveArcpyResults,
)
import traceback
from utils.MyLogging import logger

from pprint import pformat

# -----------------------------------------------------------------
def register(register_fn, ctx:Context):
    cfg = DatasetConfig(
        name="yukon",
        sde="ng911",
        tbl="StateOrEquivalentBoundary",
        local_name="StateOrEquivalentBoundary_GDB",
        role="Region",
        field_mapping_templates=[
            "Region.REGION {tblName}.State",
            "Region.REGION_ABBR {tblName}.Prov_Abbriviation",
            "Region.COUNTRY  {tblName}.Country",
            # "Region.CountryCode {tblName}.country_code",
            #  yukon_locator.Address,
            #  yukon_locator.Address2,
            #  yukon_locator.Address3,
            #  yukon_locator.Neighborhood,
            #  yukon_locator.City,
            #  yukon_locator.Subregion,
            #  yukon_locator.Region,
            #  yukon_locator.Postal,
            #  yukon_locator.PostalExt,
            #  yukon_locator.CountryCode.
        ],
        add_fields=[
            {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 10}},
            {"name": "country_code", "type": "TEXT", "args": {"field_length": 10}},
            ],
        update_logic=lambda row: (
            {
                "Prov_Abbriviation": None,
                "country_code": None,
            }
            if "__fields__" in row
            else {
                "Prov_Abbriviation": "YT",
                "country_code": "CAN",
            }
        ),
        locator_func=create_locator_for_dataset,
    )
    register_fn(cfg)


#     arcpy.geocoding.CreateLocator(
#     country_code="CAN",
#     primary_reference_data="NextGen911_Current.DBO.StateOrEquivalentBoundary Region",
#     field_mapping=[
#         "Region.REGION 'NextGen911_Current.DBO.StateOrEquivalentBoundary'.State",
# "Region.REGION_ABBR 'NextGen911_Current.DBO.StateOrEquivalentBoundary'.State",
# "Region.COUNTRY 'NextGen911_Current.DBO.StateOrEquivalentBoundary'.Country"],
#     out_locator=r"C:\Users\lost_\OneDrive\Documents\ArcGIS\Projects\MyProject11\NextGen911_Cur_CreateLocator",
#     language_code="ENG",
#     alternatename_tables=None,
#     alternate_field_mapping=None,
#     custom_output_fields=None,
#     precision_type="GLOBAL_EXTRA_HIGH",
#     version_compatibility="CURRENT_VERSION"
# )


# arcpy.geocoding.CreateLocator(
#     country_code="CAN",
#     primary_reference_data="NextGen911_Current.DBO.StateOrEquivalentBoundary Region",
#     field_mapping=[
#                     'Region.FEATURE_ID StateOrEquivalentBoundary.GlobalID',
#                     'Region.REGION StateOrEquivalentBoundary.State',
#                     'Region.COUNTRY_CODE StateOrEquivalentBoundary.Country',
#                     'Region.COUNTRY StateOrEquivalentBoundary.Country'
#                    ],
#     out_locator=r"C:\Users\lost_\OneDrive\Documents\ArcGIS\Projects\MyProject12\NextGen911_Cur_CreateLocator",
#     language_code="ENG",
#     alternatename_tables=None,
#     alternate_field_mapping=None,
#     custom_output_fields=None,
#     precision_type="GLOBAL_EXTRA_HIGH",
#     version_compatibility="CURRENT_VERSION"
# )
