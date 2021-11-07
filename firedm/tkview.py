"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        Main application gui design by tkinter
"""
import datetime
import json
import re
import time
import pycurl
import tkinter as tk
from tkinter import font as tkfont
import awesometkinter as atk
from tkinter import ttk, filedialog, colorchooser
from awesometkinter.version import __version__ as atk_version
import PIL
from queue import Queue
import os
import sys
import subprocess
import signal

if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

    __package__ = 'firedm'
    import firedm

from .view import IView
from .controller import Controller, set_option, get_option, log_runtime_info
from .utils import *
from . import config
from . import iconsbase64
from .iconsbase64 import *
from .systray import SysTray
from .about import about_notes
from .themes import *

# ignore bidi support on non-Linux operating systems
add_bidi_support = lambda widget, *args, **kwargs: widget
render_text = lambda text, *args, **kwargs: text
derender_text = lambda text, *args, **kwargs: text

# bidi support on linux
if config.operating_system == 'Linux':
    try:
        from awesometkinter.bidirender import add_bidi_support, render_text, derender_text
    except Exception as e:
        print('Bidi support error:', e)


config.atk_version = atk_version
gui_font = None

# all themes
all_themes = {}

# add builtin themes
all_themes.update(builtin_themes)


# widget's images, it will be updated with theme change
imgs = {}


def create_imgs():
    """create widget's images, should be called with theme change"""

    sizes = {'playlist_icon': 25}
    color = BTN_BG

    for k in ('refresh_icon', 'playlist_icon', 'subtitle_icon', 'about_icon', 'folder_icon',
              'play_icon', 'pause_icon', 'delete_icon', 'undo_icon', 'bat_icon', 'audio_icon'):
        v = iconsbase64.__dict__[k]

        img = atk.create_image(b64=v, color=color, size=sizes.get(k, None))

        # on mouse hover image
        img.zoomed = atk.create_image(b64=v, color=color, size=img.width() + 5)
        imgs[k] = img

    imgs['blinker_icon'] = atk.create_image(b64=download_icon, color=BTN_BG, size=12)
    imgs['done_icon'] = atk.create_image(b64=done_icon, color=BTN_BG)
    imgs['hourglass_icon'] = atk.create_image(b64=hourglass_icon, color=BTN_BG)
    imgs['select_icon'] = atk.create_image(b64=select_icon, color=HDG_FG)
    imgs['view_icon'] = atk.create_image(b64=view_icon, color=HDG_FG)
    imgs['filter_icon'] = atk.create_image(b64=filter_icon, color=HDG_FG)


app_icon_img = None
popup_icon_img = None

busy_callbacks = []


def ignore_calls_when_busy(callback):
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
        self.current_theme = all_themes.get(config.current_theme) or all_themes[config.DEFAULT_THEME]

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
        tk.Button(bottom_frame, text='cancel', command=self.destroy, bg=BTN_BG, fg=BTN_FG).pack(side='left', anchor='e', padx=5, pady=5)

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
            all_names = list(all_themes.keys())
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

        theme = all_themes[theme_name] = kwargs

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

        tk.Button.__init__(self, parent)

        if 'tooltip' in kwargs:
            tooltip_text = kwargs.pop('tooltip')
            try:
                atk.tooltip(self, tooltip_text, xoffset=15, yoffset=15)
            except Exception as e:
                print(e)

        options.update(kwargs)
        atk.configure_widget(self, **options)

        # on mouse hover effect
        if image and hasattr(image, 'zoomed'):
            self.bind('<Enter>', lambda e: self.config(image=image.zoomed), add='+')
            self.bind('<Leave>', lambda e: self.config(image=image), add='+')


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


class AutofitLabel(tk.Label):
    """label that fit contents by using 3 dots in place of truncated text
    should be autoresizable, e.g. packed with expand=True and fill='x', or grid with sticky='ew'
    """

    def __init__(self, parent=None, justify='left', anchor='w', **kwargs):
        tk.Label.__init__(self, parent, justify=justify, anchor=anchor, **kwargs)
        self.original_text = ''
        self.id = None
        self.bind('<Configure>', self.schedule)

    def schedule(self, *args):
        self.unschedule()
        self.id = self.after(500, self.update_text)

    def unschedule(self):
        if self.id:
            self.after_cancel(self.id)
            self.id = None

    def update_text(self, *args):
        txt = self.original_text or self['text']
        self.original_text = txt
        width = self.winfo_width()
        font = tkfont.Font(font=self['font'])
        txt_width = font.measure(txt)

        if txt_width > width:
            for i in range(0, len(txt), 2):
                num = len(txt) - i
                slice = num // 2
                new_txt = txt[0:slice] + ' ... ' + txt[-slice:]
                if font.measure(new_txt) <= width:
                    self['text'] = new_txt
                    break
        else:
            self['text'] = self.original_text


