#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
streets.py - ArcGIS Geocoding Locator Service Builder


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-03-21 21:56:32"
###############################################################################

from core import DatasetConfig, create_locator_for_dataset, Context
from utils.arcpy_utils import (
    giveArcpyResults,
)
import traceback
from utils.MyLogging import logger

from pprint import pformat


# -----------------------------------------------------------------
def part(*items):
    return " ".join(str(i).strip() for i in items if i not in (None, "", " ")).strip()


# -----------------------------------------------------------------
# def build_full_Addr(row):
#     addr = part(
#         part(row.get("i_unit_prefix"), row.get("Unit")),
#         part(row.get("AddNum_Pre"), row.get("Add_number"), row.get("AddNum_Suf")),
#     )
#     return addr


# -----------------------------------------------------------------
def build_full_street(row):
    # logger.traceo(f"{row=}")
    core = part(
        row.get("St_PreMod"),
        row.get("St_PreDir"),
        row.get("St_PreTyp"),
        part(row.get("St_Name"), row.get("St_PosTyp")),
        row.get("St_PosDir"),
        row.get("St_PosMod"),
    )
    return core


# -----------------------------------------------------------------
def register(register_fn, ctx:Context):
    cfg = DatasetConfig(
        name="streets",
        sde="ng911",
        tbl="RoadCenterlines",
        local_name="RoadCenterlines_GDB",
        role="StreetAddress",
        field_mapping_templates=[
            # 'StreetAddress.CITY {tblName}.City',
            # 'StreetAddress.REGION {tblName}.Prov',
            "StreetAddress.COUNTRY  {tblName}.CountryCode",
            "StreetAddress.POSTAL_LEFT {tblName}.PostCode_L",
            "StreetAddress.POSTAL_RIGHT {tblName}.PostCode_R",
            "StreetAddress.STREET_NAME_JOIN_ID {tblName}.NGUID",
            "StreetAddress.HOUSE_NUMBER_FROM_LEFT {tblName}.FromAddr_L",
            "StreetAddress.HOUSE_NUMBER_TO_LEFT {tblName}.ToAddr_L",
            "StreetAddress.HOUSE_NUMBER_FROM_RIGHT {tblName}.FromAddr_R",
            "StreetAddress.HOUSE_NUMBER_TO_RIGHT {tblName}.ToAddr_R",
            "StreetAddress.PARITY_LEFT {tblName}.Parity_L",
            "StreetAddress.PARITY_RIGHT {tblName}.Parity_R",
            "StreetAddress.STREET_PREFIX_DIR {tblName}.St_PreDir",
            "StreetAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp",
            "StreetAddress.STREET_NAME {tblName}.St_Name",
            "StreetAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp",
            "StreetAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir",
            "StreetAddress.FULL_STREET_NAME {tblName}.FullStreetName",
            "StreetAddress.CITY_LEFT {tblName}.IncMuni_L",
            "StreetAddress.CITY_RIGHT {tblName}.IncMuni_R",
            "StreetAddress.REGION_LEFT {tblName}.State_L",
            "StreetAddress.REGION_ABBR_LEFT {tblName}.Prov_Abbriviation",
            "StreetAddress.REGION_RIGHT {tblName}.State_R",
            "StreetAddress.REGION_ABBR_RIGHT {tblName}.Prov_Abbriviation",
        ],
        add_fields=[
            {"name": "FullStreetName", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 2}},
            {"name": "Prov", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "City", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "CountryCode", "type": "TEXT", "args": {"field_length": 3}},
        ],
        update_logic=lambda row: (
            {
                "FullStreetName": None,
                "Prov_Abbriviation": None,
                "Prov": None,
                "City": None,
                "St_PreMod": None,
                "St_PreDir": None,
                "St_PreTyp": None,
                "St_Name": None,
                "St_PosTyp": None,
                "St_PosDir": None,
                "St_PosMod": None,
            }
            if "__fields__" in row
            else {
                "FullStreetName": build_full_street(row),
                "Prov_Abbriviation": "YT",
                "Prov": "Yukon Territory",
                "City": "City of Whitehorse",
                "St_PreMod": row.get("St_PreMod"),
                "St_PreDir": row.get("St_PreDir"),
                "St_PreTyp": row.get("St_PreTyp"),
                "St_Name": row.get("St_Name"),
                "St_PosTyp": row.get("St_PosTyp"),
                "St_PosDir": row.get("St_PosDir"),
                "St_PosMod": row.get("St_PosMod"),
            }
        ),
        locator_func=create_locator_for_dataset,
    )
    register_fn(cfg)

    # return [f'StreetAddress.STREET_NAME_JOIN_ID {tblName}.NGUID',
    #     f'StreetAddress.HOUSE_NUMBER_FROM_LEFT {tblName}.FromAddr_L',
    #     f'StreetAddress.HOUSE_NUMBER_TO_LEFT {tblName}.ToAddr_L',
    #     f'StreetAddress.HOUSE_NUMBER_FROM_RIGHT {tblName}.FromAddr_R',
    #     f'StreetAddress.HOUSE_NUMBER_TO_RIGHT {tblName}.ToAddr_R',
    #     f'StreetAddress.PARITY_LEFT {tblName}.Parity_L',
    #     f'StreetAddress.PARITY_RIGHT {tblName}.Parity_R',
    #     f'StreetAddress.STREET_PREFIX_DIR {tblName}.St_PreDir',
    #     f'StreetAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp',
    #     f'StreetAddress.STREET_NAME {tblName}.St_Name',
    #     f'StreetAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp',
    #     f'StreetAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir',
    #     f'StreetAddress.FULL_STREET_NAME {tblName}.FullStreetName',
    #     f'StreetAddress.NEIGHBORHOOD_LEFT {tblName}.NbrhdCom_L',
    #     f'StreetAddress.NEIGHBORHOOD_RIGHT {tblName}.NbrhdCom_R',
    #     f'StreetAddress.CITY_LEFT {tblName}.IncMuni_L',
    #     f'StreetAddress.CITY_RIGHT {tblName}.IncMuni_R',
    #     f'StreetAddress.REGION_LEFT {tblName}.Region_Left',
    #     f'StreetAddress.REGION_ABBR_LEFT {tblName}.Region_ABBR_Left',
    #     f'StreetAddress.REGION_RIGHT {tblName}.Region_Right',
    #     f'StreetAddress.REGION_ABBR_RIGHT {tblName}.Region_ABBR_Right'
    #     ]

    # r = arcpy.geocoding.CreateLocator(
    #                 country_code="CAN",
    #                 primary_reference_data=f"{fc} StreetAddress",
    #                 field_mapping=giveRoadCenterLine_mapping(),
    #                 out_locator = fn,
    #                 language_code="ENG",
    #                 alternatename_tables=f"{fc_road_Alias} AlternateStreetName",
    #                 alternate_field_mapping=giveRoadAlias_mapping(),
    #                 custom_output_fields=None,
    #                 precision_type="LOCAL_EXTRA_HIGH",
    #                 version_compatibility="V3_0_TO_3_3"
    #             )


# arcpy.geocoding.CreateLocator(
#     country_code="CAN",
#     primary_reference_data="NextGen911_Current.DBO.RoadCenterlines StreetAddress",
#     field_mapping=['StreetAddress.HOUSE_NUMBER_FROM_LEFT RoadCenterlines.FromAddr_L','StreetAddress.HOUSE_NUMBER_TO_LEFT RoadCenterlines.ToAddr_L','StreetAddress.HOUSE_NUMBER_FROM_RIGHT RoadCenterlines.FromAddr_R','StreetAddress.HOUSE_NUMBER_TO_RIGHT RoadCenterlines.ToAddr_R','StreetAddress.STREET_NAME RoadCenterlines.St_Name'],
#     out_locator=r"C:\Users\lost_\OneDrive\Documents\ArcGIS\Projects\MyProject12\NextGen911_Cur_CreateLocator",
#     language_code="ENG",
#     alternatename_tables=None,
#     alternate_field_mapping=None,
#     custom_output_fields=None,
#     precision_type="GLOBAL_EXTRA_HIGH",
#     version_compatibility="CURRENT_VERSION"
# )
