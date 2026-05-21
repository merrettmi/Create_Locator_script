#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
address_points.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\address_points.py



"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-04-21 19:59:28"
###############################################################################

# import sys

import arcpy
from datetime import datetime
from core import DatasetConfig, create_locator_for_dataset, Context

from utils.arcpy_utils import (
    giveArcpyResults,
)
import traceback
from utils.MyLogging import logger

# from pprint import pformat

SSAP_LOOKUP_ADDR = None

# -----------------------------------------------------------------
def to_dt(value):
    if isinstance(value, datetime):
        return value
    if value in (None, "", " "):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception: #as e:
        return None


# -----------------------------------------------------------------
def is_active(effective, expire):
    eff = to_dt(effective)
    exp = to_dt(expire)
    now = datetime.now()

    if expire is None and effective is None:
        return True

    if eff is None:
        return now <= exp

    if exp is None:
        return eff <= now

    return eff <= now <= exp

# -----------------------------------------------------------------
# Load lookup table ONCE (called inside register())
# -----------------------------------------------------------------
def load_ssap_lookup(fc_ssap):
    logger.traceq(f"starting look up table for {fc_ssap}")

    flds = [
        # 'OBJECTID',
        # 'DiscrpAgID',
        # 'DateUpdate',
        "Effective",
        "Expire",
        # 'NGUID',
        # "Country",
        # "State",
        # 'County',
        # 'AddCode',
        # 'AddDataURI',
        # "Inc_Muni",
        # # 'Uninc_Comm',
        # "Nbrhd_Comm",
        "AddNum_Pre",
        "Add_Number",
        "AddNum_Suf",
        "St_PreMod",
        "St_PreDir",
        "St_PreTyp",
        "St_PreSep",
        "St_Name",
        "St_PosTyp",
        "St_PosDir",
        "St_PosMod",
        # 'LSt_PreDir',
        # 'LSt_Name',
        # 'LSt_Type',
        # 'LSt_PosDir',
        # 'ESN',
        # 'MSAGComm',
        # 'Post_Comm',
        # 'Post_Code',
        # 'PostCodeEx',
        "Building",
        "Floor",
        "Unit",
        # 'Room',
        # 'Seat',
        # 'Addtl_Loc',
        # 'LandmkName',
        # 'MilePost',
        # 'Place_Type',
        # 'Placement',
        # 'Longitude',
        # 'Latitude',
        # 'Elevation',
        # 'i_PublishRestrictions_Flags',
        # "i_Category",
        # "i_Status",
        # 'i_RotationAngle',
        # "i_Address",
        # 'i_Roll',
        "i_gis_key",
        # 'Shape',
        # 'i_Unit_Prefix',
        # 'GlobalID',
        # 'i_Designator',
        # 'i_Address_Authority',
        # 'i_sub_Addr_unit_from',
        # 'i_sub_Addr_unit_to',
    ]
    lookup = {}  # Will be dict of lists: {key: [row1, row2, ...]}

    try:
        with arcpy.da.SearchCursor(fc_ssap, flds) as cursor:
            for row in cursor:
                row_dict = dict(zip(flds, row))

                key = row_dict.get("i_gis_key")
                if not key or not str(key).strip():
                    continue

                eff = row_dict.get("Effective")
                exp = row_dict.get("Expire")
                if not is_active(eff, exp):
                    continue

                unit = row_dict.get("Unit")
                if not unit or str(unit).strip() == "":
                    continue

                # ✅ Store multiple rows per key
                if key not in lookup:
                    lookup[key] = []
                lookup[key].append(row_dict)

        logger.tracei(f"Loaded {len(lookup)} keys with {sum(len(v) for v in lookup.values())} total units")

    except Exception as e:
        logger.error(f"Error ': {e}")
        giveArcpyResults(None, "arcpy results")
        traceback.print_exc()
        raise
    return lookup


# -----------------------------------------------------------------
def part(*items):
    # logger.tracez(f"{items=}")
    return " ".join(str(i).strip() for i in items if i not in (None, "", " ")).strip()


# -----------------------------------------------------------------
def build_full_street(row):
    # logger.traceq(f"{row=}")

    # logger.tracer(f'{row.get("St_PreMod")}')
    core = part(
        row.get("St_PreMod"),
        row.get("St_PreDir"),
        row.get("St_PreTyp"),
        part(row.get("St_Name"), row.get("St_PosTyp")),
        row.get("St_PosDir"),
        row.get("St_PosMod"),
    )
    # logger.tracey(f"{core=}")

    # full = f"{core}, {row.get('inc_muni')}, {row.get('State')} {row.get('Post_code')}, {row.get('Country')}"
    # return full.strip()
    # logger.tracep(f"build_full_street ->{core}   {row.get('St_Name')}")
    return core


