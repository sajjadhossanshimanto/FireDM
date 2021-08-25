#!/usr/bin/env python
"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        This is main application module
"""

# standard modules
import os
import sys
import argparse
import re
import signal

# This code should stay on top to handle relative imports in case of direct call of FireDM.py
if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
    
    __package__ = 'firedm'
    import firedm


# local modules
from . import config, setting
from .controller import Controller
from .tkview import MainWindow
from .cmdview import CmdView
from .utils import parse_urls, parse_bytes, size_format
from .setting import load_setting
from .version import __version__


def main():
    description = """FireDM is an open source Download Manager with multi-connections, high speed 
    engine, it can download general files and video files from youtube and tons of other streaming websites. 
    Developed in Python, based on "LibCurl", "youtube_dl", and "Tkinter". 
    Source: https://github.com/firedm/FireDM """

    # read config file
    if '--ignore-config' not in sys.argv:
        load_setting()

    def get_default(varname):
        default_value = getattr(config, varname, None)
        return default_value

    def iterable(txt):
        # process iterable in arguments, e.g. tuple or list,
        # example --window=(600,300)
        return re.findall(r'\d+', txt)

    def int_iterable(txt):
        return map(int, iterable(txt))

    def speed(txt):
        return parse_bytes(txt)

    # region cmdline arguments
    # Since this application is based on youtube-dl as a video extractor
    # it is recommended to use arguments names same to youtube-dl, refer to:
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py

    parser = argparse.ArgumentParser(
        prog='firedm',
        description=description,
        epilog='copyright: (c) 2019-2021 FireDM. license: GNU LGPLv3, see LICENSE file for more details. '
               'Author: Mahmoud Elshahat, '
               'Isuues: https://github.com/firedm/FireDM/issues',
        usage='\n'
              '       %(prog)s [OPTIONS] URL \n'
              '       example: %(prog)s "https://somesite.com/somevideo" --connections=8 \n'
              '       Note: to run %(prog)s in GUI(Graphical User Interface) mode, use "--gui" option along with other '
              '       arguments, or start %(prog)s without any arguments.',
        add_help=False
    )

    parser.add_argument('url', type=str, nargs='?',
                        help="""url / link of the file you want to download, 
                        url must be quoted by a single or double quotation 
                        example: "www.linktomyfile" to avoid shell capturing special characters
                        which might be found in the url e.g. "&" """)

    # ------------------------------------------------------------------------------------General options---------------
    general = parser.add_argument_group(title='General options:')
    general.add_argument(
        '-h', '--help',
        action='help',
        help='show this help message and exit')
    general.add_argument(
        '-v', '--version',
        action='version', version='%(prog)s ' + __version__,
        help='Print program version and exit')
    general.add_argument(
        '--config',
        action='store_true',
        help='show current application settings and their current values and exit')
    general.add_argument(
        '--ignore-config', dest='ignore_config',
        action='store_true',
        help='Do not load settings from config file. in ~/.config/FireDM/ or (APPDATA/FireDM/ on Windows)')
    general.add_argument(
        '--ignore-dlist', dest='ignore_dlist',
        action='store_true', default=None,
        help='Do not load/save "download list" from/to  d-list config file. in ~/.config/FireDM/ or '
             '(APPDATA/FireDM/ on Windows), default="True in cmdline mode and False in GUI mode"')
    general.add_argument(
        '--use-dlist', dest='ignore_dlist',
        action='store_false', default=None,
        help='load/save "download list" from/to  d-list config file. in ~/.config/FireDM/ or '
             '(APPDATA/FireDM/ on Windows), default="False in cmdline mode and True in GUI mode"')
    general.add_argument(
        '-g', '--gui',
        action='store_true',
        help='use graphical user interface, same effect if you try running %(prog)s without any parameters')
    general.add_argument(
        '--interactive',
        action='store_true',
        help='interactive command line')
    general.add_argument(
        '--imports-only',
        action='store_true',
        help='import all packages and exit, useful when building AppImage or exe releases, since it '
             'will build pyc files and make application start faster')
    general.add_argument(
        '--persistent',
        action='store_true', default=False,
        help='save current options in global configuration file, used in cmdline mode.')

    # ----------------------------------------------------------------------------------------Filesystem options--------
    filesystem = parser.add_argument_group(title='Filesystem options:')
    filesystem.add_argument(
        '-o', '--output',
        type=str, metavar='<PATH>',
        help='target file name, if omitted remote file name will be used, '
             'if file path included, "--download-folder" flag will be ignored, \n'
             'be careful with video extension, since ffmpeg will try to convert video '
             'based on filename extension')
    filesystem.add_argument(
        '-b', '--batch-file',
        type=argparse.FileType('r', encoding='UTF-8'), metavar='<PATH>',
        help='path to text file containing multiple urls to be downloaded, file should have '
             'every url in a separate line, empty lines and lines start with "#" will be ignored.')
    filesystem.add_argument(
        '-d', '--download_folder', dest='download_folder',
        type=str, metavar='<PATH>', default=get_default("download_folder"),
        help=f'download folder path, default=%(default)s')
    filesystem.add_argument(
        '--auto-rename',
        action='store_true', default=get_default("auto_rename"),
        help='auto rename file if same name already exist on disk, default=%(default)s')

    # ---------------------------------------------------------------------------------------Network Options------------
    network = parser.add_argument_group(title='Network Options')
    network.add_argument(
        '--proxy', dest='proxy',
        metavar='URL', default=get_default("proxy"),
        help='proxy url should have a proper scheme, http, https, socks4, or socks5, e.g. '
             '"scheme://proxy_address:port", or when using login usr/pass: '
             '"scheme://usr:pass@proxy_address:port", '
             'examples: "socks5://127.0.0.1:8080",  "socks4://john:pazzz@127.0.0.1:1080", default="%(default)s"')
    network.add_argument(
        '--use-proxy-dns',
        action='store_true', default=get_default("use_proxy_dns"),
        help='use proxy dns, default=%(default)s')

    # ---------------------------------------------------------------------------------------Authentication Options-----
    authentication = parser.add_argument_group(title='Authentication Options')
    authentication.add_argument(
        '-u', '--username',
        dest='username', metavar='USERNAME', default='',
        help='Login with this account ID')
    authentication.add_argument(
        '-p', '--password',
        dest='password', metavar='PASSWORD', default='',
        help='Account password.')

    # --------------------------------------------------------------------------------------Video Options---------------
    vid = parser.add_argument_group(title='Video Options')
    vid.add_argument(
        '--extractor', dest='active_video_extractor',
        type=str, metavar='EXTRACTOR', default=get_default("active_video_extractor"),
        help="select video extractor, available choices are: ('youtube_dl', and 'ytdlp'), default=%(default)s")
    vid.add_argument(
        '--video-quality', dest='video_quality',
        type=str, metavar='QUALITY', default='best',
        help="select video quality, available choices are: ('best', '1080p', '720p', '480p', '360p', "
             "and 'lowest'), default=%(default)s")
    vid.add_argument(
        '--prefere-mp4',
        action='store_true', default=False,
        help='prefere mp4 streams if available, default=%(default)s')

    # --------------------------------------------------------------------------------------Workarounds-----------------
    workarounds = parser.add_argument_group(title='Workarounds')
    workarounds.add_argument(
        '--ibus-workaround',
        action='store_true',
        help='ibus workaround, to fix slow gui startup')
    workarounds.add_argument(
        '--no-check-certificate', dest='ignore_ssl_cert',
        action='store_true',
        help='ignore ssl certificate validation')
    workarounds.add_argument(
        '--user-agent',
        metavar='UA', dest='custom_user_agent',
        help='Specify a custom user agent')
    workarounds.add_argument(
        '--referer', dest='referer_url',
        metavar='URL', default=None,
        help='Specify a custom referer, use if the video access is restricted to one domain')

    # --------------------------------------------------------------------------------------Post-processing Options-----
    postproc = parser.add_argument_group(title='Post-processing Options')
    postproc.add_argument(
        '--add-metadata', dest='write_metadata',
        action='store_true', default=get_default("write_metadata"),
        help='Write metadata to the video file, default=%(default)s')
    postproc.add_argument(
        '--exec',
        metavar='CMD', dest='exec_cmd',
        help='Execute a command on the file after downloading and post-processing')
    postproc.add_argument(
        '--write-thumbnail', dest='download_thumbnail',
        action='store_true', default=get_default("download_thumbnail"),
        help='Write thumbnail image to disk after downloading video file, default=%(default)s')
    postproc.add_argument(
        '--checksum',
        action='store_true', default=get_default("checksum"),
        help='calculate checksums for completed files MD5 and SHA256, default=%(default)s')

    # -------------------------------------------------------------------------------------Application Update Options---
    appupdate = parser.add_argument_group(title='Application Update Options')
    appupdate.add_argument(
        '--update',
        action='store_true', dest='update_self', default=False,
        help='Update this Application and video libraries to latest version.')

    # -------------------------------------------------------------------------------------Downloader Options-----------
    downloader = parser.add_argument_group(title='Downloader Options')
    downloader.add_argument(
        '-R', '--retries', dest='refresh_url_retries',
        type=int, metavar='RETRIES', default=get_default("refresh_url_retries"),
        help='Number of retries to download a file, default=%(default)s.')
    downloader.add_argument(
        '-l', '--speed-limit', dest='speed_limit',
        type=speed, metavar='LIMIT', default=config.speed_limit,
        help=f'download speed limit, in bytes per second (e.g. 100K or 5M), zero means no limit, '
             f'current value={size_format(config.speed_limit)}/s.')
    downloader.add_argument(
        '--concurrent', dest='max_concurrent_downloads',
        type=int, metavar='NUMBER', default=get_default("max_concurrent_downloads"),
        help='max concurrent downloads, default=%(default)s.')
    downloader.add_argument(
        '--connections', dest='max_connections',
        type=int, metavar='NUMBER', default=get_default("max_connections"),
        help='max download connections per item, default=%(default)s.')

    # -------------------------------------------------------------------------------------Debugging options------------
    debug = parser.add_argument_group(title='Debugging Options')
    debug.add_argument(
        '-V', '--verbose', dest='log_level',
        type=int, metavar='NUMBER', default=get_default("log_level"),
        help='Log verbosity level in GUI mode, 1 to 3, default=%(default)s.')
    debug.add_argument(
        '--keep-temp',
        action='store_true', default=get_default("keep_temp"),
        help='keep temp files for debugging, default=%(default)s.')

    # -------------------------------------------------------------------------------------GUI options------------------
    gui = parser.add_argument_group(title='GUI Options')
    gui.add_argument(
        '--theme', dest='current_theme',
        type=str, metavar='THEME', default=get_default("current_theme"),
        help='theme name, e.g. "Dark", default=%(default)s.')
    gui.add_argument(
        '--monitor-clipboard', dest='monitor_clipboard',
        action='store_true', default=get_default("monitor_clipboard"),
        help='monitor clipboard, and process any copied url, default=%(default)s.')
    gui.add_argument(
        '--window', dest='window_size',
        type=int_iterable, metavar='(WIDTH,HIGHT)', default=get_default("window_size"),
        help='window size, example: --window=(600,400) no space allowed, default=%(default)s.')
    # ------------------------------------------------------------------------------------------------------------------
    # endregion

    args = parser.parse_args()
    custom_settings = vars(args)

    if args.config:
        for key, value in custom_settings.items():
            print(f'{key}: {value}')
        sys.exit(0)

    # print('Arguments:', custom_settings)

    if args.imports_only:
        import importlib, time
        total_time = 0

        def getversion(mod):
            try:
                version = mod.version.__version__
            except:
                version = ''
            return version

        for module in ['plyer', 'certifi', 'youtube_dl', 'yt_dlp', 'pycurl', 'PIL', 'pystray', 'awesometkinter',
                       'tkinter']:
            start = time.time()

            try:
                m = importlib.import_module(module)
                version = getversion(m)
                total_time += time.time() - start
                print(f'imported module: {module} {version}, in {round(time.time() - start, 1)} sec')
            except Exception as e:
                print(module, 'package import error:', e)

        print(f'Done, importing modules, total time: {round(total_time, 2)} sec ...')
        sys.exit(0)

    if args.referer_url:
        custom_settings['use_referer'] = True

    if args.username or args.password:
        custom_settings['use_web_auth'] = True

    if args.proxy:
        custom_settings['enable_proxy'] = True

    if args.download_folder:
        folder = os.path.realpath(args.download_folder)
        custom_settings['folder'] = args.download_folder = folder

    if args.output:
        fp = os.path.realpath(args.output)
        if os.path.isdir(fp):
            folder = fp
        else:
            folder = os.path.dirname(fp)
            name = os.path.basename(fp)
            if name:
                custom_settings['name'] = name

        if folder:
            custom_settings['folder'] = folder

    guimode = True if len(sys.argv) == 1 or args.gui else False

    # set ignore_dlist argument to True in cmdline mode if not explicitly used
    if args.ignore_dlist is None and not guimode: 
        custom_settings['ignore_dlist'] = True

    # update config module with custom settings
    config.__dict__.update(custom_settings)

    controller = None

    def cleanup():
        if guimode or args.persistent:
            setting.save_setting()
        controller.quit()
        import time
        time.sleep(1)  # give time to other threads to quit

    def signal_handler(signum, frame):
        print('\n\nuser interrupt operation, cleanup ...')
        signal.signal(signum, signal.SIG_IGN)  # ignore additional signals
        cleanup()
        print('\n\ndone cleanup ...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # ------------------------------------------------------------------------------------------------------------------
    # if running application without arguments will start the gui, otherwise will run application in cmdline
    if guimode:
        # GUI
        controller = Controller(view_class=MainWindow, custom_settings=custom_settings)
        controller.run()
    else:
        config.log_level = 1
        controller = Controller(view_class=CmdView, custom_settings=custom_settings)

        if args.update_self:
            controller.check_for_update(wait=True, threaded=False)
            sys.exit(0)

        urls = []
        url = custom_settings.pop('url')
        if url:
            urls.append(url)

        if args.batch_file:
            text = args.batch_file.read()
            urls += parse_urls(text)

        if not urls:
            print('No url(s) to download')

        elif args.interactive:
            for url in urls:
                controller.interactive_download(url)
        else:
            controller.batch_download(urls, **custom_settings, threaded=False)

    cleanup()


if __name__ == '__main__':
    main()

