#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Snap the focused Sway container to a position on the workspace.

Aceepts a named edge position (top, bottom, left, right) or a quadrant
number (1-4). If the container is already at the target position,
it will be moved to the opposite position on the next output in that
direction. Non-floating containers are made floating before snapping
unless they are in the ignore set.

Note:
    Quadrant snapping currently always assumes horizontal direction. For
    example, in a 2x2 monitor grid layout, snapping to quadrant 1 when
    already at the target position will always try moving to the next
    output horizontally and never vertically.

    The shebang may need updating to match your virtual environment.

Todo:
    Allow specifying a container to snap.
    Improve vertical/hybrid monitor layout support (untested).
    Improve quadrant snapping logic.
"""
from argparse import ArgumentParser
from config import FLOATING_ENABLE, IGNORE_FLOATING
from i3ipc import Connection
from models import Container
from sys import exit
from utils import get_focused_container, is_ignored, run_command


def snap(conn: object, con: object, direction: str, current_pos: str, target_pos: str) -> bool:
    """Snap a container to a new position."""
    if current_pos == target_pos and direction is not None:
        new_output = con.output().select(direction)
        if new_output is None:
            return False
        x, y = con.new_position(new_output, direction)
        return run_command(conn=conn, command=f'[con_id="{con.id}"] move to output {new_output.name}, focus, move position {x} {y}')
    return run_command(conn=conn, command=f'[con_id="{con.id}"] move position {target_pos}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'position',
        type=str,
        choices=['1','2','3','4','top','bottom','left','right','center'],
        help='The screen position that the container is snapped to.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Forcibly toggle floating, even if the container is ignored.'
    )
    args = parser.parse_args()
    conn = Connection()
    con = get_focused_container(conn)
    results = []

    # only operate on containers that are floating (or if we can toggle/force floating)
    if con is None or (con.type == 'con' and (is_ignored(con, IGNORE_FLOATING) and not args.force)):
        exit(1)
    elif con.type == 'con':
        results.append(run_command(conn=conn, command=FLOATING_ENABLE))

    con = Container(conn=conn)
    workspace = con.workspace()

    # layout position values
    center_x = int((workspace.width-con.width) / 2)
    center_y = int((workspace.height-con.height) / 2)
    far_x = workspace.width - con.width
    far_y = workspace.height - con.height

    # determine target position for snapping
    match args.position:
        case '1':
            direction = 'right'
            target_pos = f'{far_x} 0'
        case '2':
            direction = 'left'
            target_pos = '0 0'
        case '3':
            direction = 'left'
            target_pos = f'0 {far_y}'
        case '4':
            direction = 'right'
            target_pos = f'{far_x} {far_y}'
        case 'top':
            direction = 'up'
            target_pos = f'{center_x} 0'
        case 'bottom':
            direction = 'down'
            target_pos = f'{center_x} {far_y}'
        case 'left':
            direction = 'left'
            target_pos = f'0 {center_y}'
        case 'right':
            direction = 'right'
            target_pos = f'{far_x} {center_y}'
        case 'center':
            direction = None
            target_pos = f'{center_x} {center_y}'

    current_pos = f'{con.x} {con.y}'
    results.append(snap(conn, con, direction, current_pos, target_pos))

    # exit with the correct code
    exit(0 if all(results) else 1)