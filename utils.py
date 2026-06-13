#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Utility functions for Sway IPC scripting.

Provides helpers for querying focused Sway objects, running and logging
IPC commands, and getting user input via a menu program.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Improve logic for run_command().
    Allow clamping values for shift() that leave the min/max range.
"""
from config import HORIZONTAL, MAX_WS, MIN_WS, SHIFT_WS, SWAY_SCRIPTS_LOG, VERTICAL, WRAP_QUADRANTS
from datetime import datetime
from glob import glob
from json import loads
from os import path
from re import findall, MULTILINE, split
from subprocess import CalledProcessError, run
from sys import argv


def search_config(conn: object, regex: str) -> list:
    """Recursively search Sway config(s) for regex matches."""
    config = conn.get_config().config
    visited = set()
    
    def expand_path(_path: str) -> str:
        return path.expandvars(path.expanduser(_path.strip()))
    
    def search(text: str):
        matches = findall(regex, text, MULTILINE)
        for include in findall(r'^include\s+(.+)$', text, MULTILINE):
            for _path in glob(expand_path(include)):
                if _path not in visited:
                    visited.add(_path)
                    with open(_path, 'r') as f:
                        matches += search(f.read())
        return matches

    return search(config)

def get_focused(conn: object) -> object:
    """Return the lowest focused object, whatever it is."""
    focused = conn.get_tree().find_focused()
    while True:
        _focused = focused.find_focused()
        if _focused is not None:
            focused = _focused
            continue
        else:
            break
    return focused

def get_focused_output(conn: object, outputs: list[object]=None) -> object:
    """Return the focused output from a GET_OUTPUTS message."""
    if outputs is None:
        outputs = conn.get_outputs()
    for output in filter(lambda o: o.active, outputs):
        if output.focused:
            return output
    return None

def get_focused_workspace(conn: object, workspaces: list[object]=None) -> object:
    """Return the focused workspace from a GET_WORKSPACES message."""
    if workspaces is None:
        workspaces = conn.get_workspaces()
    for workspace in workspaces:
        if workspace.focused:
            return workspace
    return None

def get_focused_container(conn: object, containers: list[object]=None) -> object:
    """Return the focused container from a GET_TREE message."""
    if containers is None:
        containers = [c for c in conn.get_tree().descendants() if c.type in {'con','floating_con'}]
    for container in containers:
        if container.focused:
            return container
    return None

def ppt_to_px(amount: int, direction: str, basis: object) -> int:
    """Convert percentage points to pixels."""
    basis_size = basis.width if direction in HORIZONTAL else basis.height
    return int(amount * basis_size / 100)

def wrap_quadrant(quadrant: int, operation: str) -> int:
    """Return quadrant numbers depending on operation."""
    if operation in HORIZONTAL:
        method = 'horizontal'
    elif operation in VERTICAL:
        method = 'vertical'
    else:
        method = operation
    return WRAP_QUADRANTS[method][quadrant]

def get_binding_mode() -> str:
    """
    Get the current keybinding mode using swaymsg.

    This should only be used as a backup for unpatched i3ipc-python
    without GET_BINDING_STATE implemented. If available, just use
    Connection().get_binding_state() instead of this.
    See https://i3wm.org/docs/ipc.html and
    https://github.com/altdesktop/i3ipc-python/pull/200 for details.
    """
    result = run(['swaymsg', '-t', 'get_binding_state'], capture_output=True, text=True)
    return loads(result.stdout).get('name', '')

def shift(current_workspace: int, target_workspace: int, shift: int=SHIFT_WS, min_workspace: int=MIN_WS, max_workspace: int=MAX_WS) -> int:
    """Try shifting workspace numbers by an amount."""
    if (current_workspace == target_workspace) and (current_workspace+shift <= max_workspace):
        return current_workspace+shift
    elif (current_workspace == target_workspace) and (current_workspace-shift >= min_workspace):
        return current_workspace-shift
    return target_workspace

def is_marked(con: object, mark: str):
    """Return true if a container has a given mark."""
    return any(m == mark for m in con.marks)

def is_ignored(con: object, ignored: set) -> bool:
    """Return True if a container is in an ignored set."""
    return con.app_id in ignored or con.window_class in ignored or any(mark in ignored for mark in con.marks)

def build_menu_options(selection_options: list=None) -> str:
    """Return a single string of newline-separated items from a list."""
    if selection_options is None:
        selection_options = []
    return '\n'.join([str(item) for item in selection_options])

def get_menu_selection(menu_program: str, menu_args: list=None, selection_options: list=None, no_selection_return: str='') -> str:
    """Return the user's selection from a menu of options."""
    if menu_args is None:
        menu_args = []
    options = build_menu_options(selection_options)
    cmd = [menu_program] + menu_args
    try:
        result = run(cmd, input=options, capture_output=True, text=True, check=True)
        return result.stdout.strip() or no_selection_return
    except CalledProcessError:
        return no_selection_return

