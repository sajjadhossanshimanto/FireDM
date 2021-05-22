"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        Main application gui design by tkinter
"""
import datetime
import re
import time
import pycurl
import tkinter as tk
import awesometkinter as atk
from tkinter import ttk, filedialog, colorchooser
from awesometkinter.version import __version__ as atk_version
import PIL
from queue import Queue
import os, sys
from packaging.version import parse as parse_version


if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

    __package__ = 'firedm'
    import firedm

from .view import IView
from .controller import Controller, set_option, get_option
from .utils import *
from . import config
from . import iconsbase64
from .iconsbase64 import *
from .systray import SysTray
from .about import about_notes


# theme colors as global constants, you must set their values before creating widgets
# use MainWindow.apply_theme() to set all values

# main colors
MAIN_BG = None
MAIN_FG = None

# side frame colors
SF_BG = None
SF_BTN_BG = None
SF_FG = None
SF_CHKMARK = None

THUMBNAIL_BG = None  # color of thumbnail frame in Home
THUMBNAIL_FG = None  # color of base thumbnail photo
THUMBNAIL_BD = None  # thumbnail border color

# progressbar
PBAR_BG = None
PBAR_FG = None
PBAR_TXT = None

ENTRY_BD_COLOR = None

BTN_BG = None
BTN_FG = None
BTN_HBG = None  # highlight background
BTN_ABG = None  # active background
BTN_AFG = None

HDG_BG = None   # heading e.g. "Network:" heading in Settings tab
HDG_FG = None

# scrollbar
SBAR_BG = None
SBAR_FG = None

# right click menu
RCM_BG = None
RCM_FG = None
RCM_ABG = None
RCM_AFG = None

# titlebar
TITLE_BAR_BG = None
TITLE_BAR_FG = None

# selection color for DItem
SEL_BG = None
SEL_FG = None

# key:(reference key, description), reference key will be used to get the color value in case of missing key, but in
# case of some font keys, reference key is refering to background color which will be used to calculate font color
# if reference key is None, this means it can't be calculated if missing
theme_map = dict(
    # main colors
    MAIN_BG=(None, 'Main background'),
    MAIN_FG=('MAIN_BG', 'Main text color'),

    # side frame colors
    SF_BG=(None, 'Side frame background'),
    SF_BTN_BG=(None, 'Side frame button color'),
    SF_FG=('SF_BG', 'Side frame text color'),
    SF_CHKMARK=('SF_BTN_BG', 'Side Frame check mark color'),

    # Thumbnails
    THUMBNAIL_BG=('SF_BG', 'Thumbnail background'),
    THUMBNAIL_FG=('MAIN_FG', 'Default Thumbnail image color'),
    THUMBNAIL_BD=('MAIN_FG', 'Thumbnail border width'),

    # progressbar
    PBAR_BG=(None, 'Progressbar inactive ring color'),
    PBAR_FG=('MAIN_FG', 'Progressbar active ring color'),
    PBAR_TXT=('MAIN_BG', 'Progressbar text color'),

    # Entry
    ENTRY_BD_COLOR=('SF_BG', 'Entry widget border color'),

    # Button
    BTN_BG=('SF_BTN_BG', 'Button background'),
    BTN_FG=('BTN_BG', 'Button text color'),
    BTN_HBG=('SF_BG', 'Button highlight background'),
    BTN_ABG=('SF_BG', 'Button active background'),
    BTN_AFG=('BTN_ABG', 'Button active text color'),

    # Heading e.g. "Network:" heading in Settings tab
    HDG_BG=('SF_BTN_BG', 'Heading title background'),
    HDG_FG=('HDG_BG', 'Heading title text color'),

    # scrollbar
    SBAR_BG=('MAIN_BG', 'Scrollbar background'),
    SBAR_FG=('MAIN_FG', 'scrollbar active color'),

    # right click menu
    RCM_BG=('MAIN_BG', 'Right click menu background'),
    RCM_FG=('RCM_BG', 'Right click menu text color'),
    RCM_ABG=('BTN_BG', 'Right click menu active background'),
    RCM_AFG=('RCM_ABG', 'Right click menu active text color'),

    # Window titlebar
    TITLE_BAR_BG=('BTN_BG', 'Window custom titlebar background'),
    TITLE_BAR_FG=('BTN_FG', 'Window custom titlebar text color'),

    # Download item (DItem)
    SEL_BG=('SF_BG', 'Download item selection background'),
    SEL_FG=('SF_FG', 'Download item selection foreground')
    )


# fonts keys in theme map
theme_fonts_keys = ('MAIN_FG', 'SF_FG', 'BTN_FG', 'BTN_AFG', 'PBAR_TXT', 'HDG_FG', 'RCM_FG', 'RCM_AFG')


builtin_themes = {
    'light': {
        'MAIN_BG': 'white',
        'MAIN_FG': 'black',

        'SF_BG': '#ffad00',  # sf for side frame
        'SF_FG': 'black',
        'SF_BTN_BG': '#006cff',
        'SF_CHKMARK': '#006cff',  # side frame's check mark

        'THUMBNAIL_BG': '#ffad00',  # color of thumbnail frame in Home
        'THUMBNAIL_FG': '#006cff',  # color of base thumbnail photo
        'THUMBNAIL_BD': '#006cff',  # thumbnail border color

        'PBAR_BG': 'grey',  # progressbar
        'PBAR_FG': '#006cff',
        'PBAR_TXT': 'black',

        'ENTRY_BD_COLOR': '#ffad00',

        'BTN_BG': '#006cff',
        'BTN_FG': 'white',
        'BTN_HBG': '#ffad00',  # highlight background
        'BTN_ABG': '#ffad00',  # active background
        'BTN_AFG': 'white',  # active foreground

        'HDG_BG': '#006cff',   # heading e.g. Network: heading in Settings tab
        'HDG_FG': 'white',

        'SBAR_BG': '#ffad00',  # scrollbar
        'SBAR_FG': '#006cff',

        # right click menu
        'RCM_BG': 'white',
        'RCM_FG': 'black',
        'RCM_ABG': '#006cff',
        'RCM_AFG': 'white',

        # title bar
        'TITLE_BAR_BG': '#006cff',
        'TITLE_BAR_FG': 'white',

        # selection color for DItem
        'SEL_BG': 'blue',
        'SEL_FG': 'white'

    },
    'dark': {"MAIN_BG": "#1c1c21", "MAIN_FG": "white", "SF_BG": "#000300", "SF_FG": "white", "SF_BTN_BG": "#d9dc4b",
             "SF_CHKMARK": "#d9dc4b", "THUMBNAIL_BG": "#000300", "THUMBNAIL_FG": "#d9dc4b", "PBAR_BG": "#26262b",
             "PBAR_FG": "#d9dc4b", "PBAR_TXT": "white", "ENTRY_BD_COLOR": "#000300", "BTN_BG": "#d9dc4b",
             "BTN_FG": "black", "BTN_HBG": "#000300", "BTN_ABG": "#000300", "BTN_AFG": "white", "HDG_BG": "#d9dc4b",
             "HDG_FG": "black", "THUMBNAIL_BD": "#d9dc4b", "SBAR_BG": "#1c1c21", "SBAR_FG": "white",
             "RCM_BG": "#1c1c21", "RCM_FG": "white", "RCM_ABG": "#d9dc4b", "RCM_AFG": "black",
             "TITLE_BAR_BG": "#d9dc4b", "TITLE_BAR_FG": "black"}
}


def calculate_missing_theme_keys(theme):
    """calculate missing key colors
    Args:
        theme (dict): theme dictionary
    """

    # make sure we have main keys
    main_keys = ('MAIN_BG', 'SF_BG', 'SF_BTN_BG')
    default_theme = builtin_themes[config.DEFAULT_THEME]
    for key in main_keys:
        theme.setdefault(key, default_theme[key])

    # progressbar
    theme.setdefault('PBAR_BG', atk.calc_contrast_color(theme['MAIN_BG'], 10))

    for key in theme_fonts_keys:
        bg_key = theme_map[key][0]
        bg = theme.get(bg_key, default_theme[bg_key])
        theme.setdefault(key, atk.calc_font_color(bg))

    for key, v in theme_map.items():
        fallback_key = v[0]
        if fallback_key is not None:
            theme.setdefault(key, theme.get(fallback_key, default_theme[fallback_key]))


# calculate missing keys for builtin themes
for t in builtin_themes.values():
    calculate_missing_theme_keys(t)


# hold all user defined themes, user themes with the same names will override same builtin_themes
user_themes = {}


# widget's images, it will be updated with theme change
imgs = {}


def create_imgs():
    """create widget's images, should be called with theme change"""

    for k in ('refresh_icon', 'playlist_icon', 'subtitle_icon', 'about_icon', 'dropdown_icon', 'folder_icon',
              'play_icon', 'pause_icon', 'delete_icon'):
        v = iconsbase64.__dict__[k]

        if k == 'dropdown_icon':
            color = HDG_FG
        else:
            color = BTN_BG

        img = atk.create_image(b64=v, color=color)

        # on mouse hover image
        img.zoomed = atk.create_image(b64=v, color=color, size=int(img.width() * 1.2))
        imgs[k] = img


    imgs['blinker_icon'] = atk.create_image(b64=download_icon, color=BTN_BG, size=12)
    imgs['done_icon'] = atk.create_image(b64=done_icon, color=BTN_BG)
    imgs['hourglass_icon'] = atk.create_image(b64=hourglass_icon, color=BTN_BG)


app_icon_img = None
popup_icon_img = None

busy_callbacks = []


def busy_callback(callback):
    """decorator to prevent multiple execution of same function/method
    e.g. when press a button multiple times it will prevent multiple callback execution
    Note: the decorated function is responsible to remove itself from busy_callbacks list if it needs to be executed
          again.
    """
    def wrapper(*args, **kwargs):
        if callback not in busy_callbacks:
            busy_callbacks.append(callback)
            return callback(*args, **kwargs)
        else:
            log('function already running')

    # keep reference of original callback to use it later
    wrapper.original_callback = callback
    return wrapper


def free_callback(callback):
    """remove a callback from busy_callbacks list and make it available for calling again"""
    try:
        original_callback = getattr(callback, 'original_callback', None)
        busy_callbacks.remove(original_callback)
    except Exception as e:
        log('free_callback', e)


def url_watchdog(root):
    """monitor url links copied to clipboard
    intended to be run from a thread, and generate an event when find a new url

    Args:
        root (tk.Tk): root, toplevel, or any tkinter widget
    """
    log('url watchdog active!')
    old_data = ''
    new_data = ''

    # url regex
    # capture urls with: http, ftp, and file protocols
    url_reg = re.compile(r"^(https?|ftps?|file)://")

    while True:
        # monitor global termination flag
        if config.shutdown:
            break

        # read clipboard contents
        try:
            if config.monitor_clipboard:
                new_data = root.clipboard_get()
        except:
            new_data = ''

        # url processing
        if config.monitor_clipboard and new_data != old_data:
            if url_reg.match(new_data.strip()):
                root.event_generate('<<urlChangeEvent>>', when="tail")
                print('url_watchdog, new url: ', new_data)

            old_data = new_data

        # decrease cpu load
        time.sleep(2)


def center_window(window, width=None, height=None, set_geometry_wh=True, reference=None):
    """center a tkinter window on screen's center and set its geometry if width and height given

    Args:
        window (tk.root or tk.Toplevel): a window to be centered
        width (int): window's width
        height (int): window's height
        set_geometry_wh (bool): include width and height in geometry
        reference: tk window e.g parent window as a reference
    """

    # update_idletasks will cause a window to show early at the top left corner
    # then change position to center in non-proffesional way
    # window.update_idletasks()
    #
    #

    if width and height:
        if reference:
            refx = reference.winfo_x() + reference.winfo_width() // 2
            refy = reference.winfo_y() + reference.winfo_height() // 2
        else:
            refx = window.winfo_screenwidth() // 2
            refy = window.winfo_screenheight() // 2

        x = refx - width // 2
        y = refy - height // 2

        if set_geometry_wh:
            window.geometry(f'{width}x{height}+{x}+{y}')
        else:
            window.geometry(f'+{x}+{y}')

    else:
        window.eval('tk::PlaceWindow . center')


class ThemeEditor(tk.Toplevel):
    """create or edit themes
    in basic mode, user can change some basic colors and the rest of colors will be calculated automatically
    in advanced mode, all colors will be available to edit

    """
    def __init__(self, main, theme_name):
        """initialize

        Args:
            main (MainWindow obj): an instance of main gui class
            mode (str): "new" for new themes, "edit" to modify existing theme
        """
        tk.Toplevel.__init__(self)
        self.main = main
        self.title('Theme Editor')
        self.use_all_options = False

        self.is_color = self.main.is_color

        center_window(self, 100, 100, set_geometry_wh=False)

        # get theme name and current theme ----------------------------------------------------------------------------
        self.theme_name = tk.StringVar()
        self.theme_name.set(theme_name)
        self.current_theme = user_themes.get(config.current_theme) or builtin_themes.get(config.current_theme) or \
                             builtin_themes[config.DEFAULT_THEME]

        # some theme keys description ---------------------------------------------------------------------------------
        self.key_description = {k: v[1] for k, v in theme_map.items()}

        # frames ------------------------------------------------------------------------------------------------------
        self.main_frame = tk.Frame(self, bg='white')
        self.main_frame.pack(expand=True, fill='both')

        # hold color buttons and entries
        self.top_frame = atk.ScrollableFrame(self.main_frame)
        self.top_frame.pack(expand=True, fill='both')

        # hold apply button
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.pack(expand=False, fill='x')

        # hold basic color options
        basic_frame = tk.Frame(self.top_frame)
        basic_frame.pack(expand=True, fill='x')

        # hold advanced color options
        self.advanced_frame = tk.Frame(self.top_frame)

        # basic colors ------------------------------------------------------------------------------------------------
        basic_options = ['MAIN_BG', 'SF_BG', 'SF_BTN_BG', 'PBAR_FG']
        self.basic_vars = {k: tk.StringVar() for k in basic_options}

        # add basic options
        self.create_options(basic_frame, self.basic_vars)

        ttk.Separator(self.top_frame).pack(expand=True, fill='both')

        # advanced colors ---------------------------------------------------------------------------------------------
        advanced_options = [k for k in theme_map if k not in basic_options]
        self.advanced_vars = {k: tk.StringVar() for k in advanced_options}

        # add advanced options
        self.create_options(self.advanced_frame, self.advanced_vars)

        # apply button ------------------------------------------------------------------------------------------------
        tk.Entry(bottom_frame, textvariable=self.theme_name).pack(side='left', expand=True, fill='x')
        self.advanced_btn = tk.Button(bottom_frame, text='Advanced', command=self.toggle_advanced_options, bg=BTN_BG, fg=BTN_FG)
        self.advanced_btn.pack(side='left', anchor='e', padx=5, pady=5)
        tk.Button(bottom_frame, text='apply', command=self.apply, bg=BTN_BG, fg=BTN_FG).pack(side='left', anchor='e', padx=5, pady=5)

        # scroll with mousewheel
        atk.scroll_with_mousewheel(basic_frame, target=self.top_frame, apply_to_children=True)
        atk.scroll_with_mousewheel(self.advanced_frame, target=self.top_frame, apply_to_children=True)

        self.bind('<Escape>', lambda event: self.destroy())

    def toggle_advanced_options(self):
        self.use_all_options = not self.use_all_options

        if self.use_all_options:
            self.advanced_frame.pack(expand=True, fill='both')
            self.advanced_btn['text'] = 'Basic'
        else:
            self.advanced_frame.pack_forget()
            self.advanced_btn['text'] = 'Advanced'
            self.top_frame.scrolltotop()

    def create_options(self, parent, vars_map):
        """create option widgets

        Args:
            parent: tk parent frame
            vars_map (dict): theme keys vs vars
        """

        for key, var in vars_map.items():
            bg = self.current_theme.get(key)
            var.set(bg)
            fg = atk.calc_font_color(bg) if bg else None
            name = self.key_description.get(key) or key

            f = tk.Frame(parent)
            entry = tk.Entry(f, textvariable=var)
            btn = tk.Button(f, text=name, bg=bg, activebackground=bg, fg=fg, activeforeground=fg)
            btn['command'] = lambda v=var, b=btn, e=entry: self.pick_color(v, b, e)
            btn.pack(side='left', expand=True, fill='x')
            entry.pack(side='left', ipady=4)
            f.pack(expand=True, fill='x', padx=5, pady=5)

    def pick_color(self, var, btn, entry):
        """show color chooser to select a color"""
        color = var.get()
        if not self.is_color(color):
            color = 'white'
        new_color = colorchooser.askcolor(color=color, parent=self)
        if new_color:
            new_color = new_color[-1]
            if new_color:
                var.set(new_color)
                fg = atk.calc_font_color(new_color)
                btn.config(bg=new_color, activebackground=new_color, fg=fg)

    def apply(self):

        # quit this window
        self.destroy()

        theme_name = self.theme_name.get()

        # avoid builtin theme name
        if theme_name in builtin_themes:
            all_names = list(builtin_themes.keys()) + list(user_themes.keys())
            i = 2
            name = f'{theme_name}{i}'
            while name in all_names:
                i += 1
                name = f'{theme_name}{i}'

            theme_name = name

        vars_map = {}
        vars_map.update(self.basic_vars)

        if self.use_all_options:
            vars_map.update(self.advanced_vars)
        else:
            # get user changes in advanced options
            changed = {k: var for k, var in self.advanced_vars.items() if self.current_theme[k] != var.get()}
            vars_map.update(changed)

        kwargs = {k: v.get() for k, v in vars_map.items() if self.is_color(v.get())}

        theme = user_themes[theme_name] = kwargs

        # theme.update(kwargs)
        calculate_missing_theme_keys(theme)

        # apply theme
        self.main.apply_theme(theme_name)


