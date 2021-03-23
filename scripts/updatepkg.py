#!/usr/bin/env python3
"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        download latest package version, compile and copy contents to installation folder
        same as "pip install --target mytargetfolde" but pip is slow, and doesn't compile files
"""

import json
import os
import re
import shutil
import sys

from packaging.version import parse as parse_version

# get current directory
path = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(path)
sys.path.insert(0,  os.path.dirname(current_folder))  # for imports to work

from scripts.utils import download, delete_folder, extract, compile_pkg, create_folder, bkup, get_pkg_version


def get_pkg_latest_version(pkg_name, fetch_url=True):
    """get latest stable package release version on https://pypi.org/
    reference: https://warehouse.pypa.io/api-reference/
    Available strategies:
    1 - rss feed (faster and lighter), send xml info with latest release version but no info on "wheel file" url,
        pattern example: https://pypi.org/rss/project/youtube-dl/releases.xml
        example data:
                    <item>
                    <title>2020.12.14</title>
                    <link>https://pypi.org/project/youtube-dl/2020.12.14/</link>
                    <description>YouTube video downloader</description>
                    <author>dstftw@gmail.com</author>
                    <pubDate>Sun, 13 Dec 2020 17:59:21 GMT</pubDate>
                    </item>

    2- json, (slower and bigger file), send all info for the package
        url pattern: f'https://pypi.org/pypi/{pkg_name}/json' e.g.    https://pypi.org/pypi/firedm/json
        received json will be a dict with:
        keys = 'info', 'last_serial', 'releases', 'urls'
        releases = {'release_version': [{dict for wheel file}, {dict for tar file}], ...}
        dict for wheel file = {"filename":"yt_dlp-2020.10.24.post6-py2.py3-none-any.whl", 'url': 'file url'}
        dict for tar file = {"filename":"yt_dlp-2020.10.24.post6.tar.gz", 'url': 'file url'}


    Args:
        pkg_name (str): package name
        fetch_url (bool): if true, will use json API to get download url, else it will use rss feed to get version only

    Return:
        2-tuple(str, str): latest_version, and download url (for wheel file) if available
    """

    # download json info
    url = f'https://pypi.org/pypi/{pkg_name}/json' if fetch_url else f'https://pypi.org/rss/project/{pkg_name}/releases.xml'

    # get BytesIO object
    print(f'check for {pkg_name} latest version on pypi.org...')
    data = download(url)
    latest_version = None
    url = None

    if data:
        # convert to string
        contents = data.decode('utf-8')

        # rss feed
        if not fetch_url:
            match = re.findall(r'<title>(\d+.\d+.\d+.*)</title>', contents)
            latest_version = max([parse_version(release) for release in match]) if match else None

            if latest_version:
                latest_version = str(latest_version)
        # json
        else:
            j = json.loads(contents)

            releases = j.get('releases', {})
            if releases:

                latest_version = max([parse_version(release) for release in releases.keys()]) or None
                if latest_version:
                    latest_version = str(latest_version)

                    # get latest release url
                    release_info = releases[latest_version]
                    for _dict in release_info:
                        file_name = _dict['filename']
                        url = None
                        if file_name.endswith('.whl'):
                            url = _dict['url']
                            break

        return latest_version, url

    else:
        print(f"get_pkg_latest_version() --> couldn't check for {pkg_name}, url is unreachable")
        return None, None


def update_pkg(pkg_name, target_folder, src_folder=None, create_bkup=False, compile=True):
    """install or update a packagein a specific folder
    expect to download and extract a wheel file e.g. "yt_dlp-2020.10.24.post6-py2.py3-none-any.whl", which in fact
    is a zip file

    Args:
        pkg_name (str): package name
        url (str): download url (for a wheel file)
        target_folder (str): target installation folder for the package
        src_folder (str): if specified, will skip downloading from pypi and use it instead
    """

    # paths
    temp_folder = os.path.join(target_folder, f'temp_{pkg_name}')
    extract_folder = os.path.join(temp_folder, 'extracted')
    z_fn = f'{pkg_name}.zip'
    z_fp = os.path.join(temp_folder, z_fn)

    old_pkg_path = os.path.join(target_folder, pkg_name)
    new_pkg_path = os.path.join(extract_folder, pkg_name)

    # make temp folder structure
    delete_folder(temp_folder)
    create_folder(extract_folder)  

    # start processing -------------------------------------------------------
    print(f'start updating {pkg_name} please wait ...')

    if create_bkup:
        print(f'backup {pkg_name}')
        bkup(old_pkg_path)

    if not src_folder:
        # get download url
        latest_version, url = get_pkg_latest_version(pkg_name)
        current_version = get_pkg_version(os.path.join(old_pkg_path, 'version.py'))
        if parse_version(latest_version) <= parse_version(current_version):
            print(f'{pkg_name} is up-to-date, current: {current_version} - latest: {latest_version}')
            return

        if url:
            print(f'Found {pkg_name} version: {latest_version}')
        else:
            print('Failed to get url for:', pkg_name)
            return

        # download from pypi
        print(f'downloading {pkg_name} files')
        data = download(url, fp=z_fp)
        if not data:
            print(f'failed to download {pkg_name}, abort update')
            return

        # extract zip file
        print(f'extracting {z_fn}')
        extract(z_fp, extract_folder)
    
    else:
        # copy pkg folder to temp folder
        shutil.copytree(src_folder, new_pkg_path)

    # compile files from py to pyc
    if compile:
        print('compiling files, please wait')
        compile_pkg(new_pkg_path)

    # delete old package and replace it with new one
    print(f'overwrite old {pkg_name} files')
    delete_folder(old_pkg_path)
    shutil.move(new_pkg_path, target_folder)
    print('new package copied to:', old_pkg_path)

    # .dist-info folder, eg: FireDM-2021.2.9.dist-info
    r = re.compile(f'{pkg_name}.*dist-info', re.IGNORECASE)

    # delete old dist-info folder if found
    match = list(filter(r.match, os.listdir(target_folder)))
    if match:
        old_dist_info_folder = os.path.join(target_folder, match[0])
        delete_folder(old_dist_info_folder)
        print('delete old dist-info folder:', old_dist_info_folder)

    # copy new dist-info folder to destination folder
    match = list(filter(r.match, os.listdir(extract_folder)))
    if match:
        new_dist_info_folder = os.path.join(extract_folder, match[0])
        shutil.move(new_dist_info_folder, target_folder)
        print('install new dist-info folder:', new_dist_info_folder)

    # clean old files
    print('delete temp folder')
    delete_folder(temp_folder)
    print(f'{pkg_name} ..... done updating')
    return True


if __name__ == '__main__':

    if len(sys.argv) > 1:
        pkg_name = sys.argv[1]
    else:
        print('you must supply package name as an argument')
        exit()

    if len(sys.argv) > 2:
        target_folder = sys.argv[2]
    else:
        target_folder = current_folder

    if len(sys.argv) > 3:
        src_folder = sys.argv[3]
    else:
        src_folder = None

    update_pkg(pkg_name, target_folder, src_folder=src_folder)
