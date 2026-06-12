# swaywm-scripts

A collection of personal scripts to ease the use of [Sway window manager](https://github.com/swaywm/sway). Depends on [i3ipc-python](https://github.com/altdesktop/i3ipc-python) to interact with the [IPC interface](https://i3wm.org/docs/ipc.html).

I use most of these scripts every day as part of my Sway window manager workflow and configuration (full dotfiles coming later). They're under continuous development as I find ways to optimize and improve the existing code or implement new features as the ideas come to me.

# Usage

See the table below for a summary of the use case for each script. Use run each script with `--help` to get more information about the options from argparse. More details are also available in source code docstrings and comments.

| Script | Description |
| --- | --- |
| `config.py` | Constants used in other scripts. Not intended to be executed. |
| `models.py` | Wrapper classes for output, workspace, and window containers. Not intended to be executed. |
| `utils.py` | Functions used in other scripts. Not intended to be executed. |
| `focus_ws.py` | Focus a workspace number. Automatically shifts the targeted workspace by an amount when attempting to focus the current workspace. |
| `mark_opacity.py` | [Mark/unmark](https://i3wm.org/docs/userguide.html#vim_like_marks) a window as having manually controlled opacity to exempt it from being managed by the `watcher.py` script. |
| `move_con.py` | Allows for moving floating windows as if they were tiling by confining them to workspace edges. Also performs intelligent resize mode switching. |
| `move_ws.py` | Move the focused window/workspace container to a new workspace. Attempts to retain the position of floating windows on the new workspace. |
| `resize_compass.py` | Activates an appropriate [resize](https://i3wm.org/docs/userguide.html#resizingconfig) binding mode based on window and output geometry. |
| `resize_con.py` | Allows for resizing floating windows as if they were tiling by confining them to workspace edges. Also performs intelligent resize mode switching. |
| `scratchpad_picker.py` | Display a menu to pick "minimized" windows from the [scratchpad](https://i3wm.org/docs/userguide.html#_scratchpad). |
| `snap_position.py` | "Snap" the focused container to a screen corner or edge (implies floating). Allows mirroring the position to an adjacent output. |
| `toggle_bar.py` | Intelligently toggle a bar's [display mode](https://i3wm.org/docs/userguide.html#_display_mode) and account for floating window overlap. |
| `toggle_floating.py` | Intelligently toggle [floating](https://i3wm.org/docs/userguide.html#_floating) for the focused window. |
| `toggle_sticky.py` | Intelligently toggle [sticky](https://i3wm.org/docs/userguide.html#_sticky_floating_windows) (implies floating) for the focused window. |
| `watcher.py` | Watch for IPC events in the background to automatically manage [binding modes](https://i3wm.org/docs/userguide.html#binding_modes) and floating container opacity. |

## Screenshot

![Sway window manager screenshot.](https://i.imgur.com/Aiotvsh.png)

To give a few examples of what these scripts do for me in the above screenshot:
- `watcher.py` detects that the focused window is floating, and automatically sets the **[F]** binding mode.
- `watcher.py` sees that the `grep` terminal should have automatically controlled opacity, and dims it when not focused.
- `snap_position.py` automatically makes the `tail` terminal floating and positions it in the bottom-right when commanded.
- `toggle-bar.py` enabled made the bottom bar visible and moved the `tail` terminal up to avoid overlap.
- Recent commands from `focus_ws.py` and `move_ws.py` were executed and logged while moving workspaces and containers around.
- `resize_compass.py` determined that the `tail` terminal should grow from/shrink towards the bottom-right corner when I resized it.

# Installation

Feel free to use a different installation method if you want—this is just what I do. You should be fine as long as the scripts are executable, have access to `i3ipc-python`, and are keybound in your Sway configuration.

**NOTE:** A patch must be applied to `i3ipc-python` (see [pull request](https://github.com/altdesktop/i3ipc-python/pull/200)) to support the [GET_BINDING_STATE](https://i3wm.org/docs/ipc.html#_binding_state_reply) message. This is used by scripts to get the name of the currently active binding mode. You can import `get_binding_mode()` from `utils` instead if you don't want to rely on the patch, but any calls to `conn.get_binding_state()` will need to be replaced first as they currently aren't guarded with try-except blocks.

The shebang at the start of each script is `#!/home/will/.config/sway/scripts/venv/bin/python3`, so **the easiest way to get things working will probably be something like this:**
```
# make directory and cd
mkdir -p ~/.config/sway/scripts/ && cd "$_"

# create and activate the virtual environment
python3 -m venv ./venv
source ./venv/bin/activate

# install i3ipc-python, patch, then deactivate the virtual environment
pip3 install i3ipc
curl -L https://patch-diff.githubusercontent.com/raw/altdesktop/i3ipc-python/pull/200.patch | patch -p1 -d venv/lib/python*/site-packages/
deactivate

# clone the repositry
git clone https://github.com/wkittredge/swaywm-scripts.git .

# modify the shebangs (be careful if there are other files in the directory)
sed -i '1s|#!/home/[^/]*/|#!'"$HOME"'/|' *.py
```

At this point, you should be able to bind the scripts in your Sway config (remember to reload).

## Example Bindings

See below for some examples of a few bindings that I use. They've been modified to *not* use variables for easier copy-pasting, but I would recommend doing something like the following to make configuration more manageable:
```
set $mod <modifier-key>
set $scripts <path-to-scripts>
set $focusws $scripts/focus_ws.py --shift 10
...

bindsym --no-repeat $mod+1 exec $focusws 1
...
```

Examples:
```
# focus a workspace number
bindsym --no-repeat Mod4+1 exec focus_ws.py 1 --shift 10

# control focused window opacity
bindsym Mod4+bracketleft  opacity minus 0.1; exec mark_opacity.py --manual
bindsym Mod4+bracketright opacity plus 0.1;  exec mark_opacity.py --manual
bindsym Mod4+backslash    opacity set 1;     exec mark_opacity.py --auto

# move focused window
bindsym Mod4+Shift+h exec move_con.py left  80 px --enclose
bindsym Mod4+Shift+j exec move_con.py down  80 px --enclose
bindsym Mod4+Shift+k exec move_con.py up    80 px --enclose
bindsym Mod4+Shift+l exec move_con.py right 80 px --enclose

# move focused window to another workspace
bindsym --no-repeat Mod4+Shift+1 exec move_ws.py 1 --follow

# set a resize mode
bindsym Mod4+r exec resize_compass.py

# resize focused window (for quadrant 1—different modes/bindings are needed for each quadrant)
bindsym Shift+h exec resize_con.py grow   left 80 px --enclose
bindsym Shift+j exec resize_con.py grow   down 80 px --enclose
bindsym Shift+k exec resize_con.py shrink down 80 px --enclose
bindsym Shift+l exec resize_con.py shrink left 80 px --enclose

# summon scratchpad picker menu
bindsym Mod4+Shift+n exec scratchpad_picker.py --all

# snap focused window to position
bindsym --no-repeat Mod4+KP_Right exec snap_position.py right

# toggle bottom bar
bindsym Mod4+Mod1+o exec toggle_bar.py bottom

# toggle floating for focused window
bindsym Mod4+f exec toggle_floating.py

# toggle sticky for focused window
bindsym Mod4+p exec toggle_sticky.py
bindsym Mod4+Shift+p exec toggle_sticky.py --disable
```