def get_integer_input(menu_program: str, menu_args: list=None, selection_options: list=None, no_selection_return: int=None, max_attempts: int=None) -> int:
    """Wrapper for get_menu_selection() to get integer input."""
    if menu_args is None:
        menu_args = []
    max_attempts_text = '󰛤' if max_attempts is None else str(max_attempts)
    attempts = 0
    while ((max_attempts is None) or (attempts < max_attempts)):
        try:
            uinput = get_menu_selection(menu_program=menu_program, selection_options=selection_options, menu_args=menu_args)
            if not uinput:
                return no_selection_return
            else:
                return int(uinput) #return abs(int(uinput))
        except ValueError as error:
            invalid_input = str(error)[40:].strip("'")
            run(['notify-send', 'ERROR: "{}" is not an integer (attempt {} of {})'.format(invalid_input, attempts+1, max_attempts_text)])
            continue
        except Exception:
            run(['notify-send', 'ERROR: something went wrong, try again (attempt {} of {})'.format(attempts+1, max_attempts_text)])
            continue
        finally:
            attempts += 1
    return no_selection_return

def build_command(command: str, containers: list[object]=None) -> str:
    """
    Build a single compound IPC command targeting multiple containers.

    Batching commands into a single IPC call is significantly faster
    than issuing a call for every operation you want to make. This
    expects each container to receive an identical command.
    """
    if containers is None:
        return command
    return '; '.join(i for i in list(map(lambda c: f'[con_id={str(c.id)}] {command}', containers)))

def write_log(message: str, log_file: str=SWAY_SCRIPTS_LOG):
    """Append a message (and the originating filename) to the log."""
    with open(log_file, 'a') as f: f.write(f'[{path.basename(argv[0])}] {message}')

def run_command(conn: object, command: str, notify: bool=True, log: bool=False, debug: bool=False) -> bool:
    """Execute a command and check the results."""
    start_time = datetime.now()
    command_results = conn.command(command)
    processing_time = (datetime.now()-start_time).total_seconds()
    subcommands = [subcommand.strip() for subcommand in split(r'[;,]+(?![;,]$)', command)]
    del subcommands[len(command_results):]

    # if a single command (or all subcommands) succeeded
    if all(result.success for result in command_results):
        if log or debug:
            write_log(f'{start_time} [  OK  ] command "{command}" executed in {processing_time}s\n')
        if debug:
            run(['notify-send', 'COMMAND SUCCEEDED: "{}"'.format(command)])
            if len(command_results) == 1:
                write_log(f'{start_time} [ INFO ] command "{command}" returned IPC data: "{command_results[0].ipc_data}"\n')
            else:
                [write_log(f'{start_time} [ INFO ] subcommand {i+1} of command "{command}" ("{subcommands[i]}") returned IPC data: "{result.ipc_data}"\n') for i, result in enumerate(command_results)]
        return True
    
    # if a single command failed
    elif len(command_results) == len(subcommands) == 1:
        if notify or debug:
            run(['notify-send', 'COMMAND FAILED: "{}"'.format(command)])
        if log or debug:
            write_log(f'{start_time} [ FAIL ] command "{command}" failed with error: "{command_results[0].error}" in {processing_time}s\n')
        if debug:
            write_log(f'{start_time} [ INFO ] command "{command}" returned IPC data: "{command_results[0].ipc_data}"\n')
        return False
    
    # if any subcommand failed
    # replies are not returned after the first error, so we know that the last reply is the fail
    else:
        if notify or debug:
            run(['notify-send', 'COMMAND WARNING: "{}"'.format(command)])
        if log or debug:
            write_log(f'{start_time} [ WARN ] command "{command}" generated error and stopped execution at subcommand {len(subcommands)} ("{subcommands[-1]}") in {processing_time}s\n')
        for i, result in enumerate(command_results):
            if result.success:
                if log:
                    write_log(f'{start_time} [ INFO ] subcommand {i+1} of command "{command}" ("{subcommands[i]}") succeeded\n')
                if debug:
                    write_log(f'{start_time} [ INFO ] subcommand {i+1} of command "{command}" ("{subcommands[i]}") returned IPC data: "{result.ipc_data}"\n')
                continue
            else:
                if log:
                    write_log(f'{start_time} [ INFO ] subcommand {i+1} of command "{command}" ("{subcommands[i]}") failed with error: "{result.error}"\n')
                if debug:
                    write_log(f'{start_time} [ INFO ] subcommand {i+1} of command "{command}" ("{subcommands[i]}") returned IPC data: "{result.ipc_data}"\n')
                continue
        return False


if __name__ == '__main__': pass
