#!/usr/bin/env python3
"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using existing template or download a template from github
        you should execute this module from command line using: "python buildexe.py"
        this module can be executed from any operating system e.g. linux, windows, etc..
        to create exe version from scratch use cx_setup.py on windows os
"""

import os
import re
import sys
import json

fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)
project_folder = os.path.dirname(os.path.dirname(current_folder))
sys.path.insert(0,  project_folder)  # for imports to work

from scripts.updatepkg import update_pkg 
from scripts.utils import download, extract


APP_NAME = 'FireDM'

build_folder = current_folder
app_folder = os.path.join(build_folder, APP_NAME)

# check for app folder existence, otherwise download latest version from github
if not os.path.isdir(app_folder):
    print('downloading ', APP_NAME)
    data = download('https://api.github.com/repos/firedm/firedm/releases/latest').decode("utf-8")
    # "browser_download_url": "https://github.com/firedm/FireDM/releases/download/2021.2.9/FireDM-2021.2.9-x86_64.zip"
    data = json.loads(data)
    assets = data['assets']

    url = None
    for asset in assets:
        filename = asset.get('name', '')
        if filename.lower().endswith('zip'):  # e.g. FireDM-2021.2.9-x86_64.zip
            url = asset.get('browser_download_url')
            break

    if url:
        # download file
        z_fp = os.path.join(build_folder, filename)
        if not os.path.isfile(z_fp):
            download(url, z_fp)

        # unzip
        print('extracting, please wait ...')
        extract(z_fp, build_folder)

    else:
        print('Failed to download latest version, download manually '
              'from https://github.com/firedm/FireDM/releases/latest')
        exit()

lib_folder = os.path.join(app_folder, 'lib')

# update and compile packages, python version must be python 3.8 otherwise it will cause compilation error
frozen_python_version = None  

# search for python dll file to parse version e.g. python38.dll
filenames = ' '.join(os.listdir(app_folder))
match = re.search(r'python\d\d\.dll', filenames, re.I)

if match:
    match = match.group()
    frozen_python_version = f'{match[6]}.{match[7]}'
active_python_version = f'{sys.version_info[0]}.{sys.version_info[1]}'

can_compile = active_python_version == frozen_python_version

if not can_compile:
    print(f'warning require python {frozen_python_version} to compile packages, active python version: {active_python_version}')
    print('will proceed without compiling packages')

# update firedm pkg
firedm_src = os.path.join(project_folder, 'firedm')
update_pkg('firedm', lib_folder, src_folder=firedm_src, compile=can_compile)

# update video extractors
for pkg_name in ['youtube_dl', 'yt_dlp']:
    update_pkg(pkg_name,  lib_folder, compile=can_compile)

print('Done ...........')
