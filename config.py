#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Pseudo config file containing constants used by other scripts.

Note:
    The shebang may need updating to match your virtual environment.
"""
from os import getenv


# set paths
HOME = getenv('HOME')
SWAY_SCRIPTS_LOG = f'{HOME}/.config/sway/log.txt'

# set min and max workspace numbers
MIN_WS = 1
MAX_WS = 20

# try shifting workspaces by this amount when focusing the current one
SHIFT_WS = 10

# default border and bar sizes
BAR_DEFAULT_SIZE = 30
BORDER_DEFAULT_SIZE = 5

# edge tolerance for output selection
OUTPUT_EDGE_TOLERANCE = 2

# set menu options
MENU_PROGRAM = 'rofi'
MENU_ARGS_SCRATCHPAD = ['-dmenu', '-i', '-p', 'SHOW']

# set commands
TITLE_ENABLE = f'border normal {BORDER_DEFAULT_SIZE}'
TITLE_DISABLE = f'border pixel {BORDER_DEFAULT_SIZE}'
FLOATING_ENABLE = f'floating enable, {TITLE_ENABLE}, resize set 30ppt 40ppt, move position center'
FLOATING_DISABLE = 'floating disable'
STICKY_ENABLE = f'sticky enable, title_format "[󰐃] %title", {TITLE_ENABLE}'
STICKY_DISABLE = 'sticky disable, title_format "%title"'
BAR_ENABLE = 'bar mode dock'
BAR_DISABLE = 'bar mode invisible'
OPACITY_AUTO_DIM = 'opacity set 0.2'
OPACITY_AUTO_RESTORE = 'opacity set 1'

# windows that should not be allowed to toggle floating (unless forced)
IGNORE_FLOATING = {
    '_quake',
    'SpeedCrunch',
    'swappy'
}

# windows that should not be allowed to resize when floating (unless forced)
IGNORE_RESIZE = {
    '_quake',
    'SpeedCrunch',
    'swappy'
}

# windows that should not be allowed to toggle sticky (unless forced)
IGNORE_STICKY = {
}

# windows that should not be included in the scratchpad picker (unless forced)
IGNORE_SCRATCHPAD = {
    '_quake',
    'SpeedCrunch'
}

# keybinding modes that the watcher should not automatically switch from (unless forced)
IGNORE_MODES = {
    '[M+]',
    '[=]',
    '[!]',
    '[TESTING]'
}

# windows that the watcher should not automatically adjust opacity for
IGNORE_OPACITY = {
    '_quake',
    'SpeedCrunch'
}

# map sides to bar IDs
BAR_IDS = {
    'top':    'bar-0',
    'bottom': 'bar-1',
    'left':   'bar-2',
    'right':  'bar-3'
}

# map quadrants to resize modes
RESIZE_MODES = {
    1: '[󰁂]',
    2: '[󰁃]',
    3: '[󰁜]',
    4: '[󰁛]'
}

# map quadrants for wrapping
WRAP_QUADRANTS = {
    'horizontal': {1:2, 2:1, 3:4, 4:3},
    'vertical':   {1:4, 2:3, 3:2, 4:1},
    'opposite':   {1:3, 2:4, 3:1, 4:2},
    'next':       {1:2, 2:3, 3:4, 4:1},
    'previous':   {1:4, 4:3, 3:2, 2:1}
}

# normalize directions
DIRECTIONS = {
    'left':   'left',
    'down':   'down',
    'bottom': 'down',
    'up':     'up',
    'top':    'up',
    'right':  'right'
}

# normalize edges
EDGES = {
    'left':   'left',
    'down':   'bottom',
    'bottom': 'bottom',
    'up':     'top',
    'top':    'top',
    'right':  'right'
}

# map edges to opposites
OPPOSITE_EDGES = {
    'left':   'right',
    'down':   'top',
    'bottom': 'top',
    'up':     'bottom',
    'top':    'bottom',
    'right':  'left'
}

# refers to horizontal direction
HORIZONTAL = {
    'horizontal',
    'width',
    'left',
    'right'
}

# refers to vertical direction
VERTICAL = {
    'vertical',
    'height',
    'up',
    'down',
    'top',
    'bottom'
}


if __name__ == '__main__': pass