class Popup(tk.Toplevel):
    """popup window
    show simple messages, get user text input and save user choice "pressed button"
    to get user response you call show() and it will block until window is closed

    usage:

        window = Popup('Deleting "video.mp4" file', 'are you sure?',  buttons=['Yes', 'Cancel'], parent=root)
        response = window.show()
        if response == 'Yes':
            do stuff ....

    return:
        button_name, or (button_name, user_input) if get_user_input=True

    """
    def __init__(self, *args, buttons=None, parent=None, title='Attention', get_user_input=False, default_user_input='',
                 bg=None, fg=None, custom_widget=None, optout_id=None):
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
            optout_id(int): popup number as in config.popups dict, if exist will show "don't show again" option
            custom_widget: any tk widget you need to add to popup window

        """
        self.parent = parent

        # fix bidi
        rendered_msgs = [render_text(msg) for msg in args]
        self.msg = '\n'.join(rendered_msgs)

        self.buttons = buttons or ['Ok']
        self.bg = bg or MAIN_BG
        self.fg = fg or MAIN_FG
        self.window_title = title
        self.get_user_input = get_user_input
        self.default_user_input = default_user_input
        self.custom_widget = custom_widget
        self.optout_id = optout_id

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

        # don't show this message again
        if self.optout_id:
            self.optout_var = tk.BooleanVar()
            atk.Checkbutton(main_frame, text="Don't show this message again", bd=0, 
                            command=self.optout_handler, onvalue=True, offvalue=False,
                            variable=self.optout_var).pack(side='bottom', anchor='w', padx=5)

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

    def optout_handler(self):
        value = not self.optout_var.get()
        config.enable_popup(self.optout_id, value)

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
        btn = ttk.Radiobutton(f, text=text, image=img, compound='top', style=self.side_btn_style, variable=self.var,
                              value=text, cursor='hand2')
        btn.grid(row=0, column=1, sticky='ewns', padx=5, pady=10)

        # on mouse hover effect, bind frame instead of button for smoother animation transition between side buttons
        f.bind('<Enter>', lambda e: btn.config(image=img.zoomed))
        f.bind('<Leave>', lambda e: btn.config(image=img))

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

        self.get = self.var.get

    def set(self, values):
        # fix bidi
        rendered_values = [render_text(x) for x in values]
        self.var.set(rendered_values)

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

    def reset(self):
        self.set([])
        self.reset_progressbar()
        self.show_progressbar()
        self.update_title(self.original_title)

    def update_title(self, title):
        self.title_var.set(title)


class FileDialog:
    """use alternative file chooser to replace tkinter ugly file chooser on linux
    
    available options: 
        Zenity: command line tool, based on gtk
        kdialog: command line tool for kde file chooser
        gtk: use Gtk.FileChooserDialog directly thru python, "will not use", since sometimes it will raise
             error: Gdk-Message: Fatal IO error 0 (Success) on X server :1, and application will crash
    """
    def __init__(self, foldersonly=False):
        self.use = 'TK'  #, 'zenity', or 'kdialog'
        self.foldersonly = foldersonly
        self.title = 'FireDM - ' 
        self.title += 'Select a folder' if self.foldersonly else 'Select a file'
        if config.operating_system == 'Linux':
            # looking for zenity
            error, zenity_path = run_command('which zenity', verbose=False)
            if zenity_path:
                self.use = 'zenity'
            else:
                # looking for kdialog
                error, kdialog_path = run_command('which kdialog', verbose=False)
                if kdialog_path:
                    self.use = 'kdialog'

    def run(self, initialdir=''):
        initialdir = initialdir or config.download_folder
        
        if self.use == 'zenity':
            cmd = 'zenity --file-selection'
            if self.foldersonly:
                cmd += ' --directory'
            if isinstance(initialdir, str):
                cmd += f' --filename="{initialdir}"'
            retcode, path = run_command(cmd, ignore_stderr=True)
            # zenity will return either 0, 1 or 5, depending on whether the user pressed OK, 
            # Cancel or timeout has been reached
            if retcode in (0, 1, 5):
                selected_path = path

        elif self.use == 'kdialog':
            cmd = 'kdialog'
            if self.foldersonly:
                cmd += ' --getexistingdirectory'
            else:
                cmd += ' --getopenfilename'

            if isinstance(initialdir, str):
                cmd += f' "{initialdir}"'

            retcode, path = run_command(cmd, ignore_stderr=True)
            # kdialog will return either 0, 1 depending on whether the user pressed OK, Cancel
            if retcode in (0, 1):
                selected_path = path
        else:
            selected_path = self.run_default(initialdir=initialdir)

        return selected_path

    def run_default(self, initialdir=''):
        # use ugly tkinter filechooser
        if self.foldersonly:
            selected_path = filedialog.askdirectory(initialdir=initialdir)
        else:
            selected_path = filedialog.askopenfilename(initialdir=initialdir)
        
        return selected_path


filechooser = FileDialog().run
folderchooser = FileDialog(foldersonly=True).run


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
        self.foldervar = tk.StringVar()
        self.size = tk.StringVar()
        self.type = tk.StringVar()
        self.subtype = tk.StringVar()
        self.resumable = tk.StringVar()
        self.duration = tk.StringVar()


        # show default folder value
        self.update(folder=config.download_folder)

        self.create_widgets()

    @property
    def name(self):
        # convert rendered bidi text to its logical order 
        title = derender_text(self.title.get())

        ext = self.extension.get()
        if not ext.startswith('.'):
            ext = '.' + ext

        return title + ext

    @property
    def folder(self):
        path = self.foldervar.get()

        if config.operating_system == 'Linux':
            path = derender_text(path, ispath=True)
        return path

    @folder.setter
    def folder(self, path):
        if config.operating_system == 'Linux':
            path = render_text(path, ispath=True)

        self.foldervar.set(path)

    def create_widgets(self):

        def label(text='', textvariable=None, r=1, c=0, rs=1, cs=1, sticky='we'):
            return tk.Label(self, text=text, textvariable=textvariable, bg=self.bg, fg=self.fg, anchor='w'). \
                grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)

        def separator(r):
            return ttk.Separator(self, orient='horizontal').grid(sticky='ew', pady=0, row=r, column=0, columnspan=3)

        # order of properties
        fields = ('name', 'extension', 'folder', 'size', 'misc','duration')
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
        add_bidi_support(self.title_entry, render_copy_paste=True, copy_paste_menu=True, ispath=False)

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
        self.ext_entry.bind('<FocusIn>', lambda event: self.ext_entry.config(bg='white', fg='black'), add='+')
        self.ext_entry.bind('<FocusOut>', lambda event: self.ext_entry.config(bg=self.bg, fg=self.fg), add='+')

        # size ---------------------------------------------------------------------------------------------------------
        label('Size:', r=row['size'], c=0)
        label('540 MB', textvariable=self.size, r=row['size'], c=1)
        
        label('Duration:', r=row['duration_string'], c=0)
        label('N/A',r=row['duration'],textvariable=self.duration,c=1)

        # misc ---------------------------------------------------------------------------------------------------------
        misc_frame = tk.Frame(self, bg=self.bg)
        misc_frame.grid(row=row['misc'], column=0, columnspan=3, sticky='ew')
        for var in (self.type, self.subtype, self.resumable):
            tk.Label(misc_frame, textvariable=var, bg=self.bg, fg=self.fg, anchor='w').pack(sid='left')

        # download folder -------------------------------------------------------------------------------------------
        label('Folder:', r=row['folder'], c=0)

        folder_entry = tk.Entry(self, textvariable=self.foldervar, bg=self.bg, fg=self.fg, highlightthickness=0,
                                  relief='flat')
        folder_entry.grid(row=row['folder'], column=1, sticky='we', pady=5)

        add_bidi_support(folder_entry, render_copy_paste=True, copy_paste_menu=True, ispath=True)

        # colors
        folder_entry.bind('<FocusIn>', lambda event: folder_entry.config(bg='white', fg='black'), add='+')
        folder_entry.bind('<FocusOut>', lambda event: folder_entry.config(bg=self.bg, fg=self.fg), add='+')

        folder_entry.bind('<FocusOut>', self.update_recent_folders, add='+')
        folder_entry.bind('<1>', self.update_recent_folders, add='+') 
        
        self.foldervar.trace_add('write', lambda *args: set_option(download_folder=self.folder))       

        browse_btn = Button(self, text='', image=imgs['folder_icon'], transparent=True)
        browse_btn.grid(row=row['folder'], column=2, padx=(8, 1), pady=0)

        self.recent_menu = atk.RightClickMenu(browse_btn, [], bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG,
                                              bind_left_click=True, bind_right_click=False)
        self.recent_menu.add_command(label='Browse ...', command=self.change_folder)
        
        self.update_recent_menu()

    def on_menu_selection(self, x):
        self.foldervar.set(x)
        self.update_recent_folders()

    def update_recent_menu(self):

        if self.recent_menu.index(tk.END) >= 1:
            self.recent_menu.delete(1, tk.END)

        if config.recent_folders:
            self.recent_menu.add_separator()
        
            for item in config.recent_folders:
                self.recent_menu.add_command(label=item, command=lambda x=item: self.on_menu_selection(x))

    def update_recent_folders(self, *args):
        value = self.foldervar.get().strip()
        try:
            if config.recent_folders[0] == value:
                return

            config.recent_folders.remove(value)
        except:
            pass

        # add current folder value at the beginning of the list and limit list size to 10 items
        if value:
            config.recent_folders = [value] + config.recent_folders[:9]

            self.update_recent_menu()

    def change_folder(self, *args):
        """select folder from system and update folder field"""
        folder = folderchooser()
        if folder:
            self.folder = folder
            set_option(download_folder=folder)
            self.update_recent_folders()

    def update(self, **kwargs):
        """update widget's variable
        example arguments: {'name': 'The search for new planets.mp4', 'folder': '/home/downloads',
        'type': 'video', 'subtype_list': ['dash', 'fragmented'], 'resumable': True, 'total_size': 100000}

        """
        title = kwargs.get('title', None)
        extension = kwargs.get('extension', None)
        size = kwargs.get('total_size', None)
        folder = kwargs.get('folder', None)
        type_ = kwargs.get('type', '')
        subtype_list = kwargs.get('subtype_list', '')
        resumable = kwargs.get('resumable', None)

        if title:
            rendered_title = render_text(title)
            self.title.set(rendered_title)

        if extension:
            self.extension.set(extension.replace('.', ''))  # remove '.'

        if folder:
            self.folder = folder
        if size is not None:
            self.size.set(f'{format_bytes(size) if size > 0 else "unknown"}')
        if type_:
            self.type.set(type_)
        if subtype_list:
            self.subtype.set(', '.join(subtype_list))

        self.resumable.set(f'- Resumable: {resumable}' if resumable is not None else '')

    def reset(self):
        self.title.set('')
        self.extension.set('')
        self.folder = config.download_folder
        self.size.set('...')
        self.type.set('')
        self.subtype.set('')
        self.resumable.set('')

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


class Segmentbar(tk.Canvas):
    def __init__(self, master):
        self.master = master
        master_bg = atk.get_widget_attribute(master, 'background')
        bg = atk.calc_contrast_color(master_bg, 30)
        self.bars = {}
        self.height = 10
        self.width = 100
        super().__init__(self.master, bg=bg, width=self.width, height=self.height, bd=0, highlightthickness=0)
        self.bind('<Configure>', self.redraw)

    def ubdate_bars(self, segments_progress):
        # segments_progress, e.g [total size, [(starting range, length, total file size), ...]]
        size = segments_progress[0]

        # scale values
        scale = size / self.width
        scaled_values = set()  # use set to filter repeated values
        for item in segments_progress[1]:
            start, length = item
            start = start // scale  # ignore fraction, e.g. 3.7 ====> 3.0
            length = length // scale + (1 if length % scale else 0)  # ceiling, eg: 3.2 ====> 4.0
            end = start + length

            start = int(start)
            end = int(end)

            scaled_values.add((start, end))

        for item in scaled_values:
            self.update_bar(item)

    def update_bar(self, info):
        """expecting a tuple or a list with the following structure
        (range-start, length, total-file-size)"""
        start, end = info

        tag_id = self.bars.get(start, None)
        if tag_id:
            x0, y0, x1, y1 = self.coords(tag_id)
            x1 = end
            self.coords(tag_id, x0, y0, x1, y1)
        else:
            tag_id = self.create_rectangle(start, 0, end, self.height, fill=PBAR_FG, width=0)
            self.bars[start] = tag_id

        self.update_idletasks()

    def redraw(self, *args):
        # in case of window get resized by user
        scale = self.winfo_width() / self.width
        self.width = self.winfo_width()
        for tag_id in self.bars.values():
            x0, y0, x1, y1 = self.coords(tag_id)
            x0 *= scale
            x1 *= scale
            self.coords(tag_id, x0, y0, x1, y1)

        self.update_idletasks()


class DItem(tk.Frame):
    """representation view of one download item in downloads tab"""

    def __init__(self, parent, uid, status, bg=None, fg=None, on_toggle_callback=None, mode='bulk',
                 playbtn_callback=None, delbtn_callback=None, onclick=None, ondoubleclick=None, bind_map=None,
                 rcm=None, rcm_callback=None):

        self.bg = bg or atk.get_widget_attribute(parent, 'background') or MAIN_BG
        self.fg = fg or MAIN_FG

        self.uid = uid
        self.parent = parent

        tk.Frame.__init__(self, parent, bg=self.bg, highlightthickness=0)

        self.name = ''
        self.ext = ''
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
        self.shutdown_pc = ''
        self.on_completion_command = ''
        self.on_toggle_callback = on_toggle_callback
        self.playbtn_callback = playbtn_callback
        self.delbtn_callback = delbtn_callback
        self.onclick = onclick
        self.ondoubleclick = ondoubleclick
        self.bind_map = bind_map
        self.rcm = rcm
        self.rcm_callback = rcm_callback
        self.selected = False
        self.progress = ''

        self.thumbnail_img = None

        self.columnconfigure(1, weight=1)
        self.blank_img = tk.PhotoImage()

        # thumbnail
        self.thumbnail_width = 160
        self.thumbnail_height = 80

        self.latest_update = {}

        self.mode = mode
        self.view(mode=self.mode)

        self.apply_bindings()

    def __repr__(self):
        return f'DItem({self.uid})'

    def apply_bindings(self):
        if callable(self.onclick):
            self.bind('<Button-1>', self.onclick)
        if callable(self.ondoubleclick):
            self.bind('<Double-Button-1>', self.ondoubleclick)

        self.bind('<Control-1>', lambda event: self.toggle())

        if self.rcm:
            atk.RightClickMenu(self, self.rcm,
                               callback=self.rcm_callback,
                               bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG)

        # bind mousewheel
        atk.scroll_with_mousewheel(self, target=self.parent, apply_to_children=True)

        if self.bind_map:
            for x, y in self.bind_map:
                self.bind(x, y)

    def select(self, flag=True):
        """select self"""
        if flag == self.selected:
            return
        else:
            self.selected = flag

        # change highlight color
        selection_bg = SEL_BG if flag else self.bg
        selection_fg = SEL_FG if flag else self.fg
        self.config(background=selection_bg)

        def change_colors(w, fg, bg, children=False, recursive=False, execludes=None):
            # execludes an iterable of execluded widgets' class name (.winfo_class())
            atk.configure_widget(w, background=bg, foreground=fg)

            if children:
                for child in w.winfo_children():
                    if execludes and child.winfo_class() not in execludes:
                        atk.configure_widget(child, background=selection_bg, foreground=selection_fg)

                    if recursive:
                        change_colors(child, fg, bg, children, recursive)

        change_colors(self, selection_fg, selection_bg)

        if self.mode == 'compact':
            for name in ('status_icon', 'play_button', 'name_lbl', 'info_lbl', 'delete_button', 'blinker',
                         'main_frame'):
                w = getattr(self, name, None)
                if w:
                    change_colors(w, selection_fg, selection_bg)

        elif self.mode == 'bulk':
            for name in ('btns_frame', 'bar_fr', 'blinker', 'status_icon', 'play_button', 'name_lbl', 'info_lbl',
                         'info_lbl2', 'delete_button', 'bar', 'bar_fr', 'main_frame'):
                w = getattr(self, name, None)
                if w:
                    change_colors(w, selection_fg, selection_bg,
                                  children=True if name in ('bar', 'bar_fr') else False,
                                  recursive=True if name == 'bar' else False,
                                  execludes=('TProgressbar',) if name == 'bar_fr' else None)

        if callable(self.on_toggle_callback):
            self.on_toggle_callback()

        self.update_idletasks()

        # set focus, required for any "keyboard binding" to work
        self.focus_set()

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

    def view_bulk(self):
        self.main_frame = tk.Frame(self, bg=self.bg, highlightthickness=0, highlightbackground=BTN_BG)
        self.main_frame.pack(expand=True, fill='x')
        self.main_frame.columnconfigure(1, weight=1)

        # thumbnail
        self.thumbnail_img = None
        # should assign an image property for tkinter to use pixels for width and height instead of characters
        self.thumbnail_label = tk.Label(self.main_frame, bg='white', image=self.blank_img, text='', font='any 20 bold', fg='black',
                                        justify='center', highlightbackground=THUMBNAIL_BD, highlightthickness=2,
                                        compound='center', width=self.thumbnail_width, height=self.thumbnail_height)
        self.thumbnail_label.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky='ns')

        # name text
        self.name_lbl = AutoWrappingLabel(self.main_frame, bg=self.bg, fg=self.fg, anchor='w')
        self.name_lbl.grid(row=0, column=1, sticky='ewns')

        self.info_lbl = tk.Label(self.main_frame, bg=self.bg, fg=self.fg, anchor='w', justify='left')
        self.info_lbl.grid(row=1, column=1, sticky='w')

        self.btns_frame = tk.Frame(self.main_frame, bg=self.bg)
        self.btns_frame.grid(row=2, column=1, sticky='w')

        # for non-completed items
        if self.status != config.Status.completed:
            #  progressbar
            self.bar = atk.RadialProgressbar(parent=self.main_frame, size=(80, 80), fg=PBAR_FG, text_fg=PBAR_TXT,
                                             font_size_ratio=0.16)
            self.bar.grid(row=0, column=2, rowspan=4, padx=10, pady=5)

            # blinker, it will blink with received data flow
            self.blinker = tk.Label(self.bar, bg=self.bg, text='', fg=self.fg, image=self.blank_img, width=12,
                                    height=12)
            self.blinker.on = False
            self.blinker.place(relx=0.5, rely=0.8, anchor="center")

            # processing bars
            self.bar_fr = tk.Frame(self.main_frame, bg=self.bg)
            s = ttk.Style()
            self.bottom_bars_style = 'bottombars.Horizontal.TProgressbar'
            s.configure(self.bottom_bars_style, thickness=1, background=PBAR_FG,
                        troughcolor=atk.calc_contrast_color(self.bg, 30),
                        troughrelief=tk.FLAT, pbarrelief=tk.FLAT)

            self.vbar = tk.IntVar()
            self.abar = tk.IntVar()
            self.mbar = tk.IntVar()

            for lbl, var in zip(('Video: ', '    Audio: ', '    Output File: '), (self.vbar, self.abar, self.mbar)):
                tk.Label(self.bar_fr, text=lbl, bg=self.bg, fg=self.fg).pack(side='left')
                ttk.Progressbar(self.bar_fr, orient=tk.HORIZONTAL, style=self.bottom_bars_style, length=20,
                                variable=var).pack(side='left', expand=True, fill='x')

            self.bar_fr.grid(row=3, column=1, columnspan=1, sticky='ew', padx=0)
            self.bar_fr.grid_remove()

            # segments progressbar
            self.segment_bar = Segmentbar(self.main_frame)
            self.segment_bar.grid(row=4, column=0, columnspan=3, sticky='ew', padx=5, pady=(0, 5))

            # create buttons
            self.play_button = Button(self.btns_frame, image=imgs['play_icon'], command=self.playbtn_callback)
            self.play_button.pack(side='left', padx=(0, 10))

        self.delete_button = Button(self.btns_frame, image=imgs['delete_icon'], command=self.delbtn_callback)
        self.delete_button.pack(side='left', padx=(0, 10))

        # make another info label
        self.info_lbl2 = tk.Label(self.btns_frame, bg=self.bg, fg=self.fg)
        self.info_lbl2.pack(side='left', padx=(0, 10), pady=5)

        # status icon
        self.status_icon = tk.Label(self.btns_frame, bg=self.bg, text='', fg=self.fg, image=self.blank_img, width=12,
                                    height=12, compound='center')
        self.status_icon.pack(side='left', padx=5, pady=5)

        # self.bind('<Double-Button-1>', self.ondoubleclick, exclude=[self.play_button])

    def view_compact(self):
        self.main_frame = tk.Frame(self, bg=self.bg, highlightthickness=0, highlightbackground=BTN_BG)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.columnconfigure(3, weight=1)

        # status icon
        self.status_icon = tk.Label(self.main_frame, bg=self.bg, text='', fg=self.fg, image=self.blank_img, width=12,
                                    height=12, compound='center')
        self.status_icon.grid(row=0, column=0, padx=5, sticky='w')
        # blinker, it will blink with received data flow
        self.blinker = tk.Label(self.main_frame, bg=self.bg, text='', fg=self.fg, image=self.blank_img, width=12,
                                height=12)
        self.blinker.on = False
        self.blinker.grid(row=0, column=1, padx=5, sticky='w')

        self.play_button = Button(self.main_frame, image=imgs['play_icon'], command=self.playbtn_callback)
        self.play_button.grid(row=0, column=2, padx=5, sticky='w')

        # self.name_lbl = tk.Label(self.fr, bg=self.bg, fg=self.fg, anchor='w')
        self.name_lbl = AutofitLabel(self.main_frame, bg=self.bg, fg=self.fg, anchor='w')
        self.name_lbl.grid(row=0, column=3, padx=5, sticky='ew')

        self.info_lbl = tk.Label(self.main_frame, bg=self.bg, fg=self.fg, anchor='w', justify='left')
        self.info_lbl.grid(row=0, column=4, padx=5, sticky='w')

        s = ttk.Style()
        bar_style = 'bar_style.Horizontal.TProgressbar'
        s.configure(bar_style, thickness=1, background=PBAR_FG, troughcolor=PBAR_BG, troughrelief=tk.FLAT,
                    pbarrelief=tk.FLAT)

        self.bar = tk.IntVar(0)
        ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, style=bar_style, length=40,
                        variable=self.bar).grid(row=0, column=5, padx=5, sticky='w')

        self.delete_button = Button(self.main_frame, image=imgs['delete_icon'], command=self.delbtn_callback)
        self.delete_button.grid(row=0, column=6, padx=5, sticky='w')

    def view(self, mode='bulk'):
        """
        pack/grid widgets
        Args:
            mode(str): bulk, or compact
        """

        if mode in 'bulk':
            self.view_bulk()
        else:
            self.view_compact()

    def switch_view(self, mode):
        if self.mode != mode:
            self.mode = mode
            self.main_frame.destroy()
            self.view(mode)
            self.apply_bindings()
            self.update(**self.latest_update)

    def dynamic_view(self):
        """change view based on status"""

        # status icon
        if self.status == config.Status.completed:
            status_img = imgs['done_icon']
        elif self.status in (config.Status.pending, config.Status.scheduled):
            status_img = imgs['hourglass_icon']
        else:
            status_img = self.blank_img

        try:
            self.status_icon.config(image=status_img)
        except:
            pass

        # toggle play/pause icons
        try:
            if self.status in config.Status.active_states:
                img = imgs['pause_icon']
            else:
                img = imgs['play_icon']
            self.play_button.config(image=img)
            self.play_button.bind('<Enter>', lambda e: self.play_button.config(image=img.zoomed))
            self.play_button.bind('<Leave>', lambda e: self.play_button.config(image=img))
        except:
            pass

        if self.mode == 'compact':
            if self.status in config.Status.active_states:
                self.status_icon.grid_remove()
                self.blinker.grid()

            else:
                self.blinker.grid_remove()   
                self.status_icon.grid()

            if self.status == config.Status.completed:
                self.play_button.grid_remove()

        elif self.mode == 'bulk':
            if self.status == config.Status.completed:
                self.play_button.pack_forget()
                self.bar.grid_remove()
                self.bar_fr.grid_remove()
                self.segment_bar.grid_remove()

    def dynamic_show_hide(self):
        """show / hide item based on global view filter"""
        if config.view_filter.lower() == 'selected' and self.selected:
            self.show()
        elif self.status in config.view_filter_map.get(config.view_filter, ()):
            self.show()
        else:
            self.hide()
            self.select(False)

    def show(self):
        """grid self"""
        side = 'bottom' if config.ditem_show_top else 'top'
        self.pack(side=side, expand=True, fill='x', pady=0)

    def hide(self):
        """grid self"""
        self.pack_forget()

    def display_info(self):
        """display info in tkinter widgets"""
        if self.mode == 'compact':
            size = f'{self.total_size}' if self.status == config.Status.completed else f'{self.size}/{self.total_size}'
            self.info_lbl.config(text=f'{size} {self.speed} {self.eta}   {self.errors} {self.progress}')

        elif self.mode == 'bulk':
            self.info_lbl.config(text=f'{self.size}/{self.total_size} {self.speed} {self.eta}   {self.errors} '
                                      f'{self.shutdown_pc} {self.on_completion_command}')

            self.info_lbl2.config(text=f'{self.media_subtype} {self.media_type} {self.live_connections} '
                                       f'{self.completed_parts} - {self.status} {self.sched}')

        # a led like blinking button, to react with data flow
        self.toggle_blinker()

    def mark_as_failed(self, state=True):
        f = tkfont.Font(self.name_lbl, **config.gui_font)
        self.name_lbl.config(font=f)
        f.configure(overstrike=state)

        if state:
            text = 'Failed'
            stext = 'X'
            fg = 'red'
        else:
            text = self.ext if not self.thumbnail_img else ''
            stext = ''
            fg = 'black'

        if self.mode == 'compact':
            self.status_icon.config(text=stext, fg=fg)

        elif self.mode == 'bulk':
            self.thumbnail_label.config(text=text, fg=fg)

    def update(self, name=None, downloaded=None, progress=None, total_size=None, eta=None, speed=None,
               thumbnail=None, status=None, extension=None, sched=None, type=None, subtype_list=None,
               remaining_parts=None, live_connections=None, total_parts=None, shutdown_pc=None,
               on_completion_command=None, video_progress=None, audio_progress=None, merge_progress=None,
               segments_progress=None, _total_size=None, **kwargs):
        """update widgets value"""
        # print(locals())
        self.latest_update.update({k: v for k, v in locals().items() if v not in (None, self)})
        if name:
            self.name = name
            title, ext = os.path.splitext(name)
            try:
                self.name_lbl.config(text=render_text(title) + ext)
            except:
                pass

        if downloaded is not None:
            self.size = format_bytes(downloaded, percision=1, sep='')

        if _total_size is not None:
            self.total_size = format_bytes(_total_size, percision=1, sep='')

        if speed is not None:
            self.speed = f'- {format_bytes(speed, percision=1, sep="")}/s' if speed > 0 else ''

        if eta is not None:
            self.eta = f'- {format_seconds(eta, fullunit=True, percision=0, sep="")}(s)' if eta else ''

        if progress is not None:
            try:
                self.progress = f'{progress}%'
                self.bar.set(progress)
            except:
                pass

        if extension:
            ext = extension.replace('.', '').upper()
            self.ext = ext
            try:
                # negative font size will force character size in pixels
                f = f'any {int(- self.thumbnail_width * 0.8 // len(ext))} bold'
                self.thumbnail_label.config(text=ext, font=f)
            except:
                pass

        if thumbnail:
            try:
                self.thumbnail_img = atk.create_image(b64=thumbnail, size=self.thumbnail_width)
                self.thumbnail_label.config(image=self.thumbnail_img, text='')
            except:
                pass

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

            self.mark_as_failed(status == config.Status.error)

            try:
                self.dynamic_view()
            except:
                pass

            self.dynamic_show_hide()

        if sched:
            if status == config.Status.scheduled:
                self.sched = f'@{sched}'

        if type:
            self.media_type = type
            if type == 'video' and self.status != config.Status.completed:
                try:
                    self.bar_fr.grid()
                except:
                    pass

        if isinstance(subtype_list, list):
            self.media_subtype = ' '.join(subtype_list)

        if on_completion_command is not None:
            self.on_completion_command = '[-CMD-]' if on_completion_command else ''
        if shutdown_pc is not None:
            self.shutdown_pc = '[-Shutdown Pc when finish-]' if shutdown_pc else ''

        # bottom progress bars
        if video_progress:
            try:
                self.vbar.set(video_progress)
            except:
                pass

        if audio_progress:
            try:
                self.abar.set(audio_progress)
            except:
                pass

        if merge_progress:
            try:
                self.mbar.set(merge_progress)
            except:
                pass

        if segments_progress:
            try:
                self.segment_bar.ubdate_bars(segments_progress)
            except:
                pass

        self.display_info()

    def toggle_blinker(self):
        """an activity blinker "like a blinking led" """
        status = self.status
        try:
            if not self.blinker.on and status in config.Status.active_states:
                # on blinker
                self.blinker.config(image=imgs['blinker_icon'])
                self.blinker.on = True

            else:
                # off blinker
                self.blinker.config(image=self.blank_img)
                self.blinker.on = False
        except:
            pass


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
        self.controller = main.controller
        self.parent = main.root
        self.playlist = playlist or []
        self.playlist_count = len(playlist)
        self.items = []
        self.max_videos_per_page = 100
        self.total_pages = (self.playlist_count // self.max_videos_per_page) + (1 if self.playlist_count % self.max_videos_per_page else 0)
        self._current_page = 0
        self.items_per_page = min(self.playlist_count, self.max_videos_per_page)

        self.selected_videos = {}  # video_idx vs stream_idx
        self.dash_audio = {}  # video_idx vs audio_idx
        self.stream_menus = {}  # video_idx vs stream menu
        self.subtitles = {}
        self.selected_subs = {}

        self.selected_videos_num = tk.IntVar()

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

    @property
    def curr_page(self):
        return self._current_page

    @curr_page.setter
    def curr_page(self, newvalue):
        # validate, pages start from zero, e.g. if total pages = 10, start=0, end=9
        if 0 <= newvalue < self.total_pages:
            self._current_page = newvalue

            # update items
            self.update_items()

            # update displayed page num
            self.page_combo.set(self.curr_page + 1)

            # reset "select all" checkbutton
            self.select_all_var.set(False)

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)
        top_frame = tk.Frame(main_frame, bg=MAIN_BG)
        videos_frame = atk.ScrollableFrame(main_frame, bg=MAIN_BG, hscroll=False)
        videos_frame.columnconfigure(0, weight=1)
        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)

        f1 = tk.Frame(top_frame, bg=MAIN_BG)
        f1.pack(fill='x', expand=True, anchor='w')
        tk.Label(f1, text=f'Total videos: {self.playlist_count}, Selected:', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)
        tk.Label(f1, textvariable=self.selected_videos_num, bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=2, pady=5)

        Button(f1, text='Next', command=self.next_page).pack(side='right', padx=5, pady=5)
        Button(f1, text='Prev', command=self.prev_page).pack(side='right', padx=5, pady=5)

        tk.Label(f1, text=f'of {self.total_pages}', bg=MAIN_BG, fg=MAIN_FG).pack(side='right', padx=5, pady=5)
        self.page_combo = Combobox(f1, list(range(1, self.total_pages + 1)), selection=1, width=3)
        self.page_combo.callback = lambda: setattr(self, 'curr_page', int(self.page_combo.selection) - 1)
        self.page_combo.pack(side='right', padx=5, pady=5)
        tk.Label(f1, text=f'Page', bg=MAIN_BG, fg=MAIN_FG).pack(side='right', padx=5, pady=5)


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
        tk.Label(f3, text='Quality:', bg=MAIN_BG, fg=MAIN_FG).pack(side='right', padx=(20, 5), pady=5)

        # create items widgets
        for num, name in zip(range(self.items_per_page), self.playlist):
            item = self.create_item(videos_frame, num, name)

            self.items.append(item)
            item.grid(padx=5, pady=5, sticky='ew')

            atk.scroll_with_mousewheel(item, target=videos_frame, apply_to_children=True)

        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)
        Button(bottom_frame, text='Download Later',
               command=lambda: self.download(download_later=True)).pack(side='right', padx=5)
        Button(bottom_frame, text='Download', command=self.download).pack(side='right', padx=5)

        self.total_size = tk.StringVar()
        tk.Label(bottom_frame, textvariable=self.total_size, bg=MAIN_BG, fg=MAIN_FG).pack(side='left', padx=5, pady=5)

        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))

        bottom_frame.pack(side='bottom', fill='x', pady=5)
        ttk.Separator(main_frame).pack(side='bottom', fill='x')
        top_frame.pack(side='top', fill='x')
        ttk.Separator(main_frame).pack(side='top', fill='x')
        videos_frame.pack(side='bottom', expand=True, fill='both', pady=10)

    def create_item(self, parent, num, name):
        """Create an item,
        every item has video name label, stream quality combobox, and a progressbar
        """
        item = tk.Frame(parent, bg=MAIN_BG)
        item.columnconfigure(0, weight=1)
        item.columnconfigure(1, weight=1)
        item.num = num  # index in self.items
        item.video_idx = num  # video index will change with page change
        item.selected = tk.BooleanVar()
        item.stream_menu_var = tk.StringVar()
        item.stream_menu_var.trace_add('write', lambda *args, idx=item.num: self.stream_select_callback(idx))

        item.selected.trace_add('write', lambda *args, idx=item.num: self.video_select_callback(idx))

        # checkbutton
        item.checkbutton = Checkbutton(item, text=name, variable=item.selected, width=60)

        # progressbar
        custom_style = 'custom_playlist_bar.Horizontal.TProgressbar'
        self.s.configure(custom_style, thickness=3, background=PBAR_FG, troughcolor=SF_BG)
        item.bar = ttk.Progressbar(item, orient='horizontal', mode='indeterminate', style=custom_style)

        # stream menu
        item.combobox = Combobox(item, [], width=40, textvariable=item.stream_menu_var)
        item.combobox.grid(row=0, column=1, padx=5, sticky='ew')
        item.combobox.grid_remove()

        def audio_btn_callback():
            audio_idx = self.main.select_dash_audio(video_idx=item.video_idx, active=False)
            self.dash_audio[item.video_idx] = audio_idx

        item.audio_btn = Button(item, image=imgs['audio_icon'], command=audio_btn_callback, tooltip='audio quality')
        item.audio_btn.grid(row=0, column=2, padx=5)
        item.audio_btn.grid_remove()

        item.checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        def startpb():
            item.bar.grid(row=1, column=1, padx=5, sticky='ew')
            item.bar.start(10)

        def stoppb():
            item.bar.grid_remove()
            item.bar.stop()

        item.start_progressbar = startpb
        item.stop_progressbar = stoppb

        return item

    def select_audio(self, video_idx):
        """select dash audio"""
        try:
            audio_idx = int(self.dash_audio[video_idx])
            self.controller.select_audio(video_idx=video_idx, audio_idx=audio_idx)
        except :
            pass

    def update_items(self):
        # update widgets
        start_idx = self.curr_page * self.items_per_page

        # hide all items
        for item in self.items:
            item.grid_remove()

        for item, name in zip(self.items, self.playlist[start_idx:]):
            item.video_idx = start_idx + item.num
            item.checkbutton['text'] = name

            stream_menu = self.stream_menus.get(item.video_idx, [])
            stream_idx = self.selected_videos.get(item.video_idx, 1)
            item.combobox.config(values=stream_menu)

            if stream_menu:
                item.combobox.current(stream_idx)
            else:
                item.combobox.set('')

            selected = item.video_idx in self.selected_videos
            item.selected.set(selected)

            if selected:
                item.combobox.grid()
                item.audio_btn.grid()
            else:
                item.combobox.grid_remove()
                item.audio_btn.grid_remove()

            item.bar.stop()
            item.grid()

    def next_page(self):
        self.curr_page += 1

    def prev_page(self):
        self.curr_page -= 1

    @threaded
    def toggle_all(self):
        """select / unselct all video items in playlist"""

        for item in self.items:
            item.selected.set(self.select_all_var.get())

            # quit if playlist window closed
            if self.main.pl_window is None:
                break

            # add some time delay to process a video item and load stream menu before process next video
            if self.select_all_var.get():
                menu = self.stream_menus.get(item.num, [])
                # if video process failed, stream menu will contain only the headers (5 items) and no streams
                # e.g. ['Video streams:', '', 'Audio streams:', '', 'Extra streams:']
                if len(menu) <= 5:
                    time.sleep(1)

    def close(self):
        self.destroy()
        self.main.pl_window = None

    def download(self, **kwargs):
        selected_videos = sorted(self.selected_videos.keys())
        self.controller.download_playlist(selected_videos, subtitles=self.selected_subs, **kwargs)
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

        # get item
        match = [item for item in self.items if item.video_idx == video_idx]
        if not match:
            return

        item = match[0]
        item.stop_progressbar()

        combobox = item.combobox
        combobox.config(values=stream_menu)
        combobox.current(stream_idx)

        self.stream_menus[video_idx] = stream_menu

        # get subtitles
        sub = self.controller.get_subtitles(video_idx=video_idx)
        if sub:
            self.update_subtitles(sub)

        # update master stream menu
        self.update_master_menu(stream_menu)

        # follow master menu selection
        self.follow_master_selection(item, stream_menu)

    # region master stream menu
    def master_combo_callback(self):
        self.master_selection = self.master_combo.selection

        # update selected items only
        for item in [x for x in self.items if x.selected.get()]:
            self.follow_master_selection(item)

    def follow_master_selection(self, item, stream_menu=None):
        """update all selected stream menus to match master menu selection"""
        stream_menu = stream_menu or self.stream_menus.get(item.video_idx, None)

        if not stream_menu:
            return

        if self.master_selection:
            try:
                # update widget combo boxes
                for s_idx, s_name in enumerate(stream_menu):
                    if s_name.startswith(self.master_selection):
                        item.combobox.current(s_idx)
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

        we should build master menu to contain video and audio streams only and every stream will have extension and
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
            self.master_selection = self.master_combo.selection
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
            self.main.msgbox('No Subtitles available for selected videos!')

        self.update_subs_label()

    def update_subs_label(self):
        self.subtitles_label['text'] = f'Total subtitles: {len(self.subtitles)}, Selected: {len(self.selected_subs)}'
    # endregion

    @ignore_errors
    def video_select_callback(self, item_num):
        """ask controller to send stream menu when selecting a video"""
        item = self.items[item_num]
        stream_idx = item.combobox.current()

        if item.selected.get():
            item.combobox.grid()
            item.audio_btn.grid()
            item.start_progressbar()
            self.controller.get_stream_menu(video_idx=item.video_idx)
            self.selected_videos[item.video_idx] = stream_idx
        else:
            item.combobox.grid_remove()
            item.audio_btn.grid_remove()
            item.stop_progressbar()
            if item.video_idx in self.selected_videos:
                self.selected_videos.pop(item.video_idx)

        self.selected_videos_num.set(len(self.selected_videos))

        self.update_subs_label()
        self.update_total_size()

    def stream_select_callback(self, item_num):
        item = self.items[item_num]

        stream_idx = item.combobox.current()
        if item.video_idx in self.selected_videos:
            self.selected_videos[item.video_idx] = stream_idx
        self.controller.select_stream(stream_idx, video_idx=item.video_idx)

        self.select_audio(item.video_idx)
        self.update_total_size()

    def update_total_size(self):
        def get_size(video_idx):
            size = self.controller.get_property('total_size', video_idx=video_idx)
            try:
                size = int(size)
            except:
                size = 0
            return size

        total_size = sum([get_size(video_idx) for video_idx in self.selected_videos])
        self.total_size.set(f'Total Size ≈ {format_bytes(total_size)}')


class SubtitleWindow(tk.Toplevel):
    """Download subtitles window"""

    def __init__(self, main, subtitles, enable_download_button=True, enable_select_button=False, block=False,
                 selected_subs=None):
        """initialize

        Args:
            main: main window class
            subtitles (dict): subtitles, key=language, value=list of extensions, e.g. {en: ['srt', 'vtt'], ar: [...]}
            enable_download_button (bool): show download button
            enable_select_button (bool): show select button
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
            self.selected_idx = int(idx)
        self.close()


