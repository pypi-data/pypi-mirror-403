"""Tests for heuristic functions."""

import pytest

from grid_pathfinding.heuristics.base import Heuristic
from grid_pathfinding.heuristics.manhattan import ManhattanDistance


class TestManhattanDistance:
    """Test ManhattanDistance heuristic."""

    def test_calculate_same_position(self) -> None:
        """Test Manhattan distance from position to itself."""
        h = ManhattanDistance()
        assert h.calculate((5, 5, 0), (5, 5, 0)) == 0.0

    def test_calculate_horizontal_distance(self) -> None:
        """Test horizontal Manhattan distance."""
        h = ManhattanDistance()
        assert h.calculate((0, 0, 0), (3, 0, 0)) == 3.0
        assert h.calculate((5, 5, 0), (2, 5, 0)) == 3.0

    def test_calculate_vertical_distance(self) -> None:
        """Test vertical Manhattan distance."""
        h = ManhattanDistance()
        assert h.calculate((0, 0, 0), (0, 4, 0)) == 4.0
        assert h.calculate((5, 5, 0), (5, 1, 0)) == 4.0

    def test_calculate_diagonal_distance(self) -> None:
        """Test diagonal Manhattan distance (sum of components)."""
        h = ManhattanDistance()
        assert h.calculate((0, 0, 0), (3, 4, 0)) == 7.0
        assert h.calculate((1, 2, 0), (4, 6, 0)) == 7.0

    def test_calculate_3d_distance(self) -> None:
        """Test 3D Manhattan distance."""
        h = ManhattanDistance(use_3d=True)
        assert h.calculate((0, 0, 0), (3, 4, 2)) == 9.0

    def test_calculate_2d_mode(self) -> None:
        """Test 2D mode (ignoring z-axis)."""
        h = ManhattanDistance(use_3d=False)
        assert h.calculate((0, 0, 0), (3, 4, 2)) == 7.0  # Z is ignored
        assert h.calculate((0, 0, 5), (3, 4, 10)) == 7.0  # Z difference is ignored

    def test_callable(self) -> None:
        """Test that heuristic is callable."""
        h = ManhattanDistance()
        result = h((0, 0, 0), (3, 4, 0))
        assert result == 7.0

    def test_repr(self) -> None:
        """Test string representation."""
        h = ManhattanDistance(use_3d=True)
        assert "ManhattanDistance" in repr(h)
        assert "use_3d=True" in repr(h)


class TestCustomHeuristic:
    """Test creating custom heuristics."""

    def test_custom_heuristic(self) -> None:
        """Test creating a custom heuristic class."""

        class CustomHeuristic(Heuristic):
            def calculate(self, current, goal):
                # Always return 1.0
                return 1.0

        h = CustomHeuristic()
        assert h.calculate((0, 0, 0), (5, 5, 0)) == 1.0

    def test_heuristic_as_callable(self) -> None:
        """Test using heuristic as a callable."""

        class DoubleHeuristic(Heuristic):
            def calculate(self, current, goal):
                dx = abs(current[0] - goal[0])
                dy = abs(current[1] - goal[1])
                return float(2 * (dx + dy))

        h = DoubleHeuristic()
        assert h((0, 0, 0), (3, 4, 0)) == 14.0  # 2 * (3 + 4)
