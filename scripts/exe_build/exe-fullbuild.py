"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using cx_freeze
        you should execute this module from command line using: "python cx_setup.py build" on windows only.
"""

import os
import sys
import shutil
import subprocess

from cx_Freeze import setup, Executable

APP_NAME = 'FireDM'

# to run setup.py directly
if len(sys.argv) == 1:
    sys.argv.append("build")

# get current directory
fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)

print('cx_setup.py ......................................................................................')

project_folder = os.path.dirname(os.path.dirname(current_folder))
build_folder = current_folder
app_folder = os.path.join(build_folder, APP_NAME)
icon_path = os.path.join(project_folder, 'icons', '48_32_16.ico') # best use size 48, and must be an "ico" format
version_fp = os.path.join(project_folder, 'firedm', 'version.py')
requirements_fp = os.path.join(project_folder, 'requirements.txt')
main_script_path = os.path.join(project_folder, 'firedm.py')

sys.path.insert(0,  project_folder)  # for imports to work
from scripts.utils import download, delete_folder, create_folder

# create build folder
create_folder(build_folder)

# get version
version_module = {}
with open(version_fp) as f:
    exec(f.read(), version_module)  # then we can use it as: version_module['__version__']
    version = version_module['__version__']


# get required packages
with open(requirements_fp) as f:
    packages = [line.strip().split(' ')[0] for line in f.readlines() if line.strip()] + ['firedm']
    packages.remove('Pillow')
    print(packages)

includes = []
include_files = []
excludes = ['numpy', 'test', 'setuptools', 'unittest', 'PySide2']

target = Executable(
    # what to build
    script=main_script_path,
    initScript=None,
    base='Win32GUI',
    targetName=f"{APP_NAME}.exe",
    icon=icon_path,

)

setup(

    version=version,
    description=f"{APP_NAME} Download Manager",
    author="Mahmoud Elshahat",
    name=APP_NAME,

    options={"build_exe": {
        "includes": includes,
        'include_files': include_files,
        "excludes": excludes,
        "packages": packages,
        'build_exe': app_folder,
        'include_msvcr': True,
    }
    },

    executables=[target]
)

# Post processing

# there is a bug in python3.6 where tkinter name is "Tkinter" with capital T, will rename it.
try:
    print('-' * 50)
    print('rename Tkinter to tkinter')
    os.rename(f'{app_folder}/lib/Tkinter', f'{app_folder}/lib/tkinter')
except Exception as e:
    print(e)

# manually remove excluded libraries if found
for lib_name in excludes:
    folder = f'{app_folder}/lib/{lib_name}'
    delete_folder(folder, verbose=True)

# ffmpeg
ffmpeg_path = os.path.join(current_folder, 'ffmpeg.exe')
if not os.path.isfile(os.path.join(app_folder, 'ffmpeg.exe')):
    if not os.path.isfile(ffmpeg_path):
        # download from github
        ffmpeg_url = 'https://github.com/firedm/FireDM/releases/download/extra/ffmpeg_32bit.exe'
        download(ffmpeg_url, fp=ffmpeg_path)
    shutil.copy(ffmpeg_path, os.path.join(app_folder, 'ffmpeg.exe'))

# write resource fields for exe file, i.e. version, app name, copyright, etc -------------------------------------------
# using rcedit.exe from https://github.com/electron/rcedit

# check for rcedit.exe
rcedit_fp = os.path.join(current_folder, 'rcedit.exe')
if not (os.path.isfile(rcedit_fp) or os.path.isfile(os.path.join(app_folder, 'rcedit.exe'))):
    # download file, will get x86 version, for x64 visit https://github.com/electron/rcedit/releases/latest
    rcedit_url = 'https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x86.exe'
    download(rcedit_url, fp=rcedit_fp, return_data=False)

# for some reasons rcedit must be in same directory with target file to work properly
if not os.path.isfile(os.path.join(app_folder, 'rcedit.exe')):
    shutil.copy(rcedit_fp, app_folder)

cmd = f'rcedit {APP_NAME}.exe --set-file-version {version} --set-product-version {version}  ' \
      f'--set-version-string legalcopyright "copyright(c) 2019-2021 {APP_NAME}" --set-version-string  ProductName ' \
      f'"{APP_NAME}" --set-version-string  OriginalFilename "{APP_NAME}.exe" --set-version-string FileDescription ' \
      f'"{APP_NAME} download manager"'

print('-' * 50)
print('running command:', cmd)
os.chdir(app_folder)
subprocess.run(cmd, shell=True)

# clean up
os.unlink(os.path.join(app_folder, 'rcedit.exe'))

print('Done .....')

# set icon
# rcedit "FireDM.exe" --set-icon "icon.ico"
