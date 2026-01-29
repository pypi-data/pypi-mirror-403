"""Manhattan distance heuristic for pathfinding."""

from grid_pathfinding.heuristics.base import Heuristic


class ManhattanDistance(Heuristic):
    """Manhattan distance heuristic (L1 norm).

    The Manhattan distance is the sum of absolute differences in each dimension.
    This is admissible for 4-directional (2D) or 6-directional (3D) movement.

    Attributes:
        diagonal_cost: Cost multiplier for diagonal movement (not used in basic Manhattan).

    Examples:
        >>> h = ManhattanDistance()
        >>> h.calculate((0, 0, 0), (3, 4, 2))
        9.0
        >>> h.calculate((5, 5, 5), (2, 2, 2))
        9.0
    """

    __slots__ = ("_use_3d",)

    def __init__(self, use_3d: bool = True) -> None:
        """Initialize the Manhattan distance heuristic.

        Args:
            use_3d: Whether to include the z-axis in calculations. Defaults to True.
        """
        self._use_3d = use_3d

    def calculate(
        self,
        current: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> float:
        """Calculate the Manhattan distance from current to goal.

        Args:
            current: Current position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Manhattan distance (sum of absolute coordinate differences).
        """
        dx = abs(current[0] - goal[0])
        dy = abs(current[1] - goal[1])
        dz = abs(current[2] - goal[2]) if self._use_3d else 0

        return float(dx + dy + dz)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ManhattanDistance(use_3d={self._use_3d})"