class Button(tk.Button):
    """normal tk button that follows current theme and act as a transparent if it has an image"""
    def __init__(self, parent, transparent=False, **kwargs):
        options = {}
        parent_bg = atk.get_widget_attribute(parent, 'background')
        image = kwargs.get('image', None)
        options['cursor'] = 'hand2'

        if image or transparent:
            # make transparent
            options['bg'] = parent_bg
            options['fg'] = atk.calc_font_color(parent_bg)
            options['activebackground'] = parent_bg
            options['highlightbackground'] = parent_bg
            options['highlightthickness'] = 0
            options['activeforeground'] = atk.calc_font_color(parent_bg)
            options['bd'] = 0

        else:
            options['bg'] = BTN_BG
            options['fg'] = BTN_FG
            options['highlightbackground'] = BTN_HBG
            options['activebackground'] = BTN_ABG
            options['activeforeground'] = BTN_AFG
            options['padx'] = 8

        options.update(kwargs)

        tk.Button.__init__(self, parent, **options)

        # on mouse hover effect
        if image and hasattr(image, 'zoomed'):
            self.bind('<Enter>', lambda e: self.config(image=image.zoomed))
            self.bind('<Leave>', lambda e: self.config(image=image))


class Combobox(ttk.Combobox):
    def __init__(self, parent, values, selection=None, callback=None, **kwargs):
        self.selection = selection
        self.selection_idx = None
        self.callback = callback

        # style
        s = ttk.Style()
        custom_style = 'custom.TCombobox'
        # combobox is consist of a text area, down arrow, and dropdown menu (listbox)
        # arrow: arrowcolor, background
        # text area: foreground, fieldbackground
        # changing dropdown menu (Listbox) colors will be changed in MainWindow>apply_theme()
        arrow_bg = SF_BG
        textarea_bg = BTN_BG
        s.configure(custom_style, arrowcolor=atk.calc_font_color(arrow_bg),
                    foreground=atk.calc_font_color(textarea_bg), padding=4, relief=tk.RAISED)
        s.map(custom_style, fieldbackground=[('', textarea_bg)], background=[('', arrow_bg)])

        # default options
        options = dict(state="readonly", values=values, style=custom_style)

        # update options
        options.update(kwargs)

        # initialize super
        ttk.Combobox.__init__(self, parent, **options)

        # bind selection
        self.bind('<<ComboboxSelected>>', self.on_selection)

        # selection
        if selection is not None:
            self.set(selection)

    def on_selection(self, event):
        widget = event.widget
        widget.selection_clear()

        self.selection = widget.get()
        self.selection_idx = widget.current()

        if callable(self.callback):
            self.callback()


class AutoWrappingLabel(tk.Label):
    """auto-wrapping label
    wrap text based on widget changing size
    """
    def __init__(self, parent=None, justify='left', anchor='w', **kwargs):
        tk.Label.__init__(self, parent, justify=justify, anchor=anchor, **kwargs)
        self.bind('<Configure>', lambda event: self.config(wraplength=self.winfo_width()))


class CustomTitleBar(tk.Frame):
    """custom title bar"""
    def __init__(self, parent, bg, fg, afg, title='', minimize=False, maximize=False):
        tk.Frame.__init__(self, parent, bg=bg)

        self.bg = bg
        self.fg = fg
        self.afg = afg

        self.x = None
        self.y = None

        # get top level
        self.top = self.winfo_toplevel()

        # remove window manager's title bar
        self.top.overrideredirect(1)

        # buttons
        self.create_button('✖', self.top.destroy).pack(side='right', padx=3, pady=0)

        if maximize:
            self.create_button('🔺', self.toggle_maximize).pack(side='right', padx=0, pady=0)

        if minimize:
            self.create_button('🔻', self.iconify).pack(side='right', padx=0, pady=0)

        # icon
        tk.Label(self, image=popup_icon_img, bg=bg, fg=fg).pack(side='left', padx=5, pady=3)

        title = tk.Label(self, text=title, bg=bg, fg=fg)
        title.pack(side='right', padx=5, fill='x', expand=True)

        # move window with mouse move, credit to https://stackoverflow.com/a/4055612/10146012
        for w in (self, title):
            w.bind("<ButtonPress-1>", self.start_move)
            w.bind("<ButtonRelease-1>", self.stop_move)
            w.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.top.winfo_x() + deltax
        y = self.top.winfo_y() + deltay
        self.top.geometry(f"+{x}+{y}")

    def create_button(self, text, callback):
        # make transparent
        options = {}
        options['bg'] = self.bg
        options['fg'] = self.fg
        options['activebackground'] = self.bg
        options['activeforeground'] = self.afg
        options['highlightbackground'] = self.bg
        options['highlightthickness'] = 0
        options['bd'] = 0
        options['text'] = text
        options['command'] = callback

        return tk.Button(self, **options)
        # return tk.Button(self, text=text)

    def toggle_maximize(self):
        # self.top.overrideredirect(0)
        self.top.wm_attributes('-zoomed', not self.top.attributes('-zoomed'))
        # self.top.overrideredirect(1)

    def iconify(self):
        # self.top.overrideredirect(0)
        self.top.iconify()


class Popup(tk.Toplevel):
    """popup window
    show simple messages, get user text input and save user choice "pressed button"
    to get user response you call show() and it will block until window is closed

    usage:

        window = Popup('Deleting "video.mp4" file', 'are you sure?',  buttons=['Yes', 'Cancel'], parent=root)
        response = window.show()
        if response == 'Yes':
            do stuff ....

    """
    def __init__(self, *args, buttons=None, parent=None, title='Attention', get_user_input=False, default_user_input='',
                 bg=None, fg=None, custom_widget=None):
        """initialize

        Args:
            args (str): any number of string messages, each message will be in a different line
            buttons (list, tuple): list of buttons names, if user press a button, its name will be returned in response
            parent (root window): parent window, preferred main app. window or root
            title (str): window title
            get_user_input (bool): if True, an entry will be included to get user text input, e.g. new filename
            default_user_input (str): what to display in entry widget if get_user_input is True
            bg (str): background color
            fg (str): text color
            custom_widget: any tk widget you need to add to popup window

        """
        self.parent = parent
        self.msg = '\n'.join(args)
        self.buttons = buttons or ['Ok', 'Cancel']
        self.bg = bg or MAIN_BG
        self.fg = fg or MAIN_FG
        self.window_title = title
        self.get_user_input = get_user_input
        self.default_user_input = default_user_input
        self.custom_widget = custom_widget

        # entry variable
        self.user_input = tk.StringVar()
        self.user_input.set(self.default_user_input)

        # user response
        self.response = (None, None) if self.get_user_input else None

    def show(self):
        """display popup window
        this is a blocking method and it will return when window closed

        Returns:
            (str or tuple): name of pressed button or in case of "get_user_input" is True, a list of pressed button
            and entry text value will be returned
        """
        tk.Toplevel.__init__(self, self.parent)

        self.title(self.window_title)

        self.config(background=SF_BG)

        # keep popup on top
        self.wm_attributes("-topmost", 1)

        # set geometry
        # will set size depend on parent size e.g 0.5 width and 0.3 height
        width = int(self.parent.winfo_width() * 0.5)
        height = int(self.parent.winfo_height() * 0.3)
        self.minsize(width, height)
        self.maxsize(self.parent.winfo_width(), self.parent.winfo_height())

        center_window(self, width=width, height=height, reference=self.parent, set_geometry_wh=False)

        self.create_widgets()

        self.update_idletasks()

        self.focus()

        # focus on entry widget
        if self.get_user_input:
            self.user_entry.focus()

        # block and wait for window to close
        self.wait_window(self)

        return self.response

    def create_widgets(self):
        f = tk.Frame(self, bg=SF_BG)
        f.pack(expand=True, fill='both')

        # title_bar = CustomTitleBar(f, bg=TITLE_BAR_BG, fg=TITLE_BAR_FG, afg=BTN_ABG, title=self.window_title)
        # title_bar.pack(side='top', fill='x')

        main_frame = tk.Frame(f, bg=self.bg)
        main_frame.pack(padx=(5, 1), pady=(5, 1), expand=True, fill='both')

        # add buttons
        btns_fr = tk.Frame(main_frame, bg=self.bg)
        btns_fr.pack(side='bottom', anchor='e', padx=5)
        for btn_name in self.buttons:
            Button(btns_fr, command=lambda button_name=btn_name: self.button_callback(button_name),
                   text=btn_name).pack(side='left', padx=(5, 2), pady=5)

            # bind Enter key for first key
            if btn_name == self.buttons[0]:
                self.bind('<Return>', lambda event: self.button_callback(self.buttons[0]))

        # separator
        ttk.Separator(main_frame, orient='horizontal').pack(side='bottom', fill='x')

        # custom widget
        if self.custom_widget:
            self.custom_widget.pack(side='bottom', fill='x')

        # get user input
        if self.get_user_input:
            self.user_entry = tk.Entry(main_frame, textvariable=self.user_input, bg='white', fg='black', relief=tk.FLAT,
                                       bd=5, highlightcolor=ENTRY_BD_COLOR, highlightbackground=ENTRY_BD_COLOR)
            self.user_entry.pack(side='bottom', fill='x', padx=5, pady=5)

        # msg
        msg_height = len(self.msg.splitlines())
        if msg_height < 4:
            AutoWrappingLabel(main_frame, text=self.msg, bg=self.bg, fg=self.fg,
                              width=40).pack(side='top', fill='x', expand=True, padx=5, pady=5)
        else:
            txt = atk.ScrolledText(main_frame, bg=self.bg, fg=self.fg, wrap=True, autoscroll=False, hscroll=False,
                                   height=min(15, msg_height + 1))
            txt.set(self.msg)
            txt.pack(side='top', fill='x', expand=True, padx=5, pady=5)

        self.bind('<Escape>', lambda event: self.close())

    def button_callback(self, button_name):
        self.destroy()

        if self.get_user_input:
            self.response = (button_name, self.user_input.get())

        else:
            self.response = button_name

    def focus(self):
        """focus window and bring it to front"""
        self.focus_force()

    def close(self):
        self.destroy()


class ExpandCollapse(tk.Frame):
    """Expand collapse widget for frames
    basically will grid remove children widget from the target frame and resize frame to a small size e.g. 10 px
    """
    def __init__(self, parent, target, bg, fg, **kwargs):
        """initialize frame

        Args:
            parent (tk Frame): parent
            target (tk Frame): the target frame which will be collapsed / expanded
            bg (str): background color of this frame
            button_bg (str): button's background color
            button_fg (str): button's text color
        """
        tk.Frame.__init__(self, parent, bg='red', **kwargs)
        self.rowconfigure(0, weight=1)

        self.target = target

        self.label = tk.Label(self, text='⟪', bg=bg, fg=fg)
        self.label.pack(expand=True, fill='y')
        self.label.bind("<1>", self.toggle)

        # status
        self.collapsed = False

    def toggle(self, *args):
        """toggle target state"""
        if self.collapsed:
            self.expand()
        else:
            self.collapse()

    def expand(self):
        """expand target"""
        for child in self.target.winfo_children():
            child.grid()
        # self.target.grid()
        self.collapsed = False
        self.label['text'] = '⟪'

    def collapse(self):
        """collapse target"""
        for child in self.target.winfo_children():
            child.grid_remove()

        self.target['width'] = 10

        self.collapsed = True
        self.label['text'] = '⟫'


class SideFrame(tk.Frame):
    """side frame on the left containing navigation buttons
    it should have buttons like Home, Settings, Downloads, etc...
    """
    def __init__(self, parent):

        tk.Frame.__init__(self, parent, bg=SF_BG)
        # colors
        self.bg = SF_BG
        self.text_color = SF_FG
        self.button_color = SF_BTN_BG  # button image color, the actual button background will match frame bg
        self.checkmark_color = SF_CHKMARK

        s = ttk.Style()

        # create radio buttons map (name: button_obj)
        self.buttons_map = dict()

        # create buttons variable "one shared variable for all radio buttons"
        self.var = tk.StringVar()
        self.var.trace_add('write', self.on_button_selection)

        # create style for radio button inherited from normal push button
        self.side_btn_style = 'sb.TButton'

        # create layout with no focus dotted line
        s.layout(self.side_btn_style,
                 [('Button.border', {'sticky': 'nswe', 'border': '1', 'children':
                 [('Button.padding', {'sticky': 'nswe','children': [('Button.label', { 'sticky': 'nswe'})]})]})])
        s.configure(self.side_btn_style, borderwidth=0, foreground=self.text_color, anchor='center')
        s.map(self.side_btn_style, background=[('', self.bg)])

        # tabs mapping, normally it will be frames e.g. {'Home': home_frame, 'Settings': settings_frame, ... }
        self.tabs_mapping = dict()

    def set_default(self, button_name):
        """set default selected button and shown tab

        Args:
            button_name (str): button name
        """

        self.var.set(button_name)

    def create_button(self, text, fp=None, color=None, size=None, b64=None, target=None):
        """Create custom widget
        frame containing another frame as a check mark and a button

        Args:
            text (str): button's text
            fp: A filename (string), pathlib.Path object or a file object. The file object must implement read(), seek(),
            and tell() methods, and be opened in binary mode.
            color (str): color in tkinter format, e.g. 'red', '#3300ff', also color can be a tuple or a list of RGB,
            e.g. (255, 0, 255)
            size (2-tuple(int, int)): an image required size in a (width, height) tuple
            b64 (str): base64 hex representation of an image, if "fp" is given this parameter will be ignored
            target (tk Frame): a target frame (tab) that will be shown when pressing on this button

        Returns:
            ttk.RadioButton: with TButton style and grid method of parent frame
        """
        color = color or self.button_color
        size = size

        # create image from specified path
        img = atk.create_image(fp=fp, color=color, size=size, b64=b64)
        img.zoomed = atk.create_image(b64=b64, color=color, size=int(img.width() * 1.2))

        # create frame to hold custom widget
        f = tk.Frame(self, bg=SF_BG)

        # resizable
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1)

        # create check mark
        checkmark = tk.Frame(f, width=7)
        checkmark.grid_propagate(0)
        checkmark.grid(row=0, column=0, sticky='wns')

        # create radio button
        # self.side_btn_style = 'TButton'
        btn = ttk.Radiobutton(f, text=text, image=img, compound='top', style=self.side_btn_style, variable=self.var,
                              value=text, cursor='hand2')
        btn.grid(row=0, column=1, sticky='ewns', padx=5, pady=10)

        # on mouse hover effect
        btn.bind('<Enter>', lambda e: btn.config(image=img.zoomed))
        btn.bind('<Leave>', lambda e: btn.config(image=img))

        # make some references
        btn.checkmark = checkmark
        btn.img = img
        btn.frame = f

        btn.grid = f.grid  # if you grid this button it will grid its parent frame instead

        self.buttons_map[text] = btn

        # Register target frame
        if target:
            self.register_tab(text, target)

        # grid button, will add padding for first button to keep space on top
        if len(self.buttons_map) == 1:
            f.grid(sticky='ew', pady=(20, 0))
        else:
            f.grid(sticky='ew')

        return btn

    def activate_checkmark(self, button_name):
        """activate check mark for selected button

        Args:
            button_name (str): button or tab name e.g. Home, Settings, etc
        """
        for btn in self.buttons_map.values():
            btn.checkmark.config(background=self.bg)

        selected_btn = self.buttons_map[button_name]
        selected_btn.checkmark.config(background=self.checkmark_color)

    def select_tab(self, tab_name):
        """ungrid all tabs(frames) and grid only the selected tab (frame) in main frame

        Args:
            tab_name (str): tab name e.g. Home, Settings, etc
        """

        try:
            # do nothing if tab already selected
            if self.tabs_mapping[tab_name].winfo_viewable():
                return

            selected_tab = self.tabs_mapping[tab_name]
            for tab in self.tabs_mapping.values():
                if tab is not selected_tab:
                    tab.grid_remove()

            selected_tab.grid(row=1, column=2, sticky='ewns')
            self.activate_checkmark(tab_name)
        except:
            pass

    def on_button_selection(self, *args):
        """it will be called when a radio button selected"""

        button_name = self.var.get()
        self.select_tab(button_name)

    def register_tab(self, tab_name, tab):
        """Register a frame as a tab

        Args:
            tab_name (str): tab name e.g. Home, Settings, etc...
            tab (tk object): tk or ttk frame
        """
        self.tabs_mapping[tab_name] = tab


