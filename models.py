#!/home/will/.config/sway/scripts/venv/bin/python3
"""
Wrapper classes that make it easier to interact with Sway using IPC.

Todo:
    Alternative constructor classmethods for Output and Workspace.
    Container.quadrant() needs to better account for edge cases.
    Does x/y position logic break for outputs with negative x/y?
"""
from config import HORIZONTAL, OUTPUT_EDGE_TOLERANCE, RESIZE_MODES, VERTICAL
from i3ipc import Connection
from math import dist


class IPC:
    def __init__(self, conn: object=None):
        """
        Base class for establishing an IPC connection with Sway.
        """
        if not conn:
            conn = Connection()
        self._conn = conn


class Output(IPC):
    def __init__(self, output: object=None, conn: object=None):
        """
        Build an output object from an output in the GET_OUTPUTS reply.
        """

        # initialize the IPC connection
        super().__init__(conn)

        # get the focused active output if one wasn't provided
        if not output:
            for o in [o for o in self._conn.get_outputs() if o.active]:
                if o.focused:
                    output = o
                    break

        # the provided output or reply from i3ipc
        self._ipc = output

        # anchoring information
        self.id = output.ipc_data['id']
        self.name = output.ipc_data['name']
        self.layout = output.ipc_data['layout']

        # coordinates and dimensions (absolute and ignoring bars)
        self.x = output.ipc_data['rect']['x']
        self.y = output.ipc_data['rect']['y']
        self.width = output.ipc_data['rect']['width']
        self.height = output.ipc_data['rect']['height']

        # output edges (relative and ignoring bars)
        self.left = 0
        self.top = 0
        self.bottom = self.height
        self.right = self.width

        # vertices (relative and ignoring bars)
        self.v1 = (self.right, self.top)
        self.v2 = (self.left, self.top)
        self.v3 = (self.left, self.bottom)
        self.v4 = (self.right, self.bottom)

        # absolute vertices (absolute and ignoring bars)
        self.absolute_v1 = (self.x+self.width, self.y)
        self.absolute_v2 = (self.x, self.y)
        self.absolute_v3 = (self.x, self.y+self.height)
        self.absolute_v4 = (self.x+self.width, self.y+self.height)


    @classmethod
    def from_tree(self, tree=None, conn=None):
        """
        Alternative constructor to build an output object from an output in the GET_TREE reply.
        """

        # initialize the IPC connection
        super().__init__(conn)
        pass

    def sync(self) -> object:
        """Fetch updated data for this output from the IPC interface."""
        synced = Output(conn=self._conn, output=self._conn.get_tree().find_by_id(self.id))
        self.__dict__.update(synced.__dict__)

    def parent(self) -> object:
        """Return the parent of this output (root container)."""
        return self._conn.get_tree().root()

    def workspaces(self) -> list[object]:
        """Return a list of workspaces on this output as workspace objects."""
        return [Workspace(conn=self._conn, workspace=ws, output=self) for ws in self._conn.get_workspaces() if ws.ipc_data['output'] == self.name]

    def workspace(self) -> object:
        """Return the workspace currently visible on this output as a workspace object."""
        for ws in self._conn.get_workspaces():
            if ws.ipc_data['name'] == self._ipc.ipc_data['current_workspace']:
                return Workspace(conn=self._conn, workspace=ws, output=self)
        return None

    def containers(self) -> list[object]:
        """Return a list of containers on this output as container objects."""
        o = self._conn.get_tree().find_by_id(self.id)
        return [Container(conn=self._conn, container=c) for c in o.descendants() if c.ipc_data['type'] in {'con','floating_con'}]

    def container(self) -> object:
        """Return the currently focused container on this output as a container object."""
        o = self._conn.get_tree().find_by_id(self.id)
        containers = [c for c in o.descendants() if c.ipc_data['type'] in {'con','floating_con'}]
        for c in containers:
            if c.ipc_data['focused']:
                return Container(conn=self._conn, container=c)
        return None

    def neighbors(self) -> list[object]:
        """Return a list of all other outputs in the tree as output objects."""
        return [Output(conn=self._conn, output=o) for o in self._conn.get_outputs() if o.ipc_data['id'] != self.id]
    
    def select(self, direction: str) -> object:
        """Return the output in a given direction."""

        # find overlap between line segments (horizontal or veritcal output spans)
        def overlap(start_a, end_a, start_b, end_b) -> int:
            return max(0, min(end_a,end_b)-max(start_a,start_b))
    
        # get output geometry information
        def get_geometry(o: object) -> tuple:
            match direction:
                case 'right': return (self.x+self.width,  o.x,          self.y, self.y+self.height, o.y, o.y+o.height)
                case 'left':  return (self.x,             o.x+o.width,  self.y, self.y+self.height, o.y, o.y+o.height)
                case 'down':  return (self.y+self.height, o.y,          self.x, self.x+self.width,  o.x, o.x+o.width)
                case 'up':    return (self.y,             o.y+o.height, self.x, self.x+self.width,  o.x, o.x+o.width)
    
        # candidate can be selected if sides meet (within tolerance) and spans overlap
        def is_candidate(o: object) -> bool:
            self_side, cand_side, self_start, self_end, cand_start, cand_end = get_geometry(o)
            return (abs(self_side-cand_side) <= OUTPUT_EDGE_TOLERANCE) and (overlap(self_start, self_end, cand_start, cand_end) > 0)
    
        # find the span overlap between outputs
        def score(o: object) -> int:
            *_, self_start, self_end, o_start, o_end = get_geometry(o)
            return overlap(self_start, self_end, o_start, o_end)

        # return the output with the best score (candidate with most span overlap)
        candidates = [o for o in self.neighbors() if is_candidate(o)]
        if not candidates:
            return None
        return max(candidates, key=score)


