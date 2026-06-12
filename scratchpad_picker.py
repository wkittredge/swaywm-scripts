#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Show a scratchpad container selected from a menu.

Presents a list of scratchpad containers formatted as 'id: app (pid)'
with a menu program. More recently minimized containers appear at the
top by default, and containers marked as ignored are excluded unless
--all is passed.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to bypass the menu.
"""
from argparse import ArgumentParser
from config import IGNORE_SCRATCHPAD, MENU_PROGRAM, MENU_ARGS_SCRATCHPAD
from i3ipc import Connection
from sys import exit
from utils import is_ignored, get_menu_selection, run_command


def get_app_name(con: object) -> str:
    """Return the name of a container's application, if it exists."""
    if con.app_id:
        return con.app_id
    elif con.window_class:
        return con.window_class
    else:
        return '[NONE]'

def get_con_id(selection: str) -> str:
    """Extract the container ID from a menu selection."""
    con_id = selection[:selection.find(':')]
    return con_id


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Include all containers in the selection list, even if the mark or app_id is ignored.'
    )
    parser.add_argument(
        '-r', '--reverse-order',
        action='store_true',
        help='Show older containers at the top of the menu instead of newer ones.'
    )
    args = parser.parse_args()
    conn = Connection()

    # get containers from the scratchpad
    scratchpad = conn.get_tree().scratchpad().floating_nodes
    if args.all:
        cons = [f'{con.id}: {get_app_name(con)} (pid {con.pid})' for con in scratchpad]
    else:
        cons = [f'{con.id}: {get_app_name(con)} (pid {con.pid})' for con in scratchpad if not is_ignored(con, IGNORE_SCRATCHPAD)]

    # unless --reverse-order is enabled, then reverse the list so that more recently minimized containers appear first
    if not args.reverse_order:
        cons = list(reversed(cons))

    # get a selection from the menu
    selection = None
    if len(cons) > 1:
        selection = get_menu_selection(menu_program=MENU_PROGRAM, menu_args=MENU_ARGS_SCRATCHPAD, selection_options=cons)
    elif cons:
        selection = cons[0]

    # run command and exit
    exit(0 if selection and run_command(conn=conn, command=f'[con_id={get_con_id(selection)}] scratchpad show') else 1)