class MediaListBox(tk.Frame):
    """Create a custom listbox
    will be used for playlist menu and stream menu
    """
    def __init__(self, parent, background=None, title=None, **kwargs):
        """Initialize object
        Args:
            parent: tk parent Frame
            background (str): background color
            var (tk.StringVar): listbox variable
            title (str): title, e.g. Playlist, Stream Quality
        """
        self.background = background or 'white'
        kwargs['background'] = self.background
        kwargs['bd'] = 1
        tk.Frame.__init__(self, parent, **kwargs)

        s = ttk.Style()

        self.var = tk.Variable()

        self.columnconfigure(0, weight=1)
        # self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.title_var = tk.StringVar()
        self.title_var.set(title)
        self.original_title = title  # needed to reset title later
        tk.Label(self, textvariable=self.title_var, background=self.background, foreground=MAIN_FG, font='any 10 bold').grid(padx=5, pady=5, sticky='w')

        self.listbox = tk.Listbox(self, background=self.background, foreground=MAIN_FG, relief='sunken', bd=0,
                                  highlightthickness=0, listvariable=self.var, width=20, height=6,
                                  selectmode=tk.SINGLE, selectbackground=SF_CHKMARK, activestyle='none',
                                  selectforeground=atk.calc_font_color(SF_CHKMARK), exportselection=0)
        self.listbox.grid(padx=5, pady=5, sticky='ewns')

        self.bar = atk.RadialProgressbar(parent=self, size=(100, 100), fg=PBAR_FG, text_bg=self.background, text_fg=PBAR_TXT)

        # v_scrollbar
        custom_sb_style = 'm.Vertical.TScrollbar'
        s.layout(custom_sb_style, [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children':
                                                   [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])
        s.configure(custom_sb_style, troughcolor=MAIN_BG, borderwidth=1, relief='flat', width=5)
        s.map(custom_sb_style, background=[('', MAIN_FG)])
        self.v_scrollbar = ttk.Scrollbar(self, orient='vertical', style=custom_sb_style)
        self.v_scrollbar.grid(row=1, column=1, padx=5, pady=5, sticky='ns')
        self.v_scrollbar.grid_remove()

        # link scrollbar to listbox
        self.v_scrollbar['command'] = self.listbox.yview
        self.listbox['yscrollcommand'] = self.v_scrollbar_set

        # h_scrollbar
        custom_hsb_style = 'mh.Horizontal.TScrollbar'
        s.layout(custom_hsb_style, [('Horizontal.Scrollbar.trough', {'sticky': 'we', 'children':
            [('Horizontal.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])

        s.configure(custom_hsb_style, troughcolor=MAIN_BG, borderwidth=1, relief='flat', width=5)
        s.map(custom_hsb_style, background=[('', MAIN_FG)])  # slider color
        self.h_scrollbar = ttk.Scrollbar(self, orient='horizontal', style=custom_hsb_style)
        self.h_scrollbar.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        self.h_scrollbar.grid_remove()

        # link scrollbar to listbox
        self.h_scrollbar['command'] = self.listbox.xview
        self.listbox['xscrollcommand'] = self.h_scrollbar_set

        self.show_progressbar()
        # self.set_progressbar(75)

        self.set = self.var.set
        self.get = self.var.get

    def v_scrollbar_set(self, start, end):
        """Auto-hide scrollbar if not needed"""

        scrollbar = self.v_scrollbar

        # values of start, end should be 0.0, 1.0 when listbox doesn't need scroll
        if float(start) > 0 or float(end) < 1:
            scrollbar.grid()
        else:
            scrollbar.grid_remove()

        scrollbar.set(start, end)

    def h_scrollbar_set(self, start, end):
        """Auto-hide scrollbar if not needed"""
        scrollbar = self.h_scrollbar

        # values of start, end should be 0.0, 1.0 when listbox doesn't need scroll
        if float(start) > 0 or float(end) < 1:
            scrollbar.grid()
        else:
            scrollbar.grid_remove()

        scrollbar.set(start, end)

    def show_progressbar(self):
        # self.stop_progressbar()
        self.bar.place(relx=0.5, rely=0.55, anchor="center")

    def hide_progressbar(self):
        self.reset_progressbar()
        self.bar.place_forget()

    def set_progressbar(self, value):
        self.bar.var.set(value)

    def start_progressbar(self):
        self.bar.start()

    def stop_progressbar(self):
        self.bar.stop()

    def reset_progressbar(self):
        self.stop_progressbar()
        self.set_progressbar(0)

    def select(self, idx=None):
        """select item in ListBox

        Args:
            idx (int): number of row to be selected, index from zero, if this parameter is not set it will return
            current selected row

        Returns:
            int: current row number
        """

        if idx is None:
            try:
                return self.listbox.curselection()[0]
            except:
                pass
        else:
            # clear selection first
            self.listbox.selection_clear(0, tk.END)

            # select item number idx
            self.listbox.selection_set(idx)

    def set_listbox_values(self, values):
        self.var.set(values)

    def reset(self):
        self.set_listbox_values([])
        self.reset_progressbar()
        self.show_progressbar()
        self.update_title(self.original_title)

    def update_title(self, title):
        self.title_var.set(title)


class FileProperties(ttk.Frame):
    """file info display

    Example:
        Name:   The search for new planets.mp4
        Size:   128.0 MB
        Folder: /home/downloads
        video dash - Resumable: yes
    """
    def __init__(self, parent=None):
        ttk.Frame.__init__(self, parent)
        self.columnconfigure(1, weight=1)
        self.bg = MAIN_BG
        self.fg = MAIN_FG
        s = ttk.Style()

        self.style = 'FileProperties.TFrame'
        s.configure(self.style, background=self.bg)
        self.config(style=self.style)

        # variables
        self.title = tk.StringVar()
        self.extension = tk.StringVar()
        self.folder = tk.StringVar()
        self.size = tk.StringVar()
        self.type = tk.StringVar()
        self.subtype = tk.StringVar()
        self.resumable = tk.StringVar()

        # show default folder value
        self.update(folder=config.download_folder)

        self.create_widgets()

    @property
    def name(self):
        title = atk.render_bidi_text(self.title.get())

        ext = self.extension.get()
        if not ext.startswith('.'):
            ext = '.' + ext

        return title + ext

    def create_widgets(self):
        def label(text='', textvariable=None, r=1, c=0, rs=1, cs=1, sticky='we'):
            return AutoWrappingLabel(self, text=text, textvariable=textvariable, bg=self.bg, fg=self.fg, anchor='w'). \
                grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)

        def separator(r):
            return ttk.Separator(self, orient='horizontal').grid(sticky='ew', pady=0, row=r, column=0, columnspan=3)

        # order of properties
        fields = ('name', 'extension', 'folder', 'size', 'misc')
        row = {k: fields.index(k)*2+1 for k in fields}

        for n in row.values():
            separator(n + 1)

        # name ---------------------------------------------------------------------------------------------------------
        label('Name:', sticky='nw')
        # can not make an auto wrapping entry, will use both label and entry as a workaround
        self.title_entry = tk.Entry(self, textvariable=self.title)
        self.title_entry.grid(row=row['name'], column=1, columnspan=2, sticky='we')
        self.title_entry.grid_remove()

        # add bidi support for entry widget to enable editing Arabic titles
        atk.add_bidi_support(self.title_entry)

        self.title_lbl = AutoWrappingLabel(self, textvariable=self.title,  bg=self.bg, fg=self.fg, anchor='w')
        self.title_lbl.grid(row=row['name'], column=1, columnspan=2, sticky='we')

        # hide label and show entry widget when left click
        self.title_lbl.bind('<1>', lambda event: self.start_name_edit())

        # hide entry widget and show label widget
        self.title_entry.bind('<FocusOut>', lambda event: self.done_name_edit())

        # extension ----------------------------------------------------------------------------------------------------
        label('Ext:', r=row['extension'], c=0)

        self.ext_entry = tk.Entry(self, textvariable=self.extension, bg=self.bg, fg=self.fg, highlightthickness=0,
                                  relief='flat')
        self.ext_entry.grid(row=row['extension'], column=1, columnspan=2, sticky='ew')
        self.ext_entry.bind('<FocusIn>', lambda event: self.ext_entry.config(bg='white', fg='black'))
        self.ext_entry.bind('<FocusOut>', lambda event: self.ext_entry.config(bg=self.bg, fg=self.fg))

        # size ---------------------------------------------------------------------------------------------------------
        label('Size:', r=row['size'], c=0)
        label('540 MB', textvariable=self.size, r=row['size'], c=1)

        # misc ---------------------------------------------------------------------------------------------------------
        misc_frame = tk.Frame(self, bg=self.bg)
        misc_frame.grid(row=row['misc'], column=0, columnspan=3, sticky='ew')
        for var in (self.type, self.subtype, self.resumable):
            tk.Label(misc_frame, textvariable=var, bg=self.bg, fg=self.fg, anchor='w').pack(sid='left')

        # download folder -------------------------------------------------------------------------------------------
        label('Folder:', r=row['folder'], c=0)

        def update_frequent_folders(*args):
            try:
                config.frequent_download_folders.remove(self.folder.get())
            except:
                pass

            # add current folder value at the beginning of the list and limit list size to 10 items
            if self.folder.get():
                config.frequent_download_folders = [self.folder.get()] + config.frequent_download_folders[:9]

                # update combobox
                cb.config(values=config.frequent_download_folders)

        # style
        s = ttk.Style()
        custom_style = 'downloadfolder.TCombobox'
        arrow_bg = SF_BG
        textarea_bg = MAIN_BG
        s.configure(custom_style, arrowcolor=atk.calc_font_color(arrow_bg),
                    foreground=MAIN_FG, padding=2, relief=tk.RAISED, borderwidth=0, arrowsize=16)
        s.map(custom_style, fieldbackground=[('', textarea_bg)], background=[('', arrow_bg)])

        cb = ttk.Combobox(self, exportselection=0, textvariable=self.folder, values=config.frequent_download_folders,
                          style=custom_style)
        cb.grid(row=row['folder'], column=1, sticky='we', pady=5)
        cb.bind('<FocusOut>', update_frequent_folders, add='+')
        cb.bind('<1>', update_frequent_folders, add='+')
        cb.bind('<<ComboboxSelected>>', lambda event: cb.selection_clear(), add='+')

        # update global download folder with every widget edit
        self.folder.trace_add('write', lambda *args: set_option(download_folder=self.folder.get()))

        Button(self, text='', image=imgs['folder_icon'], transparent=True,
               command=self.change_folder).grid(row=row['folder'], column=2, padx=(8, 1), pady=0)

    def update(self, **kwargs):
        """update widget's variable
        example arguments: {'rendered_name': 'The search for new planets.mp4', 'folder': '/home/downloads',
        'type': 'video', 'subtype_list': ['dash', 'fragmented'], 'resumable': True, 'total_size': 100000}

        """
        title = kwargs.get('title', None)
        extension = kwargs.get('extension', None)
        rendered_name = kwargs.get('rendered_name', None)
        size = kwargs.get('total_size', None)
        folder = kwargs.get('folder', None)
        type_ = kwargs.get('type', '')
        subtype_list = kwargs.get('subtype_list', '')
        resumable = kwargs.get('resumable', None)

        if title:
            rendered_title = atk.render_bidi_text(title)
            self.title.set(rendered_title)

        if extension:
            self.extension.set(extension.replace('.', ''))  # remove '.'

        if folder:
            self.folder.set(folder)
        if size is not None:
            self.size.set(f'{size_format(size) if size > 0 else "unknown"}')
        if type_:
            self.type.set(type_)
        if subtype_list:
            self.subtype.set(', '.join(subtype_list))

        self.resumable.set(f'- Resumable: {resumable}' if resumable is not None else '')

    def reset(self):
        self.title.set('')
        self.extension.set('')
        self.folder.set(config.download_folder)
        self.size.set('...')
        self.type.set('')
        self.subtype.set('')
        self.resumable.set('')

    def change_folder(self):
        """select folder from system and update folder field"""
        folder = filedialog.askdirectory(initialdir=self.folder.get())
        if folder:
            self.folder.set(folder)
            set_option(download_folder=folder)

    def start_name_edit(self):
        """remove label and show edit entry with raw name"""
        self.title_lbl.grid_remove()
        self.title_entry.grid()
        self.title_entry.focus()
        self.title_entry.icursor("end")

    def done_name_edit(self):
        """hide name entry widget, create rendered name and show it in name label"""
        self.title_entry.grid_remove()
        self.title_lbl.grid()


class Thumbnail(tk.Frame):
    """Thumbnail image in home tab"""
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg=THUMBNAIL_BG)

        self.default_img = atk.create_image(b64=wmap_icon, color=THUMBNAIL_FG)
        self.current_img = None

        tk.Label(self, text='Thumbnail:', bg=MAIN_BG, fg=MAIN_FG).pack(padx=5, pady=(5, 0), anchor='w')

        # image label
        self.label = tk.Label(self, bg=MAIN_BG, image=self.default_img)
        self.label.pack(padx=5, pady=5)

    def reset(self):
        """show default thumbnail"""
        self.label['image'] = self.default_img

    def show(self, img=None, b64=None):
        """show thumbnail image
        Args:
            img (tk.PhotoImage): tkinter image to show
            b64 (str): base64 representation of an image
        """

        if b64:
            img = tk.PhotoImage(data=b64)

        if img and img is not self.current_img:
            self.current_img = img
            self.label['image'] = img


class DItem(tk.Frame):
    """representation view of one download item in downloads tab"""

    def __init__(self, parent, uid, status, bg=None, fg=None, on_toggle_callback=None):
        self.bg = bg or atk.get_widget_attribute(parent, 'background') or MAIN_BG
        self.fg = fg or MAIN_FG

        self.uid = uid

        tk.Frame.__init__(self, parent, bg=self.bg, highlightbackground=self.bg, highlightthickness=5)

        self.name = ''
        self.status = status
        self.size = ''  # '30 MB'
        self.total_size = ''  # 'of 100 MB'
        self.speed = ''  # '- Speed: 1.5 MB/s'
        self.eta = ''  # '- ETA: 30 seconds'
        self.live_connections = ''  # '8'
        self.total_parts = ''
        self.completed_parts = ''  # 'Done: 20 of 150'
        self.sched = ''
        self.errors = ''
        self.media_type = ''
        self.media_subtype = ''
        self.progress = 0
        self.shutdown_pc = ''
        self.on_completion_command = ''
        self.on_toggle_callback = on_toggle_callback
        self.selected = False

        self.columnconfigure(1, weight=1)
        self.blank_img = tk.PhotoImage()

        # thumbnail
        self.thumbnail_width = 120
        self.thumbnail_height = 62

        # thumbnail
        self.thumbnail_img = None
        # should assign an image property for tkinter to use pixels for width and height instead of characters
        self.thumbnail_label = tk.Label(self, bg='white', image=self.blank_img, text='', font='any 20 bold', fg='black',
                                        justify='center', highlightbackground=THUMBNAIL_BD, highlightthickness=2,
                                        compound='center', width=self.thumbnail_width, height=self.thumbnail_height)
        self.thumbnail_label.grid(row=0, column=0, rowspan=3, padx=(0, 5), sticky='ns')

        # name text
        self.name_lbl = AutoWrappingLabel(self, bg=self.bg, fg=self.fg, anchor='w')
        self.name_lbl.grid(row=0, column=1, sticky='ewns')

        self.info_lbl = tk.Label(self, bg=self.bg, fg=self.fg, anchor='w', justify='left')
        self.info_lbl.grid(row=1, column=1, sticky='w')

        btns_frame = tk.Frame(self, bg=self.bg)
        btns_frame.grid(row=2, column=1, sticky='w')

        # for non-completed items
        if self.status != config.Status.completed:
            #  progressbar
            self.bar = atk.RadialProgressbar(parent=self, size=(60, 60), fg=PBAR_FG, text_fg=PBAR_TXT,
                                             font_size_ratio=0.12)
            self.bar.grid(row=0, column=2, rowspan=3, padx=10, pady=5)

            # create buttons
            self.play_button = Button(btns_frame, image=imgs['play_icon'])
            self.play_button .pack(side='left', padx=(0, 10))

        self.delete_button = Button(btns_frame, image=imgs['delete_icon'])
        self.delete_button.pack(side='left', padx=(0, 10))

        # make another info label
        self.info_lbl2 = tk.Label(btns_frame, bg=self.bg, fg=self.fg)
        self.info_lbl2.pack(side='left', padx=(0, 10), pady=5)

        # blinker button, it will blink with received data flow
        self.blinker = tk.Label(btns_frame, bg=self.bg, text='', fg=self.fg, image=self.blank_img, width=12, height=12)
        self.blinker.on = False
        self.blinker.pack(side='left', padx=5, pady=5)

        # separator
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew', padx=0)

    def __repr__(self):
        return f'DItem({self.uid})'

    def select(self, flag=True):
        """select self"""
        if flag == self.selected:
            return
        else:
            self.selected = flag

        # change highlight color
        highlight_bg = SEL_BG if flag else self.bg
        highlight_fg = SEL_FG if flag else self.fg
        self.config(highlightbackground=highlight_bg, background=highlight_bg)

        def change_background(w):
            for child in w.winfo_children():
                try:
                    if child is not self.thumbnail_label and child.winfo_class() not in ('TSeparator', 'Menu'):
                        atk.configure_widget(child, background=highlight_bg, foreground=highlight_fg)
                except:
                    pass

                # recursive call
                if child.winfo_children():
                    change_background(child)

        change_background(self)

        # call associated callback
        if callable(self.on_toggle_callback):
            self.on_toggle_callback()

    def toggle(self):
        """toggle item selection"""
        self.select(flag=not self.selected)

    def bind(self, sequence=None, func=None, add='+', exclude=None):
        """bind events to self and all children widgets"""

        # call original bind to frame
        tk.Frame.bind(self, sequence, func, add=add)

        if not isinstance(exclude, list):
            exclude = [exclude]

        # apply bind for all children
        def bind_children(w):
            for child in w.winfo_children():
                if child in exclude or child.winfo_class() == 'Menu':
                    continue
                child.bind(sequence, func, add)

                # recursive call
                if child.winfo_children():
                    bind_children(child)

        bind_children(self)

    def show(self):
        """grid self"""
        side = 'bottom' if config.ditem_show_top else 'top'
        self.pack(side=side, expand=True, fill='x', pady=5)

    def hide(self):
        """grid self"""
        self.pack_forget()

    def display_info(self):
        """display info in tkinter widgets"""

        self.info_lbl.config(text=f'{self.size} of {self.total_size} {self.speed} {self.eta}   {self.errors} '
                                  f'{self.shutdown_pc} {self.on_completion_command}')

        self.info_lbl2.config(text=f'{self.media_subtype} {self.media_type} {self.live_connections} '
                                   f'{self.completed_parts} - {self.status} {self.sched}')

        # a led like blinking button, to react with data flow
        self.toggle_blinker()

        if self.status == config.Status.completed:
            try:
                self.play_button.pack_forget()
                self.bar.grid_forget()
            except:
                pass
        else:
            try:
                self.bar.set(self.progress)
            except:
                pass

    def update(self, rendered_name=None, downloaded=None, progress=None, total_size=None, time_left=None, speed=None,
               thumbnail=None, status=None, extension=None, sched=None, type=None, subtype_list=None,
               remaining_parts=None, live_connections=None, total_parts=None, shutdown_pc=None,
               on_completion_command=None, **kwargs):
        """update widgets value"""
        # print(locals())
        try:

            if rendered_name:
                self.name = rendered_name
                self.name_lbl.config(text=self.name)

            if downloaded is not None:
                self.size = size_format(downloaded)

            if total_size is not None:
                self.total_size = size_format(total_size)

            if speed is not None:
                self.speed = f'- Speed: {size_format(speed)}/s' if speed > 0 else ''

            if time_left is not None:
                self.eta = f'- ETA: {time_format(time_left)}' if time_left > 0 else ''

            if progress is not None:
                self.progress = progress

            if extension:
                ext = extension.replace('.', '').upper()
                # negative font size will force character size in pixels
                f = f'any {int(- self.thumbnail_width * 0.8 // len(ext))} bold'
                self.thumbnail_label.config(text=ext, font=f)

            if thumbnail:
                self.thumbnail_img = atk.create_image(b64=thumbnail, size=self.thumbnail_width)
                self.thumbnail_label.config(image=self.thumbnail_img, text='')

            if 'errors' in kwargs:
                errors = kwargs['errors']
                self.errors = f'[{errors} errs!]' if errors else ''

            if live_connections is not None:
                self.live_connections = f'- Workers: {live_connections} ' if live_connections > 0 else ''

            if total_parts:
                self.total_parts = total_parts

            if remaining_parts:
                if self.total_parts:
                    completed = self.total_parts - remaining_parts
                    self.completed_parts = f'- Done: {completed} of {self.total_parts}'

            if status:
                self.status = status
                if status == config.Status.completed:
                    self.errors = ''
                    self.completed_parts = ''

                if status != config.Status.scheduled:
                    self.sched = ''

                # toggle play/pause icons
                try:
                    if status in config.Status.active_states:
                        img = imgs['pause_icon']
                    else:
                        img = imgs['play_icon']
                    self.play_button.config(image=img)
                    self.play_button.bind('<Enter>', lambda e: self.play_button.config(image=img.zoomed))
                    self.play_button.bind('<Leave>', lambda e: self.play_button.config(image=img))
                except:
                    pass

            if sched:
                if status == config.Status.scheduled:
                    self.sched = f'@{sched}'

            if type:
                self.media_type = type

            if isinstance(subtype_list, list):
                self.media_subtype = ' '.join(subtype_list)
            
            if on_completion_command is not None:
                self.on_completion_command = '[-CMD-]' if on_completion_command else ''
            if shutdown_pc is not None:
                self.shutdown_pc = '[-Shutdown Pc when finish-]' if shutdown_pc else ''

            self.display_info()

        except Exception as e:
            log('DItem.update()> error:', e)
            if config.TEST_MODE:
                raise e

    def toggle_blinker(self):
        """an activity blinker "like a blinking led" """
        status = self.status
        if not self.blinker.on and status in (config.Status.downloading, config.Status.processing,
                                              config.Status.refreshing_url):
            # on blinker
            self.blinker.config(image=imgs['blinker_icon'])
            self.blinker.on = True

        elif status == config.Status.completed:
            self.blinker.config(image=imgs['done_icon'])

        elif status in (config.Status.pending, config.Status.scheduled):
            self.blinker.config(image=imgs['hourglass_icon'])

        else:
            # off blinker
            self.blinker.config(image=self.blank_img)
            self.blinker.on = False


class Checkbutton(tk.Checkbutton):
    """a check button with some default settings"""
    def __init__(self, parent, **kwargs):
        bg = atk.get_widget_attribute(parent, 'background')
        fg = MAIN_FG

        options = dict(bg=bg, fg=fg, anchor='w', relief='flat', activebackground=bg, highlightthickness=0,
                       activeforeground=fg, selectcolor=bg, onvalue=True, offvalue=False,)

        options.update(kwargs)

        tk.Checkbutton.__init__(self, parent, **options)


class CheckOption(tk.Checkbutton):
    """a check button option for setting tab that will update global settings in config.py"""
    def __init__(self, parent, text, key=None, onvalue=True, offvalue=False, bg=None, fg=None, callback=None):
        bg = bg or atk.get_widget_attribute(parent, 'background')
        fg = fg or MAIN_FG
        self.key = key
        self.callback = callback

        if isinstance(onvalue, bool):
            self.var = tk.BooleanVar()
        elif isinstance(onvalue, int):
            self.var = tk.IntVar()
        elif isinstance(onvalue, float):
            self.var = tk.DoubleVar()
        else:
            self.var = tk.StringVar()

        # set current setting value
        current_value = get_option(self.key, offvalue)
        self.var.set(current_value)

        tk.Checkbutton.__init__(self, parent, text=text, bg=bg, fg=fg, anchor='w', relief='flat', activebackground=bg,
                                highlightthickness=0, activeforeground=fg, selectcolor=bg, variable=self.var, onvalue=onvalue, offvalue=offvalue,
                                command=self.update_sett)

        self.set = self.var.set
        self.get = self.var.get

    def update_sett(self):
        if self.key:
            set_option(**{self.key: self.get()})

        if callable(self.callback):
            self.callback()


class LabeledEntryOption(tk.Frame):
    """an entry with a label for options in setting tab that will update global settings in config.py"""
    def __init__(self, parent, text, entry_key=None, set_text_validator=None, get_text_validator=None, bg=None, fg=None,
                 callback=None, **kwargs):
        bg = bg or atk.get_widget_attribute(parent, 'background')
        fg = fg or MAIN_FG

        tk.Frame.__init__(self, parent, bg=bg)

        # label
        tk.Label(self, text=text, fg=fg, bg=bg).pack(side='left')

        self.key = entry_key
        self.set_text_validator = set_text_validator
        self.get_text_validator = get_text_validator
        self.callback = callback

        self.var = tk.StringVar()

        # entry
        self.entry = tk.Entry(self, bg=bg, fg=fg, highlightbackground=ENTRY_BD_COLOR, textvariable=self.var, **kwargs)
        self.entry.pack(side='left', fill='x', expand=True)

        # set current setting value
        current_value = get_option(self.key, '')
        self.set(current_value)

        # update settings when text change
        self.var.trace_add('write', self.update_sett)

    def update_sett(self, *args):
        """update global settings at config.py"""
        try:
            text = self.get()

            set_option(**{self.key: text})

            if callable(self.callback):
                self.callback()
        except:
            pass

    def set(self, text):
        """set entry text and validate or format text if set_text_validator exist"""
        try:
            if self.set_text_validator:
                text = self.set_text_validator(text)

            self.var.set(text)
        except:
            pass

    def get(self):
        value = self.var.get()

        if self.get_text_validator:
            value = self.get_text_validator(value)

        return value


class CheckEntryOption(tk.Frame):
    """a check button with entry for options in setting tab that will update global settings in config.py"""

    def __init__(self, parent, text, entry_key=None, check_key=None, set_text_validator=None, get_text_validator=None,
                 entry_disabled_value='', bg=None, callback=None, fg=None, **kwargs):
        bg = bg or atk.get_widget_attribute(parent, 'background')
        fg = fg or MAIN_FG

        tk.Frame.__init__(self, parent, bg=bg)

        self.callback = callback
        self.get_text_validator = get_text_validator
        self.set_text_validator = set_text_validator
        self.entry_key = entry_key
        self.check_key = check_key
        self.entry_disabled_value = entry_disabled_value

        # checkbutton --------------------------------------------------------------------------------------------------
        self.chkvar = tk.BooleanVar()
        self.checkbutton = tk.Checkbutton(self, text=text, bg=bg, fg=fg, activeforeground=fg, selectcolor=bg, anchor='w', relief='flat', activebackground=bg,
                                          highlightthickness=0, variable=self.chkvar, onvalue=True, offvalue=False,
                                          command=self.update_sett)

        self.checkbutton.pack(side='left')

        # entry --------------------------------------------------------------------------------------------------------
        self.entry_var = tk.StringVar()

        # bind trace
        self.entry_var.trace_add('write', self.update_sett)

        self.entry = tk.Entry(self, bg=bg, fg=fg, highlightbackground=ENTRY_BD_COLOR, textvariable=self.entry_var, **kwargs)
        self.entry.pack(side='left', fill='x', expand=True)

        # Load previous values -----------------------------------------------------------------------------------------
        text = get_option(entry_key, '')

        if check_key is None:
            checked = True if text else False

        else:
            checked = get_option(check_key, False)

        self.chkvar.set(checked)

        # load entry value
        if checked:
            self.set(text)

    def update_sett(self, *args):
        try:
            checked = self.chkvar.get()
            if checked:
                text = self.get()
            else:
                text = self.entry_disabled_value

            set_option(**{self.entry_key: text})

            if self.check_key:
                set_option(**{self.check_key: checked})

            if callable(self.callback):
                self.callback()
        except:
            pass

    def set(self, text):
        """set entry text and validate or format text if set_text_validator exist"""
        try:
            if self.set_text_validator:
                text = self.set_text_validator(text)

            self.entry_var.set(text)
        except:
            pass

    def get(self):
        value = self.entry_var.get()

        if self.get_text_validator:
            value = self.get_text_validator(value)

        return value


class PlaylistWindow(tk.Toplevel):
    """class for downloading video playlist
    """

    def __init__(self, main, playlist):
        """initialize

        Args:
            main: main window class
            playlist (iterable): video names only in a playlist, e.g. ('1- cats in the wild', '2- car racing', ...)
                                 in case we have a huge playlist
                                 e.g. https://www.youtube.com/watch?v=BZyjT5TkWw4&list=PL2aBZuCeDwlT56jTrxQ3FExn-dtchIwsZ
                                 has 4000 videos, we will show 40 page each page has 100 video
        """
        self.main = main
        self.parent = main.root
        self.playlist = playlist or []
        self.playlist_count = len(playlist)
        self.items = []
        self.max_videos_per_page = 100
        self.total_pages = self.playlist_count // self.max_videos_per_page + 1 if self.playlist_count % self.max_videos_per_page else 0
        self.current_page = 0
        self.items_per_page = min(self.playlist_count, self.max_videos_per_page)

        self.selected_videos = {}  # video_idx vs stream_idx
        self.stream_menus = {}  # video_idx vs stream menu
        self.subtitles = {}
        self.selected_subs = {}

        self.videos_counter = tk.IntVar()

        self.master_strem_menu = []
        self.master_combo = None
        self.master_selection = None  # master combo_box selection
        self.video_streams = {}  # {'    mp4': [360, 240, 144], '    webm': [360, 240, 144]}
        self.audio_streams = {}  # {'    aac': [128], '    ogg': [160], '    mp3': [128], '    webm': [160, 70, 50], '    m4a': [128]}

        # initialize super
        tk.Toplevel.__init__(self, self.parent)

        self.s = ttk.Style()

        # bind window close action
        self.protocol("WM_DELETE_WINDOW", self.close)

        width = 580
        height = 345
        center_window(self, width=width, height=height, reference=self.parent)

        self.title('Playlist download window')
        self.config(bg=SF_BG)

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)
        top_frame = tk.Frame(main_frame, bg=MAIN_BG)
        videos_frame = atk.ScrollableFrame(main_frame, bg=MAIN_BG, hscroll=False)
        videos_frame.columnconfigure(0, weight=1)
        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)

        self.page_count_var = tk.StringVar()
        self.update_page_count()

        f1 = tk.Frame(top_frame, bg=MAIN_BG)
        f1.pack(fill='x', expand=True, anchor='w')
        tk.Label(f1, text=f'Total videos: {self.playlist_count}, Selected:', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)
        tk.Label(f1, textvariable=self.videos_counter, bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=2, pady=5)

        Button(f1, text='Next', command=self.next_page).pack(side='right', padx=5, pady=5)
        tk.Label(f1, textvariable=self.page_count_var, bg=MAIN_BG, fg=MAIN_FG).pack(side='right', padx=5, pady=5)
        Button(f1, text='Prev.', command=self.prev_page).pack(side='right', padx=5, pady=5)

        f2 = tk.Frame(top_frame, bg=MAIN_BG)
        f2.pack(fill='x', expand=True, anchor='w')
        self.subtitles_label = tk.Label(f2, text='Total subtitles: 0, Selected: 0', bg=MAIN_BG, fg=MAIN_FG)
        self.subtitles_label.pack(side='left', padx=5, pady=5)

        Button(f2, text='Sub', command=self.show_subtitles_window).pack(side='left', padx=5, pady=5)

        # master menu
        f3 = tk.Frame(top_frame, bg=MAIN_BG)
        f3.pack(fill='x', expand=True, anchor='w')

        # select all
        self.select_all_var = tk.BooleanVar()
        Checkbutton(f3, text='Select all', variable=self.select_all_var, command=self.toggle_all).pack(side='left', padx=5, pady=5)

        self.master_combo = Combobox(f3, [], width=40, callback=self.master_combo_callback)
        self.master_combo.pack(side='right', padx=5, pady=5)
        tk.Label(f3, text='Preferred quality:', bg=MAIN_BG, fg=MAIN_FG).pack(side='right', padx=(20, 5), pady=5)

        # create items widgets
        for idx, name in zip(range(self.items_per_page), self.playlist):
            item = self.create_item(videos_frame, idx, name)

            self.items.append(item)
            item.grid(padx=5, pady=5, sticky='ew')

            atk.scroll_with_mousewheel(item, target=videos_frame, apply_to_children=True)

        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)
        Button(bottom_frame, text='Download', command=self.download).pack(side='right')

        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))

        bottom_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        top_frame.pack(side='top', fill='x')
        ttk.Separator(main_frame).pack(side='top', fill='x', expand=True)
        videos_frame.pack(side='bottom', expand=True, fill='both')

    # region item
    def create_item(self, parent, idx, name):
        """Create an item,
        every item has video name label, stream quality combobox, and a progressbar
        """
        item = tk.Frame(parent, bg=MAIN_BG)
        item.columnconfigure(0, weight=1)
        item.columnconfigure(1, weight=1)
        item.idx = idx  # index in self.items
        item.selected = tk.BooleanVar()

        # checkbutton
        item.checkbutton = Checkbutton(item, text=name, variable=item.selected, width=60,
                                       command=lambda: self.video_select_callback(item.idx))

        # progressbar
        custom_style = 'custom_playlist_bar.Horizontal.TProgressbar'
        self.s.configure(custom_style, thickness=3, background=PBAR_FG, troughcolor=SF_BG)
        item.bar = ttk.Progressbar(item, orient='horizontal', mode='indeterminate', style=custom_style)

        # stream menu
        item.combobox = Combobox(item, [], width=40, callback=lambda: self.stream_select_callback(item.idx))

        item.checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        return item

    def get_item(self, video_idx):
        """get item widget from self.items

        Return:
            (tk widget or None)
        """

        item_idx = self.get_item_idx(video_idx)
        item = self.items.get(item_idx, None)

        return item

    def get_item_idx(self, video_idx):
        """calculate item index based on video index
        e.g. if video_idx = 301 and we have 100 item per page, this video will be number 1 in 3rd page (counting from 0)

        Return:
            (int or None): item index or None if video is not in current page
        """

        # check target page of video item
        target_page = (video_idx // self.items_per_page)
        if target_page != self.current_page:
            return None

        item_idx = video_idx - (target_page * self.items_per_page)

        return item_idx

    def get_video_idx(self, item_idx):
        """calculate video index from item index based on current page
        e.g. if item_idx = 1 and current page is 3 (counting from 0), and we have 100 item per page, then video_idx= 301

        Return:
            (int): video index in playlist
        """

        video_idx = (self.current_page * self.items_per_page) + item_idx

        return video_idx

    def refresh_items(self, start_idx):
        # update widgets
        video_idx = start_idx
        for item, name in zip(self.items, self.playlist[start_idx:]):
            item.checkbutton['text'] = name
            selected = video_idx in self.selected_videos
            item.selected.set(selected)

            stream_menu = self.stream_menus.get(video_idx, [])
            stream_idx = self.selected_videos.get(video_idx, 1)
            item.combobox.config(values=stream_menu)

            if stream_menu:
                item.combobox.current(stream_idx)
            else:
                item.combobox.set('')

            if selected:
                item.combobox.grid()
            else:
                item.combobox.grid_remove()

            item.bar.stop()

            item.grid()

            video_idx += 1

    def hide_all_items(self):
        for item in self.items:
            item.grid_remove()
    # endregion

    # region page
    def next_page(self):
        if self.current_page + 1 < self.total_pages:
            self.current_page += 1
            start_idx = self.current_page * self.items_per_page
            self.update_page_count()

            self.hide_all_items()

            self.refresh_items(start_idx)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            start_idx = self.current_page * self.items_per_page
            self.update_page_count()

            self.hide_all_items()

            self.refresh_items(start_idx)

    def update_page_count(self):
        """update page number e.g. 'Page: 1 of 40'
        """
        self.page_count_var.set(f'{self.current_page + 1} of {self.total_pages}')
    # endregion

    # region progressbar
    def start_progressbar(self, item_idx):
        item = self.items[item_idx]
        item.bar.grid(row=1, column=1, padx=5, sticky='ew')
        item.bar.start(10)

    def stop_progressbar(self, item_idx):
        item = self.items[item_idx]
        item.bar.grid_remove()
        item.bar.stop()
    # endregion

    def toggle_all(self):
        run_thread(self._toggle_all)

    def _toggle_all(self):
        """select / unselct all video items in playlist"""

        if self.select_all_var.get():
            for idx, item in enumerate(self.items):
                # quit if playlist window closed, or uncheck button
                if self.main.pl_window is None or not self.select_all_var.get():
                    break

                if item.selected.get():
                    continue

                item.checkbutton.invoke()

                # add some time delay to process a video item and load stream menu before process next video
                menu = self.stream_menus.get(idx, [])
                # if video process failed, stream menu will contain only the headers (5 items) and no streams
                # e.g. ['Video streams:', '', 'Audio streams:', '', 'Extra streams:']
                if len(menu) <= 5:
                    time.sleep(0.5)
        else:
            for item in self.items:
                if not item.selected.get():
                    continue

                item.checkbutton.invoke()

    def close(self):
        self.destroy()
        self.main.pl_window = None

    def download(self):

        # sort items
        self.selected_videos = {k: self.selected_videos[k] for k in sorted(self.selected_videos.keys())}
        # print(self.selected_videos)
        self.main.controller.download_playlist(self.selected_videos, subtitles=self.selected_subs)

        self.close()

    def update_view(self, video_idx=None, stream_menu=None, stream_idx=None):
        """update stream menu values

        example:
            stream menu = ['Video streams:                     ', '    mp4 - 360 - 8.0 MB - id:18 - 25 fps',
            '    mp4 - 240 - 4.9 MB - id:133 - 25 fps', '    mp4 - 144 - 2.2 MB - id:160 - 15 fps',
            '    webm - 360 - 4.0 MB - id:243 - 25 fps', '    webm - 240 - 2.4 MB - id:242 - 25 fps', '
             webm - 144 - 1.3 MB - id:278 - 25 fps', '',
            'Audio streams:                 ',
            '    aac - 128 - 2.6 MB - id:140', '    ogg - 160 - 3.1 MB - id:251', '    mp3 - 128 - 2.6 MB - id:140',
            '    webm - 160 - 3.1 MB - id:251', '    m4a - 128 - 2.6 MB - id:140', '    webm - 70 - 1.4 MB - id:250',
            '    webm - 50 - 1.0 MB - id:249', '',
            'Extra streams:                 ', '    mp4 - 360 - 5.1 MB - id:134 - 25 fps']

        """
        item_idx = self.get_item_idx(video_idx)
        self.stop_progressbar(item_idx)

        item = self.items[item_idx]
        combobox = item.combobox
        combobox.config(values=stream_menu)
        combobox.current(stream_idx)

        self.stream_select_callback(item_idx)
        self.stream_menus[video_idx] = stream_menu

        # get subtitles
        sub = self.main.controller.get_subtitles(video_idx=video_idx)
        if sub:
            self.update_subtitles(sub)

        # update master stream menu
        self.update_master_menu(stream_menu)

        # follow master menu selection
        self.follow_master_selection(item_idx, stream_menu)

    # region master stream menu
    def master_combo_callback(self):
        self.master_selection = self.master_combo.selection

        # update widgets
        for item_idx, item in enumerate(self.items):
            if item.selected.get():
                self.follow_master_selection(item_idx)

        # update selected streams
        for vid_idx in self.selected_videos:
            menu = self.stream_menus.get(vid_idx, [])

            for s_idx, s_name in enumerate(menu):
                if s_name.startswith(self.master_selection):
                    self.selected_videos[vid_idx] = s_idx
                    break

    def follow_master_selection(self, item_idx, stream_menu=None):
        """update all selected stream menus to match master menu selection"""
        video_idx = self.get_video_idx(item_idx)
        stream_menu = stream_menu or self.stream_menus.get(video_idx, None)
        item = self.items[item_idx]

        if not stream_menu:
            return

        combobox = item.combobox

        if self.master_selection:
            try:
                # update widget combo boxes
                for s_idx, s_name in enumerate(stream_menu):
                    if s_name.startswith(self.master_selection):
                        combobox.current(s_idx)
                        self.selected_videos[video_idx] = s_idx
                        break

            except Exception as e:
                log('follow master selection error:', e)

    def update_master_menu(self, stream_menu):
        """update master menu in playlist window
        Args:
            stream_menu (lsit): list of strings, example:
                Video Stream:
                    mp4 - 1080 - 10 MB - ...
                    webm - 720 - 5 MB - ...

                Audio Streams:
                    AAC - 128 - 4 MB - ...

                Extra Streams:
                    mp4 - 480 - 10 MB - ...

        we should build master menu to contain video and audio streams only and every stream will be extension and
        quality only, e.g. mp4 - 1080

        """

        streams = self.video_streams

        for entry in stream_menu:
            # if we reach at the empty line under Audio Streams' section will break to avoid extra streams
            if streams == self.audio_streams and entry == '':
                break

            if "Audio" in entry:
                streams = self.audio_streams

            # get streams
            try:
                ext, quality = entry.split(' - ')[:2]  # stream example  "    mp4 - 1080 - 10 MB - ..."
                quality = int(quality)

                # example video streams {'    mp4': [1080, 720, 480], '    webm': [720, 240], ...}
                quality_list = streams.setdefault(ext, [])
                if quality not in quality_list:
                    quality_list.append(quality)
            except:
                continue

        def process(streams_dict):
            for ext, quality_list in streams_dict.items():
                quality_list = sorted(quality_list, reverse=True)
                for quality in quality_list:
                    item = f'{ext} - {quality}'
                    menu.append(item)

        menu = ['Video streams:                     ']
        process(self.video_streams)
        menu += ['', 'Audio streams:                 ']
        process(self.audio_streams)

        self.master_strem_menu = menu

        self.master_combo.config(values=list(self.master_strem_menu))

        # set selection
        if not self.master_selection and len(self.master_strem_menu) >= 2:
            self.master_combo.current(1)
    # endregion

    # region subtitles
    def update_subtitles(self, sub):
        """update available subtitles, it is a sum of all subtitles for all selected videos in playlist"""

        for lang, new_ext_list in sub.items():
            ext_list = self.subtitles.get('lang', [])
            # merge 2 lists, don't use set() to avoid losing order
            self.subtitles[lang] = ext_list + [x for x in new_ext_list if x not in ext_list]

    def show_subtitles_window(self):
        if self.subtitles:
            sub_window = SubtitleWindow(self.main, self.subtitles, enable_download_button=False,
                                        enable_select_button=True, block=True, selected_subs=self.selected_subs)
            self.selected_subs = sub_window.selected_subs
        else:
            self.main.msgbox('No Subtitles available for selected videos or no videos selected!')

        self.update_subs_label()

    def update_subs_label(self):
        self.subtitles_label['text'] = f'Total subtitles: {len(self.subtitles)}, Selected: {len(self.selected_subs)}'
    # endregion

    def video_select_callback(self, item_idx):
        """ask controller to send stream menu when selecting a video"""
        item = self.items[item_idx]
        video_idx = self.get_video_idx(item_idx)

        if item.selected.get():
            item.combobox.grid(row=0, column=1, padx=5, sticky='ew')
            self.start_progressbar(item_idx)
            self.main.controller.select_playlist_video(video_idx, active=False)

            self.videos_counter.set(self.videos_counter.get() + 1)
        else:
            self.videos_counter.set(self.videos_counter.get() - 1)
            item.combobox.grid_remove()
            self.stop_progressbar(item_idx)

        self.update_subs_label()

        self.stream_select_callback(item_idx)

    def stream_select_callback(self, item_idx):
        item = self.items[item_idx]
        video_idx = self.get_video_idx(item_idx)

        stream_idx = item.combobox.current()

        if item.selected.get():
            self.selected_videos[video_idx] = stream_idx
        elif video_idx in self.selected_videos:
            self.selected_videos.pop(video_idx)


class SubtitleWindow(tk.Toplevel):
    """Download subtitles window"""

    def __init__(self, main, subtitles, enable_download_button=True, enable_select_button=False, block=False, selected_subs=None):
        """initialize

        Args:
            main: main window class
            subtitles (dict): subtitles, key=language, value=list of extensions, e.g. {en: ['srt', 'vtt'], ar: [...]}
            download_button (bool): show download button
            select_button (bool): show select button
            block (bool): block until closed
            selected_subs (dict): key=language, value=selected extension
        """
        self.main = main
        self.parent = main.root
        self.subtitles = subtitles or {}
        self.selected_subs = selected_subs or {}  # key=language, value=selected extension
        self.items = []
        self.enable_select_button = enable_select_button
        self.enable_download_button = enable_download_button

        # initialize super
        tk.Toplevel.__init__(self, self.parent)

        # bind window close
        self.protocol("WM_DELETE_WINDOW", self.close)

        width = 580
        height = 345
        center_window(self, width=width, height=height, reference=self.parent)

        self.title('Subtitles download window')
        self.config(bg=SF_BG)

        self.create_widgets()

        if block:
            self.wait_window(self)

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)
        top_frame = tk.Frame(main_frame, bg=MAIN_BG)
        subs_frame = atk.ScrollableFrame(main_frame, bg=MAIN_BG, hscroll=False)
        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)

        tk.Label(top_frame, text=f'Total Subtitles: {len(self.subtitles)} items.', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)
        self.selected_subs_label = tk.Label(top_frame, text=f'Selected: {len(self.selected_subs)} items.', bg=MAIN_BG, fg=MAIN_FG)
        self.selected_subs_label.pack(side='left', padx=5, pady=5)

        for language, extensions in self.subtitles.items():
            item = self.create_item(subs_frame, language, extensions)

            self.items.append(item)
            item.pack(fill='x', expand=True, padx=5, pady=5)

            atk.scroll_with_mousewheel(item, target=subs_frame, apply_to_children=True)

            if language in self.selected_subs:
                item.selected.set(True)

                ext = self.selected_subs[language]
                if ext in extensions:
                    item.combobox.set(ext)

        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)

        if self.enable_select_button:
            Button(bottom_frame, text='Select', command=self.select).pack(side='right')

        if self.enable_download_button:
            Button(bottom_frame, text='Download', command=self.download).pack(side='right')

        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))

        bottom_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        subs_frame.pack(side='bottom', expand=True, fill='both')
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        top_frame.pack(side='bottom', fill='x')

    def create_item(self, parent, language, extensions):
        item = tk.Frame(parent, bg=MAIN_BG)
        item.columnconfigure(0, weight=1)
        item.columnconfigure(1, weight=1)
        item.language = language
        item.selected = tk.BooleanVar()

        # checkbutton
        item.checkbutton = Checkbutton(item, text=language, variable=item.selected, width=40, command=self.update_selected_count)

        # stream menu
        item.combobox = Combobox(item, extensions, width=20)
        item.combobox.current(0)

        item.checkbutton.grid(row=0, column=0, padx=5, sticky='ew')
        item.combobox.grid(row=0, column=1, padx=5, sticky='ew')

        return item

    def close(self):
        self.destroy()
        self.main.subtitles_window = None

    def select(self):
        """callback for select button"""
        self.update_selected_subs()
        self.close()

    def update_selected_subs(self):
        """update selected subs"""
        self.selected_subs.clear()
        for item in self.items:
            if item.selected.get():
                self.selected_subs[item.language] = item.combobox.get()

    def update_selected_count(self):
        count = len([item for item in self.items if item.selected.get()])
        self.selected_subs_label['text'] = f'Selected: {count} items.'

    def download(self):
        self.update_selected_subs()

        self.main.controller.download_subtitles(self.selected_subs)

        self.close()


