"""Tests for Grid class."""

import pytest

from grid_pathfinding.core.grid import Grid, StorageType


class TestGridCreation:
    """Test Grid initialization and basic properties."""

    def test_create_sparse_grid(self) -> None:
        """Test creating a sparse grid."""
        grid = Grid(10, 10, 1, StorageType.SPARSE)
        assert grid.width == 10
        assert grid.height == 10
        assert grid.depth == 1
        assert grid.storage_type == StorageType.SPARSE

    def test_create_dense_grid(self) -> None:
        """Test creating a dense grid."""
        pytest.importorskip("numpy")
        grid = Grid(10, 10, 1, StorageType.DENSE)
        assert grid.width == 10
        assert grid.height == 10
        assert grid.depth == 1
        assert grid.storage_type == StorageType.DENSE

    def test_invalid_dimensions(self) -> None:
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError):
            Grid(0, 10, 1)
        with pytest.raises(ValueError):
            Grid(10, -1, 1)
        with pytest.raises(ValueError):
            Grid(10, 10, 0)

    def test_repr(self) -> None:
        """Test Grid string representation."""
        grid = Grid(10, 10, 1)
        assert repr(grid) == "Grid(width=10, height=10, depth=1, storage_type=SPARSE)"


class TestGridObstacles:
    """Test obstacle handling."""

    def test_no_obstacles_by_default(self) -> None:
        """Test that cells are not obstacles by default."""
        grid = Grid(10, 10, 1)
        assert not grid.is_obstacle(0, 0, 0)
        assert not grid.is_obstacle(5, 5, 0)
        assert not grid.is_obstacle(9, 9, 0)

    def test_set_obstacle(self) -> None:
        """Test setting obstacles."""
        grid = Grid(10, 10, 1)
        grid.set_obstacle(5, 5, 0, True)
        assert grid.is_obstacle(5, 5, 0)
        assert not grid.is_obstacle(4, 5, 0)

    def test_remove_obstacle(self) -> None:
        """Test removing obstacles."""
        grid = Grid(10, 10, 1)
        grid.set_obstacle(5, 5, 0, True)
        grid.set_obstacle(5, 5, 0, False)
        assert not grid.is_obstacle(5, 5, 0)

    def test_obstacle_out_of_bounds(self) -> None:
        """Test that checking obstacles out of bounds raises ValueError."""
        grid = Grid(10, 10, 1)
        with pytest.raises(ValueError, match="out of bounds"):
            grid.is_obstacle(-1, 0, 0)
        with pytest.raises(ValueError, match="out of bounds"):
            grid.is_obstacle(10, 0, 0)
        with pytest.raises(ValueError, match="out of bounds"):
            grid.is_obstacle(0, 10, 0)
        with pytest.raises(ValueError, match="out of bounds"):
            grid.is_obstacle(0, 0, 1)


class TestGridCosts:
    """Test cost handling."""

    def test_default_cost(self) -> None:
        """Test that cells have default cost of 1.0."""
        grid = Grid(10, 10, 1)
        assert grid.get_cost(5, 5, 0) == 1.0

    def test_set_cost(self) -> None:
        """Test setting cell costs."""
        grid = Grid(10, 10, 1)
        grid.set_cost(5, 5, 0, 2.5)
        assert grid.get_cost(5, 5, 0) == 2.5

    def test_invalid_cost(self) -> None:
        """Test that non-positive costs raise ValueError."""
        grid = Grid(10, 10, 1)
        with pytest.raises(ValueError, match="must be positive"):
            grid.set_cost(5, 5, 0, 0)
        with pytest.raises(ValueError, match="must be positive"):
            grid.set_cost(5, 5, 0, -1.0)


class TestGridMemory:
    """Test memory usage calculation."""

    def test_memory_usage(self) -> None:
        """Test memory usage property returns a positive value."""
        grid = Grid(10, 10, 1)
        assert grid.memory_usage > 0

    def test_memory_usage_increases_with_obstacles(self) -> None:
        """Test that memory usage increases with more obstacles."""
        grid1 = Grid(10, 10, 1)
        mem1 = grid1.memory_usage

        grid2 = Grid(10, 10, 1)
        for x in range(10):
            for y in range(10):
                grid2.set_obstacle(x, y, 0, True)
        mem2 = grid2.memory_usage

        # More obstacles should use more memory
        assert mem2 > mem1


class TestGridHash:
    """Test grid hashing for cache invalidation."""

    def test_hash_same_for_same_grid(self) -> None:
        """Test that identical grids produce same hash."""
        grid1 = Grid(10, 10, 1)
        grid2 = Grid(10, 10, 1)
        assert grid1.hash() == grid2.hash()

    def test_hash_changes_with_obstacle(self) -> None:
        """Test that hash changes when obstacle is added."""
        grid = Grid(10, 10, 1)
        hash1 = grid.hash()
        grid.set_obstacle(5, 5, 0, True)
        hash2 = grid.hash()
        assert hash1 != hash2

    def test_hash_changes_with_cost(self) -> None:
        """Test that hash changes when cost is modified."""
        grid = Grid(10, 10, 1)
        hash1 = grid.hash()
        grid.set_cost(5, 5, 0, 2.0)
        hash2 = grid.hash()
        assert hash1 != hash2


class TestGridContains:
    """Test Grid.__contains__ for bounds checking."""

    def test_contains_valid_positions(self) -> None:
        """Test that valid positions are in grid."""
        grid = Grid(10, 10, 5)
        assert (0, 0, 0) in grid
        assert (5, 5, 2) in grid
        assert (9, 9, 4) in grid

    def test_contains_invalid_positions(self) -> None:
        """Test that invalid positions are not in grid."""
        grid = Grid(10, 10, 5)
        assert (-1, 0, 0) not in grid
        assert (0, -1, 0) not in grid
        assert (0, 0, -1) not in grid
        assert (10, 0, 0) not in grid
        assert (0, 10, 0) not in grid
        assert (0, 0, 5) not in grid