class Workspace(IPC):
    def __init__(self, workspace: object=None, conn: object=None, output: object=None):
        """
        Build a workspace object from a workspace in the GET_WORKSPACES reply.
        """

        # initalize the IPC connection
        super().__init__(conn)

        # get the focused workspace from IPC if one wasn't provided
        if not workspace:
            for ws in self._conn.get_workspaces():
                if ws.focused:
                    workspace = ws
                    break

        # get the workspace's output if one wasn't provided
        if not output:
            for o in self._conn.get_outputs():
                if o.ipc_data['name'] == workspace.ipc_data['output']:
                    output = Output(conn=self._conn, output=o)
                    break

        # the provided workspace or reply from i3ipc
        self._ipc = workspace

        # the output of this workspace
        self._Output = output

        # anchoring information
        self.id = workspace.ipc_data['id']
        self.name = workspace.ipc_data['name']
        self.num = workspace.ipc_data['num']
        self.layout = workspace.ipc_data['layout']

        # coordinates and dimensions (absolute and accounting for bars)
        self.x = workspace.ipc_data['rect']['x']
        self.y = workspace.ipc_data['rect']['y']
        self.width = workspace.ipc_data['rect']['width']
        self.height = workspace.ipc_data['rect']['height']

        # bar offsets
        self.bar_left = self.x-self.output().x
        self.bar_top = self.y-self.output().y
        self.bar_right = (self.output().x+self.output().width)-(self.x+self.width)
        self.bar_bottom = (self.output().y+self.output().height)-(self.y+self.height)

        # INFO: self.bottom and self.right reflect the usable workspace dimensions and not
        # absolute screen coordinates. IPC reports the workspace geometry with bar space
        # excluded, and window positions are set relative to the workspace's usable origin.
        # Adding bar offsets would cause misalignment because Sway does not expect them.
    
        # workspace edges (relative and accounting for bars)
        self.left = self.bar_left
        self.top = self.bar_top
        self.bottom = self.height
        self.right = self.width

        # vertices (relative and accounting for bars)
        self.v1 = (self.right, self.top)
        self.v2 = (self.left, self.top)
        self.v3 = (self.left, self.bottom)
        self.v4 = (self.right, self.bottom)

    @classmethod
    def from_tree(self, tree=None, conn=None):
        """
        Alternative constructor to build a workpace object from a workspace in the GET_TREE reply.
        """

        # initialize the IPC connection
        super().__init__(conn)
        pass

    def sync(self) -> object:
        """Fetch updated data for this workspace from the IPC interface."""
        synced = Workspace(conn=self._conn, workspace=self._conn.get_tree().find_by_id(self.id))
        self.__dict__.update(synced.__dict__)

    def parent(self) -> object:
        """Return the parent of this workspace. Effectively an alias for output()."""
        return self.output()

    def output(self) -> object:
        """Return the output that this workspace is on as an output object."""
        return self._Output

    def containers(self) -> list[object]:
        """Return a list of containers on this workspace as container objects."""
        ws = self._conn.get_tree().find_by_id(self.id)
        return [Container(conn=self._conn, container=c) for c in ws.descendants() if c.ipc_data['type'] in {'con','floating_con'}]

    def floating(self) -> list[object]:
        """Return a list of floating containers on this workspace as container objects."""
        return [c for c in self.containers() if c._ipc.ipc_data['type'] == 'floating_con']
    
    def tiling(self) -> list[object]:
        """Return a list of tiling containers on this workspace as container objects."""
        return [c for c in self.containers() if c._ipc.ipc_data['type'] == 'con']

    def container(self) -> object:
        """Return the currently focused container on this workspace as a container object."""
        ws = self._conn.get_tree().find_by_id(self.id)
        containers = [c for c in ws.descendants() if c.ipc_data['type'] in {'con','floating_con'}]
        for c in containers:
            if c.ipc_data['focused']:
                return Container(conn=self._conn, container=c)
        return None


