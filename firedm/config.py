"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""
# todo: clean unused items

from queue import Queue
import os
import sys
import platform

from .version import __version__

# settings parameters to be saved on disk
settings_keys = ['current_theme', 'monitor_clipboard', 'show_download_window', 'auto_close_download_window',
                 'segment_size', 'show_thumbnail', 'speed_limit', 'max_concurrent_downloads', 'max_connections',
                 'update_frequency', 'last_update_check', 'proxy', 'proxy_type', 'raw_proxy', 'enable_proxy',
                 'log_level', 'download_folder', 'manually_select_dash_audio', 'use_referer', 'referer_url',
                 'close_action', 'process_playlist', 'keep_temp', 'auto_rename', 'checksum',
                 'use_proxy_dns', 'use_thread_pool_executor', 'write_metadata', 'check_for_update',
                 'minimize_to_systray', 'enable_systray', 'window_size', 'download_thumbnail', 'active_video_extractor',
                 'autoscroll_download_tab', 'enable_captcha_workaround',
                 'verify_ssl_cert', 'custom_user_agent', 'recent_folders', 'write_timestamp',
                 'use_playlist_numbers', 'refresh_url_retries', 'ditem_show_top', 'disable_log_popups']

# CONSTANTS
APP_NAME = 'FireDM'
APP_VERSION = __version__
APP_TITLE = f'{APP_NAME} version {APP_VERSION} .. an open source download manager'
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), 'Downloads')
DEFAULT_THEME = 'dark'
DEFAULT_CONNECTIONS = 10

# minimum segment size which can be split in 2 halves in auto-segmentation process, refer to brain.py>thread_manager.
DEFAULT_SEGMENT_SIZE = 102400  # 100 KB
DEFAULT_CONCURRENT_CONNECTIONS = 3
APP_URL = 'https://github.com/firedm/FireDM'
LATEST_RELEASE_URL = 'https://github.com/firedm/FireDM/releases/latest'

# headers,
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3721.3'
custom_user_agent = None

#  a random user agent will be used later when importing youtube-dl, if no custom user agent
http_headers = {
    'User-Agent': custom_user_agent or DEFAULT_USER_AGENT,
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
}

DEFAULT_LOG_LEVEL = 2

youtube_dl_version = None
yt_dlp_version = None
atk_version = None  # awesometkinter

TEST_MODE = False
SIMULATOR = False
FROZEN = getattr(sys, "frozen", False)  # check if app is being compiled by cx_freeze
# -------------------------------------------------------------------------------------

# current operating system  ('Windows', 'Linux', 'Darwin')
operating_system = platform.system()

# Example output: Os: Linux - Platform: Linux-5.11.0-7614-generic-x86_64-with-glibc2.32 - Machine: x86_64
operating_system_info = f"Os: {platform.system()} - Platform: {platform.platform()} - Machine: {platform.machine()}"

try:
    import distro

    # Example output: Distribution: ('Pop!_OS', '20.10', 'groovy')
    operating_system_info += f"\nDistribution: {distro.linux_distribution(full_distribution_name=True)}"
except:
    pass

# release type
isappimage = False  # AppImage release

# application exit flag
terminate = False  # for main window and downloads
shutdown = False  # complete shutdown flag

# folders --------------------------------------------------------------------------------------------------------------
if hasattr(sys, 'frozen'):  # like if application frozen by cx_freeze
    current_directory = os.path.dirname(sys.executable)
else:
    path = os.path.realpath(os.path.abspath(__file__))
    current_directory = os.path.dirname(path)
sys.path.insert(0, os.path.dirname(current_directory))
sys.path.insert(0, current_directory)

sett_folder = None
global_sett_folder = None
download_folder = DEFAULT_DOWNLOAD_FOLDER

recent_folders = []

# settings parameters
# General --------------------------------------------------------------------------------------------------------------
current_theme = DEFAULT_THEME
monitor_clipboard = True
show_download_window = True
auto_close_download_window = True
segment_size = DEFAULT_SEGMENT_SIZE  # in bytes
auto_rename = False  # auto rename file if there is an existing file with same name at download folder
autoscroll_download_tab = False
ditem_show_top = True
use_server_timestamp = False  # write 'last modified' timestamp to downloaded file

# systray, it will be disabled by default since it doesn't work properly on most operating systems except Windows.
enable_systray = True if operating_system == 'Windows' else False
minimize_to_systray = False

# gui window size
DEFAULT_WINDOW_SIZE = (780, 433)  # width, height in pixels
window_size = DEFAULT_WINDOW_SIZE


