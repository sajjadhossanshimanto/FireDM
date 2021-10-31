"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

from queue import Queue
import os
import sys
import platform

from .version import __version__

# settings parameters to be saved on disk
settings_keys = [
    'active_video_extractor', 'auto_rename', 'autoscroll_download_tab', 'check_for_update', 'checksum', 'current_theme',
    'custom_user_agent', 'disable_log_popups', 'ditem_show_top', 'download_folder', 'download_thumbnail',
    'enable_proxy', 'enable_systray', 'gui_font', 'ibus_workaround', 'ignore_ssl_cert',
    'keep_temp', 'last_update_check', 'log_level', 'max_concurrent_downloads', 'remember_web_auth', 'use_web_auth',
    'username', 'password', 'max_connections', 'minimize_to_systray', 'monitor_clipboard', 'on_download_notification',
    'proxy', 'recent_folders', 'refresh_url_retries', 'scrollbar_width', 'speed_limit', 'update_frequency',
    'use_playlist_numbers', 'use_server_timestamp', 'window_size', 'write_metadata', 'view_mode'
]

# ----------------------------------------------------------------------------------------General ----------------------
# CONSTANTS
APP_NAME = 'FireDM'
APP_VERSION = __version__
APP_TITLE = f'{APP_NAME} version {APP_VERSION} .. an open source download manager'

# minimum segment size used in auto-segmentation process, refer to brain.py>thread_manager.
SEGMENT_SIZE = 1024 * 1024  # 1 MB

APP_URL = 'https://github.com/firedm/FireDM'
LATEST_RELEASE_URL = 'https://github.com/firedm/FireDM/releases/latest'

FROZEN = getattr(sys, "frozen", False)  # check if app is being compiled by cx_freeze

operating_system = platform.system()  # current operating system  ('Windows', 'Linux', 'Darwin')

# Example output: Os: Linux - Platform: Linux-5.11.0-7614-generic-x86_64-with-glibc2.32 - Machine: x86_64
operating_system_info = f"Os: {platform.system()} - Platform: {platform.platform()} - Machine: {platform.machine()}"

try:
    import distro

    # Example output: Distribution: ('Pop!_OS', '20.10', 'groovy')
    operating_system_info += f"\nDistribution: {distro.linux_distribution(full_distribution_name=True)}"
except:
    pass

# release type
isappimage = False  # will be set to True by AppImage run script
appimage_update_folder = None  # will be set by AppImage run script

# application exit flag
shutdown = False

on_download_notification = True  # show notify message when done downloading

# ----------------------------------------------------------------------------------------Filesystem options------------
# current folders
if hasattr(sys, 'frozen'):  # like if application frozen by cx_freeze
    current_directory = os.path.dirname(sys.executable)
else:
    path = os.path.realpath(os.path.abspath(__file__))
    current_directory = os.path.dirname(path)
sys.path.insert(0, os.path.dirname(current_directory))
sys.path.insert(0, current_directory)

sett_folder = None
global_sett_folder = None
download_folder = os.path.join(os.path.expanduser("~"), 'Downloads')
recent_folders = []

auto_rename = False  # auto rename file if there is an existing file with same name at download folder
checksum = False  # calculate checksums for completed files MD5 and SHA256
use_playlist_numbers = True  # add numbers to video file names when downloading thru playlist menu.

# ---------------------------------------------------------------------------------------Network Options----------------
proxy = ''  # must be string example: 127.0.0.1:8080
enable_proxy = False

# ---------------------------------------------------------------------------------------Authentication Options---------
use_web_auth = False
remember_web_auth = False
username = ''
password = ''

# ---------------------------------------------------------------------------------------Video Options------------------
# youtube-dl abort flag, will be used by decorated YoutubeDl.urlopen(), see video.set_interrupt_switch()
ytdl_abort = False
video_extractors_list = ['youtube_dl', 'yt_dlp']
active_video_extractor = 'youtube_dl'

ffmpeg_actual_path = None
ffmpeg_download_folder = sett_folder

# ---------------------------------------------------------------------------------------Workarounds--------------------
ibus_workaround = False  # issue 256: https://github.com/firedm/FireDM/issues/256
ignore_ssl_cert = False  # ignore ssl certificate validation

#  a random user agent will be used later when importing youtube-dl, if no custom user agent
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3721.3'
custom_user_agent = None
http_headers = {
    'User-Agent': custom_user_agent or DEFAULT_USER_AGENT,
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
}

use_referer = False
referer_url = ''  # referer website url
use_cookies = False
cookie_file_path = ''

# ---------------------------------------------------------------------------------------Post-processing Options--------
download_thumbnail = False
write_metadata = False  # write metadata to video file
shutdown_pc = False
on_completion_command = ''
use_server_timestamp = False  # write 'last modified' timestamp to downloaded file

