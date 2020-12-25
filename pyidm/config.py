"""
    PyIDM

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
                 'close_action', 'process_playlist', 'keep_temp', 'auto_rename', 'dynamic_theme_change', 'checksum',
                 'use_proxy_dns', 'use_thread_pool_executor', 'write_metadata', 'check_for_update',
                 'minimize_to_systray', 'enable_systray', 'window_size', 'download_thumbnail', 'active_video_extractor',
                 'autoscroll_download_tab', 'confirm_on_resume_all', 'confirm_on_stop_all', 'enable_captcha_workaround',
                 'verify_ssl_cert', 'custom_user_agent']


# CONSTANTS
APP_NAME = 'PyIDM'
APP_VERSION = __version__
APP_TITLE = f'{APP_NAME} version {APP_VERSION} .. an open source download manager'
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), 'Downloads')
DEFAULT_THEME = 'default'
DEFAULT_CONNECTIONS = 10

# minimum segment size which can be split in 2 halves in auto-segmentation process, refer to brain.py>thread_manager.
DEFAULT_SEGMENT_SIZE = 204800  # 204800 bytes == 200 KB
DEFAULT_CONCURRENT_CONNECTIONS = 3
APP_URL = 'https://github.com/pyIDM/PyIDM'
LATEST_RELEASE_URL = 'https://github.com/pyIDM/PyIDM/releases/latest'

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
youtube_dlc_version = None

TEST_MODE = False
SIMULATOR = False
FROZEN = getattr(sys, "frozen", False)  # check if app is being compiled by cx_freeze
# -------------------------------------------------------------------------------------

# current operating system  ('Windows', 'Linux', 'Darwin')
operating_system = platform.system()
operating_system_info = f'{platform.platform()} - {platform.machine()}'  # i.e. Win7-64 and Vista-32

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

# settings parameters
# General --------------------------------------------------------------------------------------------------------------
current_theme = DEFAULT_THEME
all_themes = []
dynamic_theme_change = True
monitor_clipboard = True
show_download_window = True
auto_close_download_window = True
segment_size = DEFAULT_SEGMENT_SIZE  # in bytes
auto_rename = False  # auto rename file if there is an existing file with same name at download folder
autoscroll_download_tab = False
confirm_on_resume_all = True  # resume all non completed downloads
confirm_on_stop_all = True  # stop all active downloads

# systray, it will be disabled by default since it doesn't work properly on most operating systems except Windows.
enable_systray = True if operating_system == 'Windows' else False
minimize_to_systray = False

# gui window size
DEFAULT_WINDOW_SIZE = (780, 433)  # width, height in pixels
window_size = DEFAULT_WINDOW_SIZE


# video / audio --------------------------------------------------------------------------------------------------------
# youtube-dl abort flag, will be used by decorated YoutubeDl.urlopen(), see video.set_interrupt_switch()
ytdl_abort = False
video_extractors_list = ['youtube_dl', 'youtube_dlc']
active_video_extractor = 'youtube_dl'
show_thumbnail = True  # auto preview video thumbnail at main tab
download_thumbnail = False
process_playlist = False  # fetch videos info only if selected, since big playlist consume time/resources.
big_playlist_length = 50  # minimum number of videos in big playlist, it will ignore "process_playlist"
manually_select_dash_audio = False  # if True, will prompt user to select audio format for dash video
write_metadata = True  # write metadata to video file
enable_captcha_workaround = False

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


# media type class
class MediaType:
    general = 'general'
    video = 'video'
    audio = 'audio'
    key = 'key'
