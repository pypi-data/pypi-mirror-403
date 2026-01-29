"""Grid implementation for 3D pathfinding."""

import hashlib
import sys
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class StorageType(IntEnum):
    """Storage type for grid data."""

    SPARSE = 0
    DENSE = 1


class Grid:
    """3D grid for pathfinding with sparse or dense storage.

    Attributes:
        width: Grid width (x-axis).
        height: Grid height (y-axis).
        depth: Grid depth (z-axis).
        storage_type: Storage mode (SPARSE or DENSE).

    Examples:
        >>> grid = Grid(10, 10, 1)
        >>> grid.set_obstacle(5, 5, 0)
        >>> grid.is_obstacle(5, 5, 0)
        True
        >>> grid.is_obstacle(0, 0, 0)
        False
    """

    __slots__ = ("_width", "_height", "_depth", "_storage_type", "_obstacles", "_costs", "_array")

    def __init__(
        self,
        width: int,
        height: int,
        depth: int,
        storage_type: StorageType = StorageType.SPARSE,
    ) -> None:
        """Initialize a new Grid.

        Args:
            width: Grid width (x-axis), must be positive.
            height: Grid height (y-axis), must be positive.
            depth: Grid depth (z-axis), must be positive.
            storage_type: Storage mode (SPARSE or DENSE). Defaults to SPARSE.

        Raises:
            ValueError: If dimensions are not positive.
        """
        if width <= 0 or height <= 0 or depth <= 0:
            raise ValueError("Grid dimensions must be positive integers")

        self._width = width
        self._height = height
        self._depth = depth
        self._storage_type = storage_type

        if storage_type == StorageType.DENSE:
            try:
                import numpy as np

                # Boolean array for obstacles, float array for costs
                self._array: np.ndarray | None = np.zeros(
                    (depth, height, width), dtype=np.uint8
                )
            except ImportError:
                raise ImportError(
                    "NumPy is required for DENSE storage. "
                    "Install with 'pip install numpy' or use SPARSE storage."
                )
            self._obstacles: dict[tuple[int, int, int], bool] = {}
            self._costs: dict[tuple[int, int, int], float] = {}
        else:
            self._obstacles: dict[tuple[int, int, int], bool] = {}
            self._costs: dict[tuple[int, int, int], float] = {}
            self._array = None

    @property
    def width(self) -> int:
        """Grid width (x-axis)."""
        return self._width

    @property
    def height(self) -> int:
        """Grid height (y-axis)."""
        return self._height

    @property
    def depth(self) -> int:
        """Grid depth (z-axis)."""
        return self._depth

    @property
    def storage_type(self) -> StorageType:
        """Storage mode."""
        return self._storage_type

    def _validate_position(self, x: int, y: int, z: int) -> None:
        """Validate that a position is within grid bounds.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate.

        Raises:
            ValueError: If position is out of bounds.
        """
        if not (0 <= x < self._width and 0 <= y < self._height and 0 <= z < self._depth):
            raise ValueError(
                f"Position ({x}, {y}, {z}) out of bounds "
                f"for grid ({self._width}x{self._height}x{self._depth})"
            )

    def is_obstacle(self, x: int, y: int, z: int) -> bool:
        """Check if a cell is an obstacle.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate.

        Returns:
            True if the cell is an obstacle, False otherwise.

        Raises:
            ValueError: If position is out of bounds.
        """
        self._validate_position(x, y, z)

        if self._storage_type == StorageType.DENSE and self._array is not None:
            return bool(self._array[z, y, x])
        return self._obstacles.get((x, y, z), False)

    def set_obstacle(self, x: int, y: int, z: int, is_obstacle: bool = True) -> None:
        """Set a cell as an obstacle or traversable.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate.
            is_obstacle: True to set as obstacle, False to set as traversable.

        Raises:
            ValueError: If position is out of bounds.
        """
        self._validate_position(x, y, z)

        if self._storage_type == StorageType.DENSE and self._array is not None:
            self._array[z, y, x] = 1 if is_obstacle else 0
        else:
            if is_obstacle:
                self._obstacles[(x, y, z)] = True
            else:
                self._obstacles.pop((x, y, z), None)

    def get_cost(self, x: int, y: int, z: int) -> float:
        """Get the movement cost for a cell.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate.

        Returns:
            Movement cost (1.0 for default, higher for difficult terrain).

        Raises:
            ValueError: If position is out of bounds.
        """
        self._validate_position(x, y, z)
        return self._costs.get((x, y, z), 1.0)

    def set_cost(self, x: int, y: int, z: int, cost: float) -> None:
        """Set the movement cost for a cell.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate.
            cost: Movement cost (must be positive).

        Raises:
            ValueError: If position is out of bounds or cost is not positive.
        """
        self._validate_position(x, y, z)
        if cost <= 0:
            raise ValueError(f"Cost must be positive, got {cost}")
        self._costs[(x, y, z)] = cost

    @property
    def memory_usage(self) -> int:
        """Calculate approximate memory usage in bytes.

        Returns:
            Memory usage in bytes.
        """
        # Base object size
        base_size = sys.getsizeof(self)

        if self._storage_type == StorageType.DENSE and self._array is not None:
            # NumPy array size
            base_size += self._array.nbytes
        else:
            # Dict overhead
            for key, value in self._obstacles.items():
                base_size += sys.getsizeof(key) + sys.getsizeof(value)
            for key, value in self._costs.items():
                base_size += sys.getsizeof(key) + sys.getsizeof(value)

        return base_size

    def hash(self) -> str:
        """Calculate a hash of the grid state for cache invalidation.

        Returns:
            SHA256 hash string representing the grid state.
        """
        hasher = hashlib.sha256()
        hasher.update(str(self._width).encode())
        hasher.update(str(self._height).encode())
        hasher.update(str(self._depth).encode())

        if self._storage_type == StorageType.DENSE and self._array is not None:
            hasher.update(self._array.tobytes())
        else:
            # Hash obstacles and costs (sorted for consistency)
            for pos in sorted(self._obstacles.keys()):
                hasher.update(str(pos).encode())
                hasher.update(b"1")
            for pos in sorted(self._costs.keys()):
                hasher.update(str(pos).encode())
                hasher.update(str(self._costs[pos]).encode())

        return hasher.hexdigest()

    def __contains__(self, position: tuple[int, int, int]) -> bool:
        """Check if a position is within grid bounds.

        Args:
            position: (x, y, z) tuple.

        Returns:
            True if position is in bounds, False otherwise.
        """
        x, y, z = position
        return 0 <= x < self._width and 0 <= y < self._height and 0 <= z < self._depth

    def __repr__(self) -> str:
        """Return string representation of the grid."""
        return (
            f"Grid(width={self._width}, height={self._height}, depth={self._depth}, "
            f"storage_type={self._storage_type.name})"
        )
