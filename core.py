#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
core.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\core.py



"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = "2026-05-01 14:55:49"
###############################################################################

# import argparse
# import logging
# from math import log
# from tempfile import template
# from unittest import result

# import itertools
from typing import Callable
# import time
from pathlib import Path
from typing import  Dict, List, Optional   #, Tuple, Any, Callable
# import shutil
import traceback
# import sys
import os
# from enum import Enum

from pprint import  pformat #pprint,
from dataclasses import dataclass, field, asdict

import pkgutil
import importlib

from utils.MyLogging import logger
# from utils.MySettings import MySettings

import arcpy

from utils.arcpy_utils import (
    resolve_sde_table,
    copy_features,
    copy_table,
    rotate_backups,
    create_fgdb,
    giveArcpyResults,
    # describe_all,
    # print_describe,
    # debug_describe,
    # createAllSDEfiles,
)

# arcpy.SetMessageLevels(['COMMANDSYNTAX'])
arcpy.SetMessageLevels(["NORMAL"])
# arcpy.SetMessageLevels(["DIAGNOSTICS"])



# ============================================================
# 1. Context (DI)
# ============================================================
@dataclass
class Context:
    project_root: str
    fgdb_base: str
    fgdb: str = ""
    sde_map: dict = field(default_factory=dict)
    # env: Dict[str, Any] = field(default_factory=dict)
    locator_dir: str = ""
    use_local_gdb: bool = False
    local_gdb: str = ""

    # ------------------------------------------------------------
    def __str__(self) -> str:
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        RESET = "\033[0m"

        data = asdict(self)
        # longest = max(len(k) for k in data)
        # longest = 20
        lines = ["Context:"]
        for key, value in data.items():
            display = value if value not in ("", None, {}, []) else "None"

            if isinstance(value, dict):
                pretty = pformat(display, indent=4)
                lines.append( f"     {CYAN}{key:20}{RESET} =\n{GREEN}{pretty}{RESET}")
            else:
                lines.append(f"  {CYAN}{key:20}{RESET} = {GREEN}{display}{RESET}")

                # lines.append(f"  {CYAN}{key.ljust(longest)}{RESET} = {GREEN}{value}{RESET}")
        return "\n".join(lines)


