#!/usr/bin/env python
"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        This is main application module
"""

# standard modules
import os, sys

# This code should stay on top to handle relative imports in case of direct call of pyIDM.py
if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
    
    __package__ = 'pyidm'
    import pyidm

# check and auto install external modules
from .dependency import install_missing_pkgs
install_missing_pkgs()


# local modules
from . import config
from .controller import Controller
from .cmdview import CmdView
from .tkview import MainWindow


def main():
    c = Controller(view_class=MainWindow)
    c.run()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # calling PyIDM from command line / terminal with any arguments it will enter interactive mode 
        # without gui
        # usage: pyidm "url" --folder "/home/downloads/"

        import argparse
        parser = argparse.ArgumentParser(description='PyIDM open source internet download manager')

        parser.add_argument('url', type=str, 
                            help="""url / link of the file you want to download, 
                            url must be included inside single or double quotation 
                            example: "www.linktomyfile" to avoid shell capture special characters
                            may be found in url like "&" """)

        parser.add_argument('-f', '--folder', default=config.download_folder, type=str,
                            help=f'destination download folder/dir (default: {config.download_folder})')

        args = parser.parse_args()
        url = args.url
        folder = args.folder

        controller = Controller(view_class=CmdView, custom_settings={'log_level': 1})
        controller.interactive_download(url, folder=folder)
    
    else:
        # load GUI
        main()

