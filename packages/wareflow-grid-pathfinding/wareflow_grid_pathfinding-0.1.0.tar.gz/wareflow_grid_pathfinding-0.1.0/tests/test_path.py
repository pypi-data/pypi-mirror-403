"""Tests for Path and SearchNode classes."""

import pytest

from grid_pathfinding.core.node import Path, SearchNode


class TestSearchNode:
    """Test SearchNode class."""

    def test_create_node(self) -> None:
        """Test creating a node."""
        node = SearchNode((5, 5, 0), 10.0, 5.0)
        assert node.position == (5, 5, 0)
        assert node.g_cost == 10.0
        assert node.h_cost == 5.0
        assert node.f_cost == 15.0
        assert node.parent is None

    def test_node_with_parent(self) -> None:
        """Test creating a node with a parent."""
        parent = SearchNode((0, 0, 0), 0.0, 10.0)
        child = SearchNode((1, 0, 0), 1.0, 9.0, parent=parent)
        assert child.parent is parent
        assert child.parent.position == (0, 0, 0)

    def test_node_comparison(self) -> None:
        """Test node comparison by f_cost."""
        node1 = SearchNode((0, 0, 0), 5.0, 5.0)  # f=10
        node2 = SearchNode((1, 0, 0), 6.0, 6.0)  # f=12
        assert node1 < node2

        # Tie-break by h_cost
        node3 = SearchNode((2, 0, 0), 6.0, 4.0)  # f=10, h=4
        node4 = SearchNode((3, 0, 0), 4.0, 6.0)  # f=10, h=6
        assert node3 < node4

    def test_node_repr(self) -> None:
        """Test node string representation."""
        node = SearchNode((5, 5, 0), 10.0, 5.0)
        assert "SearchNode" in repr(node)
        assert "(5, 5, 0)" in repr(node)


class TestPath:
    """Test Path class."""

    def test_create_path(self) -> None:
        """Test creating a path."""
        path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 5.0, 10)
        assert len(path) == 3
        assert path.total_cost == 2.0
        assert path.computation_time_ms == 5.0
        assert path.nodes_explored == 10

    def test_path_getitem(self) -> None:
        """Test accessing path waypoints by index."""
        path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 5.0, 10)
        assert path[0] == (0, 0, 0)
        assert path[1] == (1, 0, 0)
        assert path[2] == (2, 0, 0)

    def test_path_iteration(self) -> None:
        """Test iterating over path waypoints."""
        waypoints = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        path = Path(waypoints, 2.0, 5.0, 10)
        result = list(path)
        assert result == waypoints

    def test_path_compress(self) -> None:
        """Test path compression (removes collinear waypoints)."""
        # Straight line - should compress to just endpoints
        path = Path(
            [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0)],
            4.0,
            5.0,
            10,
        )
        compressed = path.compress()
        assert len(compressed) == 2
        assert compressed.waypoints == [(0, 0, 0), (4, 0, 0)]

    def test_path_compress_with_turn(self) -> None:
        """Test path compression preserves turning points."""
        # Path with a turn - should keep the turn
        path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0), (2, 2, 0)], 4.0, 5.0, 10)
        compressed = path.compress()
        assert len(compressed) == 3
        assert compressed.waypoints == [(0, 0, 0), (2, 0, 0), (2, 2, 0)]

    def test_path_compress_short(self) -> None:
        """Test that short paths are not compressed."""
        path = Path([(0, 0, 0), (1, 0, 0)], 1.0, 5.0, 2)
        compressed = path.compress()
        assert len(compressed) == 2

    def test_path_segments(self) -> None:
        """Test getting path as segments."""
        path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 5.0, 3)
        segments = path.segments()
        assert len(segments) == 2
        assert segments[0] == ((0, 0, 0), (1, 0, 0))
        assert segments[1] == ((1, 0, 0), (2, 0, 0))

    def test_path_repr(self) -> None:
        """Test path string representation."""
        path = Path([(0, 0, 0), (1, 0, 0), (2, 0, 0)], 2.0, 5.0, 10)
        assert "Path" in repr(path)
        assert "waypoints=3" in repr(path)
