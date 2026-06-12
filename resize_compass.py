#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Set a Sway keybinding mode for resizing the focused container.

The resize mode is determined by the screen quadrant (Q1=top-right,
Q2=top-left, Q3=bottom-left, Q4=bottom-right) that the container
occupies. This ensures that directional resize keybindings are logical,
with containers always growing towards (and shrinking away from) the far
screen edges.

Note:
    The shebang may need updating to match your virtual environment.
"""
from argparse import ArgumentParser
from config import IGNORE_RESIZE
from i3ipc import Connection
from models import Container
from sys import exit
from utils import is_ignored, run_command, wrap_quadrant


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        '-f','--force',
        action='store_true',
        help='Enable resize mode even if the container mark or app_id is ignored.'
    )
    parser.add_argument(
        '-q', '--quadrant',
        type=int,
        choices=[1,2,3,4],
        default=None,
        help='Used to specifiy a quadrant or with --next and --previous for quadrant wrapping.'
    )
    group.add_argument(
        '-n', '--next',
        action='store_true',
        help='Cycle to the next quadrant\'s mode if a quadrant is provided.'
    )
    group.add_argument(
        '-p', '--previous',
        action='store_true',
        help='Cycle to the previous quadrant\'s mode if a quadrant is provided.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = Container(conn=conn)

    # don't operate on some containers
    # usually these containers will resize fine when tiling
    if con.floating and is_ignored(con, IGNORE_RESIZE) and not args.force:
        exit(1)

    # do resize mode cycling
    if (args.next or args.previous) and args.quadrant:
        if args.next:
            operation = 'next'
        elif args.previous:
            operation = 'previous'
        args.quadrant = wrap_quadrant(args.quadrant, operation)

    # run command and exit
    exit(0 if run_command(conn=conn, command=f'mode {con.resize_mode(args.quadrant)}') else 1)
