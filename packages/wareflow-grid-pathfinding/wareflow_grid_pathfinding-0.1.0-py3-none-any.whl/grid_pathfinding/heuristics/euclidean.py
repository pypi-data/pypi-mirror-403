"""Euclidean distance heuristic for pathfinding."""

import math

from grid_pathfinding.heuristics.base import Heuristic


class EuclideanDistance(Heuristic):
    """Euclidean distance heuristic (L2 norm).

    The Euclidean distance is the straight-line distance between two points.
    This is admissible for 8-directional (2D) or 26-directional (3D) movement.

    Examples:
        >>> h = EuclideanDistance()
        >>> h.calculate((0, 0, 0), (3, 4, 0))
        5.0
        >>> h.calculate((0, 0, 0), (3, 4, 12))
        13.0
    """

    __slots__ = ("_use_3d",)

    def __init__(self, use_3d: bool = True) -> None:
        """Initialize the Euclidean distance heuristic.

        Args:
            use_3d: Whether to include the z-axis in calculations. Defaults to True.
        """
        self._use_3d = use_3d

    def calculate(
        self,
        current: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> float:
        """Calculate the Euclidean distance from current to goal.

        Args:
            current: Current position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Euclidean distance (straight-line distance).
        """
        dx = current[0] - goal[0]
        dy = current[1] - goal[1]
        dz = current[2] - goal[2] if self._use_3d else 0

        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"EuclideanDistance(use_3d={self._use_3d})"
