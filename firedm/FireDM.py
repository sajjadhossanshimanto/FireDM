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

# This code should stay on top to handle relative imports in case of direct call of FireDM.py
if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
    
    __package__ = 'firedm'
    import firedm


# local modules
from . import config
from .controller import Controller, set_option
from .tkview import MainWindow
from .cmdview import CmdView
from .utils import parse_urls
from .setting import get_user_settings


def main():
    description = """FireDM is a python open source (Internet Download Manager) with multi-connections, high speed 
    engine, it downloads general files and videos from youtube and tons of other streaming websites . Developed 
    in Python, based on "LibCurl", and "youtube_dl". """

    user_settings = get_user_settings()

    def iterable(txt):
        # process iterable in arguments, e.g. tuple or list,
        # example --window-size=(600,300)
        return re.findall(r'\d+', txt)

    def int_iterable(txt):
        return map(int, iterable(txt))

    parser = argparse.ArgumentParser(
        prog='FireDM',
        description=description,
        epilog='copyright: (c) 2019-2021 by Mahmoud Elshahat. license: GNU LGPLv3, see LICENSE file for more details.',
        usage='------------------------------------------------------------------------------------------------------\n'
              '       firedm url options \n'
              '       firedm https://somesite.com/somevideo --nogui --max-connections=8 \n')

    parser.add_argument('url', type=str, nargs='?',
                        help="""url / link of the file you want to download, 
                        url must be quoted by a single or double quotation 
                        example: "www.linktomyfile" to avoid shell capturing special characters
                        which might be found in the url e.g. "&" """)

    parser.add_argument('--name', type=str,
                        help='file name with extension, don not use full path, also be careful with video extension, '
                             'ffmpeg will try to convert video depend on its extension, '
                             'also if name is given during batch download, all files will have same '
                             'name with different number at the end')

    parser.add_argument('--nogui', action='store_true', help='use command line only, no graphical user interface')
    parser.add_argument('--interactive', action='store_true', help='interactive command line, will be ignored if '
                                                                   '"--nogui" flag not used')
    parser.add_argument('--ignore-settings', action='store_true', help='ignore load or save user settings')
    # parser.add_argument('--test-run', action='store_true', help=f'start and exit automatically')
    parser.add_argument('--imports-only', action='store_true',
                        help='import all packages and exit, useful when building AppImage or exe releases, since it '
                             'will build pyc files and make application start faster')
    parser.add_argument('--show-settings', action='store_true',
                        help='show current application settings and their current values and exit')

    parser.add_argument('--video-quality', default='best', type=str,
                        help="select video quality, available choices are: 'best', '1080p', '720p', '480p', '360p', "
                             "'lowest', default value = best")
    parser.add_argument('--prefere-mp4', action='store_true', help='select mp4 streams if available, otherwise '
                                                                   'select any format')

    parser.add_argument('--urls-file', type=argparse.FileType('r', encoding='UTF-8'),
                        help='path to text file containing multiple urls to be downloaded, note: file should have '
                             'every url in a separate line, empty lines and lines start with "#" will be ignored \n'
                             'this flag works only with "--nogui" flag')

    # add config file arguments
    config_options = {

        "--download-folder": {"type": str, "help": "download folder full path"},
        "--speed-limit": {"type": int, "help": "download speed limit, in bytes, zero means no limit"},
        "--max-concurrent-downloads": {"type": int, "help": "max concurrent downloads"},
        "--max-connections": {"type": int, "help": "max connections per item download"},
        "--check-for-update": {"type": bool, "help": "check for application update"},
        "--update-frequency": {"type": int, "help": "check for application update frequency in days"},
        "--proxy": {"type": str, "help": "proxy, format should be as follows "
                                         "[proxy type://server name or address:port] \n"
                                         "example socks5://127.0.0.1:8080 \n"
                                         "supported proxy types:  http, https, socks4, and socks5"},
        "--use-proxy-dns": {"type": bool, "help": "use proxy dns"},
        "--log-level": {"type": int, "help": "log verbosity level in GUI mode, 1 to 3"},
        "--referer-url": {"type": str, "help": "referer website url"},
        "--keep-temp": {"type": bool, "help": "keep temp files for debugging"},
        "--auto-rename": {"type": bool, "help": "auto rename filename if same file already exist on disk"},
        "--checksum": {"type": bool, "help": "calculate checksums for completed files MD5 and SHA256"},
        "--write-metadata": {"type": bool, "help": "write metadata to downloaded file"},
        "--download-thumbnail": {"type": bool, "help": "download video thumbnail after downloading video file"},
        "--active-video-extractor": {"type": str, "help": "active video extractor, available options "
                                                          "'youtube_dl', and 'yt_dlp'"},
        "--verify-ssl-cert": {"type": bool, "help": "verify ssl cert"},
        "--custom-user-agent": {"type": str, "help": "custom user agent"},
        "--use-playlist-numbers": {"type": bool, "help": "use playlist numbers in names, "
                                                         "when downloading a playlist videos"},
        "--refresh-url-retries": {"type": int, "help": "number of retries to refresh url for expired links"},

        # gui options --------------------------------------------------------------------------------------------------
        "--current-theme": {"type": str, "help": "theme name, e.g. 'Dark'", 'gui': True},
        "--monitor-clipboard": {"type": bool, "help": "monitor clipboard, and process any copied url", 'gui': True},
        "--manually-select-dash-audio": {"type": bool, "help": "manually select dash audio for every video download, "
                                                               "works in GUI mode", 'gui': True},
        "--minimize-to-systray": {"type": bool, "help": "minimize application to systray when clicking close button",
                                  'gui': True},
        "--enable-systray": {"type": bool, "help": "enable systray", 'gui': True},
        "--window-size": {"type": int_iterable, "help": "window size, example: --window-size=600,400 no space allowed",
                          'gui': True},
        "--autoscroll-download-tab": {"type": bool, "help": "autoscroll download tab", 'gui': True},
        "--enable-captcha-workaround": {"type": bool, "help": "enable captcha workaround", 'gui': True},
        "--scrollbar-width": {"type": int, "help": f"scrollbar width", 'gui': True},
        "--ditem-show-top": {"type": bool, "help": "add new download items on top", 'gui': True},
        "--disable-log-popups": {"type": bool, "help": "disable popups", 'gui': True},
        "--ibus-workaround": {"type": bool, "help": "ibus workaround, in case you get slow gui startup", 'gui': True},
        "--on-download-notification": {"type": bool, "help": "show notification when an item download gets completed",
                                       'gui': True},
    }

    gui_group = parser.add_argument_group(title='Gui specific options ------------------------------------------------')

    for option in config_options:
        parameters = config_options[option]
        key = option[2:].replace("-", "_")
        default_value = getattr(config, key, None)
        from_sett_file = user_settings.get(key)

        default = from_sett_file or default_value

        parameters['help'] += f', current value={default}'
        parameters.update(default=default)
        _type = parameters['type']
        if _type == bool:
            parameters.pop('type')
            parameters.update(action='store_true')

        gui_option = parameters.get('gui')
        if gui_option:
            parameters.pop('gui')
            gui_group.add_argument(option, **parameters)
        else:
            parser.add_argument(option, **parameters)

    args = parser.parse_args()
    custom_settings = vars(args)

    if args.show_settings:
        for key, value in custom_settings.items():
            print(f'{key}: {value}')
        sys.exit(0)

    print('Arguments:', custom_settings)

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

    if args.proxy:
        custom_settings['enable_proxy'] = True

    if args.referer_url:
        custom_settings['use_referer'] = True

    if args.download_folder:
        custom_settings['folder'] = args.download_folder

    if args.nogui:
        custom_settings.update(log_level=1)
        controller = Controller(view_class=CmdView, custom_settings=custom_settings)

        urls = []
        url = custom_settings.pop('url')
        if url:
            urls.append(url)

        if args.urls_file:
            text = args.urls_file.read()
            urls += parse_urls(text)

        if not urls:
            print('No url(s) to download')

        elif args.interactive:
            for url in urls:
                controller.interactive_download(url)
        else:
            controller.batch_download(urls, **custom_settings, threadding=False)

        config.shutdown = True
    else:
        c = Controller(view_class=MainWindow, custom_settings=custom_settings)
        c.run()


if __name__ == '__main__':
    main()
