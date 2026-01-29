"""Warehouse simulation demo with AGV routing."""

from grid_pathfinding import Grid, find_path, HPAStar
from grid_pathfinding.costs import CongestionCost
from grid_pathfinding.algorithms import DynamicReplanner, ReplanStrategy

def main() -> None:
    """Demonstrate warehouse pathfinding."""
    print("=== Warehouse AGV Routing Demo ===\n")

    # Create a warehouse grid (50x25x1)
    grid = Grid(50, 25, 1)
    print(f"Warehouse grid: {grid}")

    # Add shelves as obstacles
    print("\nPlacing shelves...")
    # Rows of shelves
    for y in range(5, 20, 5):
        for x in range(5, 45, 8):
            # 2x3 shelf
            for sx in range(2):
                for sy in range(3):
                    if x + sx < 50 and y + sy < 25:
                        grid.set_obstacle(x + sx, y + sy, 0)

    print(f"Shelves placed")

    # AGV needs to move from pickup to delivery
    pickup = (2, 2, 0)
    delivery = (47, 22, 0)

    print(f"\nRoute planning: {pickup} -> {delivery}")

    # Use HPA* for faster planning on larger grid
    path = find_path(grid, pickup, delivery, algorithm="hpastar")

    if path:
        print(f"\nRoute found!")
        print(f"  Distance: {len(path)} steps")
        print(f"  Computation time: {path.computation_time_ms:.2f}ms")

    # Simulate congestion
    print("\n=== Congestion Simulation ===")
    cost_fn = CongestionCost(base_cost=1.0, radius=3)

    # Add other AGVs at key positions
    other_agvs = [(25, 12, 0), (30, 15, 0), (20, 10, 0)]
    for pos in other_agvs:
        cost_fn.add_agent(pos)

    print(f"Other AGVs: {cost_fn.agent_count}")

    # Dynamic replanning when obstacles appear
    print("\n=== Dynamic Replanning ===")
    replanner = DynamicReplanner(strategy=ReplanStrategy.REPAIR)

    # Get initial path
    path = find_path(grid, (5, 2, 0), (45, 22, 0))
    print(f"Initial path: {len(path)} steps")

    # Simulate an obstacle appearing (spilled cargo)
    grid.set_obstacle(25, 12, 0, True)
    print("\nObstacle detected at (25, 12, 0)!")

    # AGV is at position (20, 12, 0) when obstacle detected
    new_path = replanner.replan(grid, path, (20, 12, 0))
    if new_path:
        print(f"Replanned path: {len(new_path)} steps")
        print(f"Successfully rerouted around obstacle!")


if __name__ == "__main__":
    main()
