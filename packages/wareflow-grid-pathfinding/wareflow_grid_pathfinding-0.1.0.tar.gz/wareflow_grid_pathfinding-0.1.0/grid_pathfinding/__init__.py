"""Grid Pathfinding Package.

High-performance 3D grid pathfinding with A* and HPA* algorithms.
"""

from grid_pathfinding.algorithms.astar import AStar
from grid_pathfinding.algorithms.base import PathfindingAlgorithm
from grid_pathfinding.algorithms.hpastar import HPAStar
from grid_pathfinding.core.grid import Grid, StorageType
from grid_pathfinding.core.node import Path, SearchNode
from grid_pathfinding.heuristics.base import Heuristic
from grid_pathfinding.heuristics.manhattan import ManhattanDistance
from grid_pathfinding.movement.base import Movement
from grid_pathfinding.movement.cardinal_3d import Cardinal3D

__all__ = [
    # Core
    "Grid",
    "StorageType",
    "Path",
    "SearchNode",
    # Algorithms
    "PathfindingAlgorithm",
    "AStar",
    "HPAStar",
    # Heuristics
    "Heuristic",
    "ManhattanDistance",
    # Movement
    "Movement",
    "Cardinal3D",
    # Convenience functions
    "find_path",
]

__version__ = "0.1.0"


def find_path(
    grid: Grid,
    start: tuple[int, int, int],
    goal: tuple[int, int, int],
    algorithm: str = "astar",
    heuristic: Heuristic | None = None,
    movement: Movement | None = None,
) -> Path | None:
    """Find a path from start to goal on the given grid.

    Args:
        grid: The grid to search on.
        start: Starting position (x, y, z).
        goal: Goal position (x, y, z).
        algorithm: Algorithm to use ("astar" or "hpastar"). Defaults to "astar".
        heuristic: Optional heuristic function. Defaults to ManhattanDistance.
        movement: Optional movement pattern. Defaults to Cardinal3D.

    Returns:
        Path object if found, None otherwise.

    Raises:
        InvalidStartError: If start position is invalid.
        InvalidGoalError: If goal position is invalid.
        NoPathError: If no path exists (returns None instead of raising).

    Examples:
        >>> grid = Grid(10, 10, 1)
        >>> path = find_path(grid, (0, 0, 0), (9, 9, 0))
        >>> for pos in path:
        ...     print(pos)
        (0, 0, 0)
        (1, 0, 0)
        ...
        (9, 9, 0)
    """
    if heuristic is None:
        heuristic = ManhattanDistance()
    if movement is None:
        movement = Cardinal3D()

    if algorithm == "astar":
        algo = AStar(heuristic=heuristic, movement=movement)
    elif algorithm == "hpastar":
        algo = HPAStar(heuristic=heuristic, movement=movement)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return algo.find_path(grid, start, goal)
