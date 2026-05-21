#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
condo_address.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\condo_address.py



"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-05-01 15:41:32"
###############################################################################

import sys

import arcpy
from datetime import datetime
from core import DatasetConfig, create_locator_for_dataset, Context

from utils.arcpy_utils import (
    giveArcpyResults,
    show_fields_of_table,
    create_new_copy_of_FeatureClass,
)
import traceback
from utils.MyLogging import logger

from pprint import pformat

import re

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
# create the condo and trailer park boundary polygons
# -----------------------------------------------------------------
def create_condos( fc_pcc, ctx):
    logger.tracea("Starting Condo Lookup ...")
    logger.traceb(f"{fc_pcc=}")

    if ctx.use_local_gdb:
        dst_gdb = ctx.local_gdb       # fgdb_base + ".gdb"
    else:
        dst_gdb = ctx.sde_map['dynamicgeneral']  # dynamic general

    dst_name = "Parcels_Condo_Temp"
    logger.tracet(f"Destination for condo feature class will be: {dst_gdb}\{dst_name}")
    dest = f"{dst_gdb}\{dst_name}"
    if arcpy.Exists(dest):
        logger.tracei(f" about to delete the thing:{dest=}")
        arcpy.management.Delete(dest)


    create_new_copy_of_FeatureClass( fc_pcc, dst_gdb, dst_name)

    if ctx.use_local_gdb:
        ssap = f"{ctx.local_gdb}\{'SiteStructureAddressPoints'}"
    else:
        ssap = f"{ctx.sde_map['ng911']}\{'SiteStructureAddressPoints'}"

    dst = f"{dst_gdb}\{dst_name}"

    flds = [
        'OBJECTID',
        'PIN',
        'BaseName',
        'DESIGNATOR',
        'REMAIN_IND',
        'PLANNO',
        'ADMIN_CODE',
        # 'PCL_CLASS',
        # 'PCL_STATE',
        # 'PCL_PIN',
        'REMARKS',
        'FLOOR',
        # 'RelatedPlanNo',
        # 'Classification',
        # 'SubClass',
        # 'Calc_Area',
        # 'LCSELECTIO',
        # 'CRC_Checksum',
        'APTUNIT',
        'Zone_Class',
        'Zone_Text',
        # 'CLAIMNAME',
        # 'CLAIMNUM',
        # 'CLAIMTYPE',
        'Entity_UID',
        'Entity_Status',
        # 'RollNumber_1',
        # 'RollNumber_2',
        # 'RollNumber_3',
        # 'RollNumber_4',
        # 'RollNumber_5',
        # 'NumberOfRolls',
        # 'num_addresses',
        # 'address_1',
        # 'address_2',
        # 'address_4',
        # 'address_5',
        # 'address_3',
        'EffectiveDate',
        'ExpiredDate',
        'DateUpdated',
        'Status',
        'i_lastOperation',
        # 'Owner_1',
        # 'Owner_2',
        # 'Owner_3',
        # 'Owner_4',
        # 'Owner_5',
        # 'NumberOfOwners',
        "SHAPE@",
    ]

    whr= "(DESIGNATOR LIKE '%CONDOMINIUM%' Or REMARKS LIKE '%TRAILER%') And DESIGNATOR NOT LIKE '%UNIT%' And DESIGNATOR NOT LIKE '%STALL%' AND BASENAME NOT IN ('Easement')"
    orderby = "ORDER BY PIN"

    check_dup_pins = []
    try:
        with arcpy.da.SearchCursor(fc_pcc, field_names=flds, where_clause=whr , sql_clause=(None, orderby)) as pcc_search_cursor, \
            arcpy.da.InsertCursor(dst, field_names=flds) as pcc_insert_cursor:

            for pcc_row in pcc_search_cursor:
                pcc_row_dict = dict(zip(flds, pcc_row))

                pin = pcc_row_dict['PIN']
                if pin in check_dup_pins:
                    continue
                if not pin or not str(pin).strip():
                    continue
                check_dup_pins.append(pin)

                new_row = [pcc_row_dict[f] for f in flds]
                pcc_insert_cursor.insertRow(new_row)

    except Exception as e:
        logger.error(f"Error ': {e}")
        giveArcpyResults(None, f"arcpy results")
        traceback.print_exc()
        raise
        return False
    logger.tracea("... Done Condo Create")
    return True


