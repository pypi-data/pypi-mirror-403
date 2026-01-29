"""Dynamic replanning for handling temporary obstacles."""

from enum import IntEnum
from typing import TYPE_CHECKING

from grid_pathfinding.algorithms.astar import AStar

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid
    from grid_pathfinding.core.node import Path


class ReplanStrategy(IntEnum):
    """Replanning strategy options."""

    FULL_REPLAN = 0
    """Completely recompute the path from current position."""

    REPAIR = 1
    """Locally repair the path around the obstacle (faster)."""


class DynamicReplanner:
    """Handles dynamic replanning when obstacles appear during path execution.

    When following a path, new obstacles may appear. This class provides
    strategies for handling such situations efficiently.

    Attributes:
        strategy: The replanning strategy to use.
        repair_radius: Search radius for local repairs (REPAIR strategy).

    Examples:
        >>> from grid_pathfinding.algorithms.replanning import DynamicReplanner
        >>> replanner = DynamicReplanner(strategy=ReplanStrategy.REPAIR)
        >>> grid = Grid(10, 10, 1)
        >>> path = find_path(grid, (0, 0, 0), (9, 9, 0))
        >>> # New obstacle appears!
        >>> grid.set_obstacle(5, 5, 0, True)
        >>> # Replan around obstacle
        >>> new_path = replanner.replan(grid, path, (4, 5, 0))
    """

    __slots__ = ("_strategy", "_repair_radius", "_algorithm")

    def __init__(
        self,
        strategy: ReplanStrategy = ReplanStrategy.REPAIR,
        repair_radius: int = 10,
    ) -> None:
        """Initialize the dynamic replanner.

        Args:
            strategy: The replanning strategy to use.
            repair_radius: Search radius for local repairs.
        """
        self._strategy = strategy
        self._repair_radius = repair_radius
        self._algorithm = AStar()

    def replan(
        self,
        grid: "Grid",
        old_path: "Path",
        current_position: tuple[int, int, int],
        goal: tuple[int, int, int] | None = None,
    ) -> "Path | None":
        """Replan a path when obstacles change.

        Args:
            grid: The grid (may have new obstacles).
            old_path: The previously computed path.
            current_position: Current position along the path.
            goal: Optional goal position (defaults to old_path goal).

        Returns:
            New path if found, None otherwise.
        """
        if goal is None:
            goal = old_path.waypoints[-1]

        # Check if current position is blocked
        if grid.is_obstacle(*current_position):
            # We're stuck - try to move to a neighbor
            return self._escape_obstacle(grid, current_position, goal)

        if self._strategy == ReplanStrategy.FULL_REPLAN:
            return self._full_replan(grid, current_position, goal)
        else:
            return self._repair_path(grid, old_path, current_position, goal)

    def _full_replan(
        self,
        grid: "Grid",
        current_position: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Completely recompute the path.

        Args:
            grid: The grid.
            current_position: Current position.
            goal: Goal position.

        Returns:
            New path if found, None otherwise.
        """
        return self._algorithm.find_path(grid, current_position, goal)

    def _repair_path(
        self,
        grid: "Grid",
        old_path: "Path",
        current_position: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Locally repair the path around obstacles.

        Find the first valid position in the old path after current_position,
        then plan a path to that position. If successful, append the rest of
        the old path from that position.

        Args:
            grid: The grid.
            old_path: The previously computed path.
            current_position: Current position.
            goal: Goal position.

        Returns:
            Repaired path if found, None otherwise.
        """
        # Find the next valid waypoint in the old path
        reconnect_point = None
        reconnect_index = -1

        for i, waypoint in enumerate(old_path.waypoints):
            if waypoint == current_position:
                continue  # Skip current position

            if not grid.is_obstacle(*waypoint):
                # Check if this waypoint is reachable from current_position
                # (within repair radius)
                cx, cy, cz = current_position
                wx, wy, wz = waypoint
                distance = abs(wx - cx) + abs(wy - cy) + abs(wz - cz)

                if distance <= self._repair_radius:
                    reconnect_point = waypoint
                    reconnect_index = i
                    break

        if reconnect_point is None:
            # No valid reconnect point found, fall back to full replan
            return self._full_replan(grid, current_position, goal)

        # Plan path to reconnect point
        repair_path = self._algorithm.find_path(grid, current_position, reconnect_point)

        if repair_path is None:
            # Failed to find repair path, fall back to full replan
            return self._full_replan(grid, current_position, goal)

        # Append rest of old path from reconnect point
        remaining_waypoints = old_path.waypoints[reconnect_index:]

        # Combine paths (avoid duplicating reconnect point)
        new_waypoints = repair_path.waypoints + remaining_waypoints[1:]

        from grid_pathfinding.core.node import Path

        return Path(
            waypoints=new_waypoints,
            total_cost=repair_path.total_cost + sum(
                grid.get_cost(*wp) for wp in remaining_waypoints[1:]
            ),
            computation_time_ms=repair_path.computation_time_ms,
            nodes_explored=repair_path.nodes_explored,
        )

    def _escape_obstacle(
        self,
        grid: "Grid",
        current_position: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Try to escape from a blocked position.

        Args:
            grid: The grid.
            current_position: Current blocked position.
            goal: Goal position.

        Returns:
            Path to escape and continue, None if stuck.
        """
        # Find all non-obstacle neighbors
        from grid_pathfinding.movement.cardinal_3d import Cardinal3D

        movement = Cardinal3D()
        neighbors = movement.get_neighbors(grid, *current_position)

        if not neighbors:
            # Completely stuck
            return None

        # Try each neighbor as escape point
        best_path = None
        best_cost = float("inf")

        for neighbor in neighbors:
            path = self._algorithm.find_path(grid, neighbor, goal)
            if path and path.total_cost < best_cost:
                best_cost = path.total_cost
                # Prepend neighbor to path
                from grid_pathfinding.core.node import Path

                best_path = Path(
                    waypoints=[neighbor] + path.waypoints,
                    total_cost=grid.get_cost(*neighbor) + path.total_cost,
                    computation_time_ms=path.computation_time_ms,
                    nodes_explored=path.nodes_explored,
                )

        return best_path

    @property
    def strategy(self) -> ReplanStrategy:
        """Get the current replanning strategy."""
        return self._strategy

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"DynamicReplanner(strategy={self._strategy.name}, "
            f"repair_radius={self._repair_radius})"
        )