# -----------------------------------------------------------------
def build_house_num(row):
    # logger.tracep(f"{row=}")

    addr = part(
        part(row.get("i_unit_prefix"), row.get("Unit")),
        part(row.get("AddNum_Pre"), row.get("Add_Number"), row.get("AddNum_Suf")),
        # part(row.get("BUILDING"), row.get("LandmkName")),
        # part( build_full_street(row)),
    )
    # logger.traceo(f"build_house_num->{addr}")
    return addr

    # part(row.get("i_unit_prefix"), row.get("Unit")),
    # part(row.get("AddNum_Pre"), row.get("Add_number"), row.get("AddNum_Suf")),


# -----------------------------------------------------------------
def calc_min_max_for_unit(row):
    un = row.get('Unit', None)
    rd = row.get('St_Name', None)
    addr = row.get('Add_Number', None)

    if un is None or rd is None or addr is None:
        return None, None
    
    # logger.tracer(f"looking for unit:{un} street:{rd} addr:{addr}")    
    units = []
    
    # ✅ SSAP_LOOKUP now has structure: {key: [row1, row2, row3, ...]}
    for key, lookup_rows in SSAP_LOOKUP_ADDR.items():
        # ✅ lookup_rows is a LIST of dicts, not a single dict
        for lookup_row in lookup_rows:  # ← Loop through the list!
            unit = lookup_row.get('Unit')
            road = lookup_row.get('St_Name')
            addn = lookup_row.get('Add_Number')
            
            if rd == road and addr == addn:
                try:
                    units.append(int(unit))
                    # logger.tracen(f"---Added to min/max list: {unit}")
                except ValueError:
                    pass
    
    # logger.traces(units)
    
    if units:
        # Convert to integers for proper min/max
        try:
            int_units = [int(u) for u in units if u]
            smallest = str(min(int_units))
            largest = str(max(int_units))
            # logger.traceg(f"min:{smallest} max:{largest}")
        except (ValueError, TypeError):
            # If units aren't numeric, use string comparison
            smallest = min(units)
            largest = max(units)
    else:
        smallest = largest = un
    
    # logger.tracep(f"{smallest=} {largest=} {units}")
    return smallest, largest

# -----------------------------------------------------------------
def build_unit_from(row: dict) -> str:
    mini, _ = calc_min_max_for_unit(row)
    # if mini:
    #     logger.tracek(f"{mini=} ")
    return mini

# -----------------------------------------------------------------
def build_unit_to(row:dict) -> str:
    _, maxi = calc_min_max_for_unit(row)
    # if maxi:
    #     logger.tracej(f"{maxi=}")
    return maxi


# -----------------------------------------------------------------
def pre_process(cfg: DatasetConfig, ctx: Context):
    global SSAP_LOOKUP_ADDR
    logger.tracea("Hello Mike do an address_points pre process thing")
    logger.tracea(f"{cfg=}")
    logger.tracea(f"{ctx=}")
    logger.tracea(f"about to start loading lookups {ctx.use_local_gdb=}")
    
    # SSAP_LOOKUP_ADDR = load_ssap_lookup( r"D:\City_STUFF\Create_Locator_v4\copyOfMasterData.gdb\SiteStructureAddressPoints"  )
    if ctx.use_local_gdb:
        SSAP_LOOKUP_ADDR = load_ssap_lookup( r"D:\City_STUFF\Create_Locator_v4\copyOfMasterData.gdb\SiteStructureAddressPoints"   )
    else:
        SSAP_LOOKUP_ADDR = load_ssap_lookup( r"M:\Processing_Scripts\Create_Locator_Service\DatabasesForUse\NG911.sde\SiteStructureAddressPoints")