class AudioWindow(tk.Toplevel):
    """window for Manual audio selection for dash video"""

    def __init__(self, main, audio_menu, selected_idx):
        """initialize

        Args:
            main: main window class
            audio_menu (eterable): list of audio names
            selected_idx (int): selected audio stream index
        """
        self.main = main
        self.parent = main.root
        self.audio_menu = audio_menu or []
        self.selected_idx = selected_idx or 0

        # initialize super
        tk.Toplevel.__init__(self, self.parent)

        # bind window close
        self.protocol("WM_DELETE_WINDOW", self.close)

        width = 580
        height = 345
        center_window(self, width=width, height=height, reference=self.parent)

        self.title('Manual Audio selection for dash video')
        self.config(bg=SF_BG)

        self.create_widgets()

        # block and wait for window to close
        self.wait_window(self)

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)

        top_frame = tk.Frame(main_frame, bg=MAIN_BG)
        middle_frame = atk.ScrollableFrame(main_frame, bg=MAIN_BG, hscroll=False)
        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)

        tk.Label(top_frame, text='Select audio stream:', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)

        self.selection_var = tk.IntVar()
        self.selection_var.set(self.selected_idx)

        for idx, audio in enumerate(self.audio_menu):
            # value should be string to fix tkinter error when value is 0
            item = atk.button.Radiobutton(middle_frame, text=audio, variable=self.selection_var, value=f'{idx}')
            item.pack(padx=5, pady=5, anchor='w')

            atk.scroll_with_mousewheel(item, target=middle_frame, apply_to_children=True)

        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)
        Button(bottom_frame, text='Ok', command=self.select_audio).pack(side='right')

        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))

        bottom_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        middle_frame.pack(side='bottom', expand=True, fill='both')
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        top_frame.pack(side='bottom', fill='x')

    def close(self):
        self.destroy()

    def select_audio(self):
        idx = self.selection_var.get()
        if idx is not None:
            self.main.controller.select_audio(int(idx))

        self.close()


