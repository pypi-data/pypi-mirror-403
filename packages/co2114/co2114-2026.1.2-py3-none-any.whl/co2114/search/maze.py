from collections.abc import Iterable
import warnings
from matplotlib import pyplot as plt
from collections import deque
from typing import override
from matplotlib.figure import Figure  # for type hinting

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import pygame

from ..engine import App
from ..util.colours import (
    COLOR_BLACK, COLOR_WHITE,
    COLOR_RED, COLOR_RED_DARK, COLOR_RED_LIGHT,
    COLOR_YELLOW, COLOR_BLUE, COLOR_GREEN_LIGHT
)

from .graph import Node, Graph, GraphEnvironment
from .things import Thing, Agent

PRESET_MAZES = {
    0: [" xxx o",
        "    x ",
        "x x   ",
        "  x xx"],
    1: [" xx  o",
        "    x ",
        "x x   ",
        "    xx"],
    2: ["           o",
        "x xxxxxxxxx ",
        "x x       x ",
        "x x xxxxx x ",
        "  x x     x ",
        "x   x xx xx ",
        "xxx x  xxxx ",
        "    xx      "],
    3: ["xxx                 xxxxxxxxx",
        "x   xxxxxxxxxxxxxxxxxxx   x x",
        "x xxxx                x x x x",
        "x xxxxxxxxxxxxxxxxxxx x x x x",
        "x                     x x x x",
        "xxxxxxxxxxxxxxxxxxxxx x x x x",
        "x   xx                x x x x",
        "x x xx xxx xx xxxxxxxxx x x x",
        "x x    x   xxox         x x x",
        "x x xx xxxxxxxxxxxxxxxx x x x",
        "xxx xx             xxxx x x x",
        "xxx xxxxxxxxxxxxxx xx x x x x",
        "xxx             xx    x x x x",
        "xxxxxx xxxxxxxx xxxxxxx x x x",
        "xxxxxx xxxx             x   x",
        "       xxxxxxxxxxxxxxxxxxxxxx"],
    4: ["xxx                 xxxxxxxxx",
        "x   xxxxxxxxxxxxxxxxxxx   x x",
        "x xxxx                x x x x",
        "x xxxxxxxxxxxxxxxxxxx x x x x",
        "x                     x x x x",
        "xxxxxxxxxxxxxxxxxxxxx x x x x",
        "x   xx                x x x x",
        "x x xx xxx xx xxxxxxxxx x x x",
        "x x    x   xxox         x x x",
        "x x xx xxxxxxxxxxxxxxxx x x x",
        "xxx xx             xxxx x x x",
        "xxx xxxxxxxxxxxxxx xx x x x x",
        "xxx             xx    x x x x",
        "xxxxxx xxxxxxxx xxxxxxx x x x",
        "xxxxxx xxxx             x   x",
        "       xxxxxxxxxxxxxxxxxxxxxx"]
}

PRESET_STARTS = {
    0: (3, 0),
    1: (3, 0),
    2: (7, 0),
    3: (1, 27),
    4: (15, 0)
}


class MazeTile(Node):
    def __init__(self, passable:bool) -> None:
        """ MazeTile - A tile in a maze, either passable or not.
        
        :param passable: Whether the tile is passable.
        """
        super().__init__()
        self.is_passable:bool = passable
        self.is_goal:bool = False
        self.visited:bool = False

    def __repr__(self) -> str:
        """ Str representation of the MazeTile. """
        repr =  "⬜" if self.is_passable else "⬛"
        if hasattr(self, "location"):
            repr += str(self.location)
        return repr