# ============================================================
# 2. DatasetConfig
# ============================================================
@dataclass
class DatasetConfig:
    name: str
    sde: str
    tbl: str
    local_name: str
    role: str
    fc:str = ""
    src_fc:str = ""

    pre_process_func: Optional[Callable[["DatasetConfig", Context], None]] = None
    process_func: Optional[Callable[["DatasetConfig", Context], None]] = None
    locator_func: Optional[Callable[["DatasetConfig", Context], None]] = None

    field_mapping_templates: List[str] = field(default_factory=list)
    add_fields: List[Dict] = field(default_factory=list)
    update_logic: Optional[Callable[[Dict], Dict]] = None
    is_relationship: bool = False
    alt_tables: str | None = None


    # sde_db: str = ""
    # src_fc : str = ""
    created_locator_path: str = ""

    field_mapping_string:str = "XXXXXXXXXXXXXXXXXXXXXX"



    # ============================================================
    def pre_process(self,  ctx: Context) -> None:
        # logger.tracef(f"Pre-processing dataset '{cfg.name}'")
        if self.pre_process_func:
            self.pre_process_func(self, ctx)
        else:
            logger.tracec(pformat(self))
            logger.tracec(pformat(ctx))


    # ---------------------------------------------------------
    # Materialize SDE → FGDB
    # ---------------------------------------------------------
    def materialize(self, ctx: Context) -> str:
        print(
            f"Materializing dataset '{self.name}' from SDE '{self.sde}' table '{self.tbl}'"
        )

        # full_sde_path = resolve_sde_table(ctx.sde_map, self.sde, self.tbl)

        # Determine source path
        if ctx.use_local_gdb:
            # Use local FGDB
            full_path = os.path.join(ctx.local_gdb, self.tbl)
            logger.info(f"Using LOCAL source: {full_path}")
        else:
            # Use SDE
            full_path = resolve_sde_table(ctx.sde_map, self.sde, self.tbl)
            logger.info(f"Using SDE source: {full_path}")

        if self.is_relationship:
            return copy_table(full_path, ctx.fgdb, self.local_name)

        return copy_features(full_path, ctx.fgdb, self.local_name)

    # ---------------------------------------------------------
    # Correct table() method
    # ---------------------------------------------------------
    def table(self, ctx: Context) -> str:
        return os.path.join(ctx.fgdb, self.local_name)

    # ---------------------------------------------------------
    def process(self, ctx: Context) -> None:
        print(f"Processing dataset '{self.name}'")
        if self.process_func:
            self.process_func(self, ctx)

    # ---------------------------------------------------------
    def apply_schema_changes(self, ctx: Context) -> None:
        # logger.tracef(f"Applying schema changes for dataset '{self.name}'")
        existing = {f.name for f in arcpy.ListFields(self.table(ctx))}
        for fld in self.add_fields:
            name = fld["name"]
            ftype = fld["type"]
            args = fld.get("args", {})
            if name not in existing:
                # logger.tracef(
                #     f"Adding field '{name}' of type '{ftype}' to dataset '{self.name}' with args {args}"
                # )
                arcpy.AddField_management(self.table(ctx), name, ftype, **args)

    # ---------------------------------------------------------
    def apply_updates(self, ctx: Context) -> None:
        # logger.tracef(f"Applying updates for dataset '{self.name}'")
        if not self.update_logic:
            return

        try:
            fields = list(self.update_logic({"__fields__": True}).keys())
            # all_fields = [f.name for f in arcpy.ListFields(self.table(ctx))]
            # ✅ Add counter
            # MAX_ROWS = 25
            # counter =0

            # ✅ DEBUG: Print all available fields
            # logger.debug(f"UPDATE FIELDS requested: {fields}")
            # logger.debug(f"ALL FIELDS in table: {all_fields}")

            # ✅ Check if PIN exists
            # if "PIN" not in all_fields:
            #     logger.error(f"PIN field not found! Available fields: {all_fields}")
            #     raise ValueError("PIN field missing from table")

            # logger.traceu(f"{fields}")
            logger.tracek(f"Applying updates to dataset '{self.table(ctx)}' ")  # using fields: {fields}")
            with arcpy.da.UpdateCursor(self.table(ctx), fields) as cursor:
                for row in cursor:
                    row_dict = dict(zip(fields, row))
                    # if not row_dict.get('PIN', None):
                    #     continue

                    # if  row_dict.get('Street', None):
                    #     counter +=1
                    # print(f"{counter=}")
                    # if counter> MAX_ROWS:
                    #     break

                    new_values = self.update_logic(row_dict)
                    # logger.traceg("Updating row with values: ")
                    logger.traceh(pformat(new_values))
                    # logger.tracei(pformat(row_dict))

                    if new_values is not None:
                        # logger.traced(f"Updating row with values: {new_values}  \n OLD VALUES: {row_dict}  ")
                        cursor.updateRow([new_values[f] for f in fields])

        except Exception as e:
            logger.error(f"Error apply updates for dataset {e}")
            giveArcpyResults(None, f"apply updates for {self.table(ctx)}")
            traceback.print_exc()
            raise

    # ---------------------------------------------------------
    def build_mapping_strings(self) -> List[str]:
        logger.tracef(f"Building field mapping strings for dataset '{self.name}'")
        return [
            template.format(tblName=self.local_name)
            for template in self.field_mapping_templates
        ]

    # ---------------------------------------------------------
    def build_field_mappings(self, ctx: Context) -> arcpy.FieldMappings:
        # logger.tracef(f"Building field mappings for dataset '{self.name}'")
        fm = arcpy.FieldMappings()
        existing = {f.name for f in arcpy.ListFields(self.table(ctx))}

        for mapping_str in self.build_mapping_strings():
            logger.traceq(f"Processing mapping template: '{mapping_str}'")
            target, source = mapping_str.split()
            _, target_field = target.split(".")
            src_table, src_field = source.split(".")

            if src_field not in existing:
                raise ValueError(
                    f"[{self.name}] Source field '{src_field}' not found in {self.table(ctx)}"
                )

            f_map = arcpy.FieldMap()
            f_map.addInputField(self.table(ctx), src_field)
            out_field = f_map.outputField
            out_field.name = target_field
            f_map.outputField = out_field
            fm.addFieldMap(f_map)
            logger.tracea(f"{f_map=}")

        logger.traceu(
            f"Built field mappings for dataset '{self.name}': {[fm.getFieldMap(i).outputField.name for i in range(fm.fieldCount)]}"
        )
        return fm

    # ---------------------------------------------------------
    def build_field_mapping_string(self, ctx: Context) -> str:
        parts = []
        for mapping_str in self.build_mapping_strings():
            parts.append(mapping_str)
        return " ; ".join(parts) +" ; "

    # ---------------------------------------------------------
    def create_locator(self, ctx: Context) -> str:
        logger.tracef(f"Creating locator for dataset '{self.name}'")

        # Default to create_locator_for_dataset if locator_func is None
        func = self.locator_func or create_locator_for_dataset

        return func(self, ctx)

    # ---------------------------------------------------------
    def run_all(self, ctx: Context) -> None:
        print('*^' * 20, f"Running all steps for dataset '{self.name}'", '*-' * 20)
        self.pre_process(ctx)
        # print('*1' * 60)
        self.materialize(ctx)
        # print('*2' * 60)
        self.process(ctx)
        # print('*3' * 60)
        self.apply_schema_changes(ctx)
        # print('*4' * 60)
        self.apply_updates(ctx)
        # print('*5' * 60)
        self.create_locator(ctx)
        # print('*6' * 60)



