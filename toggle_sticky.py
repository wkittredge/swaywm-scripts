#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Toggle sticky for the focused Sway container.

When toggling or enabling sticky, a container is first made floating
(sticky only applies to floating containers). Use --enable and --disable
to bypass toggle logic and set the state directly. Certain containers
are skipped by default unless --force is passed, and the _quake terminal
always receives a hidden title.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to toggle sticky for.
    Allow forcing the floating toggle.
"""
from argparse import ArgumentParser
from config import IGNORE_STICKY, IGNORE_FLOATING, STICKY_ENABLE, FLOATING_ENABLE, STICKY_DISABLE, FLOATING_DISABLE, TITLE_DISABLE
from i3ipc import Connection
from utils import get_focused, is_ignored, run_command


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--disable',
        action='store_true',
        help='Disable sticky explicitly.'
    )
    group.add_argument(
        '-e', '--enable',
        action='store_true',
        help='Enable sticky explicitly.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Forcibly toggle sticky, even if the container is ignored.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = get_focused(conn)

    # don't operate on some containers
    if (is_ignored(con, IGNORE_STICKY) and not args.force) or con.type not in {'con','floating_con'}:
        exit(1)

    # determine floating status
    floating = con.type == 'floating_con'
    allow_floating_toggle = not is_ignored(con, IGNORE_FLOATING)
    
    # determine operation
    if args.enable:
        cmd = STICKY_ENABLE
    elif args.disable:
        if con.sticky and floating and allow_floating_toggle:
            cmd = f'{FLOATING_DISABLE}, {STICKY_DISABLE}'
        elif con.sticky and floating:
            cmd = f'{STICKY_DISABLE}, {TITLE_DISABLE}'
        else:
            cmd = STICKY_DISABLE
    else:
        if con.sticky:
            cmd = STICKY_DISABLE
        elif allow_floating_toggle and not floating:
            cmd = f'{FLOATING_ENABLE}, {STICKY_ENABLE}'
        else:
            cmd = STICKY_ENABLE

    # don't ever show the title for sticky _quake terminal
    if con.app_id == '_quake':
        cmd = f'{cmd}, {TITLE_DISABLE}'

    # run command and exit
    exit(0 if run_command(conn=conn, command=cmd) else 1)
