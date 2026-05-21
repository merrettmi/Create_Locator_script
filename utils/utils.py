#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
"""
utils.py -  some utility functions



"""
__version__ = "0.4.0"
__author__ = "Mike Merrett"
__updated__ = '2026-03-11 19:58:06'
###############################################################################

CYAN  = "\033[96m"
GREEN = "\033[92m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def colorize( s1:str, s2:str, sep:str=":") -> str:
    return f"{CYAN}{s1}{RESET}{sep}{GREEN}{s2}{RESET}"

    