# ---------------------------------------------------------------------------------------Application Update Options-----
# set this flag to True to disable update feature completely
disable_update_feature = False

check_for_update = not disable_update_feature
update_frequency = 7  # days
last_update_check = None  # date format (year, month, day)

youtube_dl_version = None
yt_dlp_version = None
atk_version = None  # awesometkinter

# ---------------------------------------------------------------------------------------Downloader Options-------------
refresh_url_retries = 1  # number of retries to refresh expired url when downloading a file, zero to disable
speed_limit = 0  # in bytes, zero == no limit
max_concurrent_downloads = 3
max_connections = 10
max_seg_retries = 10  # maximum retries for a segment until reporting downloaded, this is for segment with unknown size

# ---------------------------------------------------------------------------------------Debugging options--------------
keep_temp = False  # keep temp files / folders after done downloading for debugging

max_log_size = 1024 * 1024 * 5  # 5 MB
log_level = 2  # standard=1, verbose=2, debug=3

# log callbacks that will be executed when calling log func in utils
# callback and popup should accept 3 positional args e.g. log_callback(start, text, end)
log_callbacks = []
log_popup_callback = None
test_mode = False
simulator = False

# ---------------------------------------------------------------------------------------GUI options--------------------
DEFAULT_THEME = 'Dark'
current_theme = DEFAULT_THEME
gui_font = {}
gui_font_size_default = 10
gui_font_size_range = range(6, 26)

scrollbar_width_default = 10
scrollbar_width = scrollbar_width_default
scrollbar_width_range = range(1, 51)
monitor_clipboard = True
autoscroll_download_tab = False
ditem_show_top = True

# systray, it will be disabled by default since it doesn't work properly on most operating systems except Windows.
enable_systray = True if operating_system == 'Windows' else False
minimize_to_systray = False

DEFAULT_WINDOW_SIZE = (780, 433)  # width, height in pixels
window_size = DEFAULT_WINDOW_SIZE

view_mode = 'mix'
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# queues
error_q = Queue()  # used by workers to report server refuse connection errors
jobs_q = Queue()  # # required for failed worker jobs


# status class as an Enum
class Status:
    """used to identify status, work as an Enum"""
    downloading = 'Downloading'
    cancelled = 'Paused'
    completed = 'Completed'
    pending = 'Pending'
    processing = 'Processing'  # for any ffmpeg operations
    error = 'Failed'
    scheduled = 'Scheduled'
    refreshing_url = 'Refreshing url'
    active_states = (downloading, processing, refreshing_url)


# media type class
class MediaType:
    general = 'general'
    video = 'video'
    audio = 'audio'
    key = 'key'


# popup windows, get user responses
disable_log_popups = False

popups = {
    1: {'tag': 'html contents',
        'description': 'Show "Contents might be an html web page warning".',
        'body': 'Contents might be a web page / html, Download anyway?',
        'options': ['Ok', 'Cancel'],
        'default': 'Ok',
        'show': True
        },

    2: {'tag': 'ffmpeg',
        'description': 'Prompt to download "FFMPEG" if not found on windows os.',
        'body': 'FFMPEG is missing!',
        'options': ['Download', 'Cancel'],
        'default': 'Download',
        'show': True
        },

    4: {'tag': 'overwrite file',
        'description': 'Ask what to do if same file already exist on disk.',
        'body': 'File with the same name already exist on disk',
        'options': ['Overwrite', 'Rename', 'Cancel'],
        'default': 'Rename',
        'show': True
        },

    5: {'tag': 'non-resumable',
        'description': 'Show "Non-resumable downloads warning".',
        'body': ("Warning! \n"
                 "This remote server doesn't support chunk downloading, \n"
                 "if for any reason download stops resume won't be available and this file will be downloaded  \n"
                 "from the beginning, \n"
                 'Are you sure you want to continue??'),
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
        },

    6: {'tag': 'ssl-warning',
        'description': 'Show warning when Disabling SSL verification.',
        'body': ('WARNING: disable SSL certificate verification could allow hackers to man-in-the-middle attack '
                 'and make the communication insecure. \n\n'
                 'Are you sure?'),
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
        },

    7: {'tag': 'delete-item',
        'description': 'Confirm when deleting an item from download list.',
        'body': 'Remove item(s) from the list?\nAre you sure',
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
        },
}

for k in popups.keys():
    var_name = f'popup_{k}'
    globals()[var_name] = True
    settings_keys.append(var_name)


def get_popup(k):
    item = popups[k]
    item['show'] = globals()[f'popup_{k}']
    return item


def enable_popup(k, value):
    globals()[f'popup_{k}'] = value  # True or false
