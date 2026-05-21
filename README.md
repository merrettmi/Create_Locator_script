# Some docs on Create_locator (v4)
---

## Important things to Note:
* Condos and Trailer parks:
  * trailer parks need a bounding parcel that can be used to group all the addresses and extract a min and max unit numbers - the bounding box must be in parcels_unsurveyed -- REMARKS field must contain the word "TRAILER" and NOT have "STALL" in the field DESIGNATOR
  * Condos - assumes that every condo has a "common area" or "master" which is a bounding pologon (not from basename Condos but in Land Records) again for grouping of the condos (min and max)
  * untested is if the "Unit numbers" are mixed digits and letters - it shouldnt happen but not tested for or against


## Command line options:
        usage: build_locator.py [-h][--all] [--list] --fgdb-base FGDB_BASE [--project-root PROJECT_ROOT] [--dataset DATASET] [--local_gdb LOCAL_GDB] [--use-local-gdb]

* --all - run all the plugins and then buld a combo locator
* --list - show the list of plugins
* --project-root DIR  - so it know where the program is being run from
* --dataset DATASET  - where to get the data from (can be an SDE file or a path to a fileGDB )
* --local_gdb LOCAL_GDB - the name of the FGDB file to use


**Examples:**
  - build_locator.py  --all --fgdb-base "D:\City_STUFF\Create_Locator_v4\resulting_locators" --project-root "D:\City_STUFF\Create_Locator_v4"
      - use the SDE fiels for the data

    - build_locator.py --all --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
        - use the current directory and use a FGDB (a LOT faster) instead of the SDE database tables

    - build_locator.py" --dataset parcels --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
        - this only processes the dataset "parcels" - assuming the plugin exists
        - this line also uses a local FGDB for off network performance (i.e. working remote instead of copying a LOT of data over slow network)

---

## Individual locators -- plugins
* located in the "./plugins" directory
* each plugin is a definition of one of the locators
* the combined locator is generated when "--all" is passed to the script


### simple layout:
```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
yukon.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\yukon.py


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-03-12 18:41:11"
###############################################################################

from core import DatasetConfig, create_locator_for_dataset


# -----------------------------------------------------------------
def register(register_fn):
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
```

### Complex Layout - where everything is customizable

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
parcels.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\plugins\parcels.py


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-03-12 00:18:04"
###############################################################################

import arcpy
from datetime import datetime

from utils.MyLogging import logger
from core import DatasetConfig, create_locator_for_dataset

import traceback

from utils.arcpy_utils import (
    giveArcpyResults,
)


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
def register(register_fn):
    global SSAP_LOOKUP

    # Load lookup ONCE here — NOT at import time
    SSAP_LOOKUP = load_ssap_lookup(
        r"D:\City_STUFF\Create_Locator_v4\copyOfMasterData.gdb\SiteStructureAddressPoints"
    )

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
```



## The rest of the code:

* build_locator.py - main()
  * has the main start up code
  * parses the command line options
  * reads the plugins
  * makes a backup of the results FGDB (the modified tables)
  * starts the processing -- of the one file passed or of all
* core.py
  * runs all the different commands materialize, process, apply_schema_changes, apply_updates and create_locator
  * if all is passed then it will also run the build combo locator
```
    def run_all(self, ctx: Context) -> None:
        self.materialize(ctx)
        self.process(ctx)
        self.apply_schema_changes(ctx)
        self.apply_updates(ctx)
        self.create_locator(ctx)
```
```
    # ============================================================
    # 5. Master build_all
    # ============================================================
    def build_all(ctx: Context, composite_name: str = "WhitehorseComposite") -> str:
        rotate_backups(ctx.fgdb_base)
        ctx.fgdb = create_fgdb(ctx.fgdb_base)

        discover_plugins("plugins")

        datasets = list(REGISTRY.values())
        for cfg in datasets:
            logger.info(f"Building dataset: {cfg.name}")
            cfg.run_all(ctx)

        return create_composite_locator(ctx, composite_name, datasets)

```



## Debugging the code
* use the command line to run one dataset plugin at a time until they are all working
* Mike's logger setup is available so you can do things like:
  * logger.tracea(f" some message {someVar}")
    * there are more custom logger statements that use different colors to help identify where the code you are looking at is
* use the local FGDB while testing
  * create the local FGDB by copying the tables (from the plugins) to a local FGDB
  * see command line options above to use this file"# Create_Locator_script" 
