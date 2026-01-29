"""Base class for cost functions."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid


class CostFunction(ABC):
    """Abstract base class for cost functions.

    A cost function calculates the movement cost between two positions.
    This can be used to implement dynamic costs based on factors like
    congestion, terrain difficulty, etc.

    Examples:
        >>> class MyCostFunction(CostFunction):
        ...     def calculate(self, grid, from_pos, to_pos):
        ...         # Return cost based on some criteria
        ...         return 1.0
    """

    @abstractmethod
    def calculate(
        self,
        grid: "Grid",
        from_pos: tuple[int, int, int],
        to_pos: tuple[int, int, int],
    ) -> float:
        """Calculate the cost of moving from one position to another.

        Args:
            grid: The grid.
            from_pos: Source position (x, y, z).
            to_pos: Target position (x, y, z).

        Returns:
            Movement cost (must be positive).
        """
        raise NotImplementedError

    def __call__(
        self,
        grid: "Grid",
        from_pos: tuple[int, int, int],
        to_pos: tuple[int, int, int],
    ) -> float:
        """Allow calling cost function as a function.

        Args:
            grid: The grid.
            from_pos: Source position (x, y, z).
            to_pos: Target position (x, y, z).

        Returns:
            Movement cost.
        """
        return self.calculate(grid, from_pos, to_pos)
