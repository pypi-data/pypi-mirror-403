"""Tests for A* pathfinding algorithm."""

import pytest

from grid_pathfinding.algorithms.astar import AStar
from grid_pathfinding.core.grid import Grid
from grid_pathfinding.heuristics.manhattan import ManhattanDistance
from grid_pathfinding.movement.cardinal_3d import Cardinal3D


class TestAStarBasic:
    """Test basic A* functionality."""

    def test_find_direct_path(self) -> None:
        """Test finding a direct path on empty grid."""
        grid = Grid(10, 10, 1)
        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (3, 0, 0))

        assert path is not None
        assert path.waypoints[0] == (0, 0, 0)
        assert path.waypoints[-1] == (3, 0, 0)
        assert path.total_cost > 0

    def test_start_equals_goal(self) -> None:
        """Test when start equals goal."""
        grid = Grid(10, 10, 1)
        algo = AStar()
        path = algo.find_path(grid, (5, 5, 0), (5, 5, 0))

        assert path is not None
        assert len(path) == 1
        assert path.waypoints[0] == (5, 5, 0)
        assert path.total_cost == 0.0
        assert path.nodes_explored == 0

    def test_invalid_start_out_of_bounds(self) -> None:
        """Test that start out of bounds raises ValueError."""
        grid = Grid(10, 10, 1)
        algo = AStar()
        with pytest.raises(ValueError, match="out of bounds"):
            algo.find_path(grid, (-1, 0, 0), (5, 5, 0))

    def test_invalid_goal_out_of_bounds(self) -> None:
        """Test that goal out of bounds raises ValueError."""
        grid = Grid(10, 10, 1)
        algo = AStar()
        with pytest.raises(ValueError, match="out of bounds"):
            algo.find_path(grid, (0, 0, 0), (10, 5, 0))

    def test_start_is_obstacle(self) -> None:
        """Test that start being an obstacle raises ValueError."""
        grid = Grid(10, 10, 1)
        grid.set_obstacle(5, 5, 0, True)
        algo = AStar()
        with pytest.raises(ValueError, match="obstacle"):
            algo.find_path(grid, (5, 5, 0), (9, 9, 0))

    def test_goal_is_obstacle(self) -> None:
        """Test that goal being an obstacle raises ValueError."""
        grid = Grid(10, 10, 1)
        grid.set_obstacle(9, 9, 0, True)
        algo = AStar()
        with pytest.raises(ValueError, match="obstacle"):
            algo.find_path(grid, (0, 0, 0), (9, 9, 0))


class TestAStarObstacleAvoidance:
    """Test A* with obstacles."""

    def test_avoid_single_obstacle(self) -> None:
        """Test navigating around a single obstacle."""
        grid = Grid(10, 10, 1)
        # Block the direct path
        grid.set_obstacle(2, 0, 0)

        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (4, 0, 0))

        assert path is not None
        assert path.waypoints[0] == (0, 0, 0)
        assert path.waypoints[-1] == (4, 0, 0)
        # Path should go around the obstacle
        assert (2, 0, 0) not in path.waypoints

    def test_avoid_wall(self) -> None:
        """Test navigating around a wall with a gap."""
        grid = Grid(10, 10, 1)
        # Create a vertical wall with a gap
        for y in range(10):
            if y != 5:  # Gap at y=5
                grid.set_obstacle(5, y, 0)

        algo = AStar()
        path = algo.find_path(grid, (0, 5, 0), (9, 5, 0))

        assert path is not None
        # Path should go through the gap
        assert (5, 5, 0) in path.waypoints

    def test_no_path_exists(self) -> None:
        """Test when no path exists (completely blocked)."""
        grid = Grid(10, 10, 1)
        # Block all cells around goal
        for x in range(10):
            for y in range(10):
                grid.set_obstacle(x, y, 0)
        # Clear start and goal
        grid.set_obstacle(0, 0, 0, False)
        grid.set_obstacle(9, 9, 0, False)

        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (9, 9, 0))

        # Should return None when no path exists
        assert path is None

    def test_path_in_maze(self) -> None:
        """Test finding path through a simple maze."""
        grid = Grid(10, 10, 1)
        # Create walls with a gap
        for x in range(10):
            if x != 5:  # Gap at x=5
                grid.set_obstacle(x, 5, 0)

        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (9, 9, 0))

        assert path is not None
        # Path should go through the gap
        assert (5, 5, 0) in path.waypoints


class TestAStarWithCosts:
    """Test A* with custom cell costs."""

    def test_prefer_lower_cost_path(self) -> None:
        """Test that algorithm prefers lower cost paths."""
        grid = Grid(10, 10, 1)
        # Set high cost on direct path
        for x in range(1, 4):
            grid.set_cost(x, 0, 0, 10.0)

        # Lower cost path should go through y=1
        grid.set_cost(1, 1, 0, 1.0)
        grid.set_cost(2, 1, 0, 1.0)
        grid.set_cost(3, 1, 0, 1.0)

        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (4, 0, 0))

        assert path is not None
        # Path should go through the lower cost area
        assert (1, 1, 0) in path.waypoints or (2, 1, 0) in path.waypoints


class TestAStarPerformance:
    """Test A* performance characteristics."""

    def test_performance_100x100(self, benchmark) -> None:
        """Test A* performance on 100x100 grid."""

        def run_astar() -> None:
            grid = Grid(100, 100, 10)
            algo = AStar(heuristic=ManhattanDistance(), movement=Cardinal3D())
            path = algo.find_path(grid, (0, 0, 0), (99, 99, 9))
            assert path is not None

        # Benchmark should run in < 50ms
        result = benchmark(run_astar)
        # The path should be found
        assert result is None  # Function completes without error

    def test_nodes_explored(self) -> None:
        """Test that nodes explored is tracked correctly."""
        grid = Grid(10, 10, 1)
        algo = AStar()
        path = algo.find_path(grid, (0, 0, 0), (9, 9, 0))

        assert path is not None
        assert path.nodes_explored > 0
        assert path.computation_time_ms >= 0


class TestAStarCustomHeuristicAndMovement:
    """Test A* with custom heuristics and movement patterns."""

    def test_custom_heuristic(self) -> None:
        """Test A* with a custom heuristic."""
        from grid_pathfinding.heuristics.base import Heuristic

        class DummyHeuristic(Heuristic):
            def calculate(self, current, goal):
                return 0.0  # Always returns 0 (degenerate case)

        grid = Grid(10, 10, 1)
        algo = AStar(heuristic=DummyHeuristic())
        path = algo.find_path(grid, (0, 0, 0), (3, 0, 0))

        assert path is not None

    def test_algo_repr(self) -> None:
        """Test algorithm string representation."""
        algo = AStar(heuristic=ManhattanDistance(), movement=Cardinal3D())
        assert "AStar" in repr(algo)