class Maze(Graph):
    def __init__(self, template:list[str]|None=None) -> None:
        """ Maze class: a grid-based maze structure.
        
        :param template: Optional template to generate the maze from.
        """
        super().__init__()
        if template is not None:  # generate from template
            if not self._is_valid_template(template):
                raise ValueError(f"{self}: template provided is not valid")
            self.template = template
            self.height, self.width = len(template), len(template[0])
            self.size = self.width, self.height
            self._generate_from_template()

    @override
    def __repr__(self) -> str:
        """ String representation of the Maze. """
        return "ꡙ‍"

    def _is_valid_template(self, template:list[str]) -> bool:
        """ Checks if the provided template is valid.
        
        A valid template is a list of strings, all of the same length, containing only " ", "o", or "x".

        :param template: The template to validate.
        :return valid: Whether the template is valid.
        """
        def valid(row, size):
            """ Internal row validator. """
            return False if len(row) != size else not any(
                c not in (' ','o','x') for c in row)

        if isinstance(template, Iterable):
            if all(isinstance(row, Iterable) for row in template):
                width = len(template[0])
                return all(valid(row,width) for row in template)
        return False

    def _generate_from_template(self) -> None:
        """ Generates the maze from the provided template. 
        
        Uses internal self.template to build the maze grid.
        """
        self.grid = []
        w,h = self.width, self.height
        print(f"{self}: generating {w}x{h} maze from template")
        for i, row in enumerate(self.template):
            grid_row = []
            for j, tile in enumerate(row):
                node = MazeTile(tile != "x")  # True is passable
                if tile == "o":
                    node.is_goal = True
                node.location = (i, j)
                grid_row.append(node)
                if i > 0:
                    node.add_neighbour(self.grid[i-1][j])
                if j > 0:
                    node.add_neighbour(grid_row[j-1])
            self.grid.append(grid_row)
        self.add_node(self.grid[0][0])  # cascade adding nodes

    @override
    def plot_nodes(self) -> Figure:
        """ Plots the maze nodes using matplotlib."""
        labels = {self.grid[i][j]: f"({i},{j})" 
                    for i in range(self.width)
                        for j in range(self.height)}
        condition = lambda node: node.is_passable
        return super().plot_nodes(init=None, labels=labels, condition=condition)



class MazeEnvironment(GraphEnvironment):
    """ MazeEnvironment - An environment for maze navigation. 
    
    A type of GraphEnvironment specifically for Maze graphs.
    """
    def __init__(self, maze:Maze, *args, **kwargs) -> None:
        """ Initialises the MazeEnvironment.
        
        :param maze: The Maze to be used as the environment.
        :param args: Additional positional arguments for GraphEnvironment.
        :param kwargs: Additional keyword arguments for GraphEnvironment.
        """
        if not isinstance(maze, Maze):
            raise TypeError(f"{self}: maze must be valid Maze")
        super().__init__(maze, *args, **kwargs)
        self.size = self.width, self.height = maze.size
        self.success = False  # maze is solved

    @override
    def __repr__(self) -> str:
        """ String representation of the MazeEnvironment. """
        return self.maze.__repr__()

    @property
    def maze(self) -> Maze:
        """ Returns the maze graph of the environment. """
        return self.graph

    @property
    def grid(self) -> list[list[MazeTile]]:
        """ Returns the maze grid as a nested list of MazeTiles. """
        return self.maze.grid

    @property
    def is_done(self) -> bool:
        """ Returns whether the maze has been solved. """
        if len(self.agents) == 0: return True
        return self.success

    @property
    def goal(self) -> MazeTile|None:
        """ Returns the goal tile of the maze, if there is one. 
        """
        goal = {node for node in self.maze.nodes if node.is_goal}
        if len(goal) == 1:
            goal = next(iter(goal))
        else:
            goal = None
        return goal


    def show_graph(self, *args, **kwargs) -> Figure: 
        """ Wrapper for GraphEnvironment.show() """
        return self.show(*args, **kwargs)


    @override
    def percept(self, agent:Agent) -> set[MazeTile]:
        """ Returns the percepts for the agent: neighbouring nodes and their weights.
        
        :param agent: The agent to get percepts for.
        :return percepts: List of tuples of (neighbouring maze tile, weight).
        """
        node = agent.location
        return node.neighbours

    @override
    def execute_action(self, agent:Agent, action:tuple[str, MazeTile]) -> None:
        """ Executes the agent's action in the environment.
        
        :param agent: The agent performing the action.
        :param action: The action to be performed, as a tuple of (command, MazeTile). Command should be "move".
        """
        command, node = action  # e.g. ("move", node)
        if command == "move":
            if node in self.maze:
                self.success = agent.move_to(node)
    
    @override
    def run(self, *args, **kwargs) -> None:
        """ Run the environment for a large number of steps by default. 
        
        Non-graphical default.
        """
        super().run(10000, *args, **kwargs)

    @classmethod
    def from_template(MazeEnvironment, template:list[str]) -> "MazeEnvironment":
        """ Creates a MazeEnvironment from a template.
        
        Returns instance of MazeEnvironment built from the provided template.
        :param template: The template to build the maze from.
        :return environment: The MazeEnvironment instance.
        """
        maze = Maze(template)
        return MazeEnvironment(maze)


class GraphicMaze(MazeEnvironment):
    """ Graphical Maze Environment: A MazeEnvironment with graphical rendering capabilities. Uses MazeApp to render.
    """
    @override
    def run(self, graphical=True, lps=2, *args, **kwargs) -> None:
        """ Run the MazeEnvironment in graphical or non-graphical mode.
        
        :param graphical: Whether to run in graphical mode.
        :param lps: The number of logic updates per second in graphical mode.
        :param args: Additional positional arguments for Engine.
        :param kwargs: Additional keyword arguments for Engine.
        """
        if graphical:
            MazeApp(self, *args, name=f"{self}", lps=lps, **kwargs).run()
        else:
            super().run(*args, **kwargs)

  