# ============================================================
# def inspect_locator():
#     # After building the locator, inspect its fields
#     try:
#         import arcpy.da

#         # Get the locator's properties
#         desc = arcpy.Describe(component_locators[0])

#         # List available fields (if possible)
#         logger.info(f"Attempting to describe locator properties...")

#         # Try to get field information
#         if hasattr(desc, 'fields'):
#             logger.info(f"Locator fields: {[f.name for f in desc.fields]}")

#         # Alternative: Try using the geocoding module
#         logger.info(f"Locator properties available:")
#         for prop in dir(desc):
#             if not prop.startswith('_'):
#                 try:
#                     val = getattr(desc, prop)
#                     if not callable(val):
#                         logger.info(f"  {prop}: {val}")
#                 except:
#                     pass

#     except Exception as e:
#         logger.error(f"Could not inspect locator: {e}")


# ============================================================
# 3. Locator helpers
# ============================================================
def create_locator_for_dataset(cfg: DatasetConfig, ctx: Context) -> str:
    print(f"Creating locator for dataset '{cfg.name}'")

    try:
        # locator_name = f"{cfg.name}_locator"
        locator_name = f"{cfg.name}_l"
        out_path = os.path.join(ctx.locator_dir, locator_name + ".loc")

        # Check and delete the FULL PATH, not just the name
        if arcpy.Exists(out_path):
            logger.debug(f"Deleting existing locator: {out_path}")
            arcpy.management.Delete(out_path)

        logger.debug(f"Locator name: {locator_name}")
        logger.debug(f"Output locator path: {out_path}")

        field_mappings_str = cfg.build_field_mapping_string(ctx)
        # logger.tracej(f"Field mappings: {field_mappings_str}")
        cfg.field_mapping_string =  field_mappings_str

        # logger.tracet(f"{cfg=}")

        # Create the locator
        result = arcpy.geocoding.CreateLocator(
            country_code="CAN",
            primary_reference_data=f"{cfg.table(ctx)} {cfg.role}",
            field_mapping=field_mappings_str,
            out_locator=out_path,
            language_code="ENG",
            alternatename_tables=cfg.alt_tables,
            alternate_field_mapping=None,
            custom_output_fields=None,
            precision_type="LOCAL_EXTRA_HIGH",
        )

        # Log the results
        giveArcpyResults(result, f"CreateLocator for {cfg.name}")

        # Store the created locator path
        cfg.created_locator_path = out_path

        logger.debug(f"CreateLocator for '{cfg.name}' completed successfully")
        logger.mark1()

    except Exception as e:
        logger.error(f"Error creating locator for dataset '{cfg.name}': {e}")
        giveArcpyResults(None, f"CreateLocator for {cfg.name}")
        traceback.print_exc()
        raise

    return out_path



