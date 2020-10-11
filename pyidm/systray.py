"""
    PyIDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        system tray icon based on GTK and pystray, tested on windows and Manjaro using GTK 3.0
"""

import os
import awesometkinter as atk

from . import config
from .iconsbase64 import APP_ICON
from .utils import log, delete_file


class SysTray:
    """
    systray icon using pystray package
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon_path = os.path.join(config.sett_folder, 'systray.png')  # path to icon
        self.icon = None
        self._hover_text = None
        self.Gtk = None
        self.active = False

    def show_main_window(self, *args):
        self.main_window.unhide()

    def minimize_to_systray(self, *args):
        self.main_window.hide()

    @property
    def tray_icon(self):
        """return pillow image"""
        try:
            img = atk.create_pil_image(b64=APP_ICON, size=48)

            return img
        except Exception as e:
            log('systray: tray_icon', e)
            if config.TEST_MODE:
                raise e

    def run(self):
        # not supported on mac
        if config.operating_system == 'Darwin':
            log('Systray is not supported on mac yet')
            return

        options_map = {'Show': self.show_main_window,
                       'Minimize to Systray': self.minimize_to_systray,
                       'Quit': self.quit}

        # make our own Gtk statusIcon, since pystray failed to run icon properly on Gtk 3.0 from a thread
        if config.operating_system == 'Linux':
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk
                self.Gtk = Gtk

                # delete previous icon file (it might contains an icon file for old pyidm versions)
                delete_file(self.tray_icon_path)

                # save file to settings folder
                self.tray_icon.save(self.tray_icon_path, format='png')

                def icon_right_click(icon, button, time):
                    menu = Gtk.Menu()

                    for option, callback in options_map.items():
                        item = Gtk.MenuItem(label=option)
                        item.connect('activate', callback)
                        menu.append(item)

                    menu.show_all()
                    menu.popup(None, None, None, icon, button, time)

                icon = Gtk.StatusIcon()
                icon.set_from_file(self.tray_icon_path)
                icon.connect("popup-menu", icon_right_click)
                icon.connect('activate', self.show_main_window)

                self.active = True
                Gtk.main()
                return
            except Exception as e:
                log('Systray Gtk 3.0:', e, log_level=2)
                self.active = False

        # let pystray decide which backend to run
        try:
            from pystray import Icon, Menu, MenuItem
            items = []
            for option, callback in options_map.items():
                items.append(MenuItem(option, callback, default=True if option == 'Show' else False))

            menu = Menu(*items)
            self.icon = Icon('PyIDM', self.tray_icon, menu=menu)
            self.active = True
            self.icon.run()
        except Exception as e:
            log('systray: - run() - ', e)
            self.active = False

    def shutdown(self):
        try:
            self.active = False
            self.icon.stop()  # must be called from main thread
        except:
            pass

        try:
            # quit main, might raise (Gtk-CRITICAL **:gtk_main_quit: assertion 'main_loops != NULL' failed)
            # but it has no side effect and PyIDM quit normally
            self.Gtk.main_quit()
        except:
            pass

    def quit(self, *args):
        """callback when selecting quit from systray menu"""
        # thread safe call for main window close
        self.main_window.run_method(self.main_window.quit)

