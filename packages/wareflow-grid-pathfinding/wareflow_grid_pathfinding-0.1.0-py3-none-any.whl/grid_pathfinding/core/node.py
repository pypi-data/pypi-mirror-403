"""Node and Path data structures for pathfinding."""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_pathfinding.heuristics.base import Heuristic
    from grid_pathfinding.movement.base import Movement


@dataclass(slots=True)
class SearchNode:
    """A node in the A* search space.

    Attributes:
        position: (x, y, z) tuple representing the node's position.
        g_cost: Cost from start to this node.
        h_cost: Estimated cost from this node to goal (heuristic).
        parent: Parent node in the search tree.

    Examples:
        >>> node = SearchNode((0, 0, 0), 0.0, 10.0)
        >>> node.f_cost
        10.0
        >>> node2 = SearchNode((1, 0, 0), 1.0, 9.0, parent=node)
        >>> node2.parent.position
        (0, 0, 0)
    """

    position: tuple[int, int, int]
    g_cost: float
    h_cost: float
    parent: "SearchNode | None" = None

    @property
    def f_cost(self) -> float:
        """Total estimated cost (g + h)."""
        return self.g_cost + self.h_cost

    def __lt__(self, other: object) -> bool:
        """Compare nodes by f_cost, then by h_cost for tiebreaking.

        Args:
            other: Another SearchNode to compare with.

        Returns:
            True if this node has lower f_cost (or lower h_cost on tie).
        """
        if not isinstance(other, SearchNode):
            return NotImplemented
        if self.f_cost != other.f_cost:
            return self.f_cost < other.f_cost
        return self.h_cost < other.h_cost

    def __repr__(self) -> str:
        """Return string representation of the node."""
        parent_pos = self.parent.position if self.parent else None
        return (
            f"SearchNode(position={self.position}, g={self.g_cost:.2f}, "
            f"h={self.h_cost:.2f}, f={self.f_cost:.2f}, parent={parent_pos})"
        )


@dataclass
class Path:
    """A path found by a pathfinding algorithm.

    Attributes:
        waypoints: List of (x, y, z) tuples from start to goal.
        total_cost: Total cost of the path.
        computation_time_ms: Time taken to find the path in milliseconds.
        nodes_explored: Number of nodes explored during search.

    Examples:
        >>> path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 5.0, 10)
        >>> len(path)
        3
        >>> path[0]
        (0, 0, 0)
        >>> for pos in path:
        ...     print(pos)
        (0, 0, 0)
        (1, 0, 0)
        (2, 0, 0)
    """

    waypoints: list[tuple[int, int, int]]
    total_cost: float
    computation_time_ms: float
    nodes_explored: int

    def __len__(self) -> int:
        """Return the number of waypoints in the path."""
        return len(self.waypoints)

    def __getitem__(self, index: int) -> tuple[int, int, int]:
        """Get a waypoint by index."""
        return self.waypoints[index]

    def __iter__(self):
        """Iterate over waypoints in the path."""
        return iter(self.waypoints)

    def __repr__(self) -> str:
        """Return string representation of the path."""
        return (
            f"Path(waypoints={len(self.waypoints)}, cost={self.total_cost:.2f}, "
            f"time={self.computation_time_ms:.2f}ms, explored={self.nodes_explored})"
        )

    def compress(self) -> "Path":
        """Remove redundant waypoints (straight-line optimization).

        Returns:
            A new Path with unnecessary waypoints removed.

        Examples:
            >>> path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)], 3.0, 1.0, 5)
            >>> compressed = path.compress()
            >>> compressed.waypoints
            [(0, 0, 0), (3, 0, 0)]
        """
        if len(self.waypoints) <= 2:
            return Path(
                self.waypoints.copy(),
                self.total_cost,
                self.computation_time_ms,
                self.nodes_explored,
            )

        compressed = [self.waypoints[0]]

        for i in range(1, len(self.waypoints) - 1):
            prev_pos = self.waypoints[i - 1]
            curr_pos = self.waypoints[i]
            next_pos = self.waypoints[i + 1]

            # Check if current waypoint is necessary (direction change)
            dx1 = curr_pos[0] - prev_pos[0]
            dy1 = curr_pos[1] - prev_pos[1]
            dz1 = curr_pos[2] - prev_pos[2]

            dx2 = next_pos[0] - curr_pos[0]
            dy2 = next_pos[1] - curr_pos[1]
            dz2 = next_pos[2] - curr_pos[2]

            # If direction changes, keep the waypoint
            if (dx1, dy1, dz1) != (dx2, dy2, dz2):
                compressed.append(curr_pos)

        compressed.append(self.waypoints[-1])

        return Path(
            compressed,
            self.total_cost,
            self.computation_time_ms,
            self.nodes_explored,
        )

    def segments(self) -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
        """Get the path as a list of line segments.

        Returns:
            List of ((x1, y1, z1), (x2, y2, z2)) segments.

        Examples:
            >>> path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 1.0, 3)
            >>> path.segments()
            [((0, 0, 0), (1, 0, 0)), ((1, 0, 0), (2, 0, 0))]
        """
        return [
            (self.waypoints[i], self.waypoints[i + 1])
            for i in range(len(self.waypoints) - 1)
        ]
