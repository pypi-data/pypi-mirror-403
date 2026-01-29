"""Game NPC pathfinding demonstration."""

from grid_pathfinding import Grid, find_path
from grid_pathfinding.algorithms import DynamicReplanner, ReplanStrategy

def create_dungeon_grid() -> Grid:
    """Create a simple dungeon with rooms and corridors."""
    grid = Grid(40, 30, 2)

    # Stone walls (outer boundary)
    for x in range(40):
        grid.set_obstacle(x, 0, 0)
        grid.set_obstacle(x, 29, 0)
    for y in range(30):
        grid.set_obstacle(0, y, 0)
        grid.set_obstacle(39, y, 0)

    # Room 1 (top-left)
    for x in range(5, 15):
        for y in range(5, 15):
            if x in (5, 14) or y in (5, 14):
                grid.set_obstacle(x, y, 0)

    # Room 2 (top-right)
    for x in range(25, 35):
        for y in range(5, 15):
            if x in (25, 34) or y in (5, 14):
                grid.set_obstacle(x, y, 0)

    # Room 3 (bottom-center)
    for x in range(15, 25):
        for y in range(20, 28):
            if x in (15, 24) or y in (20, 27):
                grid.set_obstacle(x, y, 0)

    # Corridors (remove some walls)
    # Room 1 to Room 2
    for x in range(15, 25):
        grid.set_obstacle(x, 10, 0, False)

    # Room 1 to Room 3
    for y in range(15, 20):
        grid.set_obstacle(10, y, 0, False)

    # Room 2 to Room 3
    for y in range(15, 20):
        grid.set_obstacle(30, y, 0, False)

    # Add some pillars
    grid.set_obstacle(20, 10, 0, True)
    grid.set_obstacle(20, 10, 1, True)

    return grid

def main() -> None:
    """Demonstrate game NPC pathfinding."""
    print("=== Game NPC Pathfinding Demo ===\n")

    grid = create_dungeon_grid()
    print(f"Dungeon created: {grid}")

    # NPC needs to navigate through dungeon
    npc_start = (10, 10, 0)
    npc_goal = (20, 24, 0)

    print(f"\nNPC path: {npc_start} -> {npc_goal}")

    path = find_path(grid, npc_start, npc_goal)

    if path:
        print(f"\nPath found!")
        print(f"  Steps: {len(path)}")
        print(f"  Time: {path.computation_time_ms:.2f}ms")

        # Compress for smoother movement
        smooth_path = path.compress()
        print(f"  Smooth path: {len(smooth_path)} waypoints")

    # Dynamic door closing
    print("\n=== Dynamic Environment ===")
    replanner = DynamicReplanner(strategy=ReplanStrategy.REPAIR)

    # Get path through corridor
    path = find_path(grid, (8, 10, 0), (32, 10, 0))
    print(f"Path through corridor: {len(path)} steps")

    # Door closes!
    grid.set_obstacle(20, 10, 0, True)
    print("\nDoor closed at (20, 10)!")

    # NPC is at (18, 10, 0) when door closes
    new_path = replanner.replan(grid, path, (18, 10, 0))
    if new_path:
        print(f"New path: {len(new_path)} steps")
        print("NPC finds alternative route!")


if __name__ == "__main__":
    main()
