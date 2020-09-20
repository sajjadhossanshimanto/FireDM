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
import zipfile
import queue
import time
from threading import Thread
from distutils.dir_util import copy_tree

from . import config
import os

from .utils import log, download, run_command, delete_folder, version_value, delete_file
import webbrowser


def update():
    """
    download update patch and update current PyIDM files, this is available only for frozen portable version
    for windows
    """

    if config.FROZEN:
        try:
            done = download_update_patch()
            if not done:
                log('Update Failed, check log for more info', showpopup=True)
                return False

            # try to install update patch
            done = install_update_patch()
            if not done:
                log("Couldn't install updates while application running, please restart PyIDM\n\n",
                    'IMPORTANT: when you restart PyIDM it might take around 30 seconds installing updates\n',
                    'before it loads completely\n '
                    'If you see error message just ignore it and start the application again\n', showpopup=True)
                return False
            else:
                log('Update finished successfully, Please restart PyIDM', showpopup=True)
                return True
        except Exception as e:
            log('update()> error', e)
    else:
        open_update_link()


def open_update_link():
    """open browser window with latest release url on github for frozen application or source code url"""
    url = config.LATEST_RELEASE_URL if config.FROZEN else config.APP_URL
    webbrowser.open_new(url)


def check_for_new_version():
    """
    Check for new PyIDM version
    :return: changelog text or None
    """

    # url will be chosen depend on frozen state of the application
    source_code_url = 'https://github.com/pyIDM/pyIDM/raw/master/ChangeLog.txt'
    new_release_url = 'https://github.com/pyIDM/pyIDM/releases/download/extra/ChangeLog.txt'
    url = new_release_url if config.FROZEN else source_code_url

    # download ChangeLog.txt from github,
    log('check for PyIDM latest version ...')

    try:
        buffer = download(url, verbose=False)    # get BytesIO object

        if buffer:
            # convert to string
            changelog = buffer.getvalue().decode()

            # extract version number from contents
            server_version = changelog.splitlines()[0].replace(':', '').strip()

            # update latest version value
            log('Latest server version:', server_version)
            config.APP_LATEST_VERSION = server_version

            # check if this version newer than current application version
            if version_value(server_version) > version_value(config.APP_VERSION):
                log('Latest newer version:', server_version)
                return changelog
    except:
        pass

    return None


def check_for_new_patch():
    """
        download updateinfo.json file to get update patch's info, parse info and return a dict
        :return: dict of parsed info or None

        example contents of updateinfo.json
    {
    "url": "https://github.com/pyIDM/PyIDM/releases/download/2020.5.10/update_for_older_versions.zip",
    "minimum_version": "2020.5.4",
    "max_version": "2020.5.9",
    "sha256": "627FE532E34C8380A63B42AF7D3E533661F845FC4D4F84765897D036EA82C5ED",
    "description": "updated files for versions older than 2020.5.10"
    }

    """

    url = 'https://github.com/pyIDM/pyIDM/releases/download/extra/updateinfo.json'
    info = None

    # get latest update patch url
    log('check for update batches')

    try:
        buffer = download(url, verbose=False)
        if buffer:
            log('decode buffer')
            buffer = buffer.getvalue().decode()  # convert to string
            log('read json information')
            info = json.loads(buffer)

            log('update patch info:', info, log_level=3)

            url = info['url']
            minimum_version = info['minimum_version']
            max_version = info['max_version']
            sha256_hash = info['sha256']
            discription = info['description']

            app_ver, min_ver, max_ver = version_value(config.APP_VERSION), version_value(minimum_version), version_value(max_version)

            if app_ver < min_ver  or app_ver > max_ver:
                info = None

            # check if this patch already installed before, info will be stored in "update_record.info" file
            if os.path.isfile(config.update_record_path):
                with open(config.update_record_path) as file:
                    if sha256_hash in file.read():
                        log('update patch already installed before')
                        info = None
    except Exception as e:
        log('check_for_new_batch()> error,', e)
        info = None

    return info


def download_update_patch():
    """
    download update patch from server
    :return: True if succeeded
    """

    info = check_for_new_patch()

    if info:
        url = info.get('url')
        sha256_hash = info.get('sha256')

        log('downloading "update patch", please wait...')
        target_path = os.path.join(config.current_directory, 'PyIDM_update_files.zip')
        buffer = download(url, file_name=target_path)

        if not buffer:
            log('downloading "update patch", Failed!!!')
            return False

        # check download integrity / hash
        log('Integrity check ....')
        download_hash = hashlib.sha256(buffer.read()).hexdigest()

        # close buffer
        buffer.close()

        if download_hash.lower() != sha256_hash.lower():
            log('Integrity check failed, update patch has different hash, quitting...')
            log('download_hash, original_hash:')
            log('\n', download_hash, '\n', sha256_hash)
            return False
        else:
            log('Integrity check done successfully....')

        # unzipping downloaded file
        log('unzipping downloaded file')
        with zipfile.ZipFile(target_path, 'r') as zip_ref:  # extract zip file
            zip_ref.extractall(config.current_directory)

        log('delete zip file')
        delete_file(target_path, verbose=True)

        # write hash to "update_record.info" file with "append" flag
        log('write hash to file: "update_batches_record"')
        with open(config.update_record_path, 'a') as file:
            file.write('\n')
            file.write(sha256_hash)

        return True


