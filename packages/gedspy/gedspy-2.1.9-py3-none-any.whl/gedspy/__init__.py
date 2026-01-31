pattern = r"""
        _  ____   _         _____              _                     
       | ||  _ \ (_)       / ____|            | |                   
       | || |_) | _   ___ | (___   _   _  ___ | |_  ___  _ __ ___   
   _   | ||  _ < | | / _ \ \___ \ | | | |/ __|| __|/ _ \| '_ ` _ \  
  | |__| || |_) || || (_) |____) || |_| |\__ \| |_|  __/| | | | | | 
   \____/ |____/ |_| \___/|_____/  \__, ||___/ \__|\___||_| |_| |_|  
                                    __/ |                                   
                                   |___/                                   
"""

print(pattern)

print()
print("Welcome in GEDSpy v.2.1.9 library")
print()
print("Loading required packages...")

import os

import pkg_resources

from .DataPrepare import *
from .Enrichment import *


def get_package_directory():
    return pkg_resources.resource_filename(__name__, "")


_libd = get_package_directory()


if "data" not in os.listdir(_libd):

    up = UpdatePanel()
    up.update_library_database(force=True, first=True)

    del up


print("GEDSpy is ready to use")