class Container(IPC):
    def __init__(self, container: object=None, conn: object=None, workspace: object=None):
        """
        Build a container object from a container in the GET_TREE reply.
        """

        # initialize the IPC connection
        super().__init__(conn)

        # get the focused container if one wasn't provided
        if not container:
            for c in [c for c in self._conn.get_tree().descendants() if c.type in {'con','floating_con'}]:
                if c.focused:
                    container = c
                    break

        # get the container's workspace if one wasn't provided
        if not workspace:
            workspace = Workspace(conn=self._conn)

        # the provided container or reply from i3ipc
        self._ipc = container

        # the workspace of this container
        self._Workspace = workspace

        # anchoring information
        self.id = container.ipc_data['id']
        self.window_class = container.window_class
        # TODO: some containers don't have ipc_data['app_id']?
        try:
            self.app_id = container.ipc_data['app_id']
        except KeyError:
            self.app_id = container.app_id
        self.name = container.ipc_data['name']
        
        self.marks = container.ipc_data['marks']
        self.layout = container.ipc_data['layout']
        self.sticky = container.ipc_data['sticky']
        self.tiling = True if container.ipc_data['type'] == 'con' else False
        self.floating = not self.tiling

    # TODO: these might not need to be properties now.
    @property
    def absolute_x(self):
        return self._ipc.ipc_data['rect']['x']
    
    @absolute_x.setter
    def absolute_x(self, value: int):
        self._ipc.ipc_data['rect']['x'] = value

    @property
    def absolute_y(self):
        return self._ipc.ipc_data['rect']['y']-self._ipc.ipc_data['deco_rect']['height']
    
    @absolute_y.setter
    def absolute_y(self, value: int):
        self._ipc.ipc_data['rect']['y'] = value+self._ipc.ipc_data['deco_rect']['height']

    @property
    def x(self):
        return self.absolute_x-self.output().x-self.workspace().bar_left
    
    @x.setter
    def x(self, value: int):
        self.absolute_x = value+self.output().x+self.workspace().bar_left
    
    @property
    def y(self):
        return self.absolute_y-self.output().y-self.workspace().bar_top
    
    @y.setter
    def y(self, value: int):
        self.absolute_y = value+self.output().y+self.workspace().bar_top

    @property
    def width(self):
        return self._ipc.ipc_data['rect']['width']
    
    @width.setter
    def width(self, value: int):
        self._ipc.ipc_data['rect']['width'] = value

    @property
    def height(self):
        return self._ipc.ipc_data['rect']['height']+self._ipc.ipc_data['deco_rect']['height']
    
    @height.setter
    def height(self, value: int):
        self._ipc.ipc_data['rect']['height'] = value-self._ipc.ipc_data['deco_rect']['height']

    @property
    def left(self):
        return self.x
    
    @property
    def bottom(self):
        return self.y+self.height
    
    @property
    def top(self):
        return self.y
    
    @property
    def right(self):
        return self.x+self.width

    @property
    def v1(self):
        return (self.right, self.top)
    
    @property
    def v2(self):
        return (self.left, self.top)
    
    @property
    def v3(self):
        return (self.left, self.bottom)
    
    @property
    def v4(self):
        return (self.right, self.bottom)

    def sync(self) -> object:
        """Fetch updated data for this container from the IPC interface."""
        synced = Container(conn=self._conn, container=self._conn.get_tree().find_by_id(self.id))
        self.__dict__.update(synced.__dict__)

    def parent(self) -> object:
        """Return the parent of this container (either another container, or a workspace)."""
        p = self._ipc.parent
        match p.type:
            case 'con' | 'floating_con': return Container(conn=self._conn, container=p)
            case 'workspace':            return Workspace(conn=self._conn, workspace=p)
            case _:                      return None

    def workspace(self) -> object:
        """Return the workspace of this container as a workspace object."""
        return self._Workspace

    def output(self) -> object:
        "Return the output of this container as an output object."
        return self.workspace().output()

    def neighbors(self) -> list[object]:
        """Return a list of other Containers that are on the same workspace as the container object."""
        cons = self.workspace().containers()
        for i, c in enumerate(cons):
            if c.id == self.id: del cons[i]
        return cons

    def quadrant(self) -> int:
        """Return the quadrant number that this container is in."""
        # account for stacked window decorations (cursed)
        if self._ipc.parent.ipc_data['layout'] == 'stacked':
            num_stacked = len(self._ipc.parent.ipc_data['nodes'])
            deco_height = self._ipc.ipc_data['deco_rect']['height'] * (num_stacked-1)
            self.y -= deco_height
            self.height += deco_height

        output = self.output()
        top  = dist(self.v2, output.v2) <= dist(self.v3, output.v3)
        left = dist(self.v2, output.v2) <= dist(self.v1, output.v1)

        match (top, left):
            case (True,  False): return 1
            case (True,  True):  return 2
            case (False, True):  return 3
            case (False, False): return 4
        
    def resize_mode(self, quadrant: int=None) -> str:
        """Return the resize mode for a quadrant."""
        if not quadrant:
            quadrant = self.quadrant()
        return RESIZE_MODES[quadrant]

    def dist_to_side(self, side: str) -> int:
        """Return the distance between a container and workspace side."""
        match side:
            case 'left':  return self.left
            case 'down':  return self.workspace().bottom-self.bottom
            case 'up':    return self.top
            case 'right': return self.workspace().right-self.right

    def new_position(self, output: object, direction: str=None) -> tuple[int, int]:
        """
        Decide a container's position on an output.

        Provide a direction to signal that the container is aligned with
        a workspace edge, and should be mirrored to the neighboring
        edge of the given output.
        """
        current_output = self.output()
        workspace = output.workspace()
        # output.workspace() will not necessarily be the same workspace as the one the
        # container lands on, but this is fine/works because we know the geometry will be
        # the same for all workspaces on the output.

        # same output or size: direct positioning
        if output.id == current_output.id or (output.width == current_output.width and \
        output.height == current_output.height):
            x, y = self.x, self.y

        # same aspect ratio: scaled positioning
        elif output.width / output.height == current_output.width / current_output.height:
            scale = workspace.width / current_output.workspace().width
            x = int(self.x*scale)
            y = int(self.y*scale)

        # different aspect ratio: centered positioning
        else:
            x = int((workspace.width-self.width)/2)
            y = int((workspace.height-self.width)/2)

        # do workspace edge mirroring if a direction was provided
        match direction:
            case 'left':  x = workspace.width-self.width
            case 'down':  y = 0
            case 'up':    y = workspace.height-self.height
            case 'right': x = 0

        return (x, y)

    def is_max_size(self, direction: str=None) -> bool:
        """Determine if the container has reached its workspace size."""
        workspace = self.workspace()
        reached_width  = self.width  == workspace.width
        reached_height = self.height == workspace.height

        match direction:
            case _ if direction in HORIZONTAL: return reached_width
            case _ if direction in VERTICAL:   return reached_height
            case _:                            return reached_width or reached_height


if __name__ == '__main__': pass