class BatchWindow(tk.Toplevel):
    """window for batch downloading multiple files"""

    def __init__(self, main):
        """initialize

        Args:
            main: main window ref
        """
        self.main = main
        self.controller = main.controller
        self.parent = main.root

        # initialize super
        tk.Toplevel.__init__(self, self.parent)

        # bind window close
        self.protocol("WM_DELETE_WINDOW", self.close)

        width = int(self.parent.winfo_width() * 0.5)
        height = int(self.parent.winfo_height() * 0.5)
        center_window(self, width=width, height=height, reference=self.parent)

        self.title('Batch Download')
        self.config(bg=SF_BG)

        self.create_widgets()

    def load_batch_file(self):
        fp = filechooser()
        try:
            with open(fp) as f:
                text = f.read()
                urls = parse_urls(text)
                for url in urls:
                    self.add_url(url)
        except:
            pass

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=MAIN_BG)
        f = tk.Frame(main_frame, bg=MAIN_BG)
        tk.Label(f, text='Enter Links below or import urls from a file', bg=MAIN_BG,
                 fg=MAIN_FG).pack(side='left', anchor='w', padx=5, pady=5)
        Button(f, image=imgs['folder_icon'], command=self.load_batch_file,
               tooltip='load batch file').pack(side='left', padx=5)
        f.pack(anchor='w')

        self.urls_text = atk.ScrolledText(main_frame, height=4, width=10, sbar_bg=SBAR_BG, sbar_fg=SBAR_FG, bg=MAIN_BG,
                                          fg=MAIN_FG, insertbackground=MAIN_FG)
        self.urls_text.pack(expand=True, fill='both')

        atk.RightClickMenu(self.urls_text, ['Cut', 'Copy', 'Paste'],
                           callback=lambda option: self.urls_text.event_generate(f'<<{option}>>'),
                           bg=RCM_BG, fg=RCM_FG, afg=RCM_AFG, abg=RCM_ABG)
        main_frame.pack(expand=True, fill='both', padx=(10, 0), pady=(10, 0))

        options_frame = tk.Frame(main_frame, bg=MAIN_BG)
        options_frame.pack(anchor='w', pady=5, fill='x')
        tk.Label(options_frame, text='video quality:', bg=MAIN_BG, fg=MAIN_FG).pack(side='left', anchor='w', padx=5, pady=5)
        self.video_quality = Combobox(options_frame, values=['Best', '1080p', '720p', '480p', '360p', 'Lowest'],
                                      selection='Best', width=8)
        self.video_quality.pack(side='left')
        self.prefer_mp4 = tk.BooleanVar(value=False)

        tk.Checkbutton(options_frame, text='prefer mp4 format', bg=MAIN_BG, fg=MAIN_FG, anchor='w', relief='flat',
                       activebackground=MAIN_BG, highlightthickness=0, activeforeground=MAIN_FG, selectcolor=MAIN_BG,
                       variable=self.prefer_mp4, onvalue=True, offvalue=False).pack(side='right', anchor='e', padx=10)
        ttk.Separator(main_frame).pack(fill='x')

        bottom_frame = tk.Frame(main_frame, bg=MAIN_BG)
        Button(bottom_frame, text='Cancel', command=self.close).pack(side='right', padx=5)
        Button(bottom_frame, text='Download Later', command=lambda: self.download(download_later=True)).pack(side='right', padx=5)
        Button(bottom_frame, text='Download', command=self.download).pack(side='right', padx=5)
        bottom_frame.pack(side='bottom', fill='x', pady=5)

        self.set = self.urls_text.set
        self.append = self.urls_text.append
        self.clear = self.urls_text.clear

    def close(self):
        self.destroy()
        self.main.batch_window = None

    def download(self, download_later=False):
        urls = parse_urls(self.get())
        video_quality = self.video_quality.selection

        self.controller.batch_download(urls, video_quality=video_quality, download_later=download_later,
                                       folder=config.download_folder, prefer_mp4=self.prefer_mp4.get())
        self.close()

    def add_url(self, url):
        self.append('\n' + url)

    def get(self):
        return self.urls_text.get("1.0", tk.END)


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