# -----------------------------------------------------------------
def create_composite_locator(ctx: Context, name: str, datasets: list[DatasetConfig]) -> str:
    """
    Create a composite locator from multiple component locators.
    If only one locator exists, returns it directly without creating a composite.
    """
    logger.tracef(f"Creating composite locator '{name}' from datasets {[d.name for d in datasets]}")

    out_path = os.path.join(ctx.locator_dir, name + ".loc")

    # Remove existing composite if it exists
    if os.path.exists(out_path):
        logger.debug(f"Removing existing composite locator: {out_path}")
        try:
            os.remove(out_path)
        except Exception as e:
            logger.warning(f"Could not remove existing composite: {e}")

    # Collect component locators
    component_locators = []
    for ds in datasets:
        if ds.created_locator_path and os.path.exists(ds.created_locator_path):
            component_locators.append(ds.created_locator_path)
        else:
            logger.warning(f"Locator not found for dataset {ds.name}")

    if not component_locators:
        raise ValueError("No valid component locators found")

    logger.info(f"Creating composite from {len(component_locators)} locators:")
    for loc in component_locators:
        logger.info(f"  - {os.path.basename(loc)}")

    # ✅ SOLUTION 3: If only one locator, skip composite creation
    if len(component_locators) == 1:
        logger.info("Only one locator found - no composite needed")
        logger.info(f"Using locator directly: {component_locators[0]}")
        return component_locators[0]

    # ✅ SOLUTION 1: Inspect the first locator to see what fields it has
    try:
        desc = arcpy.Describe(component_locators[0])
        # print_describe(component_locators[0])
        logger.traceu(f"Locator type: {desc.dataType}")
        logger.traceu(f"Locator catalogPath: {desc.catalogPath}")

        # Try to get field information
        if hasattr(desc, 'fields'):
            available_fields = [f.name for f in desc.fields]
            logger.info(f"Locator has {len(available_fields)} fields: {available_fields}")
        else:
            logger.debug("Locator does not expose 'fields' property")

    except Exception as e:
        logger.warning(f"Could not fully inspect locator: {e}")

    # Build locator names for field map (must match ArcGIS internal truncation)
    actual_names = []
    for loc_path in component_locators:
        basename = os.path.basename(loc_path)

        # Remove .loc extension
        if basename.endswith('.loc'):
            basename = basename[:-4]

        # ArcGIS truncates to 14 characters for composite locator field maps
        truncated_name = basename[:14]
        actual_names.append(truncated_name)
        logger.debug(f"Locator: '{os.path.basename(loc_path)}' -> Field map name: '{truncated_name}'")

    logger.debug(f"All locator names for field map: {actual_names}")

    # All locators string (space-separated)
    all_locators_str = " ".join(actual_names)

    # ✅ SOLUTION 2: Build field map
    # Try different field mapping strategies based on locator roles

    # Strategy A: Standard composite locator fields (for StreetAddress/PointAddress)
    standard_fields = [
        'Address',
        'Address2',
        'Address3',
        'Neighborhood',
        'City',
        'Subregion',
        'Region',
        'Postal',
        'PostalExt',
        'CountryCode'
    ]

    logger.tracex(f"{standard_fields=}")

    # Strategy B: Minimal fields (for Parcel or other roles)
    minimal_fields = [
        'City',
        'Region',
        # 'Postal',
        # 'CountryCode'
        ]

    # Determine which roles we have
    roles = [ds.role for ds in datasets]
    logger.debug(f"Component locator roles: {roles}")

    # Choose field mapping strategy based on roles
    if 'Parcel' in roles and len(roles) == 1:
        # Only Parcel role - use minimal fields or try empty
        logger.info("Detected Parcel-only composite - using minimal field mapping")
        output_fields = minimal_fields
    else:
        # Mixed roles or StreetAddress/PointAddress - use standard fields
        logger.info("Using standard composite field mapping")
        output_fields = standard_fields

    # Build field map
    field_map_parts = [f"'{field}' {all_locators_str}" for field in output_fields]
    field_map = ";".join(field_map_parts)

    logger.traces(f"Field map: {field_map}")

    try:
        # Use semicolon-separated list of FULL PATHS
        in_locators = ";".join(component_locators)

        logger.info("Calling CreateCompositeAddressLocator...")
        logger.tracet(f"  in_address_locators: {in_locators}")
        logger.tracet(f"  in_field_map: {field_map}")
        logger.tracet(f"  out_composite_address_locator: {out_path}")

        result = arcpy.geocoding.CreateCompositeAddressLocator(
            in_address_locators=in_locators,
            in_field_map=field_map,
            in_selection_criteria="",  # Empty = use all locators with equal priority
            out_composite_address_locator=out_path
        )

        giveArcpyResults(result, f"CreateCompositeAddressLocator for {name}")
        logger.info(f"Composite locator created successfully: {out_path}")
        return out_path

    except arcpy.ExecuteError as e:
        error_msg = str(e)
        logger.error(f"ArcPy ExecuteError creating composite locator: {error_msg}")

        # If standard fields failed and we haven't tried minimal yet, try minimal
        if output_fields == standard_fields and 'not been mapped' in error_msg:
            logger.warning("Standard field mapping failed - trying minimal field mapping...")
            logger.tracey(f"{minimal_fields=}")
            try:
                minimal_map_parts = [f"'{field}' {all_locators_str}" for field in minimal_fields]
                minimal_map = ";".join(minimal_map_parts)
                logger.tracer(f"Minimal field map: {minimal_map}")

                result = arcpy.geocoding.CreateCompositeAddressLocator(
                    in_address_locators=in_locators,
                    # in_field_map=minimal_map,
                    in_field_map="parcels_l.PARCEL_NAME",
                    in_selection_criteria="",
                    out_composite_address_locator=out_path,
                    version_compatibility="V3_0_TO_3_3"
                )

                giveArcpyResults(result, f"CreateCompositeAddressLocator for {name} (minimal)")
                logger.info(f"Composite locator created with minimal mapping: {out_path}")
                return out_path

            except Exception as e2:
                logger.error(f"Minimal field mapping also failed: {e2}")

        giveArcpyResults(None, f"CreateCompositeAddressLocator for {name}")
        raise

    except Exception as e:
        logger.error(f"Failed to create composite locator: {e}")
        giveArcpyResults(None, f"CreateCompositeAddressLocator for {name}")
        raise
