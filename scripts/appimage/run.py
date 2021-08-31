"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    File description:
        This is the main script in AppImage release, responsible for sourcing firedm and other packages from 2 locations
        and load the newer version of each package.
        should be copied to AppDir
"""

import os
from packaging.version import parse
import sys
import shutil

home_folder = os.path.expanduser('~')
fp = os.path.realpath(__file__)
AppDir = os.path.dirname(fp)
sett_folder = f'{home_folder}/.config/FireDM'
site_pkgs = os.path.join(AppDir, 'usr/lib/python3.6/site-packages')
appimage_update_folder = os.path.join(sett_folder, 'appimage-update-folder')
firedm_src = os.path.join(AppDir, 'usr/src')

os.makedirs(appimage_update_folder, exist_ok=True)
sys.path.insert(0, firedm_src)
from firedm.utils import get_pkg_version

pkgs = []
for d in os.listdir(appimage_update_folder):
    folders = os.listdir(os.path.join(appimage_update_folder, d))
    if folders:
        pkg_full_path = os.path.join(appimage_update_folder, d, folders[0])
        pkgs.append(pkg_full_path)

# ignore old packages
for pkg in pkgs[:]:
    pkg_name = os.path.basename(pkg)
    pkg_version = get_pkg_version(pkg)
    if pkg_name == 'firedm':
        src_folder = firedm_src
    else:
        src_folder = site_pkgs
    orig_pkg_version = get_pkg_version(os.path.join(src_folder, pkg_name))

    # print(pkg, 'orig_pkg_version:', orig_pkg_version, ' - pkg_version:', pkg_version)

    origver = parse(orig_pkg_version)
    ver = parse(pkg_version)

    if origver > ver:
        pkgs.remove(pkg)

# add pkgs to sys.path
for pkg in pkgs:
    sys.path.insert(0, os.path.dirname(pkg))

from firedm import FireDM, config

config.isappimage = True
config.appimage_update_folder = appimage_update_folder

# fix second argument is an empty string
if len(sys.argv) > 1 and not sys.argv[1]:
    sys.argv.pop(1)

# launch application
FireDM.main()
