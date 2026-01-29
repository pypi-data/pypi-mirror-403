"""Base heuristic for pathfinding."""

from abc import ABC, abstractmethod


class Heuristic(ABC):
    """Abstract base class for heuristic functions.

    A heuristic estimates the cost from a current position to the goal.
    For A* to be optimal, the heuristic must be admissible (never overestimate).

    Examples:
        >>> class MyHeuristic(Heuristic):
        ...     def calculate(self, current, goal):
        ...         # Calculate and return estimated cost
        ...         return abs(current[0] - goal[0])
    """

    @abstractmethod
    def calculate(
        self,
        current: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> float:
        """Calculate the heuristic cost from current to goal.

        Args:
            current: Current position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Estimated cost from current to goal.
        """
        raise NotImplementedError

    def __call__(
        self,
        current: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> float:
        """Allow calling heuristic as a function.

        Args:
            current: Current position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Estimated cost from current to goal.
        """
        return self.calculate(current, goal)
