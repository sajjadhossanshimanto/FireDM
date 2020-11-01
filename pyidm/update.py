"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

# todo: change docstring to google format and clean unused code
# check and update application

import hashlib
import json
import py_compile
import shutil
import sys
import zipfile, tarfile
import queue
import time
from threading import Thread
from distutils.dir_util import copy_tree
import os
import webbrowser
from packaging.version import parse as parse_version

from . import config
from .utils import log, download, run_command, delete_folder, version_value, delete_file


def open_update_link():
    """open browser window with latest release url on github for frozen application or source code url"""
    url = config.LATEST_RELEASE_URL if config.FROZEN else config.APP_URL
    webbrowser.open_new(url)


def check_for_new_version():
    """
    Check for new PyIDM version

    Return:
        changelog text or None

    """

    latest_version = '0'
    changelog = None

    try:
        if config.FROZEN:
            # use github API to get latest version
            url = 'https://api.github.com/repos/pyidm/pyidm/releases/latest'
            buffer = download(url, verbose=False)

            if buffer:
                # convert to string
                contents = buffer.getvalue().decode()
                j = json.loads(contents)
                latest_version = j.get('tag_name', '0')

        else:
            # check pypi version
            latest_version, _ = get_pkg_latest_version('pyidm')

        if parse_version(latest_version) > parse_version(config.APP_VERSION):
            log('Found new version:', str(latest_version))

            # download change log file
            url = 'https://github.com/pyIDM/pyIDM/raw/master/ChangeLog.txt'
            buffer = download(url, verbose=False)  # get BytesIO object

            if buffer:
                # convert to string
                changelog = buffer.getvalue().decode()
    except Exception as e:
        log('check_for_new_version()> error:', e)

    return changelog


def get_pkg_latest_version(pkg):
    """get latest stable package release version on https://pypi.org/

    url pattern: f'https://pypi.python.org/pypi/{pkg}/json'
    received json will be a dict with:
    keys = 'info', 'last_serial', 'releases', 'urls'
    releases = {'release_version': [{dict for wheel file}, {dict for tar file}], ...}
    dict for wheel file = {"filename":"youtube_dlc-2020.10.24.post6-py2.py3-none-any.whl", 'url': 'file url'}
    dict for tar file = {"filename":"youtube_dlc-2020.10.24.post6.tar.gz", 'url': 'file url'}


    Args:
        pkg (str): package name

    Return:
        2-tuple(str, str): latest_version, and download url (for wheel file)
    """

    # download json info
    url = f'https://pypi.python.org/pypi/{pkg}/json'

    # get BytesIO object
    log(f'check for {pkg} latest version on pypi.org...')
    buffer = download(url, verbose=False)
    latest_version = None
    url = None

    if buffer:
        # convert to string
        contents = buffer.getvalue().decode()

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
        log(f"get_pkg_latest_version() --> couldn't check for {pkg}, url is unreachable")
        return None, None


