#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Toggle floating for the focused Sway container.

Containers in the ignore set are skipped unless --force is passed.
Explicitly disabling floating on a sticky container will also disable
sticky. By default, the keybinding mode is left to a helper script for
updaing; pass --force-keybinging-mode to set it immediately.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to toggle floating for.
"""
from config import IGNORE_FLOATING, FLOATING_ENABLE, FLOATING_DISABLE, STICKY_DISABLE
from utils import get_focused, is_ignored, run_command
from argparse import ArgumentParser
from i3ipc import Connection
from sys import exit


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--disable',
        action='store_true',
        help='Disable floating explicitly.'
    )
    group.add_argument(
        '-e', '--enable',
        action='store_true',
        help='Enable floating explicitly.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Forcibly toggle floating, even if the container is ignored.'
    )
    parser.add_argument(
        '-k', '--force-keybinding-mode',
        action='store_true',
        help='Set the keybinding mode now instead of relying on a helper.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = get_focused(conn)

    # don't operate on some containers
    if (is_ignored(con, IGNORE_FLOATING) and not args.force) or con.type not in {'con','floating_con'}:
        exit(1)

    # determine operation
    if args.enable:
        cmd = FLOATING_ENABLE
    elif args.disable:
        if con.sticky:
            cmd = f'{STICKY_DISABLE}, {FLOATING_DISABLE}'
        else:
            cmd = FLOATING_DISABLE
    else:
        if con.type == 'floating_con' and not con.sticky:
            cmd = FLOATING_DISABLE
        else:
            cmd = FLOATING_ENABLE
    
    # optionally set the keybinding mode now
    if args.force_keybinding_mode:
        if FLOATING_ENABLE in cmd:
            cmd = f'{cmd}; mode [F]'
        elif FLOATING_DISABLE in cmd:
            cmd = f'{cmd}; mode default'

    # run command and exit
    exit(0 if run_command(conn=conn, command=cmd) else 1)
