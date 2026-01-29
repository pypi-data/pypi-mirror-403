# Grid Pathfinding Package

## Overview

A high-performance, extensible 3D grid-based pathfinding library for Python. Designed for warehouse simulations, games, robotics, and operations research applications requiring intelligent agent navigation.

## Problem Statement

Current pathfinding solutions often lack:
- **3D support** for multi-level environments
- **Performance** for real-time applications with 100+ agents
- **Dynamic replanning** for temporary obstacles
- **Extensibility** for custom movement costs (congestion, terrain)
- **Simplicity** with sensible defaults

This package addresses all these needs in a reusable, well-documented library.

## Target Users

### Primary: Waresim (Warehouse Simulation)
- 100 autonomous agents (AGVs, pickers, forklifts)
- 3D warehouse layout (shelves, ramps, elevators)
- Dynamic obstacles (other agents, temporary blockages)
- Performance critical: <50ms per pathfinding call

### Secondary: Game Developers
- NPC navigation in dungeons, cities, terrains
- Fog of war support (partial visibility)
- Terrain-based costs (mud, roads, water)
- Visual debugging tools

### Tertiary: Robotics & Operations Research
- AGV route planning in warehouses/factories
- Layout optimization studies
- Bottleneck analysis
- Multi-agent coordination

## Key Features

### Core Algorithms
- **A\*** (A-Star): Optimal pathfinding with binary heap optimization
- **HPA\*** (Hierarchical Pathfinding A*): 10-100x faster for large grids
- **Dynamic Replanning**: Local repair around temporary obstacles
- **Custom Heuristics**: Manhattan, Euclidean, Chebyshev, or custom

### Grid Support
- **3D grids**: Full (x, y, z) coordinate support
- **Sparse storage**: Dict-based for memory efficiency (open spaces)
- **Dense storage**: NumPy array for performance (dense obstacles)
- **Dynamic obstacles**: Add/remove obstacles at runtime
- **Terrain costs**: Per-cell traversal costs

### Movement Patterns
- **Cardinal 3D**: 6 directions (up/down/left/right/forward/back)
- **Full 3D**: 26 directions (including diagonals)
- **Custom movement**: Define your own neighbor generation

### Advanced Features
- **Congestion avoidance**: Paths automatically avoid crowded areas
- **Path caching**: LRU cache with automatic invalidation
- **Cost functions**: Pluggable custom movement costs
- **Path smoothing**: Remove unnecessary waypoints

## Performance Targets

| Grid Size | Algorithm | Target Time | Target Memory |
|-----------|-----------|-------------|---------------|
| 100×100×10 | A* | <50ms | <5MB |
| 200×200×10 | HPA* | <5ms | <8MB |
| 500×500×20 | HPA* | <20ms | <10MB |

## Quick Start

### Installation

```bash
pip install grid-pathfinding
```

### Basic Usage

```python
from grid_pathfinding import Grid, find_path

# Create a 3D grid
grid = Grid(100, 100, 10)

# Add obstacles (shelves, walls, etc.)
grid.set_obstacle(50, 50, 5, True)

# Find path from start to goal
path = find_path(grid, (0, 0, 0), (99, 99, 9))

if path:
    print(f"Path found with {len(path)} waypoints")
    print(f"Total cost: {path.total_cost}")
    print(f"Computation time: {path.computation_time_ms:.2f}ms")

    # Navigate through waypoints
    for waypoint in path:
        print(f"Move to: {waypoint}")
```

### Advanced Usage: Congestion-Aware Routing

