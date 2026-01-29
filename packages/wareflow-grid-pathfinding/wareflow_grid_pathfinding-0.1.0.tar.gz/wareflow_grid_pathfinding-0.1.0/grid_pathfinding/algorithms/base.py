"""Base class for pathfinding algorithms."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid
    from grid_pathfinding.core.node import Path
    from grid_pathfinding.heuristics.base import Heuristic
    from grid_pathfinding.movement.base import Movement


class PathfindingAlgorithm(ABC):
    """Abstract base class for pathfinding algorithms.

    Subclasses must implement the find_path method.

    Attributes:
        heuristic: Heuristic function for estimating costs.
        movement: Movement pattern for neighbor generation.

    Examples:
        Subclass and implement find_path:

        >>> class MyAlgorithm(PathfindingAlgorithm):
        ...     def find_path(self, grid, start, goal):
        ...         # Implementation here
        ...         pass
    """

    def __init__(
        self,
        heuristic: "Heuristic | None" = None,
        movement: "Movement | None" = None,
    ) -> None:
        """Initialize the algorithm with optional heuristic and movement pattern.

        Args:
            heuristic: Optional heuristic function.
            movement: Optional movement pattern.
        """
        from grid_pathfinding.heuristics.manhattan import ManhattanDistance
        from grid_pathfinding.movement.cardinal_3d import Cardinal3D

        self.heuristic = heuristic or ManhattanDistance()
        self.movement = movement or Cardinal3D()

    @abstractmethod
    def find_path(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Find a path from start to goal on the given grid.

        Args:
            grid: The grid to search on.
            start: Starting position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Path object if found, None otherwise.

        Raises:
            InvalidStartError: If start position is invalid.
            InvalidGoalError: If goal position is invalid.
        """
        raise NotImplementedError