# -----------------------------------------------------------------
# Load lookup table ONCE (called inside register())
# -----------------------------------------------------------------
def load_ssap_lookup(fc_ssap):
    # logger.traceq(f"starting look up table for {fc_ssap}")

    flds = [
        "i_gis_key",
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
        # 'Shape',
        # 'i_Unit_Prefix',
        # 'GlobalID',
        # 'i_Designator',
        # 'i_Address_Authority',
        # 'i_sub_Addr_unit_from',
        # 'i_sub_Addr_unit_to',
        'SHAPE@',
    ]

    # where =f"i_gis_key is not null and i_gis_key != ''"

    lookup = {}

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
    # logger.tracez(f"{items=}")
    return " ".join(str(i).strip() for i in items if i not in (None, "", " ")).strip()


# -----------------------------------------------------------------
def build_full_street(row):
    # logger.traceq(f"{row=}")
    # logger.tracer(f'{row.get("St_PreMod")}')
    st = part(
        row.get("St_PreMod",""),
        row.get("St_PreDir",""),
        row.get("St_PreTyp",""),
        part(row.get("St_Name",""), row.get("St_PosTyp","")),
        row.get("St_PosDir",""),
        row.get("St_PosMod",""),
    )
    # logger.tracey(f"{core=}")
    # full = f"{core}, {row.get('inc_muni')}, {row.get('State')} {row.get('Post_code')}, {row.get('Country')}"
    # return full.strip()
    # logger.tracep(f"build_full_street ->{core}   {row.get('St_Name')}")
    logger.tracef(f"{st=}")
    return st


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

    if not un:
        # raise('not master condo')
        return None, None

    if un is None or rd is None or addr is None:
        return None, None

    # logger.tracer(f"looking for unit:{un} street:{rd} addr:{addr}")
    units = []

    # ✅ SSAP_LOOKUP now has structure: {key: [row1, row2, row3, ...]}
    for key, lookup_rows in SSAP_LOOKUP.items():
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
def condo_update_logic(row):
    global SSAP_LOOKUP
    # logger.tracev(pformat(row))
    # logger.tracea("Hello Mike do a condo thing")
    if "__fields__" in row:
        return {
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
            # "i_Unit_Prefix": None,
            'i_sub_Addr_unit_from' : None,
            'i_sub_Addr_unit_to' : None,
            }
    try:
        pin = row.get("PIN")
        # logger.tracew(f"Processing PIN: {pin}")
        if not pin or not str(pin).strip():
            logger.traceu("no data so sending None")
            return None
        # logger.mark2()
        ssap = SSAP_LOOKUP.get(pin, None)

        if not ssap:
            logger.tracet(f"no matching ssap record found for this condo {pin}")
            return None
        # else:
            # logger.traceq(f"Found matching SSAP record for this condo {pin}")
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
            'House': row.get('House', None),
            'i_sub_Addr_unit_from': build_unit_from(row),
            'i_sub_Addr_unit_to' : build_unit_to(row),
            }
        # logger.tracer(pformat(r))
        return r
    except Exception as e:
        logger.error(f"Error ': {e}")
        giveArcpyResults(None, f"arcpy results")
        traceback.print_exc()
        raise



# -----------------------------------------------------------------
def pre_process(cfg: DatasetConfig, ctx: Context):
    global SSAP_LOOKUP

    logger.tracea("Hello Mike do a condo pre process thing")
    logger.tracec(pformat(cfg))
    logger.tracec(pformat(ctx))

    if ctx.use_local_gdb:
        cfg.fc = f"{ctx.local_gdb}\SiteStructureAddressPoints"
        cfg.src_fc = f"{ctx.local_gdb}\parcels_calc_combined"
    else:
        cfg.fc = f"{ctx.sde_map[cfg.sde]}\SiteStructureAddressPoints"
        cfg.src_fc = f"{ctx.sde_map[cfg.sde]}\parcels_calc_combined"

    logger.tracea(f"about to start loading condo {cfg.fc}")

    created = create_condos( cfg.src_fc,  ctx)
    logger.tracee(f"condo creation result: {created}" )
    SSAP_LOOKUP = load_ssap_lookup( cfg.fc)

    logger.tracez(f"SSAP_LOOKUP loaded with {len(SSAP_LOOKUP)} entries")
    if not created:
        print("The condo feature class was not created - what went wrong")
        sys.exit(99)


    # x = SSAP_LOOKUP.get('8075141')
    # logger.tracez(f"SSAP_LOOKUP sample for key '8075141': {pformat(x)}")

    return

