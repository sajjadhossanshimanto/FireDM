"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

import os
import json

from . import config
from . import downloaditem
from . import model
from .utils import log, handle_exceptions, update_object

# todo: replace save_d_list and load_d_list, with save_d_map and load_d_map for future releases


def get_global_sett_folder():
    """return a proper global setting folder"""
    home_folder = os.path.expanduser('~')

    if config.operating_system == 'Windows':
        roaming = os.getenv('APPDATA')  # return APPDATA\Roaming\ under windows
        _sett_folder = os.path.join(roaming, f'.{config.APP_NAME}')

    elif config.operating_system == 'Linux':
        _sett_folder = f'{home_folder}/.config/{config.APP_NAME}/'

    elif config.operating_system == 'Darwin':
        _sett_folder = f'{home_folder}/Library/Application Support/{config.APP_NAME}/'

    else:
        _sett_folder = config.current_directory

    return _sett_folder


config.global_sett_folder = get_global_sett_folder()


def locate_setting_folder():
    """check local folder and global setting folder for setting.cfg file"""
    # look for previous setting file
    try:
        if 'setting.cfg' in os.listdir(config.current_directory):
            return config.current_directory
        elif 'setting.cfg' in os.listdir(config.global_sett_folder):
            return config.global_sett_folder
    except:
        pass

    # no setting file found will check local folder for writing permission, otherwise will return global sett folder
    try:
        folder = config.current_directory
        with open(os.path.join(folder, 'test'), 'w') as test_file:
            test_file.write('0')
        os.unlink(os.path.join(folder, 'test'))
        return config.current_directory

    except (PermissionError, OSError):
        log("No enough permission to store setting at local folder:", folder)
        log('Global setting folder will be selected:', config.global_sett_folder)

        # create global setting folder if it doesn't exist
        if not os.path.isdir(config.global_sett_folder):
            os.mkdir(config.global_sett_folder)

        return config.global_sett_folder


config.sett_folder = locate_setting_folder()


def load_d_list():
    """deprecated: kept only to load download list for legacy versions starting from version equal or older
    than 2020.9.26 .

    create and return a list of 'DownloadItem objects' based on data extracted from 'downloads.cfg' file

    """
    d_list = []

    try:
        # log('Load previous download items from', config.sett_folder)

        # get d_list
        file = os.path.join(config.sett_folder, 'downloads.cfg')
        with open(file, 'r') as f:
            # expecting a list of dictionaries
            data = json.load(f)

        # converting list of dictionaries to list of DownloadItem() objects
        for dict_ in data:
            d = update_object(downloaditem.DownloadItem(), dict_)
            if d:  # if update_object() returned an updated object not None
                d_list.append(d)

        # get thumbnails
        file = os.path.join(config.sett_folder, 'thumbnails.cfg')
        with open(file, 'r') as f:
            # expecting a list of dictionaries
            thumbnails = json.load(f)

        # clean d_list and load thumbnails
        for i, d in enumerate(d_list):
            d.live_connections = 0

            if d.status != config.Status.completed:
                d.status = config.Status.cancelled

            # use encode() to convert base64 string to byte, however it does work without it, will keep it to be safe
            d.thumbnail = thumbnails.get(str(i), '').encode()

            # update progress info
            d.load_progress_info()

    except FileNotFoundError:
        log('downloads.cfg file not found')
    except Exception as e:
        log(f'load_d_list()>: {e}')
    finally:
        if not isinstance(d_list, list):
            d_list = []
        return d_list


def load_d_map():
    """create and return a dictionary of 'uid: DownloadItem objects' based on data extracted from 'downloads.dat' file

    """
    d_map = {}

    try:

        log('Load previous download items from', config.sett_folder)

        # get data
        file = os.path.join(config.sett_folder, 'downloads.dat')
        with open(file, 'r') as f:
            # expecting a list of dictionaries
            data = json.load(f)

        # converting data to a map of uid: ObservableDownloadItem() objects
        for uid, d_dict in data.items():  # {'uid': d_dict, 'uid2': d_dict2, ...}
            d = update_object(model.ObservableDownloadItem(), d_dict)
            if d:  # if update_object() returned an updated object not None
                d.uid = uid
                d_map[uid] = d

        # get thumbnails
        file = os.path.join(config.sett_folder, 'thumbnails.dat')
        with open(file, 'r') as f:
            # expecting a list of dictionaries
            thumbnails = json.load(f)

        # clean d_map and load thumbnails
        for d in d_map.values():
            d.live_connections = 0

            if d.status not in (config.Status.completed, config.Status.scheduled):
                d.status = config.Status.cancelled

            # use encode() to convert base64 string to byte, however it does work without it, will keep it to be safe
            d.thumbnail = thumbnails.get(d.uid, '').encode()

            # update progress info
            d.load_progress_info()

    except FileNotFoundError:
        # check for legacy download.cfg file
        log('downloads.dat file not found, looking for legacy "downloads.cfg" file')
        d_list = load_d_list()

        for d in d_list:
            obs_d = update_object(model.ObservableDownloadItem(), d.__dict__)
            d_map[obs_d.uid] = obs_d

    except Exception as e:
        log(f'load_d_map()>: {e}')
        raise e
    finally:
        if not isinstance(d_map, dict):
            d_map = {}
        return d_map


def save_d_map(d_map):
    try:
        data = {}  # dictionary, key=d.uid, value=ObservableDownloadItem
        thumbnails = {}  # dictionary, key=d.uid, value=base64 binary string for thumbnail
        for uid, d in d_map.items():
            d_dict = {key: d.__dict__.get(key) for key in d.saved_properties}
            data[uid] = d_dict

            # thumbnails
            if d.thumbnail:
                # convert base64 byte to string is required because json can't handle byte objects
                thumbnails[d.uid] = d.thumbnail.decode("utf-8")

        # store d_map in downloads.cfg file
        downloads_fp = os.path.join(config.sett_folder, 'downloads.dat')
        with open(downloads_fp, 'w') as f:
            try:
                json.dump(data, f)
            except Exception as e:
                print('error save d_list:', e)

        # store thumbnails in thumbnails.cfg file
        thumbnails_fp = os.path.join(config.sett_folder, 'thumbnails.dat')
        with open(thumbnails_fp, 'w') as f:
            try:
                json.dump(thumbnails, f)
            except Exception as e:
                print('error save thumbnails file:', e)

        log('downloads items list saved in:', downloads_fp)
    except Exception as e:
        handle_exceptions(e)


def load_setting():
    settings = {}
    try:
        log('Load Application setting from', config.sett_folder)
        file = os.path.join(config.sett_folder, 'setting.cfg')
        with open(file, 'r') as f:
            settings = json.load(f)

    except FileNotFoundError:
        log('setting.cfg not found')
    except Exception as e:
        handle_exceptions(e)
    finally:
        if not isinstance(settings, dict):
            settings = {}

        # update config module
        config.__dict__.update(settings)


def save_setting():
    settings = {key: config.__dict__.get(key) for key in config.settings_keys}

    try:
        file = os.path.join(config.sett_folder, 'setting.cfg')
        with open(file, 'w') as f:
            json.dump(settings, f)
            log('setting saved in:', file)
    except Exception as e:
        log('save_setting() > error', e)