# -----------------------------------------------------------------
def register(register_fn, ctx:Context):
    global SSAP_LOOKUP_ADDR

    # Load lookup ONCE here — NOT at import time

    cfg = DatasetConfig(
        name="address_points",
        sde="ng911",
        tbl="SiteStructureAddressPoints",
        local_name="SiteStructureAddressPoints_GDB",
        role="PointAddress",
        field_mapping_templates=[
            "PointAddress.HOUSE_NUMBER {tblName}.house_number",
            "PointAddress.STREET_PREFIX_DIR {tblName}.St_PreDir",
            "PointAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp",
            "PointAddress.STREET_NAME {tblName}.St_Name",
            "PointAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp",
            "PointAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir",
            "PointAddress.FULL_STREET_NAME {tblName}.full_street_name",
            "PointAddress.BUILDING_NAME {tblName}.Building",
            # 'PointAddress.SUB_ADDRESS_BUILDING_UNIT {tblName}.Unit'
            "PointAddress.SUB_ADDRESS_UNIT {tblName}.Unit",
            "PointAddress.SUB_ADDRESS_LEVEL {tblName}.Floor",
            "PointAddress.PARCEL_JOIN_ID {tblName}.i_gis_key",
            "PointAddress.NEIGHBORHOOD {tblName}.Nbrhd_Comm",
            "PointAddress.REGION_ABBR {tblName}.Prov_Abbriviation",
            "PointAddress.COUNTRY {tblName}.Country",
            'PointAddress.SUB_ADDRESS_UNIT_FROM {tblName}.i_sub_Addr_unit_from',
            'PointAddress.SUB_ADDRESS_UNIT_TO {tblName}.i_sub_Addr_unit_to',
        ],
        add_fields=[
            {"name": "full_street_name", "type": "TEXT", "args": {"field_length": 250}},
            {"name": "house_number", "type": "TEXT", "args": {"field_length": 250}},
            {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 2}},
            {"name": "Prov", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "City", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "CountryCode", "type": "TEXT", "args": {"field_length": 3}},
        ],
        update_logic=lambda row: (
            {
                # "FULL_ADDRESS": None,
                # "Prov_Abbriviation": None,
                "Prov": None,
                "City": None,
                "CountryCode": None,
                # ✅ But ALSO include all fields you need to READ
                "St_PreMod": None,
                "St_PreDir": None,
                "St_PreTyp": None,
                "St_Name": None,
                "St_PosTyp": None,
                "St_PosDir": None,
                "St_PosMod": None,
                "i_unit_prefix": None,
                "Unit": None,
                "AddNum_Pre": None,
                "Add_Number": None,
                "AddNum_Suf": None,
                "Building": None,
                "LandmkName": None,
                "house_number": None,
                "full_street_name": None,
                # "i_Unit_Prefix": None,
                'i_sub_Addr_unit_from' : None,
                'i_sub_Addr_unit_to' : None,                
            }
            if "__fields__" in row
            else {
                # ✅ Fields you're just READING - pass through unchanged
                "St_PreMod": row.get("St_PreMod"),
                "St_PreDir": row.get("St_PreDir"),
                "St_PreTyp": row.get("St_PreTyp"),
                "St_Name": row.get("St_Name"),
                "St_PosTyp": row.get("St_PosTyp"),
                "St_PosDir": row.get("St_PosDir"),
                "St_PosMod": row.get("St_PosMod"),
                "i_unit_prefix": row.get("i_unit_prefix"),
                "Unit": row.get("Unit"),
                "AddNum_Pre": row.get("AddNum_Pre"),
                "Add_Number": row.get("Add_Number"),
                "AddNum_Suf": row.get("AddNum_Suf"),
                "Building": row.get("Building"),
                "LandmkName": row.get("LandmkName"),
                # ✅ Fields you're WRITING - calculated values
                "Prov_Abbriviation": "YT",
                "Prov": "Yukon Territory",
                "City": "City of Whitehorse",
                "CountryCode": "CAN",
                "house_number": build_house_num(row),
                "full_street_name": build_full_street(row),
                "i_sub_Addr_unit_from": build_unit_from(row),
                "i_sub_Addr_unit_to": build_unit_to(row),
            }
        ),
        locator_func=create_locator_for_dataset,
        pre_process_func=pre_process,
    )
    register_fn(cfg)

    # "FULL_ADDRESS": f"{row['HOUSE_NO']} {row['STREET_NAME']}",


#         arcpy.gp.AddField( fc, "Prov_Abbriviation", "TEXT","","","10","Prov Abbriviation","NULLABLE","","",)
#         arcpy.gp.AddField( fc, "Country_Code", "TEXT", "", "", "10", "CountryCode", "NULLABLE", "", ""  )
#         arcpy.gp.AddField( fc, "FullStreetName", "TEXT", "", "", "255", "FullStreetName", "NULLABLE", "", "",)
#         arcpy.gp.AddField( fc, "BuildingType", "TEXT", "", "", "255", "BuildingType", "NULLABLE", "", "",  )
#         arcpy.gp.AddField( fc, "LevelType", "TEXT", "", "", "255", "LevelType", "NULLABLE", "", "" )


