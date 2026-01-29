"""Base movement pattern for pathfinding."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid


class Movement(ABC):
    """Abstract base class for movement patterns.

    A movement pattern defines how agents can navigate the grid by generating
    valid neighbor positions.

    Examples:
        >>> class MyMovement(Movement):
        ...     def get_neighbors(self, grid, x, y, z):
        ...         return [(x+1, y, z), (x-1, y, z)]  # Only left/right
    """

    @abstractmethod
    def get_neighbors(
        self,
        grid: "Grid",
        x: int,
        y: int,
        z: int,
    ) -> list[tuple[int, int, int]]:
        """Get valid neighboring positions from the given position.

        Args:
            grid: The grid to navigate on.
            x: X coordinate of current position.
            y: Y coordinate of current position.
            z: Z coordinate of current position.

        Returns:
            List of valid neighboring (x, y, z) tuples.
        """
        raise NotImplementedError
