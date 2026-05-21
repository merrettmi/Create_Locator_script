#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
parcels.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\parcels.py


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-03-27 23:57:58"
###############################################################################

import arcpy
from datetime import datetime

from core import DatasetConfig, create_locator_for_dataset, Context
from utils.arcpy_utils import (
    giveArcpyResults,
)

from utils.MyLogging import logger

from pprint import pformat

import traceback



# Global lookup cache
SSAP_LOOKUP = None


# -----------------------------------------------------------------
def to_dt(value):
    if isinstance(value, datetime):
        return value
    if value in (None, "", " "):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except:
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
    # logger.traceq(f"starting look up table for {fc_ssap}")

    flds = [
        # 'OBJECTID',
        # 'DiscrpAgID',
        # 'DateUpdate',
        "Effective",
        "Expire",
        # 'NGUID',
        "Country",
        "State",
        # 'County',
        # 'AddCode',
        # 'AddDataURI',
        "Inc_Muni",
        # 'Uninc_Comm',
        "Nbrhd_Comm",
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
        "i_Category",
        "i_Status",
        # 'i_RotationAngle',
        "i_Address",
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

    # where =f"i_gis_key is not null and i_gis_key != ''"

    lookup = {}

    try:
        with arcpy.da.SearchCursor(fc_ssap, flds) as cursor:
            for row in cursor:
                row_dict = dict(zip(flds, row))

                key = row_dict.get("i_gis_key")
                if not key or not str(key).strip():
                    # logger.traced(f"kicking out because key {key=}")
                    continue
                # cat = row_dict.get("i_Category")
                # if cat != "Address_Number" and cat != 'Suite_Unit':
                #     logger.tracee(f"kicking out because category {cat}")
                #     continue

                eff = row_dict.get("Effective")
                exp = row_dict.get("Expire")
                if not is_active(eff, exp):
                    # logger.tracef(f"kicking out because not active {eff}, {exp}")
                    continue

                lookup[key] = row_dict
        # logger.tracei(f"{len(lookup)}")
    except Exception as e:
        logger.error(f"Error ': {e}")
        giveArcpyResults(None, f"arcpy results")
        traceback.print_exc()
        raise
    
    return lookup


# -----------------------------------------------------------------
def part(*items):
    return " ".join(str(i).strip() for i in items if i not in (None, "", " ")).strip()


# -----------------------------------------------------------------
# def build_full_Addr(row):
#     return part(
#         part(row.get("i_unit_prefix"), row.get("Unit")),
#         part(row.get("AddNum_Pre"), row.get("Add_number"), row.get("AddNum_Suf")),
#     )


# -----------------------------------------------------------------
def build_full_street(row):
    # logger.traceq(f"{row=}")
    r = part(
        row.get("St_PreMod") if row else None,
        row.get("St_PreDir") if row else None,
        row.get("St_PreTyp") if row else None,
        part(
            row.get("St_Name") if row else None, row.get("St_PosTyp") if row else None
        ),
        row.get("St_PosDir") if row else None,
        row.get("St_PosMod") if row else None,
    )
    # logger.tracew(f"{r=}")
    return r


# -----------------------------------------------------------------
def parcel_update_logic(row):
    # CRITICAL: Handle the __fields__ request first!
    if "__fields__" in row:
        return {
            # List ALL fields that will be returned in the actual update
            "Prov": None,
            "Prov_Abbriviation": None,
            "CountryCode": None,
            "Inc_Muni": None,
            "FULL_ADDRESS": None,
            "FullStreetName": None,
            "AddNum_Pre": None,
            "Add_Number": None,
            "AddNum_Suf": None,
            "St_PreMod": None,
            "St_PreDir": None,
            "St_PreTyp": None,
            "St_PreSep": None,
            "St_Name": None,
            "St_PosTyp": None,
            "St_PosDir": None,
            "St_PosMod": None,
            "Building": None,
            "Floor": None,
            "Unit": None,
            "i_Category": None,
            "City": None,
            # Add PIN and other fields you need to READ
            "PIN": None,
            # "Suite": None,
            # "House": None,
            "Street": None,
        }

    try:
        # logger.tracei(f"row---->{row}")
        pin = row.get("PIN")
        # if pin:
        #     logger.purple(f"{pin=}")
        # else:
        #     logger.tracej(f"{pin=}")

        # Lookup from global cache
        ssap = SSAP_LOOKUP.get(pin) if SSAP_LOOKUP else None

        # if not ssap:
        #     logger.error("why is ssap empty {ssap=}")

        r = {
            "Prov": "Yukon Territory",
            "Prov_Abbriviation": "YT",
            "CountryCode": "CAN",
            "Inc_Muni": "City of Whitehorse",
            # -- from PAC
            "FULL_ADDRESS": f"{row.get('Suite', '')} {row.get('House', '')} {row.get('Street', '')}".strip(),
            # -- from SSAP
            "FullStreetName": build_full_street(ssap),
            "AddNum_Pre": ssap.get("AddNum_Pre") if ssap else None,
            "Add_Number": ssap.get("Add_Number") if ssap else None,
            "AddNum_Suf": ssap.get("AddNum_Suf") if ssap else None,
            "St_PreMod": ssap.get("St_PreMod") if ssap else None,
            "St_PreDir": ssap.get("St_PreDir") if ssap else None,
            "St_PreTyp": ssap.get("St_PreTyp") if ssap else None,
            "St_PreSep": ssap.get("St_PreSep") if ssap else None,
            "St_Name": ssap.get("St_Name") if ssap else None,
            "St_PosTyp": ssap.get("St_PosTyp") if ssap else None,
            "St_PosDir": ssap.get("St_PosDir") if ssap else None,
            "St_PosMod": ssap.get("St_PosMod") if ssap else None,
            "Building": ssap.get("Building") if ssap else None,
            "Floor": ssap.get("Floor") if ssap else None,
            "Unit": ssap.get("Unit") if ssap else None,
            # 'Room': ssap.get("Room") if ssap else None,
            # 'Seat' : ssap.get("Seat") if ssap else None,
            # 'LandmkName': ssap.get("LandmkName") if ssap else None,
            # 'MilePost': ssap.get("MilePost") if ssap else None,
            # 'Place_Type': ssap.get("Place_Type") if ssap else None,
            # 'Placement': ssap.get("Placement") if ssap else None,
            "i_Category": ssap.get("i_Category") if ssap else None,
            "City": "City of Whitehorse",
            # 'i_Status',
            # 'i_RotationAngle',
            # 'i_Address': ssap.get("i_Address") if ssap else None,
            # 'i_Roll',
            # 'i_gis_key': ssap.get("i_gis_key") if ssap else None,
            'PIN': row.get('PIN', None),
            'Street': row.get('Street', None),
        }
        # logger.traceh(f"parcel_update_logic--->{r}")
        return r
    except Exception as e:
        logger.error(f"Error ': {e}")
        giveArcpyResults(None, f"arcpy results")
        traceback.print_exc()
        raise


# -----------------------------------------------------------------
def register(register_fn, ctx:Context):
    global SSAP_LOOKUP

    # Load lookup ONCE here — NOT at import time
    if ctx.use_local_gdb:
        SSAP_LOOKUP = load_ssap_lookup( f"{ctx.local_gdb}\SiteStructureAddressPoints"  )
    else:
        SSAP_LOOKUP = load_ssap_lookup( f"{ctx.sde_map['ng911']}\SiteStructureAddressPoints")

    cfg = DatasetConfig(
        name="parcels",
        sde="DynamicGeneral",
        tbl="Parcel_Calc_Address_CityWorks_WORKING",
        local_name="Parcel_Calc_Address_CityWorks_WORKING_GDB",
        role="Parcel",
        field_mapping_templates=[
            "Parcel.CITY {tblName}.City",
            "Parcel.REGION {tblName}.Prov",
            "Parcel.REGION_ABBR {tblName}.Prov_Abbriviation",
            "Parcel.COUNTRY  {tblName}.CountryCode",
            "Parcel.POSTAL {tblName}.OwnerZip_1",
            'Parcel.STREET_NAME {tblName}.Street',
            "Parcel.PARCEL_NAME {tblName}.PIN",
            "Parcel.HOUSE_NUMBER {tblName}.House",
            "Parcel.SUB_ADDRESS_LEVEL {tblName}.FLOOR",
            # 'Parcel.LEVEL_TYPE {tblName}.LevelType',
            "Parcel.SUB_ADDRESS_UNIT {tblName}.Suite",
            # 'Parcel.REGION_ABBR "YT"',
            # 'Parcel.COUNTRY "Canada"',
            # 'Parcel.FULL_STREET_NAME {tblName}.FullStreetName',
            "Parcel.NEIGHBORHOOD {tblName}.Nbrhd_Comm",
            # "Parcel.STREET_PREFIX_DIR {tblName}.St_PreDir",  # ssap
            # "Parcel.STREET_PREFIX_TYPE {tblName}.St_PreTyp",  # ssap
            # "Parcel.STREET_NAME {tblName}.St_Name",  # ssap
            # "Parcel.STREET_SUFFIX_TYPE {tblName}.St_PosTyp",  # ssap
            # "Parcel.STREET_SUFFIX_DIR {tblName}.St_PosDir",  # ssap
        ],
        add_fields=[
            {"name": "FULL_ADDRESS", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "FullStreetName", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PreMod", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PreDir", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PreSep", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PreTyp", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_Name", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PosTyp", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PosDir", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "St_PosMod", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Add_Number", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "AddNum_Pre", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "AddNum_Suf", "type": "TEXT", "args": {"field_length": 255}},
            # {"name": "Country", "type":"TEXT", "args": {"field_length":255}},
            {"name": "State", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Inc_Muni", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Nbrhd_Comm", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Post_Code", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Building", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Floor_new", "type": "TEXT", "args": {"field_length": 255}},
            # {"name": "LevelType", "type":"TEXT", "args": {"field_length":255}},
            {"name": "Unit", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "i_Unit_Prefix", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "i_Category", "type": "TEXT", "args": {"field_length": 50}},
            {"name": "Prov_Abbriviation", "type": "TEXT", "args": {"field_length": 2}},
            {"name": "Prov", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "City", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "CountryCode", "type": "TEXT", "args": {"field_length": 3}},
        ],
        update_logic=parcel_update_logic,
        locator_func=create_locator_for_dataset,
    )

    register_fn(cfg)


#   update_logic=lambda row: (
#             {
#                 "Prov": None,
#                 "Prov_Abbriviation": None,
#                 "FullStreetName": None,
#                 "FULL_ADDRESS": None,
#                 "Country": None,
#                 "Inc_Muni": None,
#                 }
#             if ( row.get("i_lastOperation") in (None, "ADDR_INS_not in_VGIS_or_SSAP") or
#                 row.get("address") in (None, "None None None") or
#                 row.get("status") ==0
#             ) else {
#                 "Prov": "Yukon Territory",
#                 "Prov_Abbriviation": "YT",
#                 "FullStreetName": build_full_street(row),
#                 x = find_SiteStructureAddressPoint(row),
#                 "St_PreDir": x["St_PreDir"]
#                 "FULL_ADDRESS": f"{row['HOUSE_NO']} {row['STREET_NAME']}",
#                 "Country": "CAN",
#                 "Inc_Muni": "City of Whitehorse",
#             }
#         ),


# {"name": "Add_Number", "type"="TEXT", "args": {"field_length":255}},
# {"name": "AddNum_Pre", "type"="TEXT", "args": {"field_length":255}},
# {"name": "AddNum_Suf", "type"="TEXT", "args": {"field_length":255}},

# {"name": "St_PreMod", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PreDir", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PreSep", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PreTyp", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_Name", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PosTyp", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PreDir", "type"="TEXT", "args": {"field_length":255}},
# {"name": "St_PosMod", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Country", "type"="TEXT", "args": {"field_len"args": {"field_length":255}},gth":255}},
# {"name": "Country_Code", "type"="TEXT", "args": {"field_length":255}},
# {"name": "State", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Inc_Muni", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Nbrhd_Comm", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Post_Code", "type="TEXT", "args": {"field_length":255}},
# {"name": "Building", "type"="TEXT", "args": {"field_length":255}},
# {"name":  'Floor_new' , "type"="TEXT", "args": {"field_length":255}},
# {"name": "LevelType", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Unit", "type"="TEXT", "args": {"field_length":255}},
# {"name": "i_Unit_Prefix", "type"="TEXT", "args": {"field_length":255}},

# {"name": "i_Category", "type"="TEXT", "args": {"field_length":255}},
# {"name": "Prov_Abbriviation", "type"="TEXT", "args": {"field_length":255}},


# i_lastOperation != 'ADDR_INS_not in_VGIS_or_SSAP'
#   and address != 'None None None'


# update_logic=lambda row: (
#     {
#         "Prov": None,
#         "Prov_Abbriviation": None,
#         "full_street_name": None,
#         "FULL_ADDRESS": None}
#     if "__fields__" in row else
#     {
#         "Prov": "Yukon Territory",
#         "Prov_Abbriviation": "YT",
#         "full_street_name": build_full_street(row),
#         "FULL_ADDRESS": f"{row['HOUSE_NO']} {row['STREET_NAME']}"
#     }
# ),


# return [
#         'Parcel.PARCEL_NAME {tblName}.PIN',
#         'Parcel.HOUSE_NUMBER {tblName}.House',
#         'Parcel.STREET_PREFIX_DIR {tblName}.St_PreDir',
#         'Parcel.STREET_PREFIX_TYPE {tblName}.St_PreTyp',
#         'Parcel.STREET_NAME {tblName}.St_Name',
#         'Parcel.STREET_SUFFIX_TYPE {tblName}.St_PosTyp',
#         'Parcel.STREET_SUFFIX_DIR {tblName}.St_PosDir',
#         'Parcel.FULL_STREET_NAME {tblName}.FullStreetName',
#         'Parcel.SUB_ADDRESS_UNIT {tblName}.Unit',
#         'Parcel.SUB_ADDRESS_LEVEL {tblName}.FLOOR',
#         'Parcel.SUB_ADDRESS_LEVEL_TYPE {tblName}.LevelType',
#         'Parcel.NEIGHBORHOOD {tblName}.Nbrhd_Comm',
#         'Parcel.CITY {tblName}.Inc_Muni',
#         'Parcel.REGION {tblName}.State',
#         'Parcel.REGION_ABBR {tblName}.Prov_Abbriviation',
#         'Parcel.COUNTRY {tblName}.Country'
#         ]


# r = arcpy.geocoding.CreateLocator(
#         country_code="CAN",
#         primary_reference_data=f"{fc} Parcel",
#         field_mapping=giveParcel_mapping(),
#         out_locator=fn,
#         language_code="ENG",
#         alternatename_tables=None,
#         alternate_field_mapping=None,
#         custom_output_fields=None,
#         precision_type="LOCAL_EXTRA_HIGH",
#         version_compatibility="V3_0_TO_3_3"
#     )

# arcpy.gp.AddField( fc_pcc, "FullStreetName", "TEXT", "", "", "255", "FullStreetName", "NULLABLE", "", "",)
# arcpy.gp.AddField( fc_pcc, "Add_Number", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "AddNum_Pre", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "AddNum_Suf", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )

# arcpy.gp.AddField( fc_pcc, "St_PreMod", "TEXT", "", "", "15", "Street Name Pre Modifier", "NULLABLE", "NON_REQUIRED", "")
# arcpy.gp.AddField( fc_pcc, "St_PreDir", "TEXT", "", "", "255", "Street pre dir", "NULLABLE", "", "",)
# arcpy.gp.AddField( fc_pcc, "St_PreSep", "TEXT", "", "", "20", "Street Name Pre Type Separator", "NULLABLE", "NON_REQUIRED", "StreetNamePreTypeSeparator")
# arcpy.gp.AddField( fc_pcc, "St_PreTyp", "TEXT", "", "", "255", "street pre type", "NULLABLE", "",  "",        )
# arcpy.gp.AddField( fc_pcc, "St_Name", "TEXT", "", "", "255", "street name", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "St_PosTyp", "TEXT", "", "", "255", "street post type", "NULLABLE", "", "", )
# arcpy.gp.AddField( fc_pcc, "St_PosDir", "TEXT", "", "", "255", "street post dir", "NULLABLE", "", "" )
# arcpy.gp.AddField( fc_pcc, "St_PosMod", "TEXT", "", "", "25", "Street Name Post Modifier", "NULLABLE", "NON_REQUIRED", "")
# arcpy.gp.AddField( fc_pcc, "Country", "TEXT", "", "", "255", "", "NULLABLE", "", ""  )
# arcpy.gp.AddField( fc_pcc, "Country_Code", "TEXT", "", "", "255", "r", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "State", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "Inc_Muni", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "Nbrhd_Comm", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "Post_Code", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "Building", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# # arcpy.gp.AddField(fc_pcc, 'Floor_new' , "TEXT", "", "", "255", "", "NULLABLE", "", "")
# arcpy.gp.AddField( fc_pcc, "LevelType", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )
# arcpy.gp.AddField( fc_pcc, "Unit", "TEXT", "", "",  "255", "", "NULLABLE", "", "")
# arcpy.gp.AddField( fc_pcc, "i_Unit_Prefix", "TEXT", "", "", "255", "", "NULLABLE", "", ""        )

# arcpy.gp.AddField( fc_pcc, "i_Category", "TEXT", "", "", "255", "", "NULLABLE", "", ""     )
# arcpy.gp.AddField( fc_pcc, "Prov_Abbriviation", "TEXT", "", "", "10", "Prov Abbriviation", "NULLABLE", "", "", )

#     for row in cursor:
#         rowDict = dict(zip(fields, row))

#         print(f"Busy working, please wait {next(spinny)}", end="\r")


#         pin = rowDict["pin"]
#         idx = fields.index('pin')
#         fields[idx] ='i_gis_key'
#         (lst, addr) = find_SiteStructureAddressPoint(fc_ssap, pin, fields)
#         fields[idx] = 'pin'

#         if lst != False:
#             rowDict["Add_Number"] = addr
#             for i in fields:
#                 if i != 'pin':
#                     rowDict[ i ] = lst[i]

#         rowUP = [rowDict[field] for field in fields]
#         #         cursor.updateRow(rowUP)
