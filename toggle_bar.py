#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Toggle a Waybar bar and adjust floating container positions.

When a bar is enabled, floating containers that overlap the bar zone
are moved inward to prevent them from obscuring the bar. When a bar is
disabled, floating containers that are flush or overlapping with (but
not exceeding) the bar boundary are moved outward to fill new space.

Note:
    The bar is toggled globally (on all workspaces/outputs).
    Vertical bar support is untested.
    The shebang may need updating to match your virtual environment.

Todo:
    This might be possible with SIGUSR1 per bar (see `man waybar`).
    Test with vertical bars and monitor layouts (likely more code).
"""
from argparse import ArgumentParser
from config import BAR_DEFAULT_SIZE, BAR_DISABLE, BAR_ENABLE, BAR_IDS, OPPOSITE_EDGES
from i3ipc import Connection
from models import Container, Workspace
from utils import run_command


def overlap(bar: str, con: object, output: object, opposite_bar_size: int, bar_size: int) -> int:
    """Calculate overlap between container and a bar."""
    return (getattr(output, bar)-getattr(con, bar)-opposite_bar_size)+bar_size

def enable(bar: str, bar_id: str, workspace: object) -> bool:
    """Enable a bar."""
    if run_command(conn=conn, command=f'{BAR_ENABLE} {bar_id}'):
        opposite_bar_size = getattr(workspace, f'bar_{OPPOSITE_EDGES[bar]}')
        all_floating_cons = [Container(conn=conn, container=c) for c in conn.get_tree().descendants() if c.type in {'floating_con'}]
        containers = [c for c in all_floating_cons if (BAR_DEFAULT_SIZE-overlap(bar, c, c.output(), opposite_bar_size, bar_size)) > 0]
        if containers:
            cmd = ''
            for c in containers:
                cmd += f'[con_id={c.id}] move up {BAR_DEFAULT_SIZE-overlap(bar, c, c.output(), opposite_bar_size, bar_size)} px; '
            return run_command(conn, cmd)
    return False

def disable(bar: str, bar_id: str, workspace: object) -> bool:
    """Disable a bar."""
    if run_command(conn=conn, command=f'{BAR_DISABLE} {bar_id}'):
        # opposite_bar_size is doubled because the container's edge position factors it in automatically
        opposite_bar_size = 2*getattr(workspace, f'bar_{OPPOSITE_EDGES[bar]}')
        all_floating_cons = [Container(conn=conn, container=c) for c in conn.get_tree().descendants() if c.type in {'floating_con'}]
        containers = [c for c in all_floating_cons if (0 < overlap(bar, c, c.output(), opposite_bar_size, bar_size) <= bar_size)]
        if containers:
            cmd = ''
            for c in containers:
                cmd += f'[con_id={c.id}] move down {overlap(bar, c, c.output(), opposite_bar_size, bar_size)} px; '
            return run_command(conn, cmd)
    return False


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        'bar',
        type=str,
        choices=['top','bottom','left','right'],
        default='bottom',
        help='The bar that should be enabled or disabled.'
    )
    group.add_argument(
        '-d', '--disable',
        action='store_true',
        help='Disable the bar explicitly.'
    )
    group.add_argument(
        '-e', '--enable',
        action='store_true',
        help='Enable the bar explicitly.'
    )
    args = parser.parse_args()
    conn = Connection()
    workspace = Workspace(conn=conn)
    bar_id = BAR_IDS[args.bar]
    bar_size = getattr(workspace, f'bar_{args.bar}')
    result = None
    
    # determine operation
    if args.enable:
        result = enable(args.bar, bar_id, workspace)
    elif args.disable:
        result = disable(args.bar, bar_id, workspace)
    else:
        if bar_size > 0:
            result = disable(args.bar, bar_id, workspace)
        else:
            result = enable(args.bar, bar_id, workspace)

    # exit with the correct code
    exit(0 if result else 1)