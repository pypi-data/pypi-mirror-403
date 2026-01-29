"""A* pathfinding algorithm implementation."""

import heapq
import time
from typing import TYPE_CHECKING

from grid_pathfinding.algorithms.base import PathfindingAlgorithm

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid
    from grid_pathfinding.core.node import Path


class AStar(PathfindingAlgorithm):
    """A* pathfinding algorithm using a binary heap (heapq).

    A* is a best-first search algorithm that uses both actual cost (g) and
    estimated cost (h) to guide the search. It is optimal when using an
    admissible heuristic.

    Attributes:
        heuristic: Heuristic function for estimating costs.
        movement: Movement pattern for neighbor generation.

    Examples:
        >>> from grid_pathfinding.core.grid import Grid
        >>> from grid_pathfinding.heuristics.manhattan import ManhattanDistance
        >>> from grid_pathfinding.movement.cardinal_3d import Cardinal3D
        >>> grid = Grid(10, 10, 1)
        >>> algo = AStar(heuristic=ManhattanDistance(), movement=Cardinal3D())
        >>> path = algo.find_path(grid, (0, 0, 0), (9, 9, 0))
        >>> path is not None
        True
    """

    __slots__ = ()

    def find_path(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Find a path from start to goal using A*.

        Args:
            grid: The grid to search on.
            start: Starting position (x, y, z).
            goal: Goal position (x, y, z).

        Returns:
            Path object if found, None otherwise.

        Raises:
            ValueError: If start or goal is out of bounds or is an obstacle.
        """
        # Validate start position
        if start not in grid:
            raise ValueError(
                f"Start position {start} is out of bounds "
                f"for grid {grid.width}x{grid.height}x{grid.depth}"
            )
        if grid.is_obstacle(*start):
            raise ValueError(f"Start position {start} is an obstacle")

        # Validate goal position
        if goal not in grid:
            raise ValueError(
                f"Goal position {goal} is out of bounds "
                f"for grid {grid.width}x{grid.height}x{grid.depth}"
            )
        if grid.is_obstacle(*goal):
            raise ValueError(f"Goal position {goal} is an obstacle")

        # Early exit if start == goal
        if start == goal:
            from grid_pathfinding.core.node import Path

            return Path(
                waypoints=[start],
                total_cost=0.0,
                computation_time_ms=0.0,
                nodes_explored=0,
            )

        start_time = time.perf_counter()

        # Priority queue: (f_cost, h_cost, counter, position)
        # Counter ensures stable ordering when f_cost ties
        open_set: list[tuple[float, float, int, tuple[int, int, int]]] = []
        counter = 0

        # Track nodes by position
        open_set_hash: set[tuple[int, int, int]] = {start}
        came_from: dict[tuple[int, int, int], tuple[int, int, int]] = {}

        # Cost from start to each position
        g_score: dict[tuple[int, int, int], float] = {start: 0.0}

        # Initial heuristic calculation
        h_start = self.heuristic.calculate(start, goal)
        f_start = h_start

        heapq.heappush(open_set, (f_start, h_start, counter, start))
        counter += 1

        nodes_explored = 0

        while open_set:
            # Get node with lowest f_cost
            current_f, current_h, _, current_pos = heapq.heappop(open_set)
            open_set_hash.discard(current_pos)
            nodes_explored += 1

            # Check if we reached the goal
            if current_pos == goal:
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # Reconstruct path
                path = self._reconstruct_path(came_from, start, goal)
                total_cost = g_score[goal]

                from grid_pathfinding.core.node import Path

                return Path(
                    waypoints=path,
                    total_cost=total_cost,
                    computation_time_ms=elapsed_ms,
                    nodes_explored=nodes_explored,
                )

            # Explore neighbors
            cx, cy, cz = current_pos
            for neighbor in self.movement.get_neighbors(grid, cx, cy, cz):
                # Calculate tentative g_score
                move_cost = grid.get_cost(*neighbor)
                tentative_g = g_score[current_pos] + move_cost

                # If this path to neighbor is better
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current_pos
                    g_score[neighbor] = tentative_g
                    h_score = self.heuristic.calculate(neighbor, goal)
                    f_score = tentative_g + h_score

                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score, h_score, counter, neighbor))
                        counter += 1
                        open_set_hash.add(neighbor)

        # No path found
        return None

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int, int], tuple[int, int, int]],
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> list[tuple[int, int, int]]:
        """Reconstruct the path from goal to start.

        Args:
            came_from: Dictionary mapping each position to its parent.
            start: Starting position.
            goal: Goal position.

        Returns:
            List of positions from start to goal.
        """
        path = [goal]
        current = goal

        while current != start:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AStar(heuristic={self.heuristic!r}, movement={self.movement!r})"
