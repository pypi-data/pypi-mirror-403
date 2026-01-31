"""
Variables that define how the program behaves.
Stores paths to all config files and options for the TUI.
Unexpected behaviors may arise if variables are set incorrectly.
"""

import os

# paths
CONFIG_DIR: os.PathLike = os.path.expanduser("~/.config/totp/")
HASH_FILE: os.PathLike = os.path.join(CONFIG_DIR, "data.json")
SITES_TABLE: os.PathLike = os.path.join(CONFIG_DIR, "totp.db")

LOG_DIR: os.PathLike = os.path.expanduser("~/.local/share/totp/logs/")
LOG_LEVEL: str = "INFO"

# fallbacks
BLANK_DEF: str = " "
NICK_DEF: str = "#"
SLIDER_DEF: list[str] = ["█", "◣", " "]
SITE_DEF: str = "https://www.github.com/"
DEFAULT_FG: str = "white"

# if True, ignores SLIDER_DEF
FANCY_SLIDER: bool = False

# ---
# SCHEMAS
# ---
# every item is a line
# every element in the list is a component
# required fields for every component
# - "type" as one of [site,nick,token,token_time,time,slider,filler]
# - "width" as a positive number. not needed if type is [token_time,time,filler]
# if type is "filler", instead only "filler" is needed
# if type is "token_time" then "precision" is also needed
# if type is "time" then "format" is also needed
# optional fields:
# - "alignment" as one of [right,left]
# - "space_before" as a positive number
# - "space_after" as a positive number
# - "color" as one of [white,red,green,yellow,blue,magenta,cyan]

# defines how sites are displayed
ENTRY_SCHEMA: dict = {
    "line1": [
        {"type": "site", "width": 20, "alignment": "left"},
        {"type": "token", "alignment": "right", "space_before": 8},
    ],
    "line2": [
        {"type": "nick", "width": 32, "alignment": "left", "space_after": 8},
        {"type": "token_time", "precision": 1, "alignment": "right"},
    ],
    "border": [{"type": "filler", "filler": " "}],
}

# defines how the status bar at the bottom is displayed
STATUSLINE_SCHEMA: dict = {
    "border": [{"type": "filler", "filler": "-"}],
    "line1": [
        {"type": "time", "format": "%H:%M:%S", "alignment": "left"},
        {"type": "slider", "width": 16, "alignment": "right"},
    ],
}