# ```

# ## Key Changes:

# 1. **Truncate locator names to 13 characters** (ArcGIS limitation)
# 2. **Map ALL 10 required output fields** (not just 5)
# 3. **Each field maps to ALL input locators**

# The field map should look like:
# ```
# 'Address' parcels_locat;'Address2' parcels_locat;'Address3' parcels_locat;'Neighborhood' parcels_locat;'City' parcels_locat;'Subregion' parcels_locat;'Region' parcels_locat;'Postal' parcels_locat;'PostalExt' parcels_locat;'CountryCode' parcels_locat





# -----------------------------------------------------------------
def create_composite_locator_OLD(
    ctx: Context, locator_name: str, datasets: List[DatasetConfig]
) -> str:
    logger.tracef(
        f"Creating composite locator '{locator_name}' from datasets {[d.name for d in datasets]}"
    )

    # Collect locator paths
    component_locators = [
        cfg.created_locator_path
        for cfg in datasets
        if cfg.created_locator_path and os.path.exists(cfg.created_locator_path)
    ]

    if not component_locators:
        logger.error("No locators to combine!")
        return ""

    out_path = os.path.join(ctx.locator_dir, locator_name + ".loc")

    logger.info(f"Creating composite from {len(component_locators)} locators:")
    for loc in component_locators:
        logger.info(f"  - {os.path.basename(loc)}")

    try:
        # Build field map - each output field needs to list ALL input locators that can provide it
        # Format: "output_field input_locator1 input_locator2 input_locator3"

        # Get locator names (without .loc extension)
        locator_names = [
            os.path.basename(loc).replace(".loc", "") for loc in component_locators
        ]
        all_locators_str = " ".join(locator_names)

        # Standard output fields that all locators provide
        output_fields = [
            "Address",
            # 'Address2',
            # 'Address3',
            "Neighborhood",
            "City",
            # 'Subregion',
            "Region",
            # 'Postal',
            # 'PostalExt',
            "CountryCode",
        ]

        # Build field map: each output field can use any input locator
        field_map_parts = []
        for field in output_fields:
            # Format: "'Field' locator1 locator2 locator3"
            field_map_parts.append(f"'{field}' {all_locators_str}")

        field_map = ";".join(field_map_parts)

        logger.debug(f"Field map: {field_map}")

        result = arcpy.geocoding.CreateCompositeAddressLocator(
            in_address_locators=";".join(component_locators),
            in_field_map=field_map,
            in_selection_criteria="",  # Empty means use all locators
            out_composite_address_locator=out_path,
        )

        giveArcpyResults(result, "CreateCompositeAddressLocator")
        logger.info(f"Composite locator created: {out_path}")

    except Exception as e:
        logger.error(f"Failed to create composite locator: {e}")
        traceback.print_exc()
        raise

    return out_path


