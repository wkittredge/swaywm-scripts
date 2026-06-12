#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Background watcher for firing automatic Sway commands.

Listens for IPC events and updates the active keybinding mode to match
the focused container. For example, focusing a floating container
switches to floating mode, and focusing a tiling container restores the
default mode.

Also manages the opacity of floating conatiners by dimming them when a
tiling container is focused. Focusing a floating container will restore
its opacity while dimming other floating containers. Manually changing
the opacity of a floating container will exempt it from this behavior
unless the opacity is reset.

Note:
    The shebang may need updating to match your virtual environment.

Todo:
    Improve logic for handlers.
    Prevent multiple handlers from firing within a time period?
"""
from config import IGNORE_MODES, IGNORE_OPACITY, OPACITY_AUTO_DIM, OPACITY_AUTO_RESTORE, RESIZE_MODES
from i3ipc import Connection
from models import Container
from utils import build_command, get_focused, is_ignored, is_marked, run_command


def update_opacity(conn) -> bool:
    """Intelligently set the opacity of floating windows."""
    con = Container(conn=conn)
    containers = [c for c in con.neighbors() if c.floating and not is_ignored(c, IGNORE_OPACITY) and not is_marked(c, f'_o_{c.id}')]

    cmd = build_command(command=OPACITY_AUTO_DIM, containers=containers)
    if con.floating and not is_ignored(con, IGNORE_OPACITY) and not is_marked(con, f'_o_{con.id}'):
        restore = f'[con_id={con.id}] {OPACITY_AUTO_RESTORE}'
        cmd = f'{cmd}; {restore}' if cmd else restore

    return run_command(conn=conn, command=cmd)


def set_binding_mode(conn, con, mode) -> bool:
    """Intelligently set the keybinding mode."""
    if con.type in {'con','floating_con'}:
        con = Container(conn=conn, container=con)
        if mode in RESIZE_MODES.values():
            return run_command(conn, f'mode {con.resize_mode()}')
        elif con.floating:
            return run_command(conn, 'mode [F]')
        else:
            return run_command(conn, 'mode default')
    else:
        return run_command(conn, 'mode default')


def update_mode(conn, e) -> bool:
    """Update mode based on the currently focused container."""
    mode = conn.get_binding_state()
    if mode not in IGNORE_MODES:
        con = get_focused(conn)
        return set_binding_mode(conn, con, mode)


def force_update_mode(conn, e) -> bool:
    """Forcibly update mode based on the currently focused container."""
    mode = conn.get_binding_state()
    con = get_focused(conn=conn)
    return set_binding_mode(conn, con, mode)


def handle_workspace_focus(conn, e) -> None:
    """Workspace focus handler."""
    update_mode(conn, e)


def handle_floating_toggle(conn, e) -> None:
    """Window floating toggle handler."""
    update_mode(conn, e)


def handle_window_focus(conn, e) -> None:
    """Window focus handler."""
    update_mode(conn, e)
    update_opacity(conn)


def handle_window_kill(conn, e) -> None:
    """Window kill handler."""
    update_mode(conn, e)


def handle_window_treemove(conn, e) -> None:
    """
    Window move handler.

    This refers to logical position within the tree, not visible position on the screen.
    """
    update_mode(conn, e)


def handle_window_create(conn, e) -> None:
    """Window create handler."""
    pass


def handle_binding(conn, e) -> None:
    """Keybinding handler."""
    pass


def handle_tick(conn, e) -> None:
    """IPC tick handler."""
    force_update_mode(conn, e)


if __name__ == '__main__':
    conn = Connection()
    conn.on('workspace::focus', handle_workspace_focus) # handle workspace focus
    conn.on('window::floating', handle_floating_toggle) # handle window floating state change
    conn.on('window::focus', handle_window_focus)       # handle window focus change
    conn.on('window::close', handle_window_kill)        # handle window close
    conn.on('window::move', handle_window_treemove)     # handle window move in tree
    # conn.on('window::new', handle_window_create)        # handle window create
    # conn.on('binding', handle_modes)                    # handle keybinding
    conn.on('tick', handle_tick)                        # handle IPC tick
    conn.main()
