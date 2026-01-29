"""3D cardinal movement pattern (6 directions)."""

from grid_pathfinding.movement.base import Movement


class Cardinal3D(Movement):
    """6-directional movement in 3D space (cardinal directions only).

    This movement pattern allows movement along the cardinal axes:
    - Left/Right (±X)
    - Forward/Backward (±Y)
    - Up/Down (±Z)

    Each move has a base cost of 1.0.

    Examples:
        >>> from grid_pathfinding.core.grid import Grid
        >>> grid = Grid(10, 10, 10)
        >>> movement = Cardinal3D()
        >>> neighbors = movement.get_neighbors(grid, 5, 5, 5)
        >>> len(neighbors)
        6
        >>> (6, 5, 5) in neighbors  # Right
        True
    """

    # 6 cardinal directions: ±X, ±Y, ±Z
    _DIRECTIONS = [
        (1, 0, 0),  # Right
        (-1, 0, 0),  # Left
        (0, 1, 0),  # Forward (or up in 2D)
        (0, -1, 0),  # Backward (or down in 2D)
        (0, 0, 1),  # Up (3D)
        (0, 0, -1),  # Down (3D)
    ]

    __slots__ = ()

    def get_neighbors(
        self,
        grid: "Grid",
        x: int,
        y: int,
        z: int,
    ) -> list[tuple[int, int, int]]:
        """Get valid neighboring positions using 6-directional movement.

        Args:
            grid: The grid to navigate on.
            x: X coordinate of current position.
            y: Y coordinate of current position.
            z: Z coordinate of current position.

        Returns:
            List of valid neighboring (x, y, z) tuples that are:
            - Within grid bounds
            - Not obstacles
        """
        neighbors = []

        for dx, dy, dz in self._DIRECTIONS:
            nx, ny, nz = x + dx, y + dy, z + dz

            # Check bounds
            if (nx, ny, nz) in grid:
                # Check obstacle
                if not grid.is_obstacle(nx, ny, nz):
                    neighbors.append((nx, ny, nz))

        return neighbors

    def __repr__(self) -> str:
        """Return string representation."""
        return "Cardinal3D()"