# -----------------------------------------------------------------
def register(register_fn, ctx:Context):
    global SSAP_LOOKUP

    cfg = DatasetConfig(
        name="condo_address",
        sde="DynamicGeneral",
        tbl="Parcels_Condo_Temp",
        local_name="Parcels_Condo_Temp_GDB",
        role="PointAddress",
        field_mapping_templates=[

            "PointAddress.CITY {tblName}.City",
            "PointAddress.REGION {tblName}.Prov",
            "PointAddress.REGION_ABBR {tblName}.Prov_Abbriviation",
            "PointAddress.COUNTRY  {tblName}.CountryCode",
            # "PointAddress.POSTAL {tblName}.OwnerZip_1",
            'PointAddress.STREET_NAME {tblName}.FullStreetName',
            # "PointAddress.PARCEL_NAME {tblName}.PIN",
            "PointAddress.HOUSE_NUMBER {tblName}.Add_Number",
            "PointAddress.SUB_ADDRESS_LEVEL {tblName}.FLOOR",
            # 'Parcel.LEVEL_TYPE {tblName}.LevelType',
            "PointAddress.SUB_ADDRESS_UNIT {tblName}.Add_Number",
            # 'Parcel.REGION_ABBR "YT"',
            # 'Parcel.COUNTRY "Canada"',
            # 'PointAddress.FULL_STREET_NAME {tblName}.FullStreetName',
            "PointAddress.NEIGHBORHOOD {tblName}.Nbrhd_Comm",
            "PointAddress.SUB_ADDRESS_UNIT_FROM SiteStructureAddressPoints.i_sub_Addr_unit_from",
            "PointAddress.SUB_ADDRESS_UNIT_TO SiteStructureAddressPoints.i_sub_Addr_unit_to",


# 'PointAddress.SUB_ADDRESS_UNIT TestAddressPoints.UNIT_DESIG';
# 'PointAddress.SUB_ADDRESS_UNIT_TYPE TestAddressPoints.UnitType'

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

            {"name": "LandmkName", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "house_number", "type": "TEXT", "args": {"field_length": 25}},
            # {"name": "full_street_name", "type": "TEXT", "args": {"field_length": 255}},
            {"name": "Street", "type": "TEXT", "args": {"field_length": 255}},

            {"name": "i_sub_Addr_unit_from", "type": "TEXT", "args": {"field_length": 25}},
            {"name": "i_sub_Addr_unit_to", "type": "TEXT", "args": {"field_length": 15}},
        ],

        update_logic=condo_update_logic,
        locator_func=create_locator_for_dataset,
        pre_process_func=pre_process,
    )
    register_fn(cfg)






            # "PointAddress.HOUSE_NUMBER {tblName}.house_number",
            # "PointAddress.STREET_PREFIX_DIR {tblName}.St_PreDir",
            # "PointAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp",
            # "PointAddress.STREET_NAME {tblName}.St_Name",
            # "PointAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp",
            # "PointAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir",
            # "PointAddress.FULL_STREET_NAME {tblName}.full_street_name",
            # "PointAddress.BUILDING_NAME {tblName}.Building",
            # # 'PointAddress.SUB_ADDRESS_BUILDING_UNIT {tblName}.Unit'
            # "PointAddress.SUB_ADDRESS_UNIT {tblName}.Unit",
            # "PointAddress.SUB_ADDRESS_LEVEL {tblName}.Floor",
            # "PointAddress.PARCEL_JOIN_ID {tblName}.i_gis_key",
            # "PointAddress.NEIGHBORHOOD {tblName}.Nbrhd_Comm",
            # "PointAddress.REGION_ABBR {tblName}.Prov_Abbriviation",
            # "PointAddress.COUNTRY {tblName}.Country",

            # "PointAddress.SUB_ADDRESS_UNIT {tblName}.Unit",
            # "PointAddress.SUB_ADDRESS_UNIT_FROM {tblName}.i_sub_Addr_unit_from",
            # "PointAddress.SUB_ADDRESS_UNIT_TO {tblName}.i_sub_Addr_unit_to",




    # return [f'PointAddress.HOUSE_NUMBER {tblName}.Add_Number',
    #         f'PointAddress.BUILDING_NAME {tblName}.Building',
    #         f'PointAddress.STREET_PREFIX_DIR {tblName}.St_PreDir',
    #         f'PointAddress.STREET_PREFIX_TYPE {tblName}.St_PreTyp',
    #         f'PointAddress.STREET_NAME {tblName}.St_Name',
    #         f'PointAddress.STREET_SUFFIX_TYPE {tblName}.St_PosTyp',
    #         f'PointAddress.STREET_SUFFIX_DIR {tblName}.St_PosDir',
    #         f'PointAddress.FULL_STREET_NAME {tblName}.FullStreetName',
    #         f'PointAddress.SUB_ADDRESS_UNIT {tblName}.Unit',
    #         f'PointAddress.SUB_ADDRESS_LEVEL {tblName}.Floor',
    #         f'PointAddress.PARCEL_JOIN_ID {tblName}.i_gis_key',
    #         f'PointAddress.NEIGHBORHOOD {tblName}.Nbrhd_Comm',
    #         f'PointAddress.CITY {tblName}.Inc_Muni',
    #         f'PointAddress.REGION {tblName}.State',
    #         f'PointAddress.REGION_ABBR {tblName}.Prov_Abbriviation',
    #         f'PointAddress.COUNTRY {tblName}.Country'
    #         ]

    # return [
    #     "PointAddress.FEATURE_ID SiteStructureAddressPoints.NGUID",
    #     # 'PointAddress.ADDRESS_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.HOUSE_NUMBER SiteStructureAddressPoints.Add_Number",
    #     # 'PointAddress.PARITY SiteStructureAddressPoints.NGUID',
    #     "PointAddress.BUILDING_NAME SiteStructureAddressPoints.Building",
    #     # 'PointAddress.STREET_NAME_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.STREET_PREFIX_DIR SiteStructureAddressPoints.St_PreDir",
    #     "PointAddress.STREET_PREFIX_TYPE SiteStructureAddressPoints.St_PreTyp",
    #     "PointAddress.STREET_NAME SiteStructureAddressPoints.St_Name",
    #     "PointAddress.STREET_SUFFIX_TYPE SiteStructureAddressPoints.St_PosTyp",
    #     "PointAddress.STREET_SUFFIX_DIR SiteStructureAddressPoints.St_PosDir",
    #     "PointAddress.FULL_STREET_NAME SiteStructureAddressPoints.FullStreetName",
    #     # 'PointAddress.PRIMARY_STREET_NAME_INDICATOR SiteStructureAddressPoints.NGUID',
    #     "PointAddress.SUB_ADDRESS_UNIT SiteStructureAddressPoints.Unit",

    #     "PointAddress.SUB_ADDRESS_UNIT_FROM SiteStructureAddressPoints.i_sub_Addr_unit_from",
    #     "PointAddress.SUB_ADDRESS_UNIT_TO SiteStructureAddressPoints.i_sub_Addr_unit_to",

    #     # 'PointAddress.HOUSE_NUMBER_FROM SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.HOUSE_NUMBER_TO SiteStructureAddressPoints.NGUID',
    #     "PointAddress.SUB_ADDRESS_BUILDING_UNIT SiteStructureAddressPoints.Building",
    #     "PointAddress.SUB_ADDRESS_BUILDING_UNIT_TYPE SiteStructureAddressPoints.BuildingType",

    #     "PointAddress.SUB_ADDRESS_UNIT_TYPE SiteStructureAddressPoints.i_Unit_Prefix",
    #     "PointAddress.SUB_ADDRESS_LEVEL SiteStructureAddressPoints.Floor",
    #     "PointAddress.SUB_ADDRESS_LEVEL_TYPE SiteStructureAddressPoints.LevelType",


    #     # 'PointAddress.SIDE SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.PARCEL_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.NEIGHBORHOOD_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.NEIGHBORHOOD SiteStructureAddressPoints.Nbrhd_Comm",
    #     # 'PointAddress.DISTRICT SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.CITY_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.CITY SiteStructureAddressPoints.Inc_Muni",
    #     # 'PointAddress.SUBREGION_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.SUBREGION SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.REGION_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.REGION SiteStructureAddressPoints.State",
    #     "PointAddress.REGION_ABBR SiteStructureAddressPoints.Prov_Abbriviation",
    #     # 'PointAddress.ZONE_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.ZONE SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.POSTAL_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.POSTAL SiteStructureAddressPoints.Post_Code",
    #     # 'PointAddress.POSTAL_EXT SiteStructureAddressPoints.NGUID',
    #     # 'PointAddress.COUNTRY_CODE SiteStructureAddressPoints.Country_Code',
    #     # 'PointAddress.COUNTRY_JOIN_ID SiteStructureAddressPoints.NGUID',
    #     "PointAddress.COUNTRY SiteStructureAddressPoints.Country",
    #     # 'PointAddress.LANG_CODE SiteStructureAddressPoints.NGUID'
    # ]



##### fields to add to SitestructureAddressPoints for condo logic:
# house_numbrer_from -> i_house_number_from
# house_number_to -> i_house_number_to

# sub_address_level -> i_sub_Addr_level
# sub_address_level_type -> i_sub_Addr_level_type

# sub_address_building_unit -> i_sub_Addr_building_unit
# sub_address_building_unit_type -> i_sub_Addr_building_unit_type

# sub_address_unit -> i_sub_Addr_unit
# sub_address_unit_type -> i_sub_Addr_unit_type


#### sub_address_unit_from -> i_sub_Addr_unit_from
#### sub_address_unit_to -> i_sub_Addr_unit_to

i_sub_Addr_unit_from
i_sub_Addr_unit_to