def update_pkg(pkg, url):
    """updating a package in frozen application folder
    expect to download and extract a wheel file e.g. "youtube_dlc-2020.10.24.post6-py2.py3-none-any.whl", which in fact
    is a zip file

    Args:
        pkg (str): package name
        url (str): download url (for a wheel file)
    """

    current_directory = config.current_directory
    log(f'start updating {pkg}')

    # check if the application is frozen, e.g. runs from a windows cx_freeze executable
    # if run from source, we will update system installed package and exit
    if not config.FROZEN:
        cmd = f'"{sys.executable}" -m pip install {pkg} --upgrade'
        success, output = run_command(cmd)
        if success:
            log(f'successfully updated {pkg}, please restart application', showpopup=True)
        return

    # paths
    temp_folder = os.path.join(current_directory, f'temp_{pkg}')
    extract_folder = os.path.join(temp_folder, 'extracted')
    z_fn = f'{pkg}.zip'
    z_fp = os.path.join(temp_folder, z_fn)

    target_pkg_folder = os.path.join(current_directory, f'lib/{pkg}')
    bkup_folder = os.path.join(current_directory, f'lib/{pkg}_bkup')
    new_pkg_folder = None

    # make temp folder
    log('making temp folder in:', current_directory)
    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)

    def bkup():
        # backup current package folder
        log(f'delete previous backup and backup current {pkg}:')
        delete_folder(bkup_folder)
        shutil.copytree(target_pkg_folder, bkup_folder)

    def tar_extract():
        with tarfile.open(z_fp, 'r') as tar:
            tar.extractall(path=extract_folder)

    def zip_extract():
        with zipfile.ZipFile(z_fp, 'r') as z:
            z.extractall(path=extract_folder)

    extract = zip_extract

    def compile_file(q):
        while q.qsize():
            file = q.get()

            if file.endswith('.py'):
                try:
                    py_compile.compile(file, cfile=file + 'c')
                    os.remove(file)
                except Exception as e:
                    log('compile_file()> error', e)
            else:
                print(file, 'not .py file')

    def compile_all():
        q = queue.Queue()

        # get files list and add it to queue
        for item in os.listdir(new_pkg_folder):
            item = os.path.join(new_pkg_folder, item)

            if os.path.isfile(item):
                file = item
                # compile_file(file)
                q.put(file)
            else:
                folder = item
                for file in os.listdir(folder):
                    file = os.path.join(folder, file)
                    # compile_file(file)
                    q.put(file)

        tot_files_count = q.qsize()
        last_percent_value = 0

        # create 10 worker threads
        threads = []
        for _ in range(10):
            t = Thread(target=compile_file, args=(q,), daemon=True)
            threads.append(t)
            t.start()

        # watch threads until finished
        while True:
            live_threads = [t for t in threads if t.is_alive()]
            processed_files_count = tot_files_count - q.qsize()
            percent = processed_files_count * 100 // tot_files_count
            if percent != last_percent_value:
                last_percent_value = percent
                log('#', start='', end='' if percent < 100 else '\n')

            if not live_threads and not q.qsize():
                break

            time.sleep(0.1)
        log('Finished compiling to .pyc files')

    def overwrite_pkg():
        delete_folder(target_pkg_folder)
        shutil.move(new_pkg_folder, target_pkg_folder)
        log('new package copied to:', target_pkg_folder)

    # start processing -------------------------------------------------------
    log(f'start updating {pkg} please wait ...')

    try:
        # use a thread to show some progress while backup
        t = Thread(target=bkup)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')

        # download from pypi
        log(f'step 1 of 4: downloading {pkg} raw files')
        buffer = download(url, file_name=z_fp)
        if not buffer:
            log(f'failed to download {pkg}, abort update')
            return

        # extract tar file
        log(f'step 2 of 4: extracting {z_fn}')

        # use a thread to show some progress while unzipping
        t = Thread(target=extract)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')
        log(f'{z_fn} extracted to: {temp_folder}')

        # define new pkg folder
        new_pkg_folder = os.path.join(extract_folder, pkg)

        # compile files from py to pyc
        log('step 3 of 4: compiling files, please wait')
        compile_all()

        # delete old package and replace it with new one
        log(f'step 4 of 4: overwrite old {pkg} files')
        overwrite_pkg()

        # clean old files
        log('delete temp folder')
        delete_folder(temp_folder)
        log(f'{pkg} ..... done updating \nplease restart Application now', showpopup=True)
    except Exception as e:
        log(f'update_pkg()> error', e)


def rollback_pkg_update(pkg):
    """rollback last package update

    Args:
        pkg (str): package name
    """
    if not config.FROZEN:
        log(f'rollback {pkg} update is currently working on portable windows version only')
        return

    log(f'rollback last {pkg} update ................................')

    # paths
    current_directory = config.current_directory
    target_pkg_folder = os.path.join(current_directory, f'lib/{pkg}')
    bkup_folder = os.path.join(current_directory, f'lib/{pkg}_bkup')

    try:
        # find a backup first
        if os.path.isdir(bkup_folder):
            log(f'delete active {pkg} module')
            delete_folder(target_pkg_folder)

            log(f'copy backup {pkg} module')
            shutil.copytree(bkup_folder, target_pkg_folder)

            log(f'Done restoring {pkg} module, please restart Application now', showpopup=True)
        else:
            log(f'No {pkg} backup found')

    except Exception as e:
        log('rollback_pkg_update()> error', e)