# video / audio --------------------------------------------------------------------------------------------------------
# youtube-dl abort flag, will be used by decorated YoutubeDl.urlopen(), see video.set_interrupt_switch()
ytdl_abort = False
video_extractors_list = ['youtube_dl', 'yt_dlp']
active_video_extractor = 'youtube_dl'
show_thumbnail = True  # auto preview video thumbnail at main tab
download_thumbnail = False
process_playlist = False  # fetch videos info only if selected, since big playlist consume time/resources.
big_playlist_length = 50  # minimum number of videos in big playlist, it will ignore "process_playlist"
manually_select_dash_audio = False  # if True, will prompt user to select audio format for dash video
write_metadata = True  # write metadata to video file
enable_captcha_workaround = False
use_playlist_numbers = True  # add numbers to video file names when downloading thru playlist menu.

# ffmpeg
ffmpeg_actual_path = None
ffmpeg_download_folder = sett_folder

# connection / network -------------------------------------------------------------------------------------------------
speed_limit = 0  # in bytes, zero == no limit
max_concurrent_downloads = DEFAULT_CONCURRENT_CONNECTIONS
max_connections = DEFAULT_CONNECTIONS
use_referer = False
referer_url = ''  # referer website url
verify_ssl_cert = True  # verify server's ssl certificate

# website authentication
use_web_auth = False
username = ''
password = ''

# proxy
proxy = ''  # must be string example: 127.0.0.1:8080
proxy_type = 'http'  # socks4, socks5
raw_proxy = ''  # unprocessed from user input
enable_proxy = False
use_proxy_dns = False

# use_cookies
use_cookies = False
cookie_file_path = ''

refresh_url_retries = 1  # number of retries to refresh expired url when downloading a file, zero to disable

shutdown_pc = False
on_completion_command = ''

# debugging ------------------------------------------------------------------------------------------------------------
keep_temp = False  # keep temp files / folders after done downloading for debugging
checksum = True  # calculate checksums for completed files MD5 and SHA256
use_thread_pool_executor = False
max_seg_retries = 10  # maximum retries for a segment until reporting downloaded, this is for segment with unknown size

# logging --------------------------------------------------------------------------------------------------------------
log_entry = ''  # one log line
max_log_size = 1024 * 1024 * 5  # 5 MB
log_level = DEFAULT_LOG_LEVEL  # standard=1, verbose=2, debug=3
log_recorder_q = Queue()

# log callbacks that will be executed when calling log func in utils
# callback and popup should accept 3 positional args e.g. log_callback(start, text, end)
log_callbacks = []
log_popup_callback = None
# -------------------------------------------------------------------------------------

# downloads  TODO: to be deleted
active_downloads = set()  # indexes for active downloading items
d_list = []

# queues
error_q = Queue()  # used by workers to report server refuse connection errors
jobs_q = Queue()  # # required for failed worker jobs

# update --------------------------------------------------------------------------------------------
# set this flag to True to disable update feature completely
disable_update_feature = False

check_for_update = not disable_update_feature
update_frequency = 7  # days
last_update_check = None  # date format (year, month, day)


# store hashes for installed update patches in update_record.info file at current folder xx NOT IMPLEMENTED xx
update_record_path = os.path.join(current_directory, 'update_record.info')
# -----------------------------------------------------------------------------------------------------


# operating modes
ignore_settings = False  # run application without loading or saving setting files


# status class as an Enum
class Status:
    """used to identify status, work as an Enum"""
    downloading = 'downloading'
    cancelled = 'cancelled'
    completed = 'completed'
    pending = 'pending'
    processing = 'processing'  # for any ffmpeg operations
    error = 'error'
    scheduled = 'scheduled'
    refreshing_url = 'refreshing url'
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

    3: {'tag': 'overwrite d_list', 
        'description': 'Show "Item already exist in download list warning".',
        'body': 'Item with the same name already exist in download list', 
        'options': ['Resume', 'Overwrite', 'Cancel'],
        'default': 'Resume',
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
        'body':  ("Warning! \n"
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
        'body': ('WARNING: disabling verification of SSL certificate allows bad guys to man-in-the-middle the '
                 'communication without you know it and makes the communication insecure. '
                 'Just having encryption on a transfer is not enough as you cannot be sure that you are '
                 'communicating with the correct end-point. \n'
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
    var_name = f'popup_{k}'
    item['show'] = globals()[var_name]
    return item

def enable_popup(k, value):
    item = popups[k]
    var_name = f'popup_{k}'
    globals()[var_name] = value  # True or false
