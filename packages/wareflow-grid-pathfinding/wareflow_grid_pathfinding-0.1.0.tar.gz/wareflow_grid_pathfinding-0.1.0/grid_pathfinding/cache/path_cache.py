"""LRU cache for pathfinding results."""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid
    from grid_pathfinding.core.node import Path


@dataclass
class CacheEntry:
    """A cached path entry.

    Attributes:
        path: The cached path.
        timestamp: When the path was cached.
        access_count: Number of times this entry was accessed.
    """

    path: "Path"
    timestamp: float
    access_count: int = 0


class PathCache:
    """LRU cache for pathfinding results.

    Automatically invalidates when grid changes (using hash).
    Supports optional TTL (time-to-live) for entries.

    Attributes:
        max_size: Maximum number of cached paths.
        ttl_seconds: Optional TTL for cache entries.
        default_algorithm: Default algorithm to use for cache misses.

    Examples:
        >>> from grid_pathfinding.core.grid import Grid
        >>> cache = PathCache(max_size=100)
        >>> grid = Grid(10, 10, 1)
        >>> path = cache.get_or_compute(grid, (0, 0, 0), (9, 9, 0))
        >>> # Second call returns cached result
        >>> path2 = cache.get_or_compute(grid, (0, 0, 0), (9, 9, 0))
        >>> path is path2
        True
    """

    __slots__ = (
        "_cache",
        "_max_size",
        "_ttl_seconds",
        "_compute_func",
        "_stats",
    )

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: float | None = None,
        default_algorithm: str = "astar",
    ) -> None:
        """Initialize the path cache.

        Args:
            max_size: Maximum number of cached paths.
            ttl_seconds: Optional TTL for cache entries in seconds.
            default_algorithm: Default algorithm for cache misses.
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def _make_key(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> str:
        """Create a cache key for a query.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.

        Returns:
            Cache key string.
        """
        grid_hash = grid.hash()
        key_parts = (
            str(grid_hash),
            str(start),
            str(goal),
        )
        return hashlib.sha256("|".join(key_parts).encode()).hexdigest()

    def get(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Get a cached path if available and valid.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.

        Returns:
            Cached path if found and valid, None otherwise.
        """
        key = self._make_key(grid, start, goal)

        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[key]

        # Check TTL
        if self._ttl_seconds is not None:
            age = time.time() - entry.timestamp
            if age > self._ttl_seconds:
                # Expired
                del self._cache[key]
                self._stats["misses"] += 1
                return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access_count += 1
        self._stats["hits"] += 1

        return entry.path

    def put(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
        path: "Path",
    ) -> None:
        """Cache a path result.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.
            path: The path to cache.
        """
        key = self._make_key(grid, start, goal)

        # Check if we need to evict
        if key not in self._cache and len(self._cache) >= self._max_size:
            # Remove least recently used (first item)
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1

        entry = CacheEntry(
            path=path,
            timestamp=time.time(),
        )
        self._cache[key] = entry
        self._cache.move_to_end(key)

    def invalidate(self, grid: "Grid") -> None:
        """Invalidate all cached paths for a grid.

        This is called automatically when grid changes are detected.
        For simplicity, this clears all cache entries.

        Args:
            grid: The grid that changed.
        """
        self._cache.clear()

    def get_or_compute(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
        algorithm: str = "astar",
    ) -> "Path | None":
        """Get cached path or compute if not cached.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.
            algorithm: Algorithm to use for computation.

        Returns:
            Path object if found, None otherwise.
        """
        # Try cache first
        cached = self.get(grid, start, goal)
        if cached is not None:
            return cached

        # Cache miss - compute path
        from grid_pathfinding import find_path

        path = find_path(grid, start, goal, algorithm=algorithm)

        # Cache the result (even if None, to avoid recomputing)
        if path is not None:
            self.put(grid, start, goal, path)

        return path

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)

    @property
    def stats(self) -> dict[str, int]:
        """Get cache statistics."""
        stats = self._stats.copy()
        stats["size"] = len(self._cache)
        if stats["hits"] + stats["misses"] > 0:
            stats["hit_rate"] = stats["hits"] / (stats["hits"] + stats["misses"])
        else:
            stats["hit_rate"] = 0.0
        return stats

    def __repr__(self) -> str:
        """Return string representation."""
        return f"PathCache(size={len(self._cache)}/{self._max_size}, stats={self.stats})"
