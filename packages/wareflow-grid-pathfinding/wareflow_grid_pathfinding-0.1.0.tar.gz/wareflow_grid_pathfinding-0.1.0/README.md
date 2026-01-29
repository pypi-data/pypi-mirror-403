# grid-pathfinding

High-performance 3D grid pathfinding with A* and HPA* algorithms.

## Features

- **A*** - Optimal pathfinding with heuristic search
- **HPA*** (Hierarchical Pathfinding A*) - Fast pathfinding on large grids
- **Dynamic Replanning** - Handle temporary obstacles during path execution
- **Custom Heuristics** - Manhattan, Euclidean, or create your own
- **Movement Patterns** - 6-directional (3D) or custom patterns
- **Cost Functions** - Support for terrain costs, congestion, etc.
- **Path Caching** - LRU cache with automatic invalidation
- **Pure Python** - No external dependencies (NumPy optional for dense storage)

## Installation

```bash
pip install grid-pathfinding
```

Or with uv:

```bash
uv pip install grid-pathfinding
```

## Quick Start

```python
from grid_pathfinding import Grid, find_path

# Create a 10x10x1 grid
grid = Grid(10, 10, 1)

# Find a path from (0, 0, 0) to (9, 9, 0)
path = find_path(grid, (0, 0, 0), (9, 9, 0))

# Iterate over waypoints
for pos in path:
    print(pos)

# Get path statistics
print(f"Cost: {path.total_cost}")
print(f"Time: {path.computation_time_ms}ms")
print(f"Nodes explored: {path.nodes_explored}")
```

## Examples

### With Obstacles

```python
from grid_pathfinding import Grid, find_path

grid = Grid(20, 20, 1)

# Add some obstacles
for x in range(5, 15):
    grid.set_obstacle(x, 10, 0)

path = find_path(grid, (0, 10, 0), (19, 10, 0))
# Path navigates around the wall
```

### Using HPA* for Large Grids

```python
from grid_pathfinding import Grid, find_path

# Large grid - HPA* is faster
grid = Grid(200, 200, 10)

path = find_path(grid, (0, 0, 0), (199, 199, 9), algorithm="hpastar")
```

### Dynamic Replanning

```python
from grid_pathfinding import Grid, find_path
from grid_pathfinding.algorithms import DynamicReplanner, ReplanStrategy

grid = Grid(50, 50, 1)
replanner = DynamicReplanner(strategy=ReplanStrategy.REPAIR)

# Get initial path
path = find_path(grid, (0, 0, 0), (49, 49, 0))

# New obstacle appears during execution
grid.set_obstacle(25, 25, 0, True)

# Replan from current position
new_path = replanner.replan(grid, path, (24, 25, 0))
```

### With Path Caching

```python
from grid_pathfinding import Grid, find_path
from grid_pathfinding.cache import PathCache

grid = Grid(100, 100, 10)
cache = PathCache(max_size=100)

# First call computes the path
path1 = cache.get_or_compute(grid, (0, 0, 0), (99, 99, 9))

# Second call returns cached result (much faster)
path2 = cache.get_or_compute(grid, (0, 0, 0), (99, 99, 9))

print(cache.stats)
# {'hits': 1, 'misses': 1, 'evictions': 0, 'size': 1, 'hit_rate': 0.5}
```

## API Reference

### Core Classes

#### `Grid`

```python
grid = Grid(width, height, depth, storage_type=StorageType.SPARSE)
```

- `is_obstacle(x, y, z)` - Check if a cell is blocked
- `set_obstacle(x, y, z, is_obstacle=True)` - Set obstacle state
- `get_cost(x, y, z)` - Get movement cost for a cell
- `set_cost(x, y, z, cost)` - Set movement cost
- `memory_usage` - Property: memory used in bytes

#### `Path`

```python
# Result from find_path()
path.waypoints        # List of (x, y, z) tuples
path.total_cost       # Total path cost
path.computation_time_ms  # Time to find path (ms)
path.nodes_explored  # Nodes searched

# Path operations
len(path)            # Number of waypoints
for pos in path: ... # Iterate waypoints
path.compress()      # Remove collinear waypoints
path.segments()      # Get as list of segments
```

### Algorithms

#### `AStar`

```python
from grid_pathfinding import AStar, ManhattanDistance, Cardinal3D

algo = AStar(
    heuristic=ManhattanDistance(),
    movement=Cardinal3D()
)
path = algo.find_path(grid, start, goal)
```

#### `HPAStar`

```python
from grid_pathfinding import HPAStar

algo = HPAStar(cluster_size=(10, 10, 2))
path = algo.find_path(grid, start, goal)
```

### Heuristics

- `ManhattanDistance(use_3d=True)` - L1 distance (6-dir movement)
- `EuclideanDistance(use_3d=True)` - L2 distance (26-dir movement)

### Movement Patterns

- `Cardinal3D` - 6 directions (±X, ±Y, ±Z)

## Performance

Benchmarks on typical hardware:

| Grid Size | Algorithm | Time | Memory |
|-----------|-----------|------|--------|
| 100×100×10 | A* | ~1.5ms | <1MB |
| 200×200×10 | HPA* | ~2-3ms | <2MB |

## Requirements

- Python 3.9+
- No external dependencies for sparse grids
- NumPy (optional) for dense grid storage

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=grid_pathfinding

# Run benchmarks
uv run pytest --benchmark-only
```

## License

MIT
