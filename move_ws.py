#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Move the focused container to a new workspace.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Improve follow and focus logic for workspaces and tiling containers.
    Allow specifying a container to move workspaces for.
    Implement workspace moving with menu.
"""
from argparse import ArgumentParser
from config import MAX_WS, MIN_WS, SHIFT_WS
from i3ipc import Connection
from models import Container, Output
from sys import exit
from utils import get_focused, get_focused_workspace, run_command, search_config, shift


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'workspace',
        type=int,
        choices=range(MIN_WS, MAX_WS+1),
        # nargs='?',
        help='The workspace number that the container will be moved to.'
    )
    parser.add_argument(
        '-c', '--center',
        action='store_true',
        help='Move the container to the center of the new workspace.'
    )
    parser.add_argument(
        '-f', '--follow',
        action='store_true',
        help='Follow the container to its new workspace after moving it.'
    )
    parser.add_argument(
        '-s', '--shift',
        type=int,
        default=SHIFT_WS,
        help='Shift by an amount when attempting to move to the current workpsace.'
    )
    args = parser.parse_args()
    conn = Connection()
    obj = get_focused(conn)

    if obj.type == 'workspace' and not obj.nodes:
        exit(1)
    
    # handle workspace shifting
    workspaces = conn.get_workspaces()
    origin_workspace = get_focused_workspace(conn, workspaces)
    args.workspace = shift(origin_workspace.num, args.workspace, args.shift)

    # floating containers need explicit repositioning
    if obj.type == 'floating_con':

        con = Container(conn=conn)
        outputs = conn.get_outputs()
        existing_workspaces = [ws.num for ws in workspaces]

        # find the correct output
        if args.workspace in existing_workspaces:
            ws = next(ws for ws in workspaces if ws.num == args.workspace)
            output = next((Output(conn=conn, output=o) for o in outputs if o.name == ws.output), None)
        else:
            variables = dict(search_config(conn=conn, regex=r'^set\s+(\$\S+)\s+(.+)$'))
            ws_output_map = {
                variables.get(ws, ws): variables.get(output, output)
                for ws, output in search_config(conn=conn, regex=r'^workspace\s+(\S+)\s+output\s+(\S+)$')
            }
            output_name = ws_output_map.get(str(args.workspace))
            output = next((Output(conn=conn, output=o) for o in outputs if o.name == output_name), None)

        if output is None:
            exit(1)

        # sticky containers will raise error:
        # "Can't move sticky container to another workspace on the same output"
        if con.sticky and output.id == con.output().id:
            args.follow = True
            cmd = f'workspace number {args.workspace}; [con_id="{con.id}"] focus'
        else:
            cmd = f'[con_id="{con.id}"] move container to workspace number {args.workspace}, focus'
    
        # position the window correctly
        if args.center or output is None:
            cmd = f'{cmd}, move position center'
        else:
            x, y = con.new_position(output)
            cmd = f'{cmd}, move position {x} {y}'
        
        # unless following, go back to the original workspace
        if not args.follow:
            cmd = f'{cmd}; workspace number {origin_workspace.num}'

    # let Sway handle the position for workspaces and tiling containers
    else:
        cmd = f'move container to workspace number {args.workspace}'

        if args.follow:
            cmd = f'{cmd}; workspace number {args.workspace}'

        # TODO: logic needs to be improved here, there are two(?) issues.

        # Ideally, we want to retain the same focus as before the move.
        # Using f'[con_id="{con.id}"] focus' is the obvious solution, but this will not work
        # when the focused container is a workspace because that ID won't exist after the move.
        # The same problem seems to happen with the built-in [con_id="__focused__"] criteria.
        # (Fails with error: "Criteria is empty").

        # The container that receives focus after moving also appears to depend on things
        # like the layout of the container that was moved and the workspace that it was
        # moved to. The old version of this script checked how many nodes existed and walked
        # focus down and back up with 'focus child' and 'focus parent' commands, but this is feels
        # kind of hacky. There might be a better solution. Maybe container marks could work?

    # run command and exit
    exit(0 if run_command(conn=conn, command=cmd) else 1)