def install_update_patch():
    """
    overwrite current application files with new files from patch update
    note: this function will fail if any file currently in use,
    """
    try:
        log('overwrite old PyIDM files')
        update_patch_path = os.path.join(config.current_directory, 'PyIDM_update_files')
        copy_tree(update_patch_path, config.current_directory)

        log('delete temp files')
        delete_folder(update_patch_path)
        return True
    except Exception as e:
        log('install_update_batch()> error', e)
        return False


def check_for_ytdl_update():
    """it will download "version.py" file from github to check for a new version, return ytdl_latest_version
    """

    url = 'https://github.com/ytdl-org/youtube-dl/raw/master/youtube_dl/version.py'

    # get BytesIO object
    log('check for youtube-dl latest version on Github...')
    buffer = download(url, verbose=False)

    if buffer:
        # convert to string
        contents = buffer.getvalue().decode()

        # extract version number from contents
        latest_version = contents.rsplit(maxsplit=1)[-1].replace("'", '')

        return latest_version

    else:
        log("check_for_update() --> couldn't check for update, url is unreachable")
        return None


def update_youtube_dl():
    """This block for updating youtube-dl module in the freezed application folder in windows"""
    current_directory = config.current_directory
    log('start updating youtube-dl')

    # check if the application runs from a windows cx_freeze executable
    # if run from source code, we will update system installed package and exit
    if not config.FROZEN:
        cmd = f'"{sys.executable}" -m pip install youtube_dl --upgrade'
        success, output = run_command(cmd)
        if success:
            log('successfully updated youtube_dl')
        return

    # make temp folder
    log('making temp folder in:', current_directory)
    if 'temp' not in os.listdir(current_directory):
        os.mkdir(os.path.join(current_directory, 'temp'))

    # paths
    target_module = os.path.join(current_directory, 'lib/youtube_dl')
    bkup_module = os.path.join(current_directory, 'lib/youtube_dl_bkup')
    new_module = os.path.join(current_directory, 'temp/youtube-dl-master/youtube_dl')

    def bkup():
        # backup current youtube-dl module folder
        log('delete previous backup and backup current youtube-dl module:')
        delete_folder(bkup_module)
        shutil.copytree(target_module, bkup_module)

    def unzip():
        # extract zipped module
        with zipfile.ZipFile('temp/youtube-dl.zip', 'r') as zip_ref:
            zip_ref.extractall(path=os.path.join(current_directory, 'temp'))

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
        for item in os.listdir(new_module):
            item = os.path.join(new_module, item)

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

    def overwrite_module():
        delete_folder(target_module)
        shutil.move(new_module, target_module)
        log('new module copied to:', target_module)

    # start processing -------------------------------------------------------
    log('start updating youtube-dl please wait ...')

    try:
        # use a thread to show some progress while bakup
        t = Thread(target=bkup)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')

        # download from github
        log('step 1 of 4: downloading youtube-dl raw files')
        url = 'https://github.com/ytdl-org/youtube-dl/archive/master.zip'
        response = download(url, 'temp/youtube-dl.zip')
        if response is False:
            log('failed to download youtube-dl, abort update')
            return

        # extract zip file
        log('step 2 of 4: extracting youtube-dl.zip')

        # use a thread to show some progress while unzipping
        t = Thread(target=unzip)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')
        log('youtube-dl.zip extracted to: ', current_directory + '/temp')

        # compile files from py to pyc
        log('step 3 of 4: compiling files, please wait')
        compile_all()

        # delete old youtube-dl module and replace it with new one
        log('step 4 of 4: overwrite old youtube-dl module')
        overwrite_module()

        # clean old files
        delete_folder('temp')
        log('delete temp folder')
        log('youtube_dl module ..... done updating \nplease restart Application now', showpopup=True)
    except Exception as e:
        log('update_youtube_dl()> error', e)


def rollback_ytdl_update():
    """rollback last youtube-dl update"""
    if not config.FROZEN:
        log('rollback youtube-dl update is currently working on portable windows version only')
        return

    log('rollback last youtube-dl update ................................')

    # paths
    current_directory = config.current_directory
    target_module = os.path.join(current_directory, 'lib/youtube_dl')
    bkup_module = os.path.join(current_directory, 'lib/youtube_dl_bkup')

    try:
        # find a backup first
        if os.path.isdir(bkup_module):
            log('delete active youtube-dl module')
            delete_folder(target_module)

            log('copy backup youtube-dl module')
            shutil.copytree(bkup_module, target_module)

            log('done restoring youtube-dl module')
            log('please restart Application now .................................')
        else:
            log('No backup youtube-dl modules found')

    except Exception as e:
        log('rollback_ytdl_update()> error', e)






