#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Resize the focused Sway container with optional screen edge clamping.

For floating containers, the resize amount can be clamped to keep the
container within the usable screen area (i.e., excluding bars). The
keybinding mode is automatically updated when a screen edge is reached.
Tiling containers are resized by passing the command through directly to
Sway IPC.

Notes:
    Tiling containers may raise 'Error: Cannot resize any further
    in some cases due to what appaers to be a Sway or i3-compat issue.
    Notifications are currently suppressed as a workaround.

    The shebang may need updating to match your virtual environment.

Todo:
    Fix 'Error: Cannot resize any further' (see comments).
"""
from argparse import ArgumentParser
from i3ipc import Connection
from models import Container
from sys import exit
from utils import ppt_to_px, run_command


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'operation',
        type=str,
        choices=['grow','shrink'],
        help='Whether the container is resized to be larger or smaller.'
    )
    parser.add_argument(
        'direction',
        type=str,
        choices=['left','down','up','right'],
        help='The side that the container will resize from.'
    )
    parser.add_argument(
        'amount',
        type=int,
        help='The amount of pixels or percentage points to resize the container.'
    )
    parser.add_argument(
        'unit',
        type=str,
        choices=['px','ppt'],
        default='px',
        help='Whether the container is resized in pixels or percentage points.'
    )
    parser.add_argument(
        '-e', '--enclose',
        action='store_true',
        help='Automatically adjust the resize amount to keep the container within screen edges.'
    )
    parser.add_argument(
        '-m', '--max',
        action='store_true',
        help='Resize the container the maximum enclosed amount in the given direction.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = Container()
    results = []

    # if the container is floating, then we might need to modify the command
    if con.floating:

        # convert percentage points to px
        if args.unit == 'ppt':
            args.amount = ppt_to_px(amount=args.amount, direction=args.direction, basis=con)
            args.unit = 'px'

        # if the container is growing, then we might need to modify the resize amount
        if args.operation == 'grow' and (args.max or args.enclose):
            dist = con.dist_to_side(args.direction)
            if args.max:
                args.amount = max(0, dist)
            elif args.enclose:
                args.amount = min(args.amount, dist)

        # run the command and fetch updated IPC data
        results.append(run_command(conn=conn, command=f'resize {args.operation} {args.direction} {args.amount} {args.unit}', notify=False))
        con.sync()

        # update the resize mode when a screen edge is reached if the container is enclosed
        if con.dist_to_side(args.direction) <= 0 and args.enclose:
            results.append(run_command(conn=conn, command=f'mode {con.resize_mode()}'))
        
    # if the container is tiling, then pass the command through as-is
    else:
        results.append(run_command(conn=conn, command=f'resize {args.operation} {args.direction} {args.amount} {args.unit}', notify=False))

    # Sometimes resizing causes strange behavior, which appears to be related to Sway or the IPC
    # interface itself. It doesn't seem to internally clamp values that are too large, so no resize
    # occurs and "Error: Cannot resize any further" is raised. For example, let there be two
    # side-by-side tiling containers on a workspace (split down the middle). Now try to manually
    # resize the left container with `swaymsg resize grow right 100 ppt` and see the error.

    # This might be an i3-compat issue (see swaywm GitHub), but I can't remember for sure now.
    # Nested containers also report the error, even when a resize *does* actually fire (focus a
    # parent container first to fix?). It would be nice to compensate for this here, but
    # run_command(notify=False) is temporarily easier.

    # exit with the correct code
    exit(0 if all(results) else 1)