"""

## **Example Field Map Output:**

For 3 locators (address_points, streets, city_boundary), the field map would be:
```
'Address' address_points_locator streets_locator city_boundary_locator;
'Address2' address_points_locator streets_locator city_boundary_locator;
'Address3' address_points_locator streets_locator city_boundary_locator;
'Neighborhood' address_points_locator streets_locator city_boundary_locator;
...
"""
# ============================================================
# 4. Plugin registry + discovery
# ============================================================
REGISTRY: Dict[str, DatasetConfig] = {}


# -----------------------------------------------------------------
def register_dataset(cfg: DatasetConfig) -> None:
    REGISTRY[cfg.name] = cfg


# -----------------------------------------------------------------
def discover_plugins(package: str, ctx:Context) -> None:
    plugin_path = Path(package)
    if not plugin_path.exists():
        logger.warning(f"Plugin directory does not exist: {plugin_path}")
        return

    pkg = importlib.import_module(package)
    for _, mod_name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if is_pkg:
            continue
        module = importlib.import_module(f"{package}.{mod_name}")
        if hasattr(module, "register"):
            print(f"   Registering dataset from plugin: {mod_name}")
            module.register(register_dataset, ctx)




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





# -----------------------------------------------------------------
def create_multi_combo_locator( ctx: Context, name:str, datasets: list[DatasetConfig]) -> str:
    logger.tracef(f"Create Combo_locator '{name}  from datasets {[d.name for d in datasets]}")

    out_path = os.path.join(ctx.locator_dir, name + ".loc")
    # Remove existing composite if it exists
    if os.path.exists(out_path):
        logger.debug(f"Removing existing composite locator: {out_path}")
        try:
            os.remove(out_path)
        except Exception as e:
            logger.warning(f"Could not remove existing composite: {e}")


    logger.mark4()
    print(f"{ctx}")

    #datasets = list(REGISTRY.values())


    ref_data= ""
    fld_mapping = ""
    for ds in datasets:
        logger.traceu(pformat(ds))

        # ref_data += ds.role+ " " +  os.path.join(ctx.fgdb,  ds.tbl) + "; "
        # datasets.fgdb+ "\" + ds.tbl + " " + ds.role
        ref_data += f"{ds.table(ctx)} {ds.role} ;"
        # f"{cfg.table(ctx)} {cfg.role}",
        fld_mapping += ds.field_mapping_string
        print()

    logger.trace(f"{ref_data}")

    logger.tracei(pformat(ref_data))
    logger.tracew(pformat(fld_mapping))
    logger.tracex(f"{out_path}")
    
    
    try:
        result = arcpy.geocoding.CreateLocator(
            country_code = "CAN",
            primary_reference_data = ref_data,
            field_mapping = fld_mapping,
            out_locator= out_path,
            language_code="ENG",
            alternatename_tables=None,
            alternate_field_mapping=None,
            custom_output_fields=None,
            precision_type="LOCAL_EXTRA_HIGH",
            version_compatibility="V3_0_TO_3_3"
        )
        giveArcpyResults(result, f"CreateCompositeAddressLocator for {name} (minimal)")
        logger.info(f"Composite locator created with minimal mapping: {out_path}")
        return out_path

    except Exception as e:
        logger.error(f"Failed to create composite locator: {e}")
        giveArcpyResults(None, f"CreateCompositeAddressLocator for {name}")
        raise

