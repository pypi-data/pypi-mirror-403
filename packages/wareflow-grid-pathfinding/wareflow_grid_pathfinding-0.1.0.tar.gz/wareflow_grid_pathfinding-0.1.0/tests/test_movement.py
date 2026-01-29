"""Tests for movement patterns."""

import pytest

from grid_pathfinding.core.grid import Grid
from grid_pathfinding.movement.base import Movement
from grid_pathfinding.movement.cardinal_3d import Cardinal3D


class TestCardinal3D:
    """Test Cardinal3D movement pattern."""

    def test_get_neighbors_center(self) -> None:
        """Test getting neighbors from a center position."""
        grid = Grid(10, 10, 10)
        movement = Cardinal3D()
        neighbors = movement.get_neighbors(grid, 5, 5, 5)

        assert len(neighbors) == 6
        assert (6, 5, 5) in neighbors  # Right
        assert (4, 5, 5) in neighbors  # Left
        assert (5, 6, 5) in neighbors  # Forward
        assert (5, 4, 5) in neighbors  # Backward
        assert (5, 5, 6) in neighbors  # Up
        assert (5, 5, 4) in neighbors  # Down

    def test_get_neighbors_edge(self) -> None:
        """Test getting neighbors from an edge position."""
        grid = Grid(10, 10, 10)
        movement = Cardinal3D()
        neighbors = movement.get_neighbors(grid, 0, 0, 0)

        # Corner has only 3 neighbors
        assert len(neighbors) == 3
        assert (1, 0, 0) in neighbors  # Right
        assert (0, 1, 0) in neighbors  # Forward
        assert (0, 0, 1) in neighbors  # Up

    def test_get_neighbors_with_obstacles(self) -> None:
        """Test that obstacles are not returned as neighbors."""
        grid = Grid(10, 10, 10)
        grid.set_obstacle(6, 5, 5, True)
        grid.set_obstacle(5, 6, 5, True)

        movement = Cardinal3D()
        neighbors = movement.get_neighbors(grid, 5, 5, 5)

        # Should have 4 neighbors (2 are blocked)
        assert len(neighbors) == 4
        assert (6, 5, 5) not in neighbors
        assert (5, 6, 5) not in neighbors

    def test_get_neighbors_all_obstacles(self) -> None:
        """Test when all neighbors are obstacles."""
        grid = Grid(10, 10, 10)
        # Block all neighbors of (5, 5, 5)
        for pos in [(6, 5, 5), (4, 5, 5), (5, 6, 5), (5, 4, 5), (5, 5, 6), (5, 5, 4)]:
            grid.set_obstacle(*pos, True)

        movement = Cardinal3D()
        neighbors = movement.get_neighbors(grid, 5, 5, 5)

        assert len(neighbors) == 0

    def test_repr(self) -> None:
        """Test string representation."""
        movement = Cardinal3D()
        assert repr(movement) == "Cardinal3D()"


class TestCustomMovement:
    """Test creating custom movement patterns."""

    def test_custom_movement(self) -> None:
        """Test creating a custom movement pattern."""

        class DiagonalOnly(Movement):
            """Only allow diagonal movement."""

            def get_neighbors(self, grid, x, y, z):
                neighbors = []
                for dx, dy, dz in [(1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0)]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if (nx, ny, nz) in grid and not grid.is_obstacle(nx, ny, nz):
                        neighbors.append((nx, ny, nz))
                return neighbors

        grid = Grid(10, 10, 1)
        movement = DiagonalOnly()
        neighbors = movement.get_neighbors(grid, 5, 5, 0)

        # Only 4 diagonal neighbors (if in bounds)
        assert len(neighbors) > 0
