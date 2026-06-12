#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Control automatic opacity management for the focused Sway container.

By default, floating container opacity is managed automatically by
the watcher. Passing --manual marks the container to opt out of these
changes, while --auto removes the mark to restore automatic opacity
management. Containers in the ignore set are skipped unless --force
is passed.

Note:
    Manual operations (plus/minus/set) are keybound, not IPC controlled.
    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to manage opacity for.
"""
from argparse import ArgumentParser
from config import IGNORE_OPACITY
from i3ipc import Connection
from sys import exit
from utils import get_focused_container, is_ignored, is_marked, run_command


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-a', '--auto',
        action='store_true',
        help='Unmark the container as having manually controlled opacity.'
    )
    group.add_argument(
        '-m', '--manual',
        action='store_true',
        help='Mark the container as having manually controlled opacity.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Forcibly manage opacity, even if the container is ignored.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = get_focused_container(conn)

    # don't operate on some containers
    if is_ignored(con, IGNORE_OPACITY) and not args.force:
        exit(1)

    # set/remove an "opacity mark" for the focused container
    # marked containers will not have their opacity adjusted by the watcher
    if args.manual:
        cmd = f'mark --add _o_{con.id}'
    elif args.auto and is_marked(con, f'_o_{con.id}'):
        cmd = f'unmark _o_{con.id}'

    # run command and exit
    exit(0 if run_command(conn=conn, command=cmd) else 1)
