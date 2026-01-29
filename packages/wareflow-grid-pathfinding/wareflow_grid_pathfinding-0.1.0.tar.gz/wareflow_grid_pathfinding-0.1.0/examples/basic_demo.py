"""Basic grid pathfinding demonstration."""

from grid_pathfinding import Grid, find_path

def main() -> None:
    """Demonstrate basic pathfinding."""
    print("=== Basic Pathfinding Demo ===\n")

    # Create a simple grid
    grid = Grid(20, 20, 1)
    print(f"Created grid: {grid}")

    # Add some obstacles (a wall with a gap)
    print("\nAdding obstacles...")
    for x in range(5, 15):
        if x != 10:  # Leave a gap at x=10
            grid.set_obstacle(x, 10, 0)

    # Find a path
    start = (0, 10, 0)
    goal = (19, 10, 0)

    print(f"\nFinding path from {start} to {goal}...")
    path = find_path(grid, start, goal)

    if path:
        print(f"\nPath found!")
        print(f"  Waypoints: {len(path)}")
        print(f"  Total cost: {path.total_cost:.2f}")
        print(f"  Computation time: {path.computation_time_ms:.2f}ms")
        print(f"  Nodes explored: {path.nodes_explored}")

        # Print first few waypoints
        print(f"\nFirst 5 waypoints: {path.waypoints[:5]}")
        print(f"Last 5 waypoints: {path.waypoints[-5:]}")

        # Compress the path (remove collinear waypoints)
        compressed = path.compress()
        print(f"\nCompressed path: {len(compressed)} waypoints")
    else:
        print("No path found!")

    # Example: No path exists
    print("\n=== Blocked Path Example ===")
    blocked_grid = Grid(10, 10, 1)
    # Block entire middle
    for x in range(10):
        blocked_grid.set_obstacle(x, 5, 0)

    path = find_path(blocked_grid, (0, 0, 0), (9, 9, 0))
    if path is None:
        print("Path blocked - no way to reach goal!")


if __name__ == "__main__":
    main()
