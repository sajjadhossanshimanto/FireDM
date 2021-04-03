#!/usr/bin/env python
"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        This is main application module
"""

# standard modules
import os
import sys
import argparse

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


def main():
    description = """FireDM is a python open source (Internet Download Manager) with multi-connections, high speed 
    engine, it downloads general files and videos from youtube and tons of other streaming websites . Developed 
    in Python, based on "LibCurl", and "youtube_dl". """

    parser = argparse.ArgumentParser(prog='FireDM',
                                     description=description,
                                     epilog='copyright: (c) 2019-2021 by Mahmoud Elshahat. '
                                            'license: GNU LGPLv3, see LICENSE file for more details.')

    parser.add_argument('url', type=str, nargs='?',
                        help="""url / link of the file you want to download, 
                        url must be quoted by a single or double quotation 
                        example: "www.linktomyfile" to avoid shell capturing special characters
                        which might be found in the url e.g. "&" """)

    parser.add_argument('-f', '--folder', default=config.download_folder, type=str, metavar='<path>',
                        help=f'destination download folder/dir (default: {config.download_folder})')

    parser.add_argument('--nogui', action='store_true', help=f'interactive command line')
    # parser.add_argument('-i', '--interactive', action='store_true', help=f'interactive command line')
    parser.add_argument('--ignore-settings', action='store_true', help=f'ignore loading or savng settings')
    # parser.add_argument('--test-run', action='store_true', help=f'start and exit automatically')
    parser.add_argument('--imports-only', action='store_true',
                        help=f'import all packages and exit, if you need to build pyc files')

    args = parser.parse_args()
    print('Arguments:', vars(args))

    if args.imports_only:
        import importlib, time
        total_time = 0

        def getversion(mod):
            try:
                version = m.version.__version__
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

        print(f'Done, All modules are loaded succesfully, total time: {round(total_time, 2)} sec ...')
        exit(0)

    custom_settings = vars(args)

    if args.nogui:
        url = args.url
        folder = args.folder
        custom_settings.update(log_level=1)
        controller = Controller(view_class=CmdView, custom_settings=custom_settings)
        controller.interactive_download(url, folder=folder)
    else:
        c = Controller(view_class=MainWindow, custom_settings=custom_settings)
        c.run()


if __name__ == '__main__':
    main()