class MazeApp(App):
    """ MazeApp
            Graphical version of Maze
    """
    def __init__(self,
                 environment:MazeEnvironment|None = None,
                 track_agent = False,
                 **kwargs) -> None:
        """ Construct MazeApp
        
        :param environment: The MazeEnvironment to be rendered. If None, a default maze is created.
        :param track_agent: Whether to visually track the agent's path, default False
        :param kwargs: Additional keyword arguments for App.
        """
        if environment is None:
            print(f"{self}: building new MazeEnvironment from template")
            environment = MazeEnvironment.from_template(PRESET_MAZES[0])
        if not isinstance(environment, MazeEnvironment):
            raise TypeError(f"{self}: environment must be MazeEnvironment")
        
        self.environment = environment
        self._fit_to_environment()
        super().__init__(**kwargs)

        nx = self.environment.width
        fs = min(35, max(10, self.width//nx))
        self.thing_font = pygame.font.SysFont("segoe-ui-symbol", fs)
        self.counter = -1
        self._flag = True
        self.track = track_agent

    
    def _fit_to_environment(self) -> None:
        """ Fit width and height ratios to match environment """
        _flag = self.environment.width > self.environment.height
        if _flag:
            xy_ratio = self.environment.width/self.environment.height
            a, b = self.height, self.width
        else:
            xy_ratio = self.environment.height/self.environment.width
            b, a = self.height, self.width

        a = b // xy_ratio
        b = int(a*xy_ratio)
        # a = int(a)

        self.height, self.width = (a,b) if _flag else (b,a)
        self.size = self.width, self.height

    @override
    def update(self) -> None:
        """ Update MazeApp by iterating underlying simulation environment """
        if self.counter < 0:
            self.counter += 1
            return
        if not self.environment.is_done:
            self.environment.step()
            self.counter += 1
        elif self._flag:
            print(f"{self.environment}: Maze complete after {self.counter} iterations.")
            self._flag = False

    @override
    def render(self) -> None:
        """ Render frame of MazeApp """
        # self.screen.fill(self.environment.color)
        self.render_grid()
        self.render_things()

    def render_grid(self) -> None:
        """ Render maze grid showing passable and non-passable tiles in light and dark red respectively. If the agent is tracked, visited tiles are shown in light green. """
        nx,ny = self.environment.width, self.environment.height
        self.tile_size = self.width / nx
        tile_origin = (0,0)
        grid = self.environment.grid
        tiles = []
        for i in range(ny):
            i_ = i# ny - i - 1
            
            row = []
            for j in range(nx):
                tileRect = pygame.Rect(
                    tile_origin[0] + j * self.tile_size,
                    tile_origin[1] + i * self.tile_size,
                    self.tile_size, self.tile_size)
                
                node = grid[i_][j]
                if node.is_goal:
                    color = COLOR_RED
                elif self.track and hasattr(node, "visited") and node.visited:
                    color = COLOR_GREEN_LIGHT
                elif node.is_passable:
                    color = COLOR_RED_LIGHT
                else:
                    color = COLOR_RED_DARK
                
                pygame.draw.rect(self.screen, color, tileRect)
                pygame.draw.rect(self.screen, COLOR_WHITE, tileRect, 1)
                row.append(tileRect)
            tiles.append(row)
        self.tiles = tiles
            
    def label_tile(self,
                   node:MazeTile,
                   string:str,
                   color:tuple[int,int,int] = COLOR_WHITE) -> None:
        """ Labels a tile with a string at the center of the tile.
        
        :param node: The MazeTile to label.
        :param string: The string to label the tile with.
        :param color: The color of the string.
        """
        i,j = node.location
        renderLoc = self.tiles[i][j].center
        thingRender = self.thing_font.render(string, True, color)
        thingRect = thingRender.get_rect()
        thingRect.center = renderLoc
        self.screen.blit(thingRender, thingRect)
    
    def render_things(self) -> None:
        """ Renders things to the maze environment. 
        
        Marks the goal tile with a crown emoji, agents with their string representation, and if tracking is enabled, marks frontier nodes with a question mark.
        """
        locations = {}
        for node in self.environment.maze:
            if node.is_goal:
                self.label_tile(node, "👑", COLOR_YELLOW)

        for agent in self.environment.agents:
            location = agent.location
            self.label_tile(agent.location, str(agent), COLOR_BLUE)
            
            if self.track:
                if hasattr(agent, "frontier"):
                    for node in agent.frontier:
                        self.label_tile(node, "?", COLOR_WHITE)