import awesometkinter as atk
from . import config

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


builtin_themes = {
    'Dark': {
        "MAIN_BG": "#1c1c21", "MAIN_FG": "white", "SF_BG": "#000300", "SF_FG": "white", "SF_BTN_BG": "#d9dc4b",
        "SF_CHKMARK": "#d9dc4b", "THUMBNAIL_BG": "#000300", "THUMBNAIL_FG": "#d9dc4b", "PBAR_BG": "#26262b",
        "PBAR_FG": "#d9dc4b", "PBAR_TXT": "white", "ENTRY_BD_COLOR": "#000300", "BTN_BG": "#d9dc4b",
        "BTN_FG": "black", "BTN_HBG": "#000300", "BTN_ABG": "#000300", "BTN_AFG": "white", "HDG_BG": "#d9dc4b",
        "HDG_FG": "black", "THUMBNAIL_BD": "#d9dc4b", "SBAR_BG": "#1c1c21", "SBAR_FG": "white",
        "RCM_BG": "#1c1c21", "RCM_FG": "white", "RCM_ABG": "#d9dc4b", "RCM_AFG": "black",
        "TITLE_BAR_BG": "#d9dc4b", "TITLE_BAR_FG": "black"},

    "Gainsboro-SandyBrown-Teal": {
        "MAIN_BG": "#DDDDDD", "SF_BG": "#F5A962", "SF_BTN_BG": "#3C8DAD",
        "PBAR_FG": "#125D98", "MAIN_FG": "black", "SF_FG": "#125D98", "SF_CHKMARK": "#125D98",
        "THUMBNAIL_BG": "#F5A962", "THUMBNAIL_FG": "#125D98", "THUMBNAIL_BD": "black",
        "PBAR_BG": "#d3d3d3", "PBAR_TXT": "#125D98", "ENTRY_BD_COLOR": "#F5A962",
        "BTN_BG": "#3C8DAD", "BTN_FG": "#DDDDDD", "BTN_HBG": "#F5A962", "BTN_ABG": "#F5A962",
        "BTN_AFG": "white", "HDG_BG": "#3C8DAD", "HDG_FG": "#DDDDDD", "SBAR_BG": "#DDDDDD",
        "SBAR_FG": "#125D98", "RCM_BG": "#DDDDDD", "RCM_FG": "#125D98", "RCM_ABG": "#3C8DAD",
        "RCM_AFG": "#DDDDDD", "TITLE_BAR_BG": "#3C8DAD", "TITLE_BAR_FG": "#125D98",
        "SEL_BG": "#F5A962", "SEL_FG": "black"},

    "Black_Grey_Shade-of-Pink": {
        "MAIN_BG": "#444444", "SF_BG": "#171717", "SF_BTN_BG": "#EDEDED", "PBAR_FG": "#DA0037",
        "MAIN_FG": "#EDEDED", "SF_FG": "#EDEDED", "SF_CHKMARK": "#DA0037",
        "THUMBNAIL_BG": "#171717", "THUMBNAIL_FG": "#DA0037", "THUMBNAIL_BD": "white",
        "PBAR_BG": "#4e4e4e", "PBAR_TXT": "#DA0037", "ENTRY_BD_COLOR": "#171717",
        "BTN_BG": "#EDEDED", "BTN_FG": "black", "BTN_HBG": "#171717", "BTN_ABG": "#171717",
        "BTN_AFG": "#DA0037", "HDG_BG": "#EDEDED", "HDG_FG": "black", "SBAR_BG": "#171717",
        "SBAR_FG": "#DA0037", "RCM_BG": "#444444", "RCM_FG": "#EDEDED", "RCM_ABG": "#EDEDED",
        "RCM_AFG": "#DA0037", "TITLE_BAR_BG": "#EDEDED", "TITLE_BAR_FG": "black",
        "SEL_BG": "#171717", "SEL_FG": "#EDEDED"},

    "Green-Brown": {
        "MAIN_BG": "#3A6351", "SF_BG": "#F2EDD7", "SF_BTN_BG": "#A0937D", "PBAR_FG": "#5F939A",
        "MAIN_FG": "white", "SF_FG": "black", "SF_CHKMARK": "#A0937D", "THUMBNAIL_BG": "#F2EDD7",
        "THUMBNAIL_FG": "white", "THUMBNAIL_BD": "white", "PBAR_BG": "#446d5b", "PBAR_TXT": "white",
        "ENTRY_BD_COLOR": "#F2EDD7", "BTN_BG": "#A0937D", "BTN_FG": "black", "BTN_HBG": "#F2EDD7",
        "BTN_ABG": "#446d5b", "BTN_AFG": "white", "HDG_BG": "#A0937D", "HDG_FG": "black",
        "SBAR_BG": "#3A6351", "SBAR_FG": "white", "RCM_BG": "#3A6351", "RCM_FG": "white",
        "RCM_ABG": "#A0937D", "RCM_AFG": "black", "TITLE_BAR_BG": "#A0937D", "TITLE_BAR_FG": "black",
        "SEL_BG": "#F2EDD7", "SEL_FG": "black"},

    "Yellow-Foil-covered Sneakers": {
        "MAIN_BG": "#333652", "SF_BG": "#90adc6", "SF_BTN_BG": "#fad02c",
        "PBAR_FG": "#e9eaec", "MAIN_FG": "#e9eaec", "SF_FG": "black",
        "SF_CHKMARK": "#e9eaec", "THUMBNAIL_BG": "#90adc6", "THUMBNAIL_FG": "white",
        "THUMBNAIL_BD": "white", "PBAR_BG": "#3d405c", "PBAR_TXT": "white",
        "ENTRY_BD_COLOR": "#90adc6", "BTN_BG": "#fad02c", "BTN_FG": "black",
        "BTN_HBG": "#e9eaec", "BTN_ABG": "#90adc6", "BTN_AFG": "white",
        "HDG_BG": "#fad02c", "HDG_FG": "black", "SBAR_BG": "#333652", "SBAR_FG": "#90adc6",
        "RCM_BG": "#333652", "RCM_FG": "#e9eaec", "RCM_ABG": "#fad02c", "RCM_AFG": "black",
        "TITLE_BAR_BG": "#fad02c", "TITLE_BAR_FG": "black", "SEL_BG": "#90adc6",
        "SEL_FG": "black"},

    "Red_Black": {
        "SF_BTN_BG": "#960000", "PBAR_FG": "#e09f3e", "MAIN_FG": "white", "SF_FG": "white",
        "SF_CHKMARK": "#e09f3e", "THUMBNAIL_FG": "white", "THUMBNAIL_BD": "white", "PBAR_BG": "#0a0a0a",
        "PBAR_TXT": "white", "BTN_BG": "#960000", "BTN_FG": "white", "BTN_AFG": "white", "HDG_BG": "#960000",
        "HDG_FG": "white", "SBAR_FG": "#960000", "RCM_FG": "white", "RCM_ABG": "#960000", "RCM_AFG": "white",
        "TITLE_BAR_BG": "#960000", "TITLE_BAR_FG": "black", "SEL_FG": "white"},

    "Orange_Black": {
        "SF_BTN_BG": "#e09f3e", "PBAR_FG": "#FFFFFF", "MAIN_FG": "white", "SF_FG": "white",
        "SF_CHKMARK": "white", "THUMBNAIL_FG": "white", "THUMBNAIL_BD": "white", "PBAR_BG": "#0a0a0a",
        "PBAR_TXT": "white", "BTN_BG": "#e09f3e", "BTN_FG": "black", "BTN_AFG": "white",
        "HDG_BG": "#e09f3e", "HDG_FG": "black", "SBAR_FG": "#e09f3e", "RCM_FG": "white",
        "RCM_ABG": "#e09f3e", "RCM_AFG": "black", "TITLE_BAR_BG": "#e09f3e", "TITLE_BAR_FG": "black",
        "SEL_FG": "white"}
}


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
