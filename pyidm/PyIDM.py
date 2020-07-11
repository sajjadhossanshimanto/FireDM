#!/usr/bin/env python
"""
    pyIDM

    multi-connections internet download manager, based on "pyCuRL/curl", "youtube_dl", and "PySimpleGUI"

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

# This is the main application module ........................................

# standard modules
import os, sys

# install update if user downloaded an update batch "FROZEN application only"
if hasattr(sys, 'frozen'):  # like if application frozen by cx_freeze
    current_directory = os.path.dirname(sys.executable)

    # Should copy contents of PyIDM_update_files folder and overwrite PyIDM original files
    update_batch_path = os.path.join(current_directory, 'PyIDM_update_files')
    if os.path.isdir(update_batch_path):
        from distutils.dir_util import copy_tree, remove_tree
        copy_tree(update_batch_path, current_directory)
        print('done installing updates')

        # delete folder
        remove_tree(update_batch_path)

# standard modules
from threading import Thread
import time


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
from .utils import *
from . import config
from . import video
from .gui import MainWindow, SysTray, sg


# messages will be written to clipboard to check for any PyIDM instance with the same version running
QUERY_MSG = f'PyIDM "{config.APP_VERSION}", any one there?'
AFFIRMATIVE_MSG = f'PyIDM "{config.APP_VERSION}", already running'

# fix for pyperclip Gtk module
clipboard.init_gtk_clipboard = alternative_to_gtk_clipboard


def clipboard_listener():
    """Monitor clipboard for any copied url, also a way to allow only one App. instance"""

    # dummy check if clipboard running properly
    try:
        _ = clipboard.paste()
    except Exception as e:
        log("clipboard error:", e)
        return

    old_data = ''

    while True:
        # read clipboard contents
        new_data = clipboard.paste()

        # Solo App. guard, if user try to launch app. executable while it is already running
        if new_data == QUERY_MSG:  # a message coming from new App. instance
            # send a yes response # it will be read by is_solo() as an exit signal
            clipboard.copy(AFFIRMATIVE_MSG)

        # url processing
        if config.monitor_clipboard and new_data != old_data:
            if new_data.strip().startswith('http'):
                config.main_window_q.put(('url', new_data))

            old_data = new_data

        # monitor global termination flag
        if config.shutdown:
            break

        # decrease cpu load
        time.sleep(1)


def is_solo():
    """send a message thru clipboard to check if a previous app instance already running"""
    try:
        original = clipboard.paste()  # get original clipboard value

        # write this message to clipboard to check if there is an active PyIDM instance
        clipboard.copy(QUERY_MSG)

        # wait to get a reply
        time.sleep(1.2)

        # get the current clipboard content
        answer = clipboard.paste()

        # restore clipboard original value
        clipboard.copy(original)

        if answer == AFFIRMATIVE_MSG:
            return False
        else:
            return True
    except Exception as e:
        # if any exception will just move on and return True
        log('Solo state can not be verified, moving on...', e)
        return True


def main():

    # quit if there is previous instance of this App. already running
    if not is_solo():
        print('previous instance already running')
        sg.Popup(f'PyIDM version {config.APP_VERSION} already running or maybe systray icon is active', title=f'PyIDM version {config.APP_VERSION}')
        config.shutdown = True
        return

    # import youtube-dl in a separate thread
    Thread(target=video.import_ytdl, daemon=True).start()

    # run clipboard monitor thread
    Thread(target=clipboard_listener, daemon=True, name='clipboard_listener').start()

    # run systray
    systray = SysTray()
    Thread(target=systray.run, daemon=True).start()

    # create main window
    main_window = MainWindow()

    # create main run loop
    while True:

        if main_window and main_window.active:
            main_window.run()
            sleep_time = 0.1
        else:
            main_window = None
            sleep_time = 0.5

        # sleep a little to save cpu resources
        time.sleep(sleep_time)

        # if systray.active:  # not implemented
        #     # set hover text for systray
        #     state = f'PyIDM is active \n{main_window.total_speed}' if not config.terminate else 'PyIDM is off'
        #     systray.update(hover_text=state)

        # read Main queue
        for _ in range(config.main_q.qsize()):
            value = config.main_q.get()
            if value == 'start_main_window':
                if not main_window:
                    main_window = MainWindow()
                else:
                    main_window.un_hide()
            elif value == 'minimize_to_systray':
                if main_window:
                    main_window.hide()
            elif value == 'close_to_systray':
                if main_window:
                    main_window.close()

        # global shutdown flag
        if config.shutdown or not(main_window or systray.active):
            # print('config.shutdown, systray.active', config.shutdown, systray.active)
            systray.shutdown()
            config.shutdown = True
            if main_window:
                main_window.close()
            break


if __name__ == '__main__':
    main()