#                     print(f"Busy working, please wait {next(spinny)} {rowDict['St_Name']}", end="\r")
#                 rowDict["Prov_Abbriviation"] = "YT"
#                 rowDict["Country_Code"] = "CAN"
#                 rowDict["FullStreetName"] = calc_street(rowDict)
#                 if rowDict["Building"]:
#                     rowDict["BuildingType"] = "Building"
#                 if rowDict["floor"]:
#                     rowDict["LevelType"] = "Floor"


#             'PointAddress.HOUSE_NUMBER {tblName}.Add_Number',
#             'PointAddress.BUILDING_NAME {tblName}.Building',
#             'PointAddress.STREET_PREFIX_DIR {tblName}.St_PreDir',
#             'PointAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp',
#             'PointAddress.STREET_NAME {tblName}.St_Name',
#             'PointAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp',
#             'PointAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir',
#             'PointAddress.FULL_STREET_NAME {tblName}.FullStreetName',
#             'PointAddress.SUB_ADDRESS_UNIT {tblName}.Unit',
#             'PointAddress.SUB_ADDRESS_LEVEL {tblName}.Floor',
#             'PointAddress.PARCEL_JOIN_ID {tblName}.i_gis_key',
#             'PointAddress.NEIGHBORHOOD {tblName}.Nbrhd_Comm',
#             'PointAddress.CITY {tblName}.Inc_Muni',
#             'PointAddress.REGION {tblName}.State',
#             'PointAddress.REGION_ABBR {tblName}.Prov_Abbriviation',
#             'PointAddress.COUNTRY {tblName}.Country'


# def build_address(row):
#     """
#     row = dict-like object with keys:
#     BUILDING, LandmkName, i_unit_prefix, Unit,
#     AddNum_Pre, Add_number, AddNum_Suf,
#     st_premod, st_preDir, St_pretyp,
#     St_Name, St_PosTyp, St_PosDir, St_PosMod,
#     inc_muni, State, Post_code, Country
#     """

#     def part(*items):
#         """Join non-empty items with a space, trimming each."""
#         return " ".join(str(i).strip() for i in items if i not in (None, "", " ")).strip()

#     # --- BUILD THE ADDRESS CORE ---
#     core = part(
#         part(row["BUILDING"], row["LandmkName"]),
#         part(row["i_unit_prefix"], row["Unit"]),
#         part(row["AddNum_Pre"], row["Add_number"], row["AddNum_Suf"]),
#         row["st_premod"],
#         row["st_preDir"],
#         row["St_pretyp"],
#         part(row["St_Name"], row["St_PosTyp"]),
#         row["St_PosDir"],
#         row["St_PosMod"]
#     )

#     # --- FINAL FULL ADDRESS ---
#     full = f"{core}, {row['inc_muni']}, {row['State']} {row['Post_code']}, {row['Country']}"

#     return full.strip()
# arcpy.geocoding.CreateLocator(
#     country_code="CAN",
#     primary_reference_data="SiteStructureAddressPoints PointAddress",
#     field_mapping=['PointAddress.HOUSE_NUMBER SiteStructureAddressPoints.Add_Number',

#                    'PointAddress.STREET_NAME SiteStructureAddressPoints.St_Name',
#                    'PointAddress.SUB_ADDRESS_UNIT SiteStructureAddressPoints.Unit',
#                    'PointAddress.SUB_ADDRESS_UNIT_FROM SiteStructureAddressPoints.i_sub_Addr_unit_from',
#                    'PointAddress.SUB_ADDRESS_UNIT_TO SiteStructureAddressPoints.i_sub_Addr_unit_to',
#                    'PointAddress.SUB_ADDRESS_LEVEL SiteStructureAddressPoints.Floor'
#                    ,'PointAddress.SUB_ADDRESS_BUILDING_UNIT SiteStructureAddressPoints.Unit',
#                    'PointAddress.COUNTRY SiteStructureAddressPoints.Country'],
#     out_locator=r"C:\Users\lost_\OneDrive\Documents\ArcGIS\Projects\MyProject12\SiteStructureA_CreateLocator",
#     language_code="ENG",
#     alternatename_tables=None,
#     alternate_field_mapping=None,
#     custom_output_fields=None,
#     precision_type="GLOBAL_EXTRA_HIGH",
#     version_compatibility="CURRENT_VERSION"
# )