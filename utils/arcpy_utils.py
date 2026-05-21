#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
arcpy_utils.py - ArcGIS Geocoding Locator Service Builder

arcpy_utils.py
Generic ArcPy utilities for:
- SDE discovery
- SDE table path resolution
- FGDB creation
- backup rotation
- dataset copying (features + relationship tables)




arcpy.TestSchemaLock()


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = '2026-04-21 17:21:52'
###############################################################################

import os
import shutil
import arcpy
from pathlib import Path

# from build_locator import BASEDIR
from utils.MyLogging import logger
from pprint import pformat #,  pprint

import getPassword as getPassword


# ------------------------------------------------------------
# Discover SDE files
# ------------------------------------------------------------
def discover_sde_files(project_root: str) -> dict:
    sde_dir = os.path.join(project_root, "DatabasesForUse")
    sde_map = {}

    if not os.path.exists(sde_dir):
        raise FileNotFoundError(f"DatabasesForUse directory not found: {sde_dir}")

    for file in os.listdir(sde_dir):
        if file.lower().endswith(".sde"):
            key = os.path.splitext(file)[0].lower()
            sde_map[key] = os.path.join(sde_dir, file)

    return sde_map


# ------------------------------------------------------------
# Resolve table inside SDE
# ------------------------------------------------------------
def resolve_sde_table(sde_map: dict, sde_key: str, table_name: str) -> str:
    key = sde_key.lower()
    if key not in sde_map:
        raise KeyError(f"SDE '{sde_key}' not found in DatabasesForUse/")
    return os.path.join(sde_map[key], table_name)


# ------------------------------------------------------------
# Backup rotation
# ------------------------------------------------------------
def rotate_backups(base_path: str, max_versions: int = 9) -> None:
    print(f"Rotating Backups at: {base_path}")
    arcpy.env.workspace = None
    arcpy.ClearWorkspaceCache_management()

    base = Path(base_path).resolve()

    if base.suffix == ".gdb":
        base = base.with_suffix("")

    try:
        # 1. Delete only the oldest backup
        oldest = base.with_suffix(f".backups.{max_versions}.gdb")
        if oldest.exists():
            shutil.rmtree(oldest)

        # 2. Shift backups upward
        for i in range(max_versions - 1, 0, -1):
            src = base.with_suffix(f".backups.{i}.gdb")
            dst = base.with_suffix(f".backups.{i+1}.gdb")
            if src.exists():
                os.rename(src, dst)

        # 3. Move current FGDB to .backups.1.gdb
        current = base.with_suffix(".gdb")
        if current.exists():
            os.rename(current, base.with_suffix(".backups.1.gdb"))

    except Exception as e:
        print(f"Error: {e}")
        raise


# ------------------------------------------------------------
# FGDB creation
# ------------------------------------------------------------
def create_fgdb(base_path: str) -> str:
    arcpy.ClearWorkspaceCache_management()
    gdb_path = f"{base_path}.gdb"
    folder, name = os.path.split(gdb_path)

    if not os.path.exists(folder):
        os.makedirs(folder)

    arcpy.CreateFileGDB_management(folder, name)
    return gdb_path


# ------------------------------------------------------------
# Copy utilities
# ------------------------------------------------------------
def copy_features(full_path: str, fgdb: str, name: str) -> str:
    """
    Copy features from source to target FGDB.
    
    Args:
        full_path: Full path to source (SDE or local FGDB)
        fgdb: Target FGDB
        name: Output feature class name
    """
    arcpy.ClearWorkspaceCache_management()
    out_path = os.path.join(fgdb, name)
    # logger.tracef(f"Copying features from '{full_path}' to '{out_path}'")

    if not arcpy.Exists(full_path):
        raise FileNotFoundError(f"Source not found: {full_path}")

    arcpy.management.CopyFeatures(full_path, out_path)
    # logger.info(".... Copy Features Done.")
    return out_path


# ------------------------------------------------------------
def copy_table(full_path: str, fgdb: str, name: str) -> str:
    """
    Copy table from source to target FGDB.
    
    Args:
        full_path: Full path to source (SDE or local FGDB)
        fgdb: Target FGDB
        name: Output table name
    """
    arcpy.ClearWorkspaceCache_management()
    out_path = os.path.join(fgdb, name)
    logger.tracef(f"Copying table from '{full_path}' to '{out_path}'")

    if not arcpy.Exists(full_path):
        raise FileNotFoundError(f"Source not found: {full_path}")

    arcpy.conversion.TableToTable(full_path, fgdb, name)
    logger.info(".... Copy TableToTable Done.")
    return out_path



# ------------------------------------------------------------
# most arcpy functions return a Result object that can be used to check status and messages
# ------------------------------------------------------------
def giveArcpyResults(r, txt=""):
    # Always print ArcPy messages
    msgs = arcpy.GetMessages()
    # logger.debug(f"ArcPy messages for {txt}:\n{msgs}")

    # If r is None, this was a geocoding tool
    if r is None:
        # Detect failure by scanning messages

        if "ERROR" in msgs.upper():
            logger.error(f"{txt} - ArcPy reported an error")
            logger.warning(msgs)
        else:
            logger.info(f"{txt} - Completed (geocoding tool returned no Result object)")
            logger.warning(msgs)
        return

    # If r is a real Result object
    statusCode = {
        0: "New", 1: "Submitted", 2: "Waiting", 3: "Executing",
        4: "Succeeded", 5: "Failed", 6: "Timed out", 7: "Cancelling",
        8: "Cancelled", 9: "Deleting", 10: "Deleted",
    }

    status = r.status
    logger.warning(f"{txt} - Result Status={status} - {statusCode.get(status, 'Unknown')}")
    # logger.mark7()

    for idx in range(r.messageCount):
        logger.warning(f"Message {idx}: {r.getMessage(idx)}")
    # logger.mark8()

    for idx in range(r.outputCount):
        logger.warning(f"Output {idx}: {r.getOutput(idx)}")
    # logger.mark9()



# ------------------------------------------------------------
# Show the fields of a table
# ------------------------------------------------------------
def show_fields_of_table( table):
        # table ='D:/City_STUFF/Create_Locator_v4/copyOfMasterData.gdb/SiteStructureAddressPoints'
        # table ='D:/City_STUFF/Create_Locator_v4/copyOfMasterData.gdb/Parcel_Calc_Address_CityWorks_WORKING'
    fields = arcpy.ListFields(table)

    print('SiteStructureAddressPoints')
    for field in fields:
        print(f"         '{field.name}',")
    print('------------------------------------------------')



# ------------------------------------------------------------
# dump all the describe attribs
# ------------------------------------------------------------
def describe_all(path):
    d = arcpy.Describe(path)
    props = {}

    for attr in dir(d):
        # Skip private and methods
        if attr.startswith("_"):
            continue

        try:
            value = getattr(d, attr)
        except Exception:
            continue

        # Skip methods
        if callable(value):
            continue

        props[attr] = value

    return props

# ------------------------------------------------------------
def print_describe(path):
    logger.mark9()
    logger.mark6()
    x = arcpy.Describe(path)
    inspect_object( x)
    logger.mark9()

    # Try locator properties first
    try:
        props = arcpy.geocoding.GetLocatorProperties(path)
        if props:
            print("\nLocator properties:\n")
        else:
            print("\nLocator has no properties. Falling back to Describe.\n")
            props = describe_all(path)
    except Exception:
        props = describe_all(path)

    print(f"Describe properties for: {path}\n")
    for k, v in sorted(props.items()):
        print(f"{k:25} : {v}")

    logger.mark9()



# ------------------------------------------------------------
def inspect_object(obj):
    methods = []
    variables = []

    for name in dir(obj):
        if name.startswith("_"):
            continue  # skip private/magic

        try:
            value = getattr(obj, name)
        except Exception:
            continue  # unreadable attribute

        if callable(value):
            methods.append(name)
        else:
            variables.append((name, value))

    return methods, variables

# ------------------------------------------------------------
def debug_describe(path):
    logger.mark8()
    logger.mark7()


    print("Exists:", arcpy.Exists(path))
    print("Describe:", arcpy.Describe(path))
    print("DataType:", getattr(arcpy.Describe(path), "dataType", "<none>"))
    print("CatalogPath:", getattr(arcpy.Describe(path), "catalogPath", "<none>"))
    logger.mark7()

    d = arcpy.Describe(path)

    print("\n=== RAW DIR() OUTPUT ===")
    for attr in dir(d):
        print(attr)

    print("\n=== ATTRIBUTE PROBE ===")
    for attr in dir(d):
        if attr.startswith("_"):
            continue

        try:
            val = getattr(d, attr)
            print(f"{attr:25} : {val!r}")
        except Exception as e:
            print(f"{attr:25} : <ERROR: {e}>")
    logger.mark8()


# ------------------------------------------------------------
def create_new_copy_of_FeatureClass( src, dst_gdb, dst_name):

    desc = arcpy.Describe(src)
    logger.traceg(pformat(desc))
    
    logger.tracef(f"{dst_gdb}{os.sep}{dst_name}")
    arcpy.management.CreateFeatureclass(
        out_path=dst_gdb,
        out_name=dst_name,
        geometry_type=desc.shapeType,
        spatial_reference=desc.spatialReference
    )

    for f in desc.fields:
        if f.type not in ("OID", "Geometry"):
            arcpy.management.AddField(
                in_table=f"{dst_gdb}{os.sep}{dst_name}",
                field_name=f.name,
                field_type=f.type,
                field_length=f.length
            )


#-----------------------------------------------------------------
""" get the password from getPassword and the 2 ini files """
def retrievePassword( whichDB ):
    arg= ['5_MakeBackupsOfProduction.py', whichDB]
    return getPassword.main(arg)



#-----------------------------------------------------------------
def createAllSDEfiles(SDEfiles = None, BaseDir = None):

    if SDEfiles is None:
        SDEfiles = os.path.join(BaseDir, "DatabasesForUse")


    # the database name (using full name to be accurate)
    #   and the user account
    DICT_of_SDE ={'gis_DynamicGeneral_prd4': "SDE",
                    'NextGen911_Current': "SDE",
                    # 'gis_DynamicAssets_prd4': "SDE",
                    # 'gis_StaticGeneral_prd4': "SDE",
                    # 'gis_StaticAssets_prd4': "SDE",
                    # 'GIS_SandBoxNRCan_prd4': "SDE",
                    # 'gis_SandBoxA_prd4': "SDE",
                    # 'gis_SandBoxB_prd4': "SDE",
                    # 'gis_SandBoxC_prd4': "SDE",
                    # 'GlobalAttachmentRepository': "SDE",
                    }
    try:
        for db, un in DICT_of_SDE.items():
            # logger.tracek( f"{SDEfiles}")
            logger.tracek( f'{db}.sde')

            pw = retrievePassword( db )  ## get the password from the 2 ini files
            logger.tracei( f"db: {db}")

            if os.path.exists( SDEfiles + f'{os.sep}{db}.sde'):
                os.remove(  SDEfiles + f'{os.sep}{db}.sde')

            arcpy.CreateDatabaseConnection_management(
                    SDEfiles + os.sep,
                    f'{db}.sde',
                    "SQL_SERVER",
                    'vm-db-prd4',
                    "DATABASE_AUTH",
                    un,
                    pw,
                    "SAVE_USERNAME",
                    db,
                    '#',
                    '#', # "TRANSACTIONAL" #,
                    # "sde.DEFAULT"
                    )
        logger.tracef(f"Created all the SDE files in {SDEfiles}")

    except arcpy.ExecuteError as e:
        print(f"<ERROR: {e}>")
    except Exception  as e:
        print(f"<ERROR: {e}>")