def rcm_marker(rcm, default=None):
    """decorator for rcm callback to let RightClick Menu mark its last selection"""
    blank = tk.PhotoImage()
    callback = rcm.callback

    def inner(option, markonly=False):
        last_idx = rcm.index(tk.END)
        compound = 'right'
        for i in range(0, last_idx + 1):
            if rcm.entrycget(i, 'label').strip() == option:
                rcm.entryconfig(i, image=imgs['done_icon'], compound=compound)
            else:
                rcm.entryconfig(i, image=blank, compound=compound)
        if not markonly:
            callback(option)

    if default:
        inner(default, markonly=True)

    rcm.callback = inner


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
        self.batch_window = None  # batch download window

        # queues for executing methods on gui from a thread
        self.command_q = Queue()
        self.response_q = Queue()
        self.counter = 0  # a counter to give a unique number
        self.update_view_q = Queue()

        # ibus workaround
        self.should_restart_ibus = False

        if config.ibus_workaround:
            # don't run it in a separate thread otherwise tkinter might start making widgets in
            # same time thread start killing ibus-x11, which result in 
            # X Error of failed request:  BadWindow (invalid Window parameter)
            self.ibus_workaround()

        # root ----------------------------------------------------------------------------------------------------
        self.root = tk.Tk()

        self.initialize_font()

        # assign window size
        try:
            self.width, self.height = config.window_size
        except:
            self.width, self.height = config.DEFAULT_WINDOW_SIZE

        center_window(self.root, width=self.width, height=self.height)

        if config.window_maximized or config.force_window_maximize:
            if config.operating_system in ('Windows', 'Darwin'):
                self.root.wm_state('zoomed')
            else:
                self.root.attributes('-zoomed', True)

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

    def ibus_workaround(self):
        # issue 256: https://github.com/firedm/FireDM/issues/256
        # because of ibus bug, FireDM take longer time to load with every run as time goes on, same as 
        # any tkinter application.
        # workaround is to kill ibus-x11 then restart ibus again after FireDM finish loading
        # reported bug at https://github.com/ibus/ibus/issues/2324
        # however this workaround makes FireDM loads faster, ibus will still affect gui performance when 
        # it gets restarted again.
        # hope they fix this bug as soon as possible
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE, universal_newlines=True)
        output, error = p.communicate()
        if error: return

        for line in output.splitlines():
            if 'ibus-x11' in line:
                pid = int(line.split(None, 1)[0])
                try:
                    os.kill(pid, signal.SIGKILL)
                    log('stopped ibus-x11 temporarily to fix issue at https://github.com/firedm/FireDM/issues/256 and https://github.com/ibus/ibus/issues/2324')
                    self.should_restart_ibus = True
                    time.sleep(0.1)  # a small delay to fix gui not starting sometimes.
                except Exception as e:
                    print(e)

    def restart_ibus(self):
        # will use default ibus parameter as in Pop!_OS 20.10 - GNOME 3.38.3: ibus-daemon --panel disable --xim
        # also will add -d to run as a daemon, and -r to replace all and start ibus-x11 again
        cmd = ['ibus-daemon', '--panel', 'disable', '--xim', '-d', '-r']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        output, error = p.communicate()
        if error:
            log('output, error:', output, error)
        else:
            log(f'restarted ibus-daemon successfully, issue 256, (cmd: {" ".join(cmd)})')

    # region themes
    def share_theme(self, theme_name=None):
        theme_name = theme_name or self.themes_menu.get()

        theme = all_themes.get(theme_name)

        if theme:
            stripped_theme = strip_theme(theme)
            data = {theme_name: stripped_theme}
            data = json.dumps(data, indent=4)
            self.copy(data)
            self.popup(f'Theme "{theme_name}" copied to clipboard')

    def add_theme(self, theme_name, theme_info):
        """add theme to all_themes dict
        args:
            theme_name(str): theme name, e.g. "Green-Brown"
            theme_info(dict): theme info, e.g.
                {
                    "MAIN_BG": "#3A6351",
                    "SF_BG": "#F2EDD7",
                    "SF_BTN_BG": "#A0937D",
                    "PBAR_FG": "#5F939A",
                    "BTN_ABG": "#446d5b",
                }
        """
        # rename theme if already exist
        if theme_name in all_themes:
            theme_name = auto_rename(theme_name, all_themes.keys())

        # remove invalid colors
        theme_info = {k: v for k, v in theme_info.items() if self.is_color(v)}

        # add missing keys
        calculate_missing_theme_keys(theme_info)

        # add theme
        all_themes[theme_name] = theme_info

    @ignore_errors
    def manual_theme_entry(self):
        """show popup to get themes dict from user"""

        def show_window():
            top = tk.Toplevel(master=self.root, bg=SF_BG)
            top.title('Manual theme Entry')
            width = int(self.root.winfo_width() * 0.9)
            height = int(self.root.winfo_height() * 0.9)

            center_window(top, width=width, height=height, reference=self.root, set_geometry_wh=False)
            txt = """Add themes manually, example:
{
    "my theme": {
        "MAIN_BG": "grey",
        "SF_BG": "#000300",
        "SF_BTN_BG": "#d9dc4b",
        "THUMBNAIL_FG": "#d9dc4b",
        "PBAR_FG": "#d9dc4b",
        "THUMBNAIL_BD": "#d9dc4b"
    },
    "another theme": {
        "MAIN_BG": "blue",
        "SF_BG": "red",
        "SF_BTN_BG": "#d9dc4b",
        "THUMBNAIL_FG": "#d9dc4b",
        "PBAR_FG": "#d9dc4b",
        "THUMBNAIL_BD": "#d9dc4b"
    }
}"""
            fr = tk.Frame(top, bg=MAIN_BG)
            fr.pack(fill='x', padx=(10, 0), pady=5)
            tk.Label(fr, text='Add themes manually:', bg=MAIN_BG, fg=MAIN_FG, justify='left').pack(padx=5, side='left')
            Button(fr, text='Tip!', command=lambda: self.popup(txt, title='help')).pack(side='left', padx=5, pady=5)

            st = atk.ScrolledText(top, bg=MAIN_BG, fg=MAIN_FG, bd=1, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG,
                                  insertbackground=MAIN_FG, highlightbackground=SF_BG, highlightcolor=SF_BG, padx=5,
                                  pady=5, hscroll=False, height=10)
            st.pack(padx=(10, 0), pady=(10, 0), fill='both', expand=True)
            st.focus_set()
            x = ''

            def callback():
                nonlocal x
                x = st.get("1.0", tk.END)
                top.destroy()

            fr2 = tk.Frame(top, bg=MAIN_BG)
            fr2.pack(fill='x', padx=(10, 0))
            Button(fr2, text='Cancel', command=top.destroy).pack(side='right', padx=5, pady=5)
            Button(fr2, text='Ok', command=callback).pack(side='right', padx=5, pady=5)
            top.wait_window()
            return x

        user_input = json.loads(show_window())
        for theme_name, theme_info in user_input.items():
            self.add_theme(theme_name, theme_info)

        self.update_theme_menu()
        self.themes_menu.current(tk.END)

    def update_theme_menu(self):
        sel = self.themes_menu.get()
        values = list(all_themes.keys())
        values = values
        self.themes_menu.config(values=values)
        idx = values.index(sel) if sel in values else 0
        self.themes_menu.current(idx)

    def save_user_themes(self):
        try:
            file = os.path.join(config.sett_folder, 'user_themes.cfg')
            user_themes = {k: v for k, v in all_themes.items() if k not in builtin_themes}
            stripped_user_themes = {k: strip_theme(v) for k, v in user_themes.items()}
            save_json(file, stripped_user_themes)
        except Exception as e:
            log('save_themes() > error', e)

    def load_user_themes(self):
        try:
            fp = os.path.join(config.sett_folder, 'user_themes.cfg')
            themes = load_json(fp)

            if themes:
                for name, theme in themes.items():
                    self.add_theme(name, theme)

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
        ThemeEditor(self, f'usertheme_{len(all_themes) + 1}')

    def del_theme(self):
        sel = self.themes_menu.get()
        if sel not in builtin_themes.keys():
            all_themes.pop(sel)
            self.update_theme_menu()
        else:
            self.popup('can\'t delete builtin theme', 'only user/custom themes can be deleted',
                       title='Not allowed')

    def apply_theme(self, theme_name=None):
        """change global color variables

           Args:
               theme_name (str): theme name
        """

        theme_name = theme_name or self.themes_menu.get() or config.DEFAULT_THEME
        theme = all_themes.get(theme_name) or all_themes.get(config.DEFAULT_THEME)

        if theme:
            config.current_theme = theme_name

            # clean invalid color values
            theme = {k: v for k, v in theme.items() if self.is_color(v)}

            # add missing keys
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
        self.gui_timer = time.time()

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
        tk.Label(self.side_frame, textvariable=self.total_speed, bg=SF_BG,
                 fg=SF_FG).grid(sticky='s', pady=10)

        ff = ExpandCollapse(self.main_frame, self.side_frame, MAIN_BG, MAIN_FG)
        ff.grid(row=1, column=1, sticky='ewns')

        self.assign_font_for(self.root)

        # set scrollbar width
        self.set_scrollbar_width(config.scrollbar_width)

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

        self.url_entry = tk.Entry(home_tab, bg=MAIN_BG, highlightcolor=ENTRY_BD_COLOR, insertbackground=MAIN_FG,
                                  highlightbackground=ENTRY_BD_COLOR, fg=MAIN_FG, textvariable=self.url_var)
        self.url_entry.grid(row=0, column=0, columnspan=4, padx=5, pady=(45, 5), sticky='ew', ipady=8, ipadx=5)

        atk.RightClickMenu(self.url_entry, ['Cut', 'Copy', 'Paste'],
                           callback=lambda selected: self.url_entry.event_generate(f'<<{selected}>>'),
                           bg=RCM_BG, fg=RCM_FG, afg=RCM_AFG, abg=RCM_ABG)

        # retry button -------------------------------------------------------------------------------------------------
        self.retry_btn = Button(home_tab, image=imgs['refresh_icon'], command=lambda: self.refresh_url(self.url), tooltip='Retry')
        self.retry_btn.grid(row=0, column=4, padx=(0, 5), pady=(40, 5))

        # thumbnail ----------------------------------------------------------------------------------------------------
        self.thumbnail = Thumbnail(parent=home_tab)
        self.thumbnail.grid(row=1, column=3, rowspan=1, padx=5, pady=10, sticky='e')

        # video menus --------------------------------------------------------------------------------------------------
        self.pl_menu = MediaListBox(home_tab, bg, 'Playlist:')
        self.pl_menu.grid(row=1, column=0, rowspan=1, pady=10, padx=5, sticky='nsew')
        Button(self.pl_menu, image=imgs['playlist_icon'], command=self.show_pl_window, tooltip='Download Playlist').place(relx=1, rely=0, x=-40, y=5)
        self.stream_menu = MediaListBox(home_tab, bg, 'Streams:')
        self.stream_menu.grid(row=1, column=1, rowspan=1, padx=15, pady=10, sticky='nsew')
        Button(self.stream_menu, image=imgs['audio_icon'], command=self.select_dash_audio, tooltip='audio quality').place(relx=1, rely=0, x=-40, y=5)

        # bind menu selection
        self.pl_menu.listbox.bind('<<ListboxSelect>>', self.video_select_callback)
        self.stream_menu.listbox.bind('<<ListboxSelect>>', self.stream_select_callback)

        # playlist download, sub buttons -------------------------------------------------------------------------------
        pl_sub_frame = tk.Frame(home_tab, background=MAIN_BG)

        Button(pl_sub_frame, image=imgs['bat_icon'], command=self.show_batch_window, tooltip='Batch download').pack(pady=0, padx=5)
        Button(pl_sub_frame, image=imgs['subtitle_icon'], command=self.show_subtitles_window, tooltip='Download Subtitle').pack(pady=20, padx=5)
        Button(pl_sub_frame, image=imgs['about_icon'], command=self.show_about_notes, tooltip='About').pack(pady=0, padx=5)

        pl_sub_frame.grid(row=1, column=4, padx=5, pady=10)

        # file properties ----------------------------------------------------------------------------------------------
        self.file_properties = FileProperties(parent=home_tab)
        self.file_properties.grid(row=2, column=0, columnspan=3, rowspan=1, sticky='wes', padx=5, pady=10)

        # bind click anywhere on main frame to unfocus name widget
        home_tab.bind('<1>', lambda event: self.root.focus(), add='+')

        # download button ----------------------------------------------------------------------------------------------
        db_fr = tk.Frame(home_tab, width=60, background=MAIN_BG)
        db_fr.grid(row=2, column=3, padx=1, pady=5, sticky='e')
 
        Button(db_fr, text='Download', command=self.download_btn_callback, font='any 12').pack(side='left')
        # download Later button ----------------------------------------------------------------------------------------
        later_btn = Button(db_fr, text='▼', font='any 12', width=1) 
        later_btn.pack(side='left', fill='y', pady=1)

        def later_btn_handler(option):
            later = (option == 'Download Later')
            self.download_btn_callback(download_later=later)

        atk.RightClickMenu(later_btn, ['Download now', 'Download Later'], callback=later_btn_handler,
                           bg=RCM_BG, fg=RCM_FG, afg=RCM_AFG, abg=RCM_ABG, bind_left_click=True, bind_right_click=False)

        # spacer to keep the column with a fixed size for zoomed button images to look better on mouse hover
        tk.Frame(home_tab, width=60, background=MAIN_BG).grid(row=2, column=4, padx=5, pady=10)

        return home_tab

    def create_downloads_tab(self):
        tab = tk.Frame(self.main_frame, background=MAIN_BG)

        # top frame
        top_fr = tk.Frame(tab, bg=HDG_BG)
        top_fr.pack(fill='x', pady=(5, 0), padx=0)

        self.select_btn = Button(top_fr, text='', image=imgs['select_icon'], tooltip='select')
        self.select_btn.pack(side='left', padx=5, pady=10)

        self.select_btn.rcm = atk.RightClickMenu(
            self.select_btn,
            ['Select all', 'Select None', 'Select completed', 'Select Uncompleted'],
            callback=lambda option_name: self.select_ditems(option_name),
            bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG, bind_left_click=True,
            bind_right_click=False)

        self.view_btn = Button(top_fr, text='', image=imgs['view_icon'], tooltip='view')
        self.view_btn.pack(side='left', padx=5)

        view_mode_menu = ['bulk', 'compact', 'mix']
        self.view_btn.rcm = atk.RightClickMenu(
            self.view_btn,
            view_mode_menu,
            callback=lambda option_name: self.switch_view(option_name),
            bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG, bind_left_click=True,
            bind_right_click=False)

        # validate view_mode
        if config.view_mode not in view_mode_menu:
            config.view_mode = view_mode_menu[2]

        rcm_marker(self.view_btn.rcm, default=config.view_mode)

        self.filter_btn = Button(top_fr, text='', image=imgs['filter_icon'], tooltip='filter')
        self.filter_btn.pack(side='left', padx=5)

        self.filter_btn.rcm = atk.RightClickMenu(
            self.filter_btn,
            config.view_filter_map.keys(),
            callback=self.filter_view,
            bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG, bind_left_click=True,
            bind_right_click=False)

        rcm_marker(self.filter_btn.rcm, default=config.view_filter)

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
        self.stat_lbl.pack(fill='x', padx=0, pady=2, ipadx=5)

        # Scrollable
        self.d_tab = atk.ScrollableFrame(tab, bg=MAIN_BG, vscroll=True, hscroll=False,
                                         autoscroll=config.autoscroll_download_tab, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG)

        self.d_tab.pack(expand=True, fill='both')

        return tab

    def create_settings_tab(self):
        bg = MAIN_BG
        fg = MAIN_FG

        tab = atk.ScrollableFrame(self.main_frame, bg=bg, sbar_fg=SBAR_FG, sbar_bg=SBAR_BG, hscroll=False)

        def heading(text):
            tk.Label(tab, text=' ' + text, bg=HDG_BG, fg=HDG_FG, anchor='w',
                     font='any 10 bold').pack(anchor='w', expand=True, fill='x', ipady=3, pady=(0, 5))

        def separator():
            ttk.Separator(tab).pack(fill='both', expand=True, pady=(5, 30))

        # ----------------------------------------------------------------------------------------GUI options-----------
        heading('GUI options:')

        # themes -------------------------
        themes_frame = tk.Frame(tab, bg=bg)
        themes_frame.pack(anchor='w', expand=True, fill='x')

        tk.Label(themes_frame, bg=bg, fg=fg, text='Theme:  ').pack(side='left')

        # sorted themes names
        themes_names = natural_sort(list(all_themes.keys()))
        sel_theme_name = config.current_theme if config.current_theme in themes_names else config.DEFAULT_THEME

        self.themes_menu = Combobox(themes_frame, values=themes_names, selection=sel_theme_name, width=35)
        self.themes_menu.pack(side='left', ipadx=5)

        def apply_theme():
            theme_name = self.themes_menu.get()
            if theme_name != config.current_theme:
                self.apply_theme(theme_name)
        Button(themes_frame, text='Apply', command=apply_theme).pack(side='left', padx=5)

        theme_opt_btn = Button(themes_frame, text='Options', command=self.del_theme, tooltip='theme options')
        theme_opt_btn.pack(side='left', padx=10)

        theme_opt_map = {
            'New theme': self.new_theme,
            'Manual theme(s) entry': self.manual_theme_entry,
            'Edit theme': self.edit_theme,
            'Copy theme info': self.share_theme,
            'Delete theme': self.del_theme,
        }

        atk.RightClickMenu(theme_opt_btn, theme_opt_map.keys(), callback=lambda option: theme_opt_map[option](),
                           bind_left_click=True, bind_right_click=False, bg=RCM_BG, fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG)

        # font -----------------------------
        font_size_var = tk.IntVar(value=gui_font['size'])

        def update_font():
            font_size = font_size_var.get()
            gui_font.config(family=fonts_menu.selection, size=font_size)
            set_option(gui_font=gui_font.actual())

        font_families = sorted(tkfont.families())
        # font_properties = gui_font.actual() # {'family': 'DejaVu Sans', 'size': 10, 'weight': 'normal',
        #                                        'slant': 'roman', 'underline': 0, 'overstrike': 0}
        
        font_frame = tk.Frame(tab, bg=bg)
        font_frame.pack(anchor='w', expand=True, fill='x')

        tk.Label(font_frame, bg=bg, fg=fg, text='Font:  ').pack(side='left')

        fonts_menu = Combobox(font_frame, values=font_families, selection=gui_font['family'], callback=update_font)
        fonts_menu.pack(side='left', ipadx=5, padx=5)

        tk.Label(font_frame, bg=bg, fg=fg, text='Font size:').pack(side='left', padx=(10, 5))
        tk.Spinbox(font_frame, from_=6, to=25, state='readonly', textvariable=font_size_var, justify='center',
                   command=update_font, readonlybackground=MAIN_BG, fg=MAIN_FG, buttonbackground=SF_BG,
                   width=4, repeatinterval=0).pack(side='left', padx=5, ipady=2)

        # scrollbar width ---------------------------
        sb_frame = tk.Frame(tab, bg=bg)
        sb_frame.pack(anchor='w', expand=True, fill='x')

        sbw = config.scrollbar_width
        sbw = sbw if 0 < sbw < 51 else 25

        sbw_var = tk.IntVar(value=sbw)

        tk.Label(sb_frame, bg=bg, fg=fg, text='Scrollbar width (1 ~ 50): ').pack(side='left')
        tk.Spinbox(sb_frame, from_=1, to=50, state='readonly', textvariable=sbw_var, justify='center',
                   command=lambda: self.set_scrollbar_width(sbw_var.get()), readonlybackground=MAIN_BG, fg=MAIN_FG,
                   buttonbackground=SF_BG, width=4).pack(side='left', padx=5, ipady=2)
 
        CheckOption(tab, 'Enable systray icon "requires application restart"', key='enable_systray').pack(anchor='w')
        CheckOption(tab, 'Minimize to systray when closing application window',
                    key='minimize_to_systray').pack(anchor='w')

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

        CheckOption(tab, 'Maximize window on startup',
                    key='force_window_maximize').pack(anchor='w')

        separator()

        # ------------------------------------------------------------------------------------Popup messages------------
        heading('Popup messages:')

        for k, item in config.popups.items():
            description = item['description']
            var_name = f'popup_{k}'
            CheckOption(tab, description, key=var_name).pack(anchor='w')

        CheckOption(tab, 'Disable extra info popups, "same info will be available in the log tab"',
                    key='disable_log_popups').pack(anchor='w')

        separator()

        # ------------------------------------------------------------------------------------General options-----------
        heading('General options:')
        CheckOption(tab, 'Monitor clipboard for copied urls', key='monitor_clipboard').pack(anchor='w')
        CheckOption(tab, 'Show notification when finish downloading a file',
                    key='on_download_notification').pack(anchor='w')

        sett_folder_frame = tk.Frame(tab, bg=bg)
        sett_folder_frame.pack(anchor='w', expand=True, fill='x')
        tk.Label(sett_folder_frame, text='Settings Folder:', bg=bg, fg=fg).pack(side='left')
        tk.Label(sett_folder_frame, text=config.sett_folder, bg=bg, fg=fg).pack(side='left')
        Button(sett_folder_frame, text='Open', command=lambda: open_folder(config.sett_folder)).pack(side='right',
                                                                                                     padx=5)

        separator()

        # ------------------------------------------------------------------------------------Filesystem options--------
        heading('Filesystem options:')
        CheckOption(tab, 'Auto rename file if same name exists in download folder', key='auto_rename').pack(anchor='w')
        fr = tk.Frame(tab, bg=bg)
        fr.pack(anchor='w', expand=True, fill='x')
        CheckOption(fr, 'Auto number playlist filenames', key='use_playlist_numbers').pack(side='left', anchor='w')
        CheckOption(fr, 'Reverse numbers (requires manual url refresh)',
                    key='reverse_playlist').pack(side='left', anchor='w', padx=5)

        separator()
        # ------------------------------------------------------------------------------------Network options-----------
        heading('Network options:')
        proxy_frame = tk.Frame(tab, bg=bg)
        proxy_entry = CheckEntryOption(proxy_frame, 'Proxy:', check_key='enable_proxy', entry_key='proxy')
        proxy_entry.pack(side='left', expand=True, fill='x')

        def prefix_callback(scheme):
            url = proxy_entry.get()
            u = url.split('://', maxsplit=1)
            netloc = u[1] if len(u) > 1 else u[0]
            url = f'{scheme}{netloc}'
            proxy_entry.set(url)

        prefix_menu = ['http://', 'https://', 'socks4://', 'socks4a://', 'socks5://', 'socks5h://']
        prefix_btn = Button(proxy_frame, text='prefix', tooltip='add or change prefix')
        prefix_btn.pack(side='left', padx=5)
        atk.RightClickMenu(prefix_btn, prefix_menu, callback=prefix_callback, bind_left_click=True, bg=RCM_BG,
                           fg=RCM_FG, abg=RCM_ABG, afg=RCM_AFG)

        tip = ['proxy url should have one of below schemes:', 'http, https, socks4, socks4a, socks5, or socks5h', '',
               'e.g. "scheme://proxy_address:port"', '', 'if proxy server requires login',
               '"scheme://usr:pass@proxy_address:port"', '',
               'examples:', 'socks5h://127.0.0.1:8080', 'socks4://john:pazzz@127.0.0.1:1080']

        btn = Button(proxy_frame, text='tip!')
        btn.pack(side='left', padx=5)
        atk.RightClickMenu(btn, tip, bind_left_click=True, bg=RCM_BG, fg=RCM_FG, abg=RCM_BG, afg=RCM_FG)

        proxy_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        separator()

        # ------------------------------------------------------------------------------------Video options-------------
        heading('Video options:')

        # video extractor backend -------------------------
        extractor_frame = tk.Frame(tab, bg=bg)
        tk.Label(extractor_frame, bg=bg, fg=fg, text='Select video extractor engine:  ').pack(side='left')
        self.extractors_menu = Combobox(extractor_frame, values=config.video_extractors_list,
                                        selection=config.active_video_extractor)
        self.extractors_menu.callback = lambda: self.controller.set_video_backend(self.extractors_menu.selection)
        self.extractors_menu.pack(side='left')
        extractor_frame.pack(anchor='w')

        separator()

        # ------------------------------------------------------------------------------------Authentication options----
        heading('Website Authentication options:')
        login_frame = tk.Frame(tab, bg=bg)
        CheckOption(login_frame, 'Enable!', key='use_web_auth').pack(side='left')
        LabeledEntryOption(login_frame, 'User:', entry_key='username').pack(side='left', padx=10)
        LabeledEntryOption(login_frame, 'Pass:', entry_key='password', show='*').pack(side='left', padx=5)
        CheckOption(login_frame, 'remember user/pass', key='remember_web_auth').pack(side='left')
        login_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        separator()

        # ------------------------------------------------------------------------------------Workarounds---------------
        heading('Workarounds:')
        if config.operating_system == 'Linux':
            CheckOption(tab, 'Enable ibus workaround, to fix slow application startup.',
                        key='ibus_workaround').pack(anchor='w')

        # cookies
        def get_cookie_file(target):
            """get cookie file path"""
            fp = filechooser()
            if fp:
                target.set(fp)

        cookies_frame = tk.Frame(tab, bg=MAIN_BG)
        cookies = CheckEntryOption(cookies_frame, 'Cookies file:', check_key='use_cookies',
                                   entry_key='cookie_file_path')
        cookies.pack(side='left', expand=True, fill='x')
        Button(cookies_frame, image=imgs['folder_icon'],
               command=lambda: get_cookie_file(cookies)).pack(side='left', padx=5)
        cookies_frame.pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        CheckEntryOption(tab, 'Referee url:', check_key='use_referer',
                         entry_key='referer_url').pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        def update_headers():
            config.http_headers['User-Agent'] = config.custom_user_agent or config.DEFAULT_USER_AGENT

        # config.HEADERS.update('User-Agent'=config.custom_user_agent)
        CheckEntryOption(tab, 'Custom user agent:', entry_key='custom_user_agent',
                         callback=update_headers).pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        # ssl certificate validation
        def ignore_ssl_warning():
            if config.ignore_ssl_cert:
                res = self.show_popup(6)

                if res != 'Yes':
                    config.ignore_ssl_cert = False
                    ignore_ssl_option.set(False)

        ignore_ssl_option = CheckOption(tab, "ignore ssl certificate validation", key='ignore_ssl_cert',
                                        callback=ignore_ssl_warning)
        ignore_ssl_option.pack(anchor='w')

        separator()

        # ------------------------------------------------------------------------------------Post-processing options---
        heading('Post-processing options:')
        CheckOption(tab, 'Show "MD5 and SHA256" checksums for downloaded files in log', key='checksum').pack(anchor='w')
        CheckOption(tab, 'Use server timestamp for downloaded files',
                    key='use_server_timestamp').pack(anchor='w')
        CheckOption(tab, 'Write metadata to media files', key='write_metadata').pack(anchor='w')
        CheckOption(tab, 'Write thumbnail image to disk', key='download_thumbnail').pack(anchor='w')

        tk.Label(tab, text='Select action to run after "ALL" download items are completed:', bg=bg,
                 fg=fg).pack(anchor='w', padx=5)

        CheckEntryOption(tab, ' Run command:  ', entry_key='on_completion_command').pack(anchor='w', fill='x',
                                                                                         expand=True, padx=(0, 5))
        CheckOption(tab, ' Shutdown computer', key='shutdown_pc').pack(anchor='w', fill='x', expand=True, padx=(0, 5))

        separator()

        # ------------------------------------------------------------------------------------Downloader options--------
        heading('Downloader options:')
        LabeledEntryOption(tab, 'Concurrent downloads (1 ~ 100): ', entry_key='max_concurrent_downloads',
                           get_text_validator=lambda x: int(x) if 0 < int(x) < 101 else 3, width=8).pack(anchor='w')
        LabeledEntryOption(tab, 'Connections per download (1 ~ 100): ', entry_key='max_connections', width=8,
                           get_text_validator=lambda x: int(x) if 0 < int(x) < 101 else 10).pack(anchor='w')

        # speed limit
        speed_frame = tk.Frame(tab, bg=bg)
        CheckEntryOption(speed_frame, 'Speed Limit (kb/s, mb/s. gb/s): ', entry_key='speed_limit', width=8,
                         set_text_validator=lambda x: format_bytes(x), callback=self.show_speed_limit,
                         get_text_validator=lambda x: self.validate_speed_limit(x),
                         entry_disabled_value=0).pack(side='left')
        self.speed_limit_label = tk.Label(speed_frame, bg=bg, fg=fg)
        self.speed_limit_label.pack(side='left', padx=10)
        speed_frame.pack(anchor='w')
        self.show_speed_limit()

        LabeledEntryOption(tab, 'Auto refreshing expired urls [Num of retries]: ', entry_key='refresh_url_retries',
                           width=8, get_text_validator=lambda x: int(x)).pack(anchor='w')

        separator()

        # ------------------------------------------------------------------------------------Debugging options---------
        heading('Debugging:')
        CheckOption(tab, 'keep temp files / folders after done downloading for debugging.',
                    key='keep_temp').pack(anchor='w')
        CheckOption(tab, 'Re-raise all caught exceptions / errors for debugging "Application will crash on any Error"',
                    key='TEST_MODE').pack(anchor='w')
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

        atk.RightClickMenu(self.log_text, ['Cut', 'Copy', 'Paste'],
                           callback=lambda option: self.log_text.event_generate(f'<<{option}>>'),
                           bg=RCM_BG, fg=RCM_FG, afg=RCM_AFG, abg=RCM_ABG)

        def copy_log():
            self.copy(self.log_text.get(1.0, tk.END))
            self.msgbox('Log text copied to clipboard')

        btn_frame = tk.Frame(tab, bg=MAIN_BG)
        tk.Label(btn_frame, text='Log Level:', bg=MAIN_BG, fg=MAIN_FG, font='any 10 bold').pack(side='left')
        level_menu = Combobox(btn_frame, values=(1, 2, 3), selection=config.log_level, width=5)
        level_menu.callback = lambda: set_option(log_level=int(level_menu.selection))
        level_menu.pack(side='left', padx=5)

        Button(btn_frame, text='Clear', command=self.log_text.clear).pack(side='right', padx=5)
        Button(btn_frame, text='copy Log', command=copy_log).pack(side='right', padx=5)

        btn_frame.pack(pady=5, expand=True, fill='x')
        self.log_text.pack(expand=True, fill='both')

        return tab

    def create_update_tab(self):
        bg = MAIN_BG
        fg = MAIN_FG
        tab = tk.Frame(self.main_frame, bg=bg)

        tk.Label(tab, text=' Update Tab:', bg=HDG_BG, fg=HDG_FG, anchor='w',
                 font='any 10 bold').pack(anchor='n', expand=False, fill='x', ipady=3, pady=(0, 5))

        update_frame = tk.Frame(tab, bg=bg)
        update_frame.pack(anchor='n', fill='both', expand=True, pady=(20, 0))

        update_frame.columnconfigure(4, weight=1)

        def lbl(var):
            return tk.Label(update_frame, bg=bg, fg=fg, textvariable=var, padx=5)

        CheckEntryOption(update_frame, 'Check for update every: ', entry_key='update_frequency', width=4,
                         justify='center',
                         check_key='check_for_update', get_text_validator=lambda x: int(x) if int(x) > 0 else 7) \
            .grid(row=0, column=1, sticky='w')
        tk.Label(update_frame, bg=bg, fg=fg, text='days', padx=5).grid(row=0, column=2, sticky='w')

        # FireDM update
        self.firedm_update_note = tk.StringVar()
        self.firedm_update_note.set(f'FireDM version: {config.APP_VERSION}')
        lbl(self.firedm_update_note).grid(row=1, column=1, sticky='w', pady=20, padx=20)

        # youtube-dl and yt_dlp
        self.youtube_dl_update_note = tk.StringVar()
        self.youtube_dl_update_note.set(f'youtube-dl version: {config.youtube_dl_version}')
        lbl(self.youtube_dl_update_note).grid(row=2, column=1, sticky='w', pady=(0, 20), padx=20)

        self.yt_dlp_update_note = tk.StringVar()
        self.yt_dlp_update_note.set(f'yt_dlp version: {config.yt_dlp_version}')
        lbl(self.yt_dlp_update_note).grid(row=3, column=1, sticky='w', pady=(0, 20), padx=20)

        if config.FROZEN or config.isappimage:
            for i, pkg in enumerate(('firedm', 'youtube_dl', 'yt_dlp')):
                Button(update_frame, text='Rollback', command=lambda x=pkg: self.rollback_pkg_update(x),
                       tooltip=f'restore previous {pkg} version',
                       image=imgs['undo_icon']).grid(row=i + 1, column=3, sticky='w', pady=5)

        Button(update_frame, text='Check for updates', compound='left',
               command=self.check_for_update).grid(row=3, column=4, padx=20)

        # progressbar while updating packages
        self.update_progressbar = atk.RadialProgressbar(parent=update_frame, size=100, fg=PBAR_FG, text_bg=bg,
                                                        text_fg=PBAR_TXT)
        self.update_progressbar.grid(row=1, column=4, rowspan=2, columnspan=3, pady=50, padx=20)

        if config.isappimage:
            appimage_note = f'Note: AppImage update folder located at: {config.appimage_update_folder} \n'\
                            f'it can be safely deleted to use original AppImage packages'
            AutoWrappingLabel(update_frame, bg=bg, fg=fg, anchor='w', text=appimage_note,
                     justify='left').grid(row=4, column=1, columnspan=6, pady=50, sticky='ew', padx=20)

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
        text = format_bytes(sl) if sl else '.. No Limit!'
        self.speed_limit_label.config(text=f'current value: {text}')

    def remember_window_size(self, *args):
        """save current window size in config.window_size"""

        # check if window is maximized, wm_state returns the current state of window: either normal, iconic, withdrawn,
        # icon, or (Windows and Mac OS X only) zoomed
        # ref https://tcl.tk/man/tcl8.6/TkCmd/wm.htm#M62
        if config.operating_system in ('Windows', 'Darwin'):
            try:
                config.window_maximized = (self.root.wm_state() == 'zoomed')
            except Exception as e:
                log('error getting window maximize state:', e)

        if not config.window_maximized:
            config.window_size = (self.root.winfo_width(), self.root.winfo_height())

    def initialize_font(self):
        # get default font by creating a dummy label widget
        lbl = tk.Label(self.root, text='hello world')

        global gui_font
        gui_font = tkfont.Font(font=lbl['font'])

        # load user font settings
        try:
            if config.gui_font['size'] not in config.gui_font_size_range:
                config.gui_font['size'] = config.gui_font_size_default
                
            gui_font.config(**config.gui_font)
        except Exception as e:
            log('loading user font error:', e, log_level=3)

    def assign_font_for(self, widget):

        # apply custom font to a widget and all its children
        allwidgets = [widget] + self.get_all_children(widget)
        for w in allwidgets:
            atk.configure_widget(w, font=gui_font)

    def set_scrollbar_width(self, width):
        if width not in config.scrollbar_width_range:
            width = config.scrollbar_width_default
            
        allwidgets = self.get_all_children(self.root)
        scrollbars = [w for w in allwidgets if w.winfo_class() == 'TScrollbar']
        for sb in scrollbars:
            atk.configure_widget(sb, width=width)

        set_option(scrollbar_width=width)

    def get_all_children(self, widget):
        """get all child objects under tkinter widget"""
        children = []

        def get_children(parent):
            for w in parent.winfo_children():
                children.append(w)

                if w.winfo_children():
                    get_children(w)

        get_children(widget)

        return children

    # endregion

    # region DItem
    def create_ditem(self, uid, **kwargs):
        """create new DItem and show it in downloads tab

        Args:
            uid (str): download item's uid
            kwargs: key/values to update a download item
        """
        status = kwargs.get('status')
        mode = kwargs.get('mode', config.view_mode)

        if mode == 'mix':
            mode = 'bulk' if status in config.Status.active_states else 'compact'

        # check if item already created before
        if uid in self.d_items:
            return

        b_map = (
            ('<Button-2>', lambda event, x=uid: self.on_item_rightclick(x)),
            ('<Button-3>', lambda event, x=uid: self.on_item_rightclick(x)),
            ('<Shift-1>', lambda event, x=uid: self.on_shift_click(x)),
            ('<Delete>', lambda event: self.delete_selected()),
            ('<Return>', lambda event: self.open_selected_file())
        )

        # right click menu
        rcm_map = {
            'Open File  (Enter)': lambda uid: self.controller.play_file(uid=uid),
            'Open File Location': lambda uid: self.controller.open_folder(uid=uid),
            'Watch while downloading': lambda uid: self.controller.play_file(uid=uid),
            'copy webpage url': lambda uid: self.copy(self.controller.get_property('url', uid=uid)),
            'copy direct url': lambda uid: self.copy(self.controller.get_property('eff_url', uid=uid)),
            'copy playlist url': lambda uid: self.copy(self.controller.get_property('playlist_url', uid=uid)),
            'Resume': lambda uid: self.resume_selected(),
            'Pause': lambda uid: self.stop_selected(),
            'Delete  (Del)': lambda uid: self.delete_selected(),
            'Schedule / unschedule': lambda uid: self.schedule_selected(),
            'Toggle Shutdown Pc when finish': lambda uid: self.controller.toggle_shutdown(uid),
            'On item completion command': lambda uid: self.set_on_completion_command(uid),
            'Properties': lambda uid: self.msgbox(self.controller.get_properties(uid=uid)),
        }

        rcm = []
        for i, item in enumerate(rcm_map.keys()):
            # filter options for completed items
            if not (status == config.Status.completed and i in (2, 6, 7, 9, 10, 11)):
                rcm.append(item)

            # add separators
            if i in (5, 9, 11) and rcm[-1] != '---':
                rcm.append('---')

        def rcm_callback(key, x=uid):
            rcm_map[key](uid)

        bg = atk.calc_contrast_color(MAIN_BG, 10) if len(self.d_items) % 2 != 0 else MAIN_BG
        d_item = DItem(self.d_tab, uid, status, on_toggle_callback=self.update_stat_lbl, mode=mode, bg=bg,
                       playbtn_callback=lambda *args, x=uid: self.toggle_download(x),
                       delbtn_callback=lambda *args, x=uid: self.delete(x),
                       onclick=lambda *args, x=uid: self.on_toggle_ditem(x),
                       ondoubleclick=lambda *args, x=uid: self.controller.play_file(uid=x),
                       bind_map=b_map,
                       rcm=rcm, rcm_callback=rcm_callback)

        self.d_items[uid] = d_item

        # font
        self.assign_font_for(d_item)

        # get segment progress
        kwargs['segments_progress'] = self.controller.get_segments_progress(uid=uid)

        # update d_item info
        d_item.update(**kwargs)

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
        """resume downloading selected and Uncompleted items in downloads tab"""
        for item in self.get_selected_items():
            if item.status in (config.Status.cancelled, config.Status.error):
                self.resume_download(item.uid)

    def stop_selected(self):
        """stop downloading selected items in downloads tab"""
        for item in self.get_selected_items():
            self.stop_download(item.uid)

    def delete(self, uid):
        """delete download item"""

        res = self.show_popup(7)

        if res != 'Yes':
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
        res = self.show_popup(7)

        if res != 'Yes':
            return

        # temporarily disable autoscroll
        if config.autoscroll_download_tab:
            self.d_tab.autoscroll = False

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

        if config.autoscroll_download_tab:
            # enable autoscroll
            self.root.update_idletasks()
            self.d_tab.autoscroll = True

    def switch_view(self, mode):
        config.view_mode = mode
        items = {uid: item for uid, item in self.d_items.items()}
        self.d_items.clear()

        # todo: should fix errors when using item.switch_view() instead of recreating items
        for uid, item in items.items():
            kwargs = item.latest_update
            selected = item.selected
            item.destroy()
            self.create_ditem(uid, **kwargs, mode=mode)
            new_item = self.d_items[uid]
            new_item.select(selected)
            new_item.dynamic_show_hide()
        self.update_stat_lbl()
        self.d_tab.scrolltotop()

    def filter_view(self, option):
        config.view_filter = option
        for item in self.d_items.values():
            item.dynamic_show_hide()

    def select_ditems(self, command):
        """select ditems in downloads tab
        Args:
            command (str): one of ['Select all', 'Select None', 'Select completed', 'Select Uncompleted']
        """
        items = [item for item in self.d_items.values() if item.winfo_viewable()]

        # reset selection
        for item in items:
            item.select(False)

        if command == 'Select None':
            return

        if command == 'Select completed':
            items = [item for item in self.d_items.values() if item.status == config.Status.completed]

        elif command == 'Select Uncompleted':
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

        for item in self.d_items.values():
            if item is not current_item:
                item.select(False)

        current_item.select()

    def get_selected_items(self):
        """return a list of selected items"""
        return [item for item in self.d_items.values() if item.selected]

    def update_stat_lbl(self):
        """update the number of selected download items and display it on a label in downloads tab"""
        count = len(self.get_selected_items())
        s = [item.status for item in self.d_items.values()]

        # self.select_lbl['text'] = f'  Selected [{count} of {len(self.d_items)}]'
        self.stat_lbl['text'] = f'Selected: [{count} of {len(self.d_items)}] - ' \
                                f'Active: {sum([s.count(x) for x in config.Status.active_states])}, ' \
                                f'Completed: {s.count(config.Status.completed)},  ' \
                                f'Cancelled: {s.count(config.Status.cancelled)},  ' \
                                f'Scheduled: {s.count(config.Status.scheduled)}, ' \
                                f'Pending: {s.count(config.Status.pending)}'

        if s.count(config.Status.downloading) > 0:
            self.resume_all_btn['text'] = 'Stop All'
        else:
            self.resume_all_btn['text'] = 'Resume All'

    # endregion

    # region download
    def download_btn_callback(self, download_later=False):
        """callback for download button in main tab"""

        # download
        self.download(name=self.file_properties.name, folder=self.file_properties.folder, download_later=download_later)

    def download(self, uid=None, **kwargs):
        """Send command to controller to download an item

        Args:
            uid (str): download item's unique identifier, if omitted active item will be downloaded
            kwargs: key/value for any legit attributes in DownloadItem
        """

        if uid is None:
            kwargs['video_idx'] = self.pl_menu.select()

        self.controller.download(uid=uid, **kwargs)

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

        self.download(uid, silent=True)

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
        video_idx = kwargs.get('video_idx', None)
        stream_idx = kwargs.get('stream_idx', None)

        if 'status' in kwargs:
            self.root.after(100, self.update_stat_lbl)

        # load previous download items in d_tab, needed at startup
        if command == 'd_list':
            d_list = kwargs.get('d_list')
            for i, item in enumerate(d_list):
                # self.root.after(1000 + i * 5, lambda k=item: self.create_ditem(**k, focus=False))
                self.create_ditem(**item, focus=False)
            self.root.update_idletasks()
            gui_loading_time = round(time.time() - self.gui_timer, 2)
            ibus_hint = ''
            if config.operating_system == 'Linux' and not config.ibus_workaround and gui_loading_time > 10:
                ibus_hint = ' - Slow startup!!!, try to enable "ibus workaround" in settings'
            log('Gui Loading time:', gui_loading_time, 'seconds', ibus_hint)

            # restart ibus
            if self.should_restart_ibus:
                self.root.after(1000, self.restart_ibus)

            self.update_stat_lbl()

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
                self.controller.get_stream_menu(video_idx=0)
            else:
                self.pl_menu.reset()

        # update stream menu
        elif command == 'stream_menu':
            stream_menu = kwargs['stream_menu']

            # make sure this data belong to selected item in playlist
            if self.pl_menu.select() == video_idx:
                self.stream_menu.hide_progressbar()
                self.stream_menu.set(stream_menu)
                self.stream_menu.select(stream_idx)
                self.controller.report_d(video_idx=video_idx, active=True)

            # pass to playlist download window
            if self.pl_window:
                self.pl_window.update_view(video_idx=video_idx, stream_menu=stream_menu, stream_idx=stream_idx)

        # create new items
        elif command == 'new':
            ditem = self.d_items.get(uid)
            if ditem and ditem.status == config.Status.completed:
                ditem.destroy()
                self.d_items.pop(uid)
                ditem = None
            
            if not ditem:
                self.select_tab('Downloads')

            self.create_ditem(**kwargs)

        # update current item
        elif command == 'update':
            # update active item
            if active and (self.pl_menu.select() == video_idx or not self.pl_menu.get()):
                self.file_properties.update(**kwargs)

                # thumbnail
                img_base64 = kwargs.get('thumbnail', None)
                if img_base64:
                    self.thumbnail.show(b64=img_base64)

                if stream_idx is not None:
                    self.stream_menu.select(stream_idx)

            # update item in d_tab
            elif uid in self.d_items:
                item = self.d_items[uid]
                item.update(**kwargs)
                if config.view_mode == 'mix':
                    view_mode = 'bulk' if item.status in config.Status.active_states else 'compact'
                    item.switch_view(view_mode)

        # handle signals for post processor callbacks
        elif command == 'signal':
            signal_id = kwargs.get('signal_id')
            self.execute_post_processor(signal_id)

        # total speed
        elif command == 'total_speed':
            ts = format_bytes(kwargs.get('total_speed'), tail='/s')
            self.total_speed.set(ts)

    # endregion

    # region general

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
        # start = time.time()
        # self.root.destroy()  # destroy all widgets and quit mainloop, consume 4~5 seconds to destroy widgets???
        self.root.quit()  # quit main loop without destroying widgets, faster to quit application
        # print(time.time() - start) 

        # save themes
        self.save_user_themes()

        # quit systray
        self.systray.shutdown()

        print('Gui terminated')

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

    def post_startup(self):
        """it will be called after gui displayed"""

        # register log callbacks
        config.log_callbacks.append(self.log_callback)
        config.log_popup_callback = self.log_popup

        # log runtime info
        log_runtime_info()

        # log extra pkgs info
        log('Tkinter version:', self.root.call("info", "patchlevel"))
        log('AwesomeTkinter version:', atk_version)
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
        if not config.disable_update_feature:
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

    @ignore_calls_when_busy
    def show_about_notes(self):
        res = self.popup(about_notes, buttons=['Home', 'Help!', 'Close'], title='About FireDM')
        if res == 'Help!':
            open_webpage('https://github.com/firedm/FireDM/blob/master/docs/user_guide.md')
        elif res == 'Home':
            open_webpage('https://github.com/firedm/FireDM')

        free_callback(self.show_about_notes)

    @ignore_calls_when_busy
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
        video_idx = self.pl_menu.select()
        stream_idx = idx or self.stream_menu.select()
        if stream_idx is not None:
            self.controller.select_stream(stream_idx, video_idx=video_idx)

    def video_select_callback(self, *args, idx=None):
        idx = idx or self.pl_menu.select()

        if idx is not None:
            self.stream_menu.reset()
            self.stream_menu.start_progressbar()
            self.thumbnail.reset()
            self.controller.get_stream_menu(video_idx=idx)

    def show_subtitles_window(self):
        if self.subtitles_window:
            self.msgbox('Subtitles window already opened')
            return

        subs = self.controller.get_subtitles()
        if subs:
            self.subtitles_window = SubtitleWindow(self, subs)
        else:
            self.msgbox('No Subtitles available')

    def show_batch_window(self):
        if self.batch_window:
            self.msgbox('batch window already opened')
            return

        self.batch_window = BatchWindow(self)

    def show_pl_window(self):
        if self.pl_window:
            self.msgbox('Playlist window already opened')
            return

        # pl = [f'video {x}' for x in range(1, 5001)]  # test
        pl = self.pl_menu.get()
        if not pl:
            self.msgbox('No videos in playlist')
            return

        self.pl_window = PlaylistWindow(self, pl)

    def select_dash_audio(self, uid=None, video_idx=None, active=True):
        # select audio for dash video
        selected_idx = None
        menu = self.controller.get_audio_menu(uid=uid, video_idx=video_idx)
        if menu:
            selected_audio = self.controller.get_selected_audio(uid=uid, video_idx=video_idx)
            idx = menu.index(selected_audio) if selected_audio else 0

            aw = AudioWindow(self, menu, idx)
            # print('aw.selected_idx:', aw.selected_idx)
            self.controller.select_audio(aw.selected_idx, uid=uid, video_idx=video_idx, active=active)
            selected_idx = aw.selected_idx
        else:
            self.popup('No selections available', 'select a dash video stream and try again!')

        return selected_idx
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

        # reroute urls to batch window if opened
        if self.batch_window:
            self.batch_window.add_url(url)
        else:
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
    def get_user_response(self, msg, options, popup_id=None):
        """thread safe - get user response
        it will be called by controller to get user decision
        don't call it internally, it will freeze gui, instead use self.show_popup() or self.popup()

        Args:
            msg (str): message to be displayed in popup message
            options (list, tuple): names of buttons in popup window
        """
        if popup_id:
            res = self.run_method(self.show_popup, popup_id, get_response=True)
        else:
            res = self.run_method(self.popup, msg, buttons=options, get_response=True)
        return res

    def msgbox(self, *args):
        """thread safe - popup message that can be called from a thread

        Args:
            args (str): any number of string arguments
        """
        self.run_method(self.popup, *args, get_response=False, buttons=['Ok'], title='Info')

    def show_popup(self, popup_id, **kwargs):
        """
        show a preset popup

        Args:
            popup_id(int): popup message key as in config.popups dict

        Returns:
            str or tuple(str, str)
        """

        popup = config.get_popup(popup_id)
        msg = popup['body']
        options = popup['options']
        if not popup['show']:
            return popup['default']

        res = self.popup(msg, buttons=options, optout_id=popup_id, **kwargs)
        return res

    def popup(self, *args, buttons=None, title='Attention', get_user_input=False, default_user_input='', bg=None,
              fg=None, **kwargs):
        x = Popup(*args, buttons=buttons, parent=self.root, title=title, get_user_input=get_user_input,
                  default_user_input=default_user_input, bg=bg, fg=fg, **kwargs)
        response = x.show()
        return response

    def log_callback(self, start, text, end):
        """thread safe - log callback to be executed when calling utils.log"""
        msg = start + text + end

        # fix bidi, todo: add bidi support to awesometkinter.ScrolledText
        msg = render_text(msg)
        self.run_method(self.log_text.append, msg, get_response=False)

    def log_popup(self, start, text, end):
        """thread safe log popup callback to be executed when calling utils.log with showpopup=True"""
        if not config.disable_log_popups:
            self.msgbox(text)

    # endregion


if __name__ == '__main__':
    try:
        controller = Controller(view_class=MainWindow)
        controller.run()
    except Exception as e:
        print('error:', e)

