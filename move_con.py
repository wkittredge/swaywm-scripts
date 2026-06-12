#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Move the focused Sway container in a given direction.

For floating containers, movement can be clamped to keep the container
within the usable screen area, and the container can be moved to an
adjacent output when it reaches the edge. The active resize keybinding
mode is updated after movement when --set-resize-mode is passed,
wrapping to the appropriate quadrant when a workspace edge is reached.
Tiling containers are passed through to Sway directly.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to move.
"""
from argparse import ArgumentParser
from i3ipc import Connection
from models import Container
from sys import exit
from utils import ppt_to_px, run_command, wrap_quadrant


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'direction',
        type=str,
        choices=['left','down','up','right'],
        help='The direction to move the container in.'
    )
    parser.add_argument(
        'amount',
        type=int,
        help='The amount of pixels or percentage points to move the container.'
    )
    parser.add_argument(
        'unit',
        type=str,
        choices=['px','ppt'],
        default='px',
        help='Whether the container is moved in pixels or percentage points.'
    )
    parser.add_argument(
        '-e', '--enclose',
        action='store_true',
        help='Automatically adjust movement amount to keep the container within screen edges.'
    )
    parser.add_argument(
        '-m', '--max',
        action='store_true',
        help='Move the container the maximum enclosed amount in the given direction.'
    )
    parser.add_argument(
        # only used with --set-resize-mode
        '-q', '--quadrant',
        type=int,
        choices=[1,2,3,4],
        default=None,
        help='Used to inform the script of the original resize mode to enable quadrant wrapping.'
    )
    parser.add_argument(
        '-r', '--set-resize-mode',
        action='store_true',
        help='Enable resize keybinding mode after moving the container.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = Container()
    results = []

    # if the container is floating, then we might need to modify the command
    if con.floating:

        # convert percentage points to px
        if args.unit == 'ppt':
            args.amount = ppt_to_px(args.amount, args.direction, con)
            args.unit = 'px'
        
        # we might need to modify the movement amount
        if args.max:
            args.amount = max(0, con.dist_to_side(args.direction))
        elif args.enclose:
            args.amount = min(args.amount, con.dist_to_side(args.direction))
        
        # move the container, or try wrapping to another output
        if args.amount != 0:
            results.append(run_command(conn, f'move {args.direction} {args.amount} {args.unit}'))
        elif (con.dist_to_side(args.direction) == 0) and not args.set_resize_mode:
            new_output = con.output().select(args.direction)
            if new_output is not None:
                x, y = con.new_position(new_output, args.direction)
                results.append(run_command(conn=conn, command=f'[con_id="{con.id}"] move to output {new_output.name}, focus, move position {x} {y}'))

        # set an appropriate resize mode
        if args.set_resize_mode:
            con.sync()
            if not con.is_max_size(args.direction):
                args.quadrant = None
            else:
                args.quadrant = wrap_quadrant(args.quadrant, args.direction)
            results.append(run_command(conn=conn, command=f'mode {con.resize_mode(args.quadrant)}'))

    # if the container is tiling, then pass the command through as-is
    else:
        results.append(run_command(conn=conn, command=f'move {args.direction} {args.amount} {args.unit}'))

        if args.set_resize_mode and (args.quadrant is None):
            results.append(run_command(conn=conn, command=f'mode {con.resize_mode()}'))

    # exit with the correct code
    exit(0 if all(results) else 1)
