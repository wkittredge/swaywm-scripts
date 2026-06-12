#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Focus a Sway workspace number, optionally shifting when already focused.

When navigating to a workspace that is already focused, --shift offsets
the target workspace number by the given amount to allow workspace
cycling.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Implement workspace focus switching with menu.
    Implement --next and --previous workspace selection.
"""
from argparse import ArgumentParser
from config import MAX_WS, MIN_WS, SHIFT_WS
from i3ipc import Connection
from sys import exit
from utils import get_focused_workspace, run_command, shift


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'workspace',
        type=int,
        choices=range(MIN_WS, MAX_WS+1),
        help='The workspace number that focus will be navigated to.'
    )
    parser.add_argument(
        '-s', '--shift',
        type=int,
        default=SHIFT_WS,
        help='Shift by an amount when attempting to navigate to the current workspace.'
    )
    args = parser.parse_args()
    conn = Connection()

    # handle workspace shifting
    current_workspace = get_focused_workspace(conn)
    args.workspace = shift(current_workspace.num, args.workspace, args.shift, MIN_WS, MAX_WS)
    
    # run command and exit
    exit(0 if run_command(conn=conn, command=f'workspace number {args.workspace}') else 1)