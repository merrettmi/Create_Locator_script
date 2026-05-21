#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
r"""
build_locator.py - ArcGIS Geocoding Locator Service Builder
D:\City_STUFF\Create_Locator_v4\build_locator.py
D:\City_STUFF\Create_Locator_v4\build_locator.py


"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = '2026-04-21 15:48:16'
###############################################################################

import argparse
# import logging
# from tempfile import template
# from unittest import result

import itertools
# from time import perf_counter
from datetime import datetime

from pathlib import Path

import os

from pprint import pprint
from utils.MySettings import MySettings

from utils.arcpy_utils import createAllSDEfiles, discover_sde_files

from core import (
    Context,
    REGISTRY,
    discover_plugins,
    rotate_backups,
    create_fgdb,
    create_multi_combo_locator,
    # create_composite_locator,
    # DatasetConfig,
)

runCounter = MySettings.getRunCounter()

# setup the logger
# logger = logging.getLogger(__file__)
# CustomFormatter.setupLogger(
#     logger, (__file__).replace(".py", ".log"), False)

print(f"\n{'='*60}")
print(f"Starting {str(Path(__file__).name)} v{__version__}.{runCounter}")
print(f"By {__author__} | Last Updated: {__updated__}")
print(f"{'='*60}\n")


print("Loading arcpy (this may take a moment)...")
import arcpy
# from arcgis.gis import GIS

# BASEDIR = r"M:\Processing_Scripts\Create_Locator_Service"
BASEDIR = r"D:\City_STUFF\Create_Locator_v3"



# import argument_parcer
# import DatasetConfig

# some spinners just to show it hasnt frozen at long operations
# spinny =itertools.cycle([" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂", "▁"])
# spinny =itertools.cycle(["-", "≻", "›", "⟩", "|", "⟨", "‹", "≺", "-", "≺", "‹", "⟨", "|", "⟩", "›", "≻"])
# spinny =itertools.cycle(["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"])
# spinny =itertools.cycle(["■", "◤", "◸","◤","■","◥","◹","◥","■","◢","◿","◢","■","◣","◺","◣"])
spinny = itertools.cycle(["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"])
# spinny = itertools.cycle(['-', '/', '|', '\\'])
# print(f"Busy working, please wait {next(spinny)}", end="\r")

# arcpy.SetMessageLevels(['COMMANDSYNTAX'])
# arcpy.SetMessageLevels(["NORMAL"])
arcpy.SetMessageLevels(['DIAGNOSTICS'])
arcpy.env.parallelProcessingFactor = "90%"

# build_locator.py



CYAN  = "\033[96m"
GREEN = "\033[92m"
PURPLE = "\x1b[1;35;40m"

BOLD  = "\033[1m"
RESET = "\033[0m"



def add_date_suffix(text: str) -> str:
    date_str = datetime.datetime.now().strftime("%d_%m_%Y")
    return f"{text}_{date_str}"



# -----------------------------------------------------------------
def main():
    print("\n\nStarting Main Processing")
    parser = argparse.ArgumentParser(description="Whitehorse Locator Builder")
    parser.add_argument("--all", action="store_true", help="Build all datasets")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--fgdb-base", type=str, required=True, help="Base FGDB path (without .gdb)")
    parser.add_argument("--project-root", type=str, default=".", help="Project root (default: current dir)")
    parser.add_argument("--dataset", type=str, help="Build a single dataset")
    parser.add_argument('--local_gdb', type=str, help="Path to local FGDB (default: project_root/local_data.gdb)" )
    parser.add_argument('--use-local-gdb', default=False, action="store_true", help="flag for using local sourse gdb or not-local sde")
    # parser.add_argument("--dataset", type=str, help="Build a single dataset", choices=[city_boundary, address_points, parcels])

    args = parser.parse_args()
    for key, value in vars(args).items():
        print(f"  {CYAN}{key:20}{RESET} = {GREEN}{value}{RESET}")

    createAllSDEfiles( None, BASEDIR)


    project_root = os.path.abspath(args.project_root)
    fgdb_base = os.path.abspath( args.fgdb_base)

    sde_map = discover_sde_files(project_root)


    # Determine local GDB path
    if args.use_local_gdb:
        if args.local_gdb:
            local_gdb = os.path.abspath(args.local_gdb)
        else:
            # Default: project_root/local_data.gdb
            local_gdb = os.path.join(project_root, "local_data.gdb")

        if not os.path.exists(local_gdb):
            print(f"ERROR: Local FGDB not found: {local_gdb}")
            return
        print("Database Source:")
        print(f"  {CYAN}Using local FGDB:{RESET} {GREEN}{local_gdb}{RESET}")
    else:
        local_gdb=""
    print('-' * 50)


    # print("Command line Args:")
    # for key, value in vars(args).items():
    #     print(f"  {key:20} = {value}")

    print(f"{BOLD}Command line Args:{RESET}")
    for key, value in vars(args).items():
        print(f"  {CYAN}{key:20}{RESET} = {GREEN}{value}{RESET}")
    print('-' * 50)
    # logger.mark()
    ctx = Context(
        project_root=project_root,
        fgdb_base=fgdb_base,
        sde_map=sde_map,
        use_local_gdb=args.use_local_gdb,
        local_gdb=local_gdb,
    )
    print(f"{ctx}")
    print('-' * 60)




    rotate_backups(ctx.fgdb_base, 5)
    
    ctx.fgdb = create_fgdb(ctx.fgdb_base)

    ctx.locator_dir = os.path.join(project_root, "Locators")
    os.makedirs(ctx.locator_dir, exist_ok=True)

    discover_plugins("plugins", ctx)

    if args.list:
        print("Available datasets:")
        for name in REGISTRY:
            print(f"  - {name}")

        pprint(vars(args))
        print(f"{args.local_gdb=}")

        # table ='D:/City_STUFF/Create_Locator_v4/copyOfMasterData.gdb/SiteStructureAddressPoints'
        # show_fields_of_table(table)

        # table ='D:/City_STUFF/Create_Locator_v4/copyOfMasterData.gdb/Parcel_Calc_Address_CityWorks_WORKING'
        # show_fields_of_table(table)

        return


    if args.dataset:
        if args.dataset not in REGISTRY:
            print(f"Dataset '{args.dataset}' not found.")
            return
        cfg = REGISTRY[args.dataset]
        if args.use_local_gdb:
            cfg.use_local_gdb = True
        print(f"Building dataset: {cfg.name} {cfg.use_local_gdb=}")
        cfg.run_all(ctx)
        print(f"Done: {cfg.name}")
        return

    if args.all:
        datasets = list(REGISTRY.values())
        for cfg in datasets:
            print(f"Building dataset: {cfg.name}")
            cfg.run_all(ctx)
        # composite = create_composite_locator(ctx, "WhitehorseComposite", datasets)

        name = add_date_suffix("WhitehorseComposite" )
        composite = create_multi_combo_locator(ctx, name, datasets)
        
        print(f"Composite locator created: {composite}")
        return

    print("No action specified. Use --all, --dataset, or --list.")


# -----------------------------------------------------------------
if __name__ == "__main__":
    main()