class DatePicker(tk.Toplevel):
    """Date picker window"""

    def __init__(self, parent, min_year=None, max_year=None, title='Date Picker'):
        """initialize

        Args:
            parent: parent window
            min_year (int): minimum year to show
            max_year (int): max. year to show
            title (str): window title
        """
        self.parent = parent

        today = datetime.datetime.today()
        self.min_year = min_year or today.year - 20
        self.max_year = max_year or today.year + 20

        self.selected_date = None

        self.fields = {'Year': {'values': list(range(self.min_year, self.max_year + 1)), 'selection': today.year},
                       'Month': {'values': list(range(1, 13)), 'selection': today.month},
                       'Day': {'values': list(range(1, 31)), 'selection': today.day},
                       'Hour': {'values': list(range(0, 60)), 'selection': today.hour},
                       'Minute': {'values': list(range(0, 60)), 'selection': today.minute},
                       }

        # initialize super
        tk.Toplevel.__init__(self, self.parent)

        # bind window close
        self.protocol("WM_DELETE_WINDOW", self.close)

        width = 420
        height = 180
        center_window(self, width=width, height=height, reference=self.parent)

        self.title(title)
        self.config(bg=SF_BG)

        self.create_widgets()

        self.wait_window(self)

    def is_leap(self, year):
        """year -> 1 if leap year, else 0, source: datetime.py"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def days_in_month(self, year, month):
        """year, month -> number of days in that month in that year, modified from source: datetime.py"""
        default = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        if month == 2 and self.is_leap(year):
            return 29
        return default[month]

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)
        top_frame = tk.Frame(main_frame, bg=MAIN_BG)
        tk.Label(top_frame, text='Select Date and time:', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)

        middle_frame = tk.Frame(main_frame, bg=MAIN_BG)

        def set_field(field_name, value):
            x = self.fields[field_name]
            x['selection'] = int(value)

            # set correct days according to month and year
            year = self.fields['Year']['selection']
            month = self.fields['Month']['selection']
            day = self.fields['Day']['selection']
            days_in_month = self.days_in_month(year, month)
            self.day_combo.config(values=list(range(1, days_in_month + 1)))
            if day > days_in_month:
                self.day_combo.set(days_in_month)

        c = 0
        for key, item in self.fields.items():
            tk.Label(middle_frame, text=key, bg=MAIN_BG, fg=MAIN_FG).grid(row=0, column=c, padx=5, sticky='w')
            cb = Combobox(middle_frame, values=item['values'], selection=item['selection'], width=5)
            cb.grid(row=1, column=c, padx=(5, 10), sticky='w')
            cb.callback = lambda field_name=key, combo=cb: set_field(field_name, combo.selection)

            # get day combo box reference
            if key == 'Day':
                self.day_combo = cb

            c += 1

        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)
        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)
        Button(bottom_frame, text='Ok', command=self.set_selection).pack(side='right')

        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))
        bottom_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        middle_frame.pack(side='bottom', expand=True, fill='both')
        ttk.Separator(main_frame).pack(side='bottom', fill='x', expand=True)
        top_frame.pack(side='bottom', fill='x')

    def close(self):
        self.destroy()

    def set_selection(self):
        """return selected date"""
        values = [int(item['selection']) for item in self.fields.values()]
        self.selected_date = datetime.datetime(*values)
        self.close()


class MainWindow(IView):
    """Main GUI window

    virtual events:
        urlChangeEvent: fired when url changed, used by url_entry, generated by url_watchdog() when new url copied
                        to clipboard, it can be triggered any time if we need url_entry to update its contents,
                        example: root.event_generate('<<urlChangeEvent>>', when='tail')
        updateViewEvent: fired when controller call update view method
        runMethodEvent: used for thread-safe operation, e.g. when a thread wants to call a method in MainWindow, it will
                        call MainWindow.run_thread, which in return fires this event, then run_method_handler will be
                        invoked as a response for this event and run actual method
    """

    def __init__(self, controller=None):
        self.controller = controller

        self.url = ''
        self.url_after_id = None  # identifier returned by 'after' method, keep it for future cancelling
        self.d_items = {}  # hold DItem objects  {'UID': DItem()}

        self.pl_window = None  # playlist download window
        self.subtitles_window = None  # subtitles download window

        # queues for executing methods on gui from a thread
        self.command_q = Queue()
        self.response_q = Queue()
        self.counter = 0  # a counter to give a unique number
        self.update_view_q = Queue()

        # root ----------------------------------------------------------------------------------------------------
        self.root = tk.Tk()

        # # default font
        # self.root.option_add("*Font", "helvetica")

        # assign window size
        try:
            self.width, self.height = config.window_size
        except:
            self.width, self.height = config.DEFAULT_WINDOW_SIZE

        center_window(self.root, width=self.width, height=self.height)

        # prevent window resize to zero
        self.root.minsize(100, 100)
        self.root.title(f'FireDM ver.{config.APP_VERSION}')
        self.main_frame = None

        # set window icon
        global app_icon_img, popup_icon_img
        app_icon_img = atk.create_image(b64=APP_ICON, size=48)
        popup_icon_img = atk.create_image(b64=APP_ICON, size=22)

        self.root.iconphoto(True, app_icon_img)

        # themes
        self.load_user_themes()

        # select tkinter theme required for things to be right on windows,
        # only 'alt', 'default', and 'classic' works fine on windows 10
        s = ttk.Style()
        s.theme_use('default')

        # apply firedm theme
        self.apply_theme(config.current_theme)

        self.create_main_widgets()

        # bind window close
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        # bind custom paste for all entry widgets
        self.root.bind_class("Entry", "<<Paste>>", self.custom_paste)

        # bind virtual events
        self.root.bind('<<urlChangeEvent>>', self.url_change_handler)
        self.root.bind("<<updateViewEvent>>", self.update_view_handler)
        self.root.bind("<<runMethodEvent>>", self.run_method_handler)

        # remember window size
        self.root.bind('<Configure>', self.remember_window_size)

        # initialize systray
        self.systray = SysTray(self)

        self.root.after(1000, self.post_startup)

        # number vs callback, e.g. ask controller to update youtube-dl sending any identifier e.g. "500",
        # when controller finishes this job it will send a signal with same number "500", then tkview will call
        # the associated callback
        self.post_processors = {}

        # set global binds
        self.bind_keyboard('<Delete>', self.delete_selected, widgets=[self.d_tab])
        self.bind_keyboard('<Return>', self.open_selected_file, widgets=[self.d_tab])

    # region themes
    def save_user_themes(self):
        try:
            file = os.path.join(config.sett_folder, 'user_themes.cfg')
            save_json(file, user_themes)
        except Exception as e:
            log('save_themes() > error', e)

    def load_user_themes(self):
        try:
            global user_themes
            # print('load user themes')
            file = os.path.join(config.sett_folder, 'user_themes.cfg')
            themes = load_json(file)
            # print(themes)

            if themes:
                # remove invalid colors
                for name, theme in themes.items():
                    themes[name] = {k: v for k, v in theme.items() if self.is_color(v)}

                user_themes = themes
            else:
                user_themes = {}
        except Exception as e:
            log('load_themes() > error', e)

    def is_color(self, color):
        """validate if a color is a valid tkinter color

        Args:
            color (str): color name e.g. 'red' or '#abf3c5'

        Returns:
            (bool): True if color is a valid tkinter color
        """

        try:
            # it will raise exception if color is not valid
            self.root.winfo_rgb(color)
            return True
        except Exception as e:
            print('is color:', e)
            return False

    def edit_theme(self):
        ThemeEditor(self, self.themes_menu.get())

    def new_theme(self):
        ThemeEditor(self, f'custom_{len(user_themes) + 1}')

    def del_theme(self):
        try:
            sel = self.themes_menu.get()
            user_themes.pop(sel)
            values = list(self.themes_menu['values'])
            values.remove(sel)
            self.themes_menu.config(values=values)
            self.themes_menu.current(0)
        except:
            pass

    def apply_theme(self, theme_name=None):
        """change global color variables

           Args:
               theme_name (str): theme name
        """

        theme_name = theme_name or self.themes_menu.get() or config.DEFAULT_THEME

        # look first in user themes, then in builtin theme
        theme = user_themes.get(theme_name) or builtin_themes.get(theme_name) or builtin_themes.get(config.DEFAULT_THEME)

        if theme:
            # clean invalid color values
            theme = {k: v for k, v in theme.items() if self.is_color(v)}

            config.current_theme = theme_name

            # add missing keys to other builtin themes
            calculate_missing_theme_keys(theme)

            # update global variables
            globals().update(theme)

        # custom combobox dropdown menu (listbox) https://www.tcl.tk/man/tcl/TkCmd/ttk_combobox.htm
        # option add *TCombobox*Listbox.background color
        # option add *TCombobox*Listbox.font font
        # option add *TCombobox*Listbox.foreground color
        # option add *TCombobox*Listbox.selectBackground color
        # option add *TCombobox*Listbox.selectForeground color

        self.root.option_add('*TCombobox*Listbox.background', BTN_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', atk.calc_font_color(BTN_BG))
        self.root.option_add('*TCombobox*Listbox.selectBackground', SF_BG)
        self.root.option_add('*TCombobox*Listbox.selectForeground', atk.calc_font_color(SF_BG))

        # create images
        create_imgs()

        if self.main_frame:
            self.restart_gui()

    # endregion

    # region widgets
    def create_main_widgets(self):

        # create main frame ---------------------------------------------------------------------------------------
        self.main_frame = tk.Frame(self.root, width=self.width, height=self.height, background=MAIN_BG)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1000)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.pack(expand=True, fill='both')

        # top right frame
        tk.Frame(self.main_frame, background=SF_BG, height=10).grid(row=0, column=1, columnspan=2, sticky='new')

        # home tab
        self.home_tab = self.create_home_tab()

        # settings tab
        self.sett_frame = self.create_settings_tab()

        # downloads tab
        self.downloads_frame = self.create_downloads_tab()

        # log tab
        self.log_tab = self.create_log_tab()

        # side frame
        self.side_frame = SideFrame(parent=self.main_frame)

        # create side frame buttons
        self.side_frame.create_button('Home', b64=home_icon, target=self.home_tab)
        self.side_frame.create_button('Downloads', b64=download_icon, target=self.downloads_frame)
        self.side_frame.create_button('Settings', b64=sett_icon, target=self.sett_frame)
        self.side_frame.create_button('Log', b64=log_icon, target=self.log_tab)

        if not config.disable_update_feature:
            # update tab
            self.update_tab = self.create_update_tab()
            self.side_frame.create_button('Update', b64=refresh_icon, target=self.update_tab)

        # set default button
        self.side_frame.set_default('Home')

        # grid side frame
        self.side_frame.grid(row=0, column=0, sticky='wns', rowspan=2)

        # total speed
        self.total_speed = tk.StringVar()
        tk.Label(self.main_frame, textvariable=self.total_speed, bg=SF_BG,
                 fg=SF_FG).grid(row=1, column=0, sticky='s', rowspan=2)

        ff = ExpandCollapse(self.main_frame, self.side_frame, MAIN_BG, MAIN_FG)
        ff.grid(row=1, column=1, sticky='ewns')

    def create_home_tab(self):
        bg = MAIN_BG

        home_tab = tk.Frame(self.main_frame, background=bg)
        # home_tab = atk.Frame3d(self.main_frame, bg=bg)

        home_tab.rowconfigure(1, weight=1)
        home_tab.columnconfigure(0, weight=1)
        home_tab.columnconfigure(1, weight=1)

        # url entry ----------------------------------------------------------------------------------------------------
        self.url_var = tk.StringVar()
        self.url_var.trace_add('write', self.url_entry_callback)

        self.url_entry = tk.Entry(home_tab, bg=MAIN_BG, highlightcolor=ENTRY_BD_COLOR,
                                  highlightbackground=ENTRY_BD_COLOR, fg=MAIN_FG, textvariable=self.url_var)
        self.url_entry.grid(row=0, column=0, columnspan=4, padx=5, pady=(45, 5), sticky='ew', ipady=8, ipadx=5)

        def url_rcm_handler(option):
            if option == 'Copy selection':
                try:
                    self.copy(self.url_entry.selection_get())
                except:
                    pass
            elif option == 'Paste':
                try:
                    self.url_entry.delete("sel.first", "sel.last")
                except:
                    pass
                self.url_entry.insert(tk.INSERT, self.paste())
            elif option == 'Clear field':
                self.url_var.set('')

        atk.RightClickMenu(self.url_entry, ['Paste', 'Clear field', 'Copy selection'], callback=url_rcm_handler,
                           bg=RCM_BG, fg=RCM_FG, afg=RCM_AFG, abg=RCM_ABG)

        # retry button -------------------------------------------------------------------------------------------------
        self.retry_btn = Button(home_tab, image=imgs['refresh_icon'], command=lambda: self.refresh_url(self.url))
        # self.retry_btn.image = retry_img
        self.retry_btn.grid(row=0, column=4, padx=(0, 5), pady=(40, 5))

        # thumbnail ----------------------------------------------------------------------------------------------------
        self.thumbnail = Thumbnail(parent=home_tab)
        self.thumbnail.grid(row=1, column=3, columnspan=1, rowspan=1, padx=5, pady=10, sticky='e')

        # video menus --------------------------------------------------------------------------------------------------
        self.pl_menu = MediaListBox(home_tab, bg, 'Playlist:')
        self.pl_menu.grid(row=1, column=0, columnspan=1, rowspan=1, pady=10, padx=5, sticky='nsew')
        Button(self.pl_menu, image=imgs['playlist_icon'], command=self.show_pl_window).place(relx=1, rely=0, x=-40, y=5)
        self.stream_menu = MediaListBox(home_tab, bg, 'Stream Quality:')
        self.stream_menu.grid(row=1, column=1, columnspan=1, rowspan=1, padx=15, pady=10, sticky='nsew')

        # bind menu selection
        self.pl_menu.listbox.bind('<<ListboxSelect>>', self.video_select_callback)
        self.stream_menu.listbox.bind('<<ListboxSelect>>', self.stream_select_callback)

        # playlist download, sub buttons -------------------------------------------------------------------------------
        pl_sub_frame = tk.Frame(home_tab, background=MAIN_BG)

        Button(pl_sub_frame, image=imgs['playlist_icon'], command=self.show_pl_window).pack(pady=0, padx=5)
        Button(pl_sub_frame, image=imgs['subtitle_icon'], command=self.show_subtitles_window).pack(pady=20, padx=5)
        Button(pl_sub_frame, image=imgs['about_icon'], command=self.show_about_notes).pack(pady=0, padx=5)

        pl_sub_frame.grid(row=1, column=4, padx=5, pady=10)

        # file properties ----------------------------------------------------------------------------------------------
        self.file_properties = FileProperties(parent=home_tab)
        self.file_properties.grid(row=2, column=0, columnspan=3, rowspan=1, sticky='wes', padx=5, pady=10)

        # bind click anywhere on main frame to unfocus name widget
        home_tab.bind('<1>', lambda event: self.root.focus(), add='+')

        # download button ----------------------------------------------------------------------------------------------
        Button(home_tab, text='Download', command=self.download_btn_callback,
               font='any 12').grid(row=2, column=3, padx=1, pady=5, sticky='es')

        # spacer to keep the column with a fixed size for zoomed button images to look better on mouse hover
        tk.Frame(home_tab, width=60, background=MAIN_BG).grid(row=2, column=4, padx=5, pady=10)

        return home_tab

    def create_downloads_tab(self):
        tab = tk.Frame(self.main_frame, background=MAIN_BG)

        # top frame
        top_fr = tk.Frame(tab, bg=HDG_BG)
        top_fr.pack(fill='x', pady=(5, 0), padx=(5, 0))

        self.select_btn = Button(top_fr, text='', image=imgs['dropdown_icon'])
        self.select_btn.pack(side='left', padx=5, pady=10)
        self.select_lbl = tk.Label(top_fr, text='', bg=HDG_BG, fg=HDG_FG)
        self.select_lbl.pack(side='left', padx=5, pady=10)

        select_menu = atk.RightClickMenu(self.select_btn,
                                         ['Select all', 'Select None', 'Select completed', 'Select non completed'],
                                         callback=lambda option_name: self.select_ditems(option_name),
                                         bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG)

        self.select_btn.bind("<Button-1>", select_menu.popup)

        def resume_all_handler():
            caption = self.resume_all_btn['text'].strip()
            # caption will be changed from self.update_stat_lbl() method
            if caption == 'Resume All':
                self.resume_all()
            else:
                self.stop_all()

        self.resume_all_btn = Button(top_fr, text='Resume All', bg=SF_BG, fg=SF_BTN_BG, command=resume_all_handler)
        self.resume_all_btn.pack(side='right', padx=5)

        self.resume_all_btn.bind('<Enter>', lambda e: self.resume_all_btn.config(text=' ' + self.resume_all_btn['text'] + ' '))
        self.resume_all_btn.bind('<Leave>', lambda e: self.resume_all_btn.config(text=self.resume_all_btn['text'].strip()))

        self.stat_lbl = tk.Label(tab, text='', bg=SF_BG, fg=SF_BTN_BG, anchor='w')
        self.stat_lbl.pack(fill='x', padx=(5, 0), pady=2, ipadx=5)

        # Scrollable
        self.d_tab = atk.ScrollableFrame(tab, bg=MAIN_BG, vscroll=True, hscroll=False,
                                         autoscroll=config.autoscroll_download_tab, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG)

        self.d_tab.pack(expand=True, fill='both')

        # bind mousewheel
        atk.scroll_with_mousewheel(self.d_tab)

        return tab

    def create_settings_tab(self):
        bg = MAIN_BG
        fg = MAIN_FG

        tab = atk.ScrollableFrame(self.main_frame, bg=bg, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG)

        def heading(text):
            tk.Label(tab, text=' ' + text, bg=HDG_BG, fg=HDG_FG, anchor='w',
                     font='any 10 bold').pack(anchor='w', expand=True, fill='x', ipady=3, pady=(0, 5))

        def separator():
            ttk.Separator(tab).pack(fill='both', expand=True, pady=(5, 30))

        # general ------------------------------------------------------------------------------------------------------
        heading('General:')

        # themes -------------------------
        themes_frame = tk.Frame(tab, bg=bg)
        themes_frame.pack(anchor='w', expand=True, fill='x')

        tk.Label(themes_frame, bg=bg, fg=fg, text='Select Theme:  ').pack(side='left')

        # sorted themes names
        themes_names = natural_sort(list(builtin_themes.keys()) + list(user_themes.keys()))

        self.themes_menu = Combobox(themes_frame, values=themes_names, selection=config.current_theme)
        self.themes_menu.pack(side='left', ipadx=5)
        Button(themes_frame, text='Apply', command=self.apply_theme).pack(side='left', padx=5)

        Button(themes_frame, text='Delete', command=self.del_theme).pack(side='right', padx=5)
        Button(themes_frame, text='New', command=self.new_theme).pack(side='right', padx=5)
        Button(themes_frame, text='Edit', command=self.edit_theme).pack(side='right', padx=5)

        CheckOption(tab, 'Enable systray icon "requires application restart"', key='enable_systray').pack(anchor='w')
        CheckOption(tab, 'Minimize to systray when closing application window', key='minimize_to_systray').pack(anchor='w')
        CheckOption(tab, 'Monitor clipboard for copied urls', key='monitor_clipboard').pack(anchor='w')
        CheckOption(tab, 'Auto rename file if same name exists in download folder', key='auto_rename').pack(anchor='w')

        CheckOption(tab, 'Show "MD5 and SHA256" checksums for downloaded files in log', key='checksum').pack(anchor='w')

        def autoscroll_callback():
            self.d_tab.autoscroll = config.autoscroll_download_tab
            if config.ditem_show_top:
                autotop.set(False)
                config.ditem_show_top = False

        def autotop_callback():
            if config.autoscroll_download_tab:
                autoscroll.set(False)
                self.d_tab.autoscroll = config.autoscroll_download_tab = False

        autoscroll = CheckOption(tab, 'Autoscroll downloads tab to bottom when adding new item.',
                                 key='autoscroll_download_tab', callback=autoscroll_callback)
        autoscroll.pack(anchor='w')
        autotop = CheckOption(tab, 'Show new download item at the top of downloads tab.',
                              key='ditem_show_top', callback=autotop_callback)
        autotop.pack(anchor='w')

        CheckOption(tab, 'write "last modified" timestamp to downloaded file', key='write_timestamp').pack(anchor='w')

        sett_folder_frame = tk.Frame(tab, bg=bg)
        sett_folder_frame.pack(anchor='w', expand=True, fill='x')
        tk.Label(sett_folder_frame, text='Settings Folder:', bg=bg, fg=fg).pack(side='left')
        tk.Label(sett_folder_frame, text=config.sett_folder, bg=bg, fg=fg).pack(side='left')
        Button(sett_folder_frame, text='Open', command=lambda: open_folder(config.sett_folder)).pack(side='right', padx=5)

        separator()

        # Video / Audio ------------------------------------------------------------------------------------------------
        heading('Video / Audio:')

        CheckOption(tab, 'Write metadata to media files', key='write_metadata').pack(anchor='w')
        CheckOption(tab, 'Manually select audio format for dash videos', key='manually_select_dash_audio').pack(
            anchor='w')
        CheckOption(tab, 'Download Video Thumbnail', key='download_thumbnail').pack(anchor='w')
        CheckOption(tab, 'Enable CAPTCHA! workaround', key='enable_captcha_workaround').pack(anchor='w')
        CheckOption(tab, 'Add numbers to filenames when downloading thru playlist menu',
                    key='use_playlist_numbers').pack(anchor='w')

        # video extractor backend -------------------------
        extractor_frame = tk.Frame(tab, bg=bg)
        tk.Label(extractor_frame, bg=bg, fg=fg, text='Select video extractor engine:  ').pack(side='left')
        self.extractors_menu = Combobox(extractor_frame, values=config.video_extractors_list,
                                        selection=config.active_video_extractor)
        self.extractors_menu.callback = lambda: self.controller.set_video_backend(self.extractors_menu.selection)
        self.extractors_menu.pack(side='left')
        extractor_frame.pack(anchor='w')

        separator()

        # Network ------------------------------------------------------------------------------------------------------
        heading('Network:')

        # concurrent downloads
        LabeledEntryOption(tab, 'Concurrent downloads (1 ~ 100): ', entry_key='max_concurrent_downloads',
                           get_text_validator=lambda x: int(x) if 0 < int(x) < 101 else 3, width=8).pack(anchor='w')
        LabeledEntryOption(tab, 'Connections per download (1 ~ 100): ', entry_key='max_connections', width=8,
                           get_text_validator=lambda x: int(x) if 0 < int(x) < 101 else 10).pack(anchor='w')

        # speed limit
        speed_frame = tk.Frame(tab, bg=bg)
        CheckEntryOption(speed_frame, 'Speed Limit (kb/s, mb/s. gb/s): ', entry_key='speed_limit', width=8,
                         set_text_validator=lambda x: size_format(x), callback=self.show_speed_limit,
                         get_text_validator=lambda x: self.validate_speed_limit(x),
                         entry_disabled_value=0).pack(side='left')
        self.speed_limit_label = tk.Label(speed_frame, bg=bg, fg=fg)
        self.speed_limit_label.pack(side='left', padx=10)
        speed_frame.pack(anchor='w')
        self.show_speed_limit()

        # proxy
        proxy_frame = tk.Frame(tab, bg=bg)
        CheckEntryOption(proxy_frame, 'Proxy:', check_key='enable_proxy', entry_key='raw_proxy',
                         callback=self.set_proxy).pack(side='left', expand=True, fill='x')

        self.proxy_type_var = tk.StringVar()
        self.proxy_type_var.set(get_option('proxy_type', 'http'))

        def proxy_type_option(text):
            atk.button.Radiobutton(proxy_frame, text=text, value=text, variable=self.proxy_type_var, bg=bg,
                                   fg=fg).pack(side='left', padx=2)

        proxy_type_option('http')
        proxy_type_option('https')
        proxy_type_option('socks4')
        proxy_type_option('socks5')

        proxy_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))
        self.proxy_type_var.trace_add('write', self.set_proxy)

        CheckOption(tab, 'use proxy DNS', key='use_proxy_dns', callback=self.set_proxy).pack(anchor='w')

        # login
        login_frame = tk.Frame(tab, bg=bg)
        CheckOption(login_frame, 'Login', key='use_web_auth').pack(side='left')
        LabeledEntryOption(login_frame, 'User:', entry_key='username').pack(side='left', padx=(0, 5))
        LabeledEntryOption(login_frame, 'Pass:', entry_key='password', show='*').pack(side='left', padx=5)
        login_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        # cookies ---------------------------------------------
        def get_cookie_file(target):
            """get cookie file path"""
            fp = filedialog.askopenfilename()
            if fp:
                target.set(fp)

        cookies_frame = tk.Frame(tab, bg=MAIN_BG)
        cookies = CheckEntryOption(cookies_frame, 'Cookies file:', check_key='use_cookies', entry_key='cookie_file_path')
        cookies.pack(side='left', expand=True, fill='x')
        Button(cookies_frame, text='...', transparent=True, command=lambda: get_cookie_file(cookies)).pack(side='left')
        cookies_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        CheckEntryOption(tab, 'Referee url:', check_key='use_referer',
                         entry_key='referer_url').pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        def update_headers():
            config.http_headers['User-Agent'] = config.custom_user_agent or config.DEFAULT_USER_AGENT

        # config.HEADERS.update('User-Agent'=config.custom_user_agent)
        CheckEntryOption(tab, 'Custom user agent:', entry_key='custom_user_agent',
                         callback=update_headers).pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        # verify server's ssl certificate
        def ssl_disable_warning():
            if not config.verify_ssl_cert:
                # get user confirmation
                msg = ('WARNING: disabling verification of SSL certificate allows bad guys to man-in-the-middle the '
                       'communication without you know it and makes the communication insecure. '
                       'Just having encryption on a transfer is not enough as you cannot be sure that you are '
                       'communicating with the correct end-point. \n'
                       'Are you sure?')

                res = self.popup(msg, buttons=['Yes', 'Cancel'])

                if res != 'Yes':
                    ssl_cert_option.set(True)

        ssl_cert_option = CheckOption(tab, "verify server's SSL certificate", key='verify_ssl_cert',
                                      callback=ssl_disable_warning)
        ssl_cert_option.pack(anchor='w')

        LabeledEntryOption(tab, 'Auto refreshing expired urls [Num of retries]: ', entry_key='refresh_url_retries',
                           width=8, get_text_validator=lambda x: int(x)).pack(anchor='w')

        separator()

        # On Completion actions ----------------------------------------------------------------------------------------
        heading('On Download Completion:')
        tk.Label(tab, text='Select action to run after "ALL" download items are completed:', bg=bg,
                 fg=fg).pack(anchor='w', padx=5)

        CheckEntryOption(tab, ' Run command:  ', entry_key='on_completion_command').pack(anchor='w', fill='x',
                                                                                         expand=True, padx=(0, 5))
        CheckOption(tab, ' Shutdown computer', key='shutdown_pc').pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        separator()

        # Debugging ----------------------------------------------------------------------------------------------------
        heading('Debugging:')
        CheckOption(tab, 'keep temp files / folders after done downloading for debugging.', key='keep_temp').pack(anchor='w')
        CheckOption(tab, 'Re-raise all caught exceptions / errors for debugging "Application will crash on any Error"', key='TEST_MODE').pack(anchor='w')
        CheckOption(tab, 'Use ThreadPoolExecutor instead of individual threads', key='use_thread_pool_executor').pack(anchor='w')
        CheckOption(tab, 'Use Download Simulator', key='SIMULATOR').pack(anchor='w')

        separator()

        # add padding
        for w in tab.pack_slaves():
            if not w.pack_info().get('pady'):
                w.pack_configure(pady=5)

            # bind mousewheel scroll
            atk.scroll_with_mousewheel(w, target=tab, apply_to_children=True)

        return tab

    def create_log_tab(self):
        bg = MAIN_BG
        fg = MAIN_FG

        tab = tk.Frame(self.main_frame, bg=bg)

        # limit lines in log output to save memory, one line around 100 characters, 1000 lines will be 100000 chars
        # around 100 KB in memory
        self.log_text = atk.ScrolledText(tab, max_chars=100000, bg=bg, fg=fg, bd=1, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG,
                                         highlightbackground=SF_BG, highlightcolor=SF_BG, padx=5, pady=5)

        def copy_log():
            self.copy(self.log_text.get(1.0, tk.END))
            self.msgbox('Log text copied to clipboard')

        btn_frame = tk.Frame(tab, bg=MAIN_BG)
        tk.Label(btn_frame, text='Log Level:', bg=MAIN_BG, fg=BTN_BG, font='any 10 bold').pack(side='left')
        level_menu = Combobox(btn_frame, values=(1, 2, 3), selection=config.log_level, width=5)
        level_menu.callback = lambda: set_option(log_level=int(level_menu.selection))
        level_menu.pack(side='left', padx=5)

        Button(btn_frame, text='Clear', command=self.log_text.clear).pack(side='right', padx=5)
        # Button(btn_frame, text='Folder', command=lambda: open_folder(config.sett_folder)).pack(side='right', padx=5)
        # Button(btn_frame, text='Log File', command=open_log_file).pack(side='right', padx=5)
        Button(btn_frame, text='copy Log', command=copy_log).pack(side='right', padx=5)

        btn_frame.pack(pady=5, expand=True, fill='x')
        self.log_text.pack(expand=True, fill='both')

        return tab

    def create_update_tab(self):
        # update -----------------------------------------------------------------------------------------------------
        bg = MAIN_BG
        fg = MAIN_FG
        tab = tk.Frame(self.main_frame, bg=bg)

        tk.Label(tab, text=' Update Tab:', bg=HDG_BG, fg=HDG_FG, anchor='w',
                 font='any 10 bold').pack(anchor='n', expand=False, fill='x', ipady=3, pady=(0, 5))

        update_frame = tk.Frame(tab, bg=bg)
        update_frame.pack(anchor='n', fill='both', expand=True, pady=(20, 0))

        update_frame.columnconfigure(2, weight=1)

        def lbl(var):
            return tk.Label(update_frame, bg=bg, fg=fg, textvariable=var, padx=5)

        CheckEntryOption(update_frame, 'Check for update every: ', entry_key='update_frequency', width=4,
                         justify='center',
                         check_key='check_for_update', get_text_validator=lambda x: int(x) if int(x) > 0 else 7) \
            .grid(row=0, column=0, columnspan=2, sticky='w')
        tk.Label(update_frame, bg=bg, fg=fg, text='days', padx=5).grid(row=0, column=2, sticky='w')

        # FireDM update
        self.firedm_update_note = tk.StringVar()
        self.firedm_update_note.set(f'FireDM version: {config.APP_VERSION}')
        lbl(self.firedm_update_note).grid(row=1, column=1, columnspan=2, sticky='w', pady=20)
        Button(update_frame, image=imgs['refresh_icon'], text='  Manually Check for update!', compound='left',
               command=self.check_for_update).grid(row=1, column=3, sticky='w', padx=(20, 5))

        # youtube-dl and yt_dlp
        self.youtube_dl_update_note = tk.StringVar()
        self.youtube_dl_update_note.set(f'youtube-dl version: {config.youtube_dl_version}')
        lbl(self.youtube_dl_update_note).grid(row=2, column=1, columnspan=2, sticky='w', pady=20)

        self.yt_dlp_update_note = tk.StringVar()
        self.yt_dlp_update_note.set(f'yt_dlp version: {config.yt_dlp_version}')
        lbl(self.yt_dlp_update_note).grid(row=3, column=1, columnspan=2, sticky='w')

        if config.FROZEN and config.operating_system == 'Windows':
            Button(update_frame, text='Rollback update', command=lambda: self.rollback_pkg_update('youtube_dl'))\
                .grid(row=2, column=3, sticky='w', pady=5, padx=(20, 5))

            Button(update_frame, text='Rollback update', command=lambda: self.rollback_pkg_update('yt_dlp'))\
                .grid(row=3, column=3, sticky='w', pady=5, padx=(20, 5))

        # progressbar while updating packages
        self.update_progressbar = atk.RadialProgressbar(parent=update_frame, size=100, fg=PBAR_FG, text_bg=bg,
                                                        text_fg=PBAR_TXT)
        self.update_progressbar.grid(row=1, column=4, rowspan=3, pady=5, padx=20, sticky='e')

        return tab

    def select_tab(self, tab_name):
        """select and focus tab

        Args:
            tab_name (str): Name of button on side-bar
        """

        self.side_frame.select_tab(tab_name)

    def set_on_completion_command(self, uid):
        item = self.d_items.get(uid)
        if item.status == config.Status.completed:
            return
        current_command = self.controller.get_on_completion_command(uid)
        button, command = self.popup('Set command to run in terminal after this item download completes',
                                     'press "Disable" to disable command',
                                     get_user_input=True, default_user_input=current_command,
                                     buttons=['Apply', 'Disable'])

        if button == 'Apply':
            self.controller.set_on_completion_command(uid, command.strip())
        elif button == 'Disable':
            self.controller.set_on_completion_command(uid, '')

    def set_proxy(self, *args):
        enabled = config.enable_proxy
        raw_proxy = config.raw_proxy
        proxy_type = config.proxy_type = self.proxy_type_var.get()

        if not enabled:
            config.proxy = ''
            return

        # proxy dns
        if config.use_proxy_dns:
            if proxy_type == 'socks4':
                proxy_type = 'socks4a'
            elif proxy_type == 'socks5':
                proxy_type = 'socks5h'

        if raw_proxy:
            raw_proxy = raw_proxy.split('://')[-1]
            proxy = proxy_type + '://' + raw_proxy
        else:
            proxy = ''

        config.proxy = proxy

        # print('config.proxy = ', config.proxy)

        return proxy

    def validate_speed_limit(self, sl):
        # if no units entered will assume it KB
        try:
            _ = int(sl)  # will succeed if it has no string
            sl = f'{sl} KB'
        except:
            pass

        sl = parse_bytes(sl)
        return sl

    def show_speed_limit(self):
        """display current speed limit in settings tab"""
        sl = get_option('speed_limit', 0)
        text = size_format(sl) if sl else '.. No Limit!'
        self.speed_limit_label.config(text=f'current value: {text}')

    def remember_window_size(self, *args):
        """save current window size in config.window_size"""
        config.window_size = (self.root.winfo_width(), self.root.winfo_height())

    # endregion

    # region DItem
    def create_ditem(self, uid, **kwargs):
        """create new DItem and show it in downloads tab

        Args:
            uid (str): download item's uid
            focus (bool): select d_tab and scroll to show ditem after creation
            kwargs: key/values to update a download item
        """
        status = kwargs.get('status')

        # check if item already created before
        if uid in self.d_items:
            return
        d_item = DItem(self.d_tab, uid, status, on_toggle_callback=self.update_stat_lbl)
        excludes = []

        if status != config.Status.completed:
            # bind buttons commands
            d_item.play_button['command'] = lambda: self.toggle_download(d_item.uid)

            excludes += [d_item.play_button]

        d_item.delete_button['command'] = lambda: self.delete(d_item.uid)

        # bind double click to play a file
        d_item.bind('<Double-Button-1>', lambda event, x=uid: self.controller.play_file(uid=x), exclude=excludes)

        # right click menu
        right_click_map = {'Open File  (Enter)': lambda uid: self.controller.play_file(uid=uid),
                           'Open File Location': lambda uid: self.controller.open_folder(uid=uid),
                           'Watch while downloading': lambda uid: self.controller.play_file(uid=uid),
                           'copy webpage url': lambda uid: self.copy(self.controller.get_webpage_url(uid=uid)),
                           'copy direct url': lambda uid: self.copy(self.controller.get_direct_url(uid=uid)),
                           'copy playlist url': lambda uid: self.copy(self.controller.get_playlist_url(uid=uid)),
                           'Resume': lambda uid: self.resume_selected(),
                           'Pause': lambda uid: self.stop_selected(),
                           'Delete  (Del)': lambda uid: self.delete_selected(),
                           'Schedule / unschedule': lambda uid: self.schedule_selected(),
                           'Toggle Shutdown Pc when finish': lambda uid: self.controller.toggle_shutdown(uid),
                           'On item completion command': lambda uid: self.set_on_completion_command(uid),
                           'Properties': lambda uid: self.msgbox(self.controller.get_properties(uid=uid)),
                           }

        entries = list(right_click_map.keys())
        # add separators
        for i in (-7, -3, -1):
            entries.insert(i, '---')

        atk.RightClickMenu(d_item, entries,
                           callback=lambda key, uid=d_item.uid: right_click_map[key](uid),
                           bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG)

        self.d_items[uid] = d_item
        d_item.update(**kwargs)

        # bind mousewheel
        atk.scroll_with_mousewheel(d_item, target=self.d_tab, apply_to_children=True)

        d_item.bind('<Button-1>', lambda event, uid=uid: self.on_toggle_ditem(uid))
        d_item.bind('<Button-2>', lambda event, uid=uid: self.on_item_rightclick(uid), add='+')
        d_item.bind('<Button-3>', lambda event, uid=uid: self.on_item_rightclick(uid), add='+')
        d_item.bind('<Control-1>', lambda event: d_item.toggle())
        d_item.bind('<Shift-1>', lambda event, uid=uid: self.on_shift_click(uid))

        d_item.show()

    def on_shift_click(self, uid):
        """batch select ditems in downloads tab"""
        current_item = self.d_items[uid]
        current_item.select()

        items_list = list(self.d_items.values())
        selected_numbers = [items_list.index(item) for item in items_list if item.selected]
        if len(selected_numbers) > 1:
            for i in range(selected_numbers[0], selected_numbers[-1] + 1):
                items_list[i].select()

    def open_selected_file(self):
        selected_items = self.get_selected_items()
        if len(selected_items) == 1:
            item = selected_items[0]
            self.controller.open_file(uid=item.uid)

    def resume_selected(self):
        """resume downloading selected and non completed items in downloads tab"""

        for uid, item in self.get_selected_items():
            if item.status in (config.Status.cancelled, config.Status.error):
                self.resume_download(uid)

    def stop_selected(self):
        """stop downloading selected items in downloads tab"""
        for uid, item in self.get_selected_items():
            self.stop_download(uid)

    def delete(self, uid):
        """delete download item"""
        # get user confirmation
        msg = 'Are you sure you want to delete:\n' \
              f'{self.d_items[uid].name}'
        res = self.popup(msg, buttons=['Ok', 'Cancel'])

        if res != 'Ok':
            return

        # temporarily disable autoscroll
        if config.autoscroll_download_tab:
            self.d_tab.autoscroll = False

        # pop d
        d = self.d_items.pop(uid)

        d.destroy()

        self.controller.delete(uid)

        if config.autoscroll_download_tab:
            # enable autoscroll
            self.root.update_idletasks()
            self.d_tab.autoscroll = True

    def delete_selected(self):
        """remove selected download items from downloads tab
        only temp files will be removed, completed files on disk will never be deleted"""
        selected_items = self.get_selected_items()
        num = len(selected_items)
        if not num:
            return

        elif num == 1:
            item = selected_items[0]
            self.delete(item.uid)
            return

        # get user confirmation
        msg = 'Are you sure you want to clear selected download items from downloads list?\n' \
              'note: only temp files will be removed, completed files on disk will never be deleted\n'
        res = self.popup(msg, buttons=['Ok', 'Cancel'])

        if res != 'Ok':
            return

        deleted = []
        # remove from gui
        for uid, item in self.d_items.items():
            if item.selected:
                deleted.append(uid)
                item.destroy()

        self.d_items = {k: v for k, v in self.d_items.items() if k not in deleted}

        self.update_stat_lbl()

        # actual DownloadItem remove by controller
        for uid in deleted:
            self.controller.delete(uid)

        # solve canvas doesn't auto resize itself
        self.d_tab.scrolltotop()

    def select_ditems(self, command):
        """select ditems in downloads tab
        Args:
            command (str): one of ['Select all', 'Select None', 'Select completed', 'Select non completed']
        """
        items = self.d_items.values()

        # reset selection
        for item in items:
            item.select(False)

        if command == 'Select None':
            return

        if command == 'Select completed':
            items = [item for item in self.d_items.values() if item.status == config.Status.completed]

        elif command == 'Select non completed':
            items = [item for item in self.d_items.values() if item.status != config.Status.completed]

        # set selection
        for item in items:
            item.select()

    def on_item_rightclick(self, uid):
        item = self.d_items[uid]

        if not item.selected:
            self.on_toggle_ditem(uid)

    def on_toggle_ditem(self, uid):
        current_item = self.d_items[uid]
        current_item.select()

        for item in self.d_items.values():
            if item is not current_item:
                item.select(False)

    def get_selected_items(self):
        """return a list of selected items"""
        return [item for item in self.d_items.values() if item.selected]

    def update_stat_lbl(self):
        """update the number of selected download items and display it on a label in downloads tab"""
        count = len(self.get_selected_items())
        s = [item.status for item in self.d_items.values()]

        self.select_lbl['text'] = f'  Selected [{count} of {len(self.d_items)}]'
        self.stat_lbl['text'] = f'Downloading: {s.count(config.Status.downloading)}, ' \
                                f'Completed: {s.count(config.Status.completed)},  ' \
                                f'Cancelled: {s.count(config.Status.cancelled)},  ' \
                                f'Sceduled: {s.count(config.Status.scheduled)}, ' \
                                f'Pending: {s.count(config.Status.pending)}'

        if s.count(config.Status.downloading) > 0:
            self.resume_all_btn['text'] = 'Stop All'
        else:
            self.resume_all_btn['text'] = 'Resume All'

    # endregion

    # region download
    def download_btn_callback(self):
        """callback for download button in main tab"""
        # select audio for dash video
        if config.manually_select_dash_audio:
            menu = self.controller.get_audio_menu()
            if menu:
                selected_audio = self.controller.get_selected_audio()
                idx = menu.index(selected_audio) if selected_audio else 0

                AudioWindow(self, menu, idx)

        # download
        self.download(name=self.file_properties.name, folder=self.file_properties.folder.get())

    def download(self, uid=None, **kwargs):
        """Send command to controller to download an item

        Args:
            uid (str): download item's unique identifier, if omitted active item will be downloaded
            kwargs: key/value for any legit attributes in DownloadItem
        """
        self.controller.download(uid, **kwargs)

    def toggle_download(self, uid):
        item = self.d_items[uid]

        if item.status in config.Status.active_states:
            self.stop_download(uid)
        else:
            self.resume_download(uid)

    def stop_download(self, uid):
        self.controller.stop_download(uid)

    def resume_download(self, uid):
        """start / resume download for a download item

        Args:
            uid (str): download item's unique identifier
        """

        self.download(uid)

    def resume_all(self):
        for uid, item in self.d_items.items():
            if item.status not in config.Status.active_states and item.status != config.Status.completed:
                self.resume_download(uid)

    def stop_all(self):
        for uid, item in self.d_items.items():
            self.stop_download(uid)
    # endregion

    # region update view

    def update_view(self, **kwargs):
        """thread safe update view, it will be called from controller's thread"""

        # run thru queue and event
        data = {'kwargs': kwargs}
        self.update_view_q.put(data)

        # generate event
        # self.root.event_generate('<<updateViewEvent>>', when='tail')
        self.generate_event('<<updateViewEvent>>')

        # direct running, not sure if it will work correctly because of threading and tkinter
        # self._update_view(**kwargs)

    def update_view_handler(self, event):
        # print('update view handler................................')
        if self.update_view_q.qsize():
            data = self.update_view_q.get_nowait()

            kwargs = data.get('kwargs', {})

            # call method
            self._update_view(**kwargs)

    def _update_view(self, **kwargs):
        """real update view"""
        command = kwargs.get('command')
        uid = kwargs.get('uid')
        active = kwargs.get('active', None)

        if 'status' in kwargs:
            self.root.after(100, self.update_stat_lbl)

        # load previous download items in d_tab, needed at startup
        if command == 'd_list':
            d_list = kwargs.get('d_list')
            for i, item in enumerate(d_list):
                self.root.after(1000 + i * 5, lambda k=item: self.create_ditem(**k, focus=False))

        # update playlist menu
        elif command == 'playlist_menu':
            menu = kwargs['playlist_menu']
            if menu:
                self.pl_menu.hide_progressbar()
                self.pl_menu.set(menu)
                num = len(menu)
                self.pl_menu.update_title(f'{num} video{"s" if num>1 else ""}:')

                # select first video
                self.pl_menu.select(0)

                self.stream_menu.start_progressbar()
                self.controller.select_playlist_video(0)
            else:
                self.pl_menu.reset()

        # update stream menu
        elif command == 'stream_menu':
            video_idx = kwargs['video_idx']
            stream_menu = kwargs['stream_menu']
            stream_idx = kwargs['stream_idx']

            # make sure this data belong to selected item in playlist
            if self.pl_menu.select() == video_idx:
                self.stream_menu.hide_progressbar()
                self.stream_menu.set(stream_menu)
                self.stream_menu.select(stream_idx)

            # pass to playlist download window
            if self.pl_window:
                self.pl_window.update_view(video_idx=video_idx, stream_menu=stream_menu, stream_idx=stream_idx)

        # create new items
        elif command == 'new':
            ditem = self.d_items.get(uid)
            if ditem and ditem.status == config.Status.completed:
                ditem.destroy()
                self.d_items.pop(uid)
            self.create_ditem(**kwargs, focus=True)
            self.select_tab('Downloads')

        # update current item
        elif command == 'update':
            # update active item
            if active:
                self.file_properties.update(**kwargs)

                # thumbnail
                img_base64 = kwargs.get('thumbnail', None)
                if img_base64:
                    self.thumbnail.show(b64=img_base64)

            # update item in d_tab
            elif uid in self.d_items:
                self.d_items[uid].update(**kwargs)

        # handle signals for post processor callbacks
        elif command == 'signal':
            signal_id = kwargs.get('signal_id')
            self.execute_post_processor(signal_id)

        # total speed
        elif command == 'total_speed':
            ts = size_format(kwargs.get('total_speed'), tail='/s')
            self.total_speed.set(ts)

    # endregion

    # region general
    def bind_keyboard(self, seq, callback, add='+', widgets=None):
        """bind keyboard keys, it should be bind to root to work correctly
        widgets: list of widgets that must be visible to execute the callback
        """

        def custom_callback(*args):
            if widgets:
                if any([widget.winfo_viewable() for widget in widgets]):
                    callback()
            else:
                callback()

        self.root.bind(seq, custom_callback, add=add)

    def run(self):
        """run application"""
        self.root.mainloop()

    def close(self):
        """hide main window or terminate application"""
        self.hide()
        if not (config.minimize_to_systray and self.systray.active):
            self.quit()

    def quit(self):
        """Quit application and systray"""
        config.shutdown = True
        self.root.destroy()  # destroy all widgets and quit mainloop

        # save themes
        self.save_user_themes()
        print('Gui terminated')

        # quit systray
        self.systray.shutdown()

    def reset(self):
        self.pl_menu.reset()
        self.stream_menu.reset()
        self.thumbnail.reset()
        self.file_properties.reset()

        self.controller.reset()

    def get_unique_number(self):
        self.counter += 1
        return self.counter

    def run_method_handler(self, event):
        """run a method in self.command_q
        it will be triggered by custom event

        data example in command_q:
        {'id': unique_id, 'method': f, 'args': args, 'kwargs': kwargs, 'get_response': get_response}
        """

        if self.command_q.qsize():
            data = self.command_q.get_nowait()

            f = data['method']
            args = data.get('args', [])
            kwargs = data.get('kwargs', {})
            get_response = data.get('get_response', False)

            # call method
            try:
                res = f(*args, **kwargs)

                # return response thru queue
                if get_response:
                    data['response'] = res
                    self.response_q.put(data)
            except Exception as e:
                log('run method:', e)

    def run_method(self, f, *args, get_response=False, **kwargs):
        """run a method from a thread
        it will add argument to a queue which will be parsed from main thread, then wait on a response queue to return
        value from this method

        self.command_listener will process command_q, call passed method and return values in response_q

        Args:
            f (callable): a method to be called
            get_response (bool): get return value from called method

        Example:
            if view is an object from this class
            view.run_method(view.get_user_response, msg, options)
        """

        if config.shutdown:
            return

        unique_id = self.get_unique_number()
        self.command_q.put({'id': unique_id, 'method': f, 'args': args, 'kwargs': kwargs, 'get_response': get_response})

        # fire an event
        self.generate_event('<<runMethodEvent>>')

        # wait for right response
        if get_response:
            while True:
                data = self.response_q.get()
                if unique_id == data['id']:
                    return data['response']
                else:
                    self.response_q.put(data)
                time.sleep(0.01)

    def update_youtube_dl_info(self):
        """write youtube-dl and yt_dlp version once it gets imported"""

        self.youtube_dl_update_note.set(f'youtube-dl version: {config.youtube_dl_version or "Loading ... "}')
        self.yt_dlp_update_note.set(f'yt_dlp version: {config.yt_dlp_version or "Loading ... "}')

        if not all((config.youtube_dl_version, config.yt_dlp_version)):
            self.root.after(1000, self.update_youtube_dl_info)

    def rollback_pkg_update(self, pkg):
        """restore previous package version e.g. youtube-dl and yt_dlp"""
        response = self.popup(f'Delete last {pkg} update and restore previous version?', buttons=['Ok', 'Cancel'])

        if response == 'Ok':
            self.select_tab('Log')
            self.controller.rollback_pkg_update(pkg)

    def restart_gui(self):
        self.main_frame.destroy()
        self.d_items.clear()
        self.create_main_widgets()
        self.select_tab('Settings')

        # get download items
        self.root.after(1000, self.controller.get_d_list)

        self.run()

    def post_startup(self):
        """it will be called after gui displayed"""

        # register log callbacks
        config.log_callbacks.append(self.log_callback)
        config.log_popup_callback = self.log_popup

        # log runtime info
        self.controller.log_runtime_info()

        # log extra pkgs info
        log('Tkinter version:', self.root.call("info", "patchlevel"))
        log('AwesomeTkinter version:', atk_version)
        # minimum AwesomeTkinter version warning
        atk_min_version = '2021.4.2'
        if parse_version(atk_version) < parse_version(atk_min_version):
            atk_warning = f'WARNING!, "AwesomeTkinter" package is outdated, ' \
                          f'please upgrade to latest version, to avoid application malfunctioning \n' \
                          f'use command: python3 -m pip install awesometkinter --upgrade'
            log(atk_warning, file=sys.stderr)

        log('Pillow version:', PIL.__version__)
        log('PyCUrl version:', pycurl.version)
        log()

        # get download items
        self.controller.get_d_list()

        # start url monitor thread
        run_thread(url_watchdog, self.root, daemon=True)

        # run systray
        if config.enable_systray:
            run_thread(self.systray.run, daemon=True)
        else:
            log('systray disabled in settings ...')

        # update youtube-dl version info once gets loaded
        self.update_youtube_dl_info()

        # auto check for update, run after 1 minute to make sure
        # video extractors loaded completely before checking for update
        self.root.after(60000, self.controller.auto_check_for_update)

    def focus(self):
        """focus main window and bring it to front"""

        self.root.deiconify()
        self.root.lift()

    def generate_event(self, sequence):
        """generate an event

        Args:
            sequence (str): an event sequence accepted by tkinter, e.g. '<<myVirtualEvent>>' or '<1>', note double marks
            for virtual event names
        """
        try:
            self.root.event_generate(sequence, when='tail')
        except:
            pass

    def hide(self):
        self.root.withdraw()

    def unhide(self):
        self.root.deiconify()

    def schedule_selected(self):
        selected_items = self.get_selected_items()
        sched_items = [item for item in selected_items if item.status == config.Status.scheduled]
        if sched_items:
            for item in sched_items:
                self.controller.schedule_cancel(uid=item.uid)
        else:
            # show date picker
            dp = DatePicker(self.root, title='Schedule Download Item')
            if dp.selected_date:
                for item in selected_items:
                    self.controller.schedule_start(uid=item.uid, target_date=dp.selected_date)

    def show_about_notes(self):
        res = self.popup(about_notes, buttons=['Home', 'Help!', 'Close'], title='About FireDM')
        if res == 'Help!':
            open_webpage('https://github.com/firedm/FireDM/blob/master/docs/user_guide.md')
        elif res == 'Home':
            open_webpage('https://github.com/firedm/FireDM')

    @busy_callback
    def check_for_update(self):
        log('\n\nstart Checking for update ....')
        self.select_tab('Log')

        def cleanup():
            """will be executed when controller finishes checking for update"""
            self.update_progressbar.stop()
            self.update_progressbar.set(0)

            # make function available again
            free_callback(self.check_for_update)

        # run progressbar
        self.update_progressbar.start()
        signal_id = self.add_postprocessor(cleanup)
        self.controller.check_for_update(signal_id=signal_id)

    def add_postprocessor(self, callback):
        signal_id = len(self.post_processors)
        self.post_processors[signal_id] = callback
        return signal_id

    def execute_post_processor(self, signal_id):
        callback = self.post_processors.get(signal_id, None)
        if callable(callback):
            callback()
        else:
            log('post processor not found for signal_id:', signal_id)

    # endregion

    # region video
    def stream_select_callback(self, *args, idx=None):
        idx = idx or self.stream_menu.select()
        if idx is not None:
            self.controller.select_stream(idx)

    def video_select_callback(self, *args, idx=None):
        idx = idx or self.pl_menu.select()

        if idx is not None:
            self.stream_menu.reset()
            self.stream_menu.start_progressbar()
            self.thumbnail.reset()
            self.controller.select_playlist_video(idx)

    def show_subtitles_window(self):
        if self.subtitles_window :
            self.msgbox('Subtitles window already opened')
            return

        subs = self.controller.get_subtitles()
        if subs:
            self.subtitles_window = SubtitleWindow(self, subs)
        else:
            self.msgbox('No Subtitles available')

    def show_pl_window(self):
        if self.pl_window:
            self.msgbox('Playlist window already opened')
            return

        # pl = ('1- #EZScience_ Preparing to Launch the Perseverance Rover to Mars', '2- #EZScience Episode 9 Part 2_ Mars Perseverance Rover Will Look for Signs of Ancient Life', "3- #EZScience Episode 9 Part 1_ Launching to Mars with NASA's Perseverance Rover", '4- #EZScience Episode 8_ Your Career Questions Answered!', '5- #EZScience Episode 7_ Your Space Science Questions Answered!', "6- #EZScience Episode 6_ NASA's Hubble Space Telescope — Our Window to the Stars", '7- #EZScience Episode 5_ Balloon Science', '8- #EZScience Episode 4_ The Path to Mars 2020', '9- #EZScience Episode 3_ Our Favorite Star — The Sun', '10- #EZScience Episode 2_ The Search for New Planets', '11- #EZScience Episode 1_ Exploring the Moon with Apollo')
        pl = self.pl_menu.get()
        if not pl:
            self.msgbox('No videos in playlist')
            return

        self.pl_window = PlaylistWindow(self, pl)

    def get_offline_webpage_path(self):
        """get the file path of the offline webpage contents as a workaround for captcha
        """

        msg = 'Found Captcha when downloading webpage contents, you should open this link in your browser' \
              ' and  save webpage manually on the disk (as htm or html), then press below "select file" button to ' \
              'select your saved webpage file'
        fp = None

        btn = self.popup(msg, buttons=['Select file', 'Cancel'], title='Captcha found')

        if btn == 'Select file':
            fp = filedialog.askopenfilename()

        return fp

    # endregion

    # region url, clipboard
    def refresh_url(self, url):
        self.url_var.set('')
        self.url_var.set(url)

        # select home tab
        self.select_tab('Home')

    def url_change_handler(self, event):
        """update url entry contents when new url copied to clipboard"""

        url = self.paste().strip()
        self.url_var.set(url)

        # select home tab
        self.select_tab('Home')

        self.focus()

        return "break"

    def url_entry_callback(self, *args):
        """callback for url entry edit"""
        url = self.url_var.get().strip()

        if self.url != url:
            self.url = url
            self.reset()

            # cancel previous job
            if self.url_after_id:
                self.root.after_cancel(self.url_after_id)

            # schedule job to process this url
            if url:
                self.url_after_id = self.root.after(1000, self.process_url, url)

    def copy(self, value):
        """copy clipboard value

        Args:
            value (str): value to be copied to clipboard
        """
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(value))
        except:
            pass

    def paste(self):
        """get clipboard value"""
        try:
            value = self.root.clipboard_get()
        except:
            value = ''

        return value

    def custom_paste(self, event):
        """custom paste text in entry widgets
        Ack: https://stackoverflow.com/a/46636970
        """
        try:
            event.widget.delete("sel.first", "sel.last")
        except:
            pass

        value = self.paste().strip()
        event.widget.insert("insert", value)
        return "break"

    def process_url(self, url):
        self.reset()
        if not url:
            return
        self.pl_menu.start_progressbar()
        self.controller.process_url(url)
    # endregion

    # region log and popup
    def get_user_response(self, msg, options):
        """thread safe - get user response
        it will be called by controller to get user decision
        don't call it internally, it will freeze gui, instead use self.popup()

        Args:
            msg (str): message to be displayed in popup message
            options (list, tuple): names of buttons in popup window
        """
        res = self.run_method(self.popup, msg, buttons=options, get_response=True)
        return res

    def msgbox(self, *args):
        """thread safe - popup message that can be called from a thread

        Args:
            args (str): any number of string arguments
        """
        self.run_method(self.popup, *args, get_response=False, buttons=['Ok'], title='Info')

    def popup(self, *args, buttons=None, title='Attention', get_user_input=False, default_user_input='', bg=None,
              fg=None):
        x = Popup(*args, buttons=buttons, parent=self.root, title=title, get_user_input=get_user_input,
                  default_user_input=default_user_input, bg=bg, fg=fg)
        response = x.show()
        return response

    def log_callback(self, start, text, end):
        """thread safe - log callback to be executed when calling utils.log"""
        msg = start + text + end
        self.run_method(self.log_text.append, msg, get_response=False)

    def log_popup(self, start, text, end):
        """thread safe log popup callback to be executed when calling utils.log with showpopup=True"""
        self.msgbox(text)

    # endregion


if __name__ == '__main__':
    try:
        controller = Controller(view_class=MainWindow)
        controller.run()
    except Exception as e:
        print('error:', e)
        raise e