```python
from grid_pathfinding import Grid, Pathfinder, CongestionCost

# Setup warehouse with congestion avoidance
warehouse = Grid(200, 200, 10)

# Create pathfinder with HPA* for performance
pf = Pathfinder(
    width=200,
    height=200,
    depth=10,
    algorithm="hpastar",
    enable_cache=True
)

# Add congestion cost function
congestion = CongestionCost(
    base_cost=1.0,
    congestion_penalty=2.0,
    radius=4
)
pf.algorithm.cost_function = congestion

# Find path that avoids congestion
path = pf.find((0, 0, 0), (199, 199, 9))

# Update agent positions for congestion tracking
congestion.update_agent_position("agv_001", (10, 10, 0))

# Replan when obstacles appear
pf.add_obstacle((50, 50, 5))
new_path = pf.replan()
```

## Architecture

### Module Structure

```
grid_pathfinding/
├── core/
│   ├── grid.py          # Grid representation (sparse/dense)
│   ├── node.py          # SearchNode, Path
│   └── coordinates.py   # Point3D, utilities
├── algorithms/
│   ├── astar.py         # A* implementation
│   ├── hpastar.py       # Hierarchical A*
│   └── replanning.py    # Dynamic replanning
├── heuristics/
│   ├── manhattan.py     # Manhattan distance
│   └── euclidean.py     # Euclidean distance
├── movement/
│   └── cardinal_3d.py   # 6-directional movement
├── costs/
│   └── congestion.py    # Congestion-based costs
└── cache/
    └── path_cache.py    # LRU path caching
```

### Key Design Decisions

| Aspect | Choice | Justification |
|--------|-------|---------------|
| **Grid storage** | Dict (sparse) default, NumPy (dense) optional | Memory efficient for open spaces, fast for dense |
| **Priority queue** | heapq (binary heap) | O(log n), built-in, fast |
| **Result type** | Path object with metadata | Rich API, extensible |
| **Cache strategy** | LRU with composite key | Auto-invalidation on grid changes |
| **Extensibility** | ABC for heuristics/costs/movement | Easy to customize |

## Development Roadmap

### Phase 1: Foundation (MVP)
- [ ] Grid class with sparse/dense storage
- [ ] A* algorithm with heapq optimization
- [ ] Basic heuristics (Manhattan, Euclidean)
- [ ] Cardinal 3D movement
- [ ] Core unit tests

### Phase 2: Performance
- [ ] HPA* implementation with clustering
- [ ] Path caching (LRU)
- [ ] Performance benchmarks
- [ ] Memory profiling

### Phase 3: Advanced Features
- [ ] Dynamic replanning strategies
- [ ] Congestion cost function
- [ ] Custom movement patterns
- [ ] Path smoothing

### Phase 4: Polish
- [ ] Complete API documentation
- [ ] Usage examples (Waresim, games, robotics)
- [ ] Integration tests
- [ ] PyPI publication

## Tooling

We use **uv** as the package manager and **pytest** for testing.

### Setup

```bash
# Install uv
pip install uv

# Initialize project
uv init --name grid-pathfinding
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=grid_pathfinding

# Run benchmarks
uv run pytest --benchmark-only
```

## Dependencies

### Runtime (Optional)
- **NumPy** (optional): For dense grid storage only
- Pure Python mode works without any dependencies

### Development
```bash
uv add --dev pytest pytest-cov pytest-benchmark black mypy
```

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance benchmarks
- **black**: Code formatting
- **mypy**: Type checking

## Success Criteria

- ✅ A* <50ms on 100×100×10 grid
- ✅ HPA* <5ms on 200×200×10 grid
- ✅ Memory usage <10MB including cache
- ✅ Test coverage >90%
- ✅ Simple API (<3 lines for basic usage)
- ✅ Complete documentation with examples
- ✅ PyPI publication

## Contributing

This package follows best practices:
- Type hints for all public APIs
- Google-style docstrings
- pytest for testing
- Semantic versioning
- Clear separation of concerns

## License

MIT License - See LICENSE file for details

## References

- [A* Algorithm](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [HPA* Paper](https://www.aaai.org/Papers/AAAI/2004/AAAI04-100.pdf)
- [Pathfinding in Games](https://www.gamedeveloper.com/programming/implementing-a-in-pathfinding)
