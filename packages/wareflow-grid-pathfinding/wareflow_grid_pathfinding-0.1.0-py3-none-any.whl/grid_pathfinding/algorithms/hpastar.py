"""HPA* (Hierarchical Pathfinding A*) implementation."""

import heapq
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from grid_pathfinding.algorithms.astar import AStar

if TYPE_CHECKING:
    from grid_pathfinding.core.grid import Grid
    from grid_pathfinding.core.node import Path
    from grid_pathfinding.heuristics.base import Heuristic
    from grid_pathfinding.movement.base import Movement


@dataclass(slots=True, frozen=True)
class Cluster:
    """A cluster (subregion) of the grid for hierarchical pathfinding.

    Attributes:
        x: X coordinate of cluster origin.
        y: Y coordinate of cluster origin.
        z: Z coordinate of cluster origin.
        width: Cluster width.
        height: Cluster height.
        depth: Cluster depth.
    """

    x: int
    y: int
    z: int
    width: int
    height: int
    depth: int

    def contains(self, pos: tuple[int, int, int]) -> bool:
        """Check if a position is within this cluster."""
        px, py, pz = pos
        return (
            self.x <= px < self.x + self.width
            and self.y <= py < self.y + self.height
            and self.z <= pz < self.z + self.depth
        )

    def entrances(
        self,
        grid: "Grid",
        movement: "Movement",
    ) -> list[tuple[int, int, int]]:
        """Get entrance cells (boundary cells accessible from outside).

        Args:
            grid: The grid to check obstacles.
            movement: Movement pattern for finding neighbors.

        Returns:
            List of entrance positions.
        """
        entrances: list[tuple[int, int, int]] = []

        # Check all cells on the cluster boundary
        for dz in range(self.depth):
            for dy in range(self.height):
                for dx in range(self.width):
                    cx, cy, cz = self.x + dx, self.y + dy, self.z + dz

                    # Check if this cell is on the boundary
                    on_boundary = (
                        dx == 0
                        or dx == self.width - 1
                        or dy == 0
                        or dy == self.height - 1
                        or dz == 0
                        or dz == self.depth - 1
                    )

                    if not on_boundary:
                        continue

                    # Check if traversable
                    if grid.is_obstacle(cx, cy, cz):
                        continue

                    # Check if has neighbor outside cluster
                    for neighbor in movement.get_neighbors(grid, cx, cy, cz):
                        if not self.contains(neighbor):
                            entrances.append((cx, cy, cz))
                            break

        return entrances


@dataclass(slots=True, frozen=True)
class AbstractNode:
    """A node in the abstract graph.

    Attributes:
        position: Grid position.
        cluster: The cluster this node belongs to.
    """

    position: tuple[int, int, int]
    cluster: Cluster


@dataclass(slots=True)
class AbstractEdge:
    """An edge in the abstract graph.

    Attributes:
        from_node: Source abstract node.
        to_node: Target abstract node.
        cost: Edge cost.
        path: Local path between nodes.
    """

    from_node: AbstractNode
    to_node: AbstractNode
    cost: float
    path: list[tuple[int, int, int]] = field(default_factory=list)


class HPAStar(AStar):
    """Hierarchical Pathfinding A* (HPA*).

    HPA* decomposes the grid into clusters, builds an abstract graph,
    and performs pathfinding on the abstract graph for efficiency.

    Attributes:
        cluster_size: Size of each cluster (width, height, depth).
        heuristic: Heuristic function.
        movement: Movement pattern.

    Examples:
        >>> from grid_pathfinding.core.grid import Grid
        >>> algo = HPAStar(cluster_size=(10, 10, 2))
        >>> grid = Grid(100, 100, 10)
        >>> path = algo.find_path(grid, (0, 0, 0), (99, 99, 9))
    """

    __slots__ = ("_cluster_size", "_abstract_graph", "_clusters")

    def __init__(
        self,
        cluster_size: tuple[int, int, int] = (10, 10, 2),
        heuristic: "Heuristic | None" = None,
        movement: "Movement | None" = None,
    ) -> None:
        """Initialize HPA*.

        Args:
            cluster_size: Size of each cluster (width, height, depth).
            heuristic: Optional heuristic function.
            movement: Optional movement pattern.
        """
        super().__init__(heuristic=heuristic, movement=movement)
        self._cluster_size = cluster_size
        self._abstract_graph: dict[AbstractNode, list[tuple[AbstractNode, float]]] = {}
        self._clusters: list[Cluster] = []

    def _build_clusters(
        self,
        grid: "Grid",
    ) -> list[Cluster]:
        """Divide grid into clusters.

        Args:
            grid: The grid to cluster.

        Returns:
            List of clusters.
        """
        clusters = []
        cw, ch, cd = self._cluster_size

        for z in range(0, grid.depth, cd):
            for y in range(0, grid.height, ch):
                for x in range(0, grid.width, cw):
                    # Adjust cluster size if at boundary
                    width = min(cw, grid.width - x)
                    height = min(ch, grid.height - y)
                    depth = min(cd, grid.depth - z)

                    clusters.append(Cluster(x, y, z, width, height, depth))

        return clusters

    def _build_abstract_graph(
        self,
        grid: "Grid",
    ) -> tuple[
        dict[AbstractNode, list[tuple[AbstractNode, float]]],
        dict[tuple[int, int, int], AbstractNode],
    ]:
        """Build the abstract graph.

        Args:
            grid: The grid to build graph for.

        Returns:
            Tuple of (abstract graph, position to node mapping).
        """
        graph: dict[AbstractNode, list[tuple[AbstractNode, float]]] = {}
        pos_to_node: dict[tuple[int, int, int], AbstractNode] = {}

        # Create abstract nodes at cluster entrances
        for cluster in self._clusters:
            for pos in cluster.entrances(grid, self.movement):
                if pos not in pos_to_node:
                    node = AbstractNode(position=pos, cluster=cluster)
                    pos_to_node[pos] = node
                    graph[node] = []

        # Add start and goal nodes
        # (These will be added dynamically during search)

        return graph, pos_to_node

    def _find_local_path(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> list[tuple[int, int, int]] | None:
        """Find a local path within a cluster.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.

        Returns:
            List of positions if path found, None otherwise.
        """
        # Use A* with a limited search scope
        path = super().find_path(grid, start, goal)
        if path:
            return path.waypoints
        return None

    def find_path(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
    ) -> "Path | None":
        """Find a path using HPA*.

        Args:
            grid: The grid to search on.
            start: Starting position.
            goal: Goal position.

        Returns:
            Path object if found, None otherwise.
        """
        # Validate positions (reuse parent class logic)
        if start not in grid:
            raise ValueError(f"Start position {start} out of bounds")
        if grid.is_obstacle(*start):
            raise ValueError(f"Start position {start} is an obstacle")
        if goal not in grid:
            raise ValueError(f"Goal position {goal} out of bounds")
        if grid.is_obstacle(*goal):
            raise ValueError(f"Goal position {goal} is an obstacle")

        # Early exit
        if start == goal:
            from grid_pathfinding.core.node import Path

            return Path([start], 0.0, 0.0, 0)

        start_time = time.perf_counter()

        # Build clusters
        self._clusters = self._build_clusters(grid)

        # Build abstract graph
        graph, pos_to_node = self._build_abstract_graph(grid)

        # Add start and goal as temporary abstract nodes
        start_cluster = next((c for c in self._clusters if c.contains(start)), None)
        goal_cluster = next((c for c in self._clusters if c.contains(goal)), None)

        if start_cluster is None or goal_cluster is None:
            # Fallback to regular A* if clustering failed
            return super().find_path(grid, start, goal)

        # Run high-level A* on abstract graph
        abstract_path = self._abstract_a_star(
            grid, start, goal, graph, pos_to_node
        )

        if not abstract_path:
            # Fallback to regular A*
            return super().find_path(grid, start, goal)

        # Refine path with local searches
        full_path = [start]
        total_cost = 0.0

        for i in range(len(abstract_path) - 1):
            current = abstract_path[i]
            next_pos = abstract_path[i + 1]

            # Find local path
            if current == start:
                local_end = next_pos
            else:
                local_end = next_pos

            local_path = self._find_local_path(grid, current, local_end)
            if local_path:
                # Skip first position as it's already in full_path
                full_path.extend(local_path[1:])
                total_cost += sum(
                    grid.get_cost(*local_path[j]) for j in range(len(local_path) - 1)
                )
            else:
                # Fallback to direct connection
                if current != local_end:
                    full_path.append(local_end)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        from grid_pathfinding.core.node import Path

        # Count nodes in abstract path as approximation
        nodes_explored = len(abstract_path) * 10

        return Path(
            waypoints=full_path,
            total_cost=total_cost,
            computation_time_ms=elapsed_ms,
            nodes_explored=nodes_explored,
        )

    def _abstract_a_star(
        self,
        grid: "Grid",
        start: tuple[int, int, int],
        goal: tuple[int, int, int],
        graph: dict[AbstractNode, list[tuple[AbstractNode, float]]],
        pos_to_node: dict[tuple[int, int, int], AbstractNode],
    ) -> list[tuple[int, int, int]]:
        """Run A* on the abstract graph.

        Args:
            grid: The grid.
            start: Start position.
            goal: Goal position.
            graph: Abstract graph.
            pos_to_node: Position to node mapping.

        Returns:
            List of positions forming the abstract path.
        """
        # Find nearest abstract nodes to start and goal
        start_nodes = self._find_nearby_abstract_nodes(start, pos_to_node)
        goal_nodes = self._find_nearby_abstract_nodes(goal, pos_to_node)

        if not start_nodes or not goal_nodes:
            return []

        # Try combinations of start/goal nodes
        best_path = None
        best_cost = float("inf")

        for sn in start_nodes:
            for gn in goal_nodes:
                path = self._abstract_search(graph, sn, gn)
                if path:
                    # Build full path
                    full = [start]
                    full.extend(p.position for p in path)
                    full.append(goal)

                    # Estimate cost
                    cost = self._estimate_path_cost(grid, full)
                    if cost < best_cost:
                        best_cost = cost
                        best_path = full

        return best_path if best_path else []

    def _find_nearby_abstract_nodes(
        self,
        pos: tuple[int, int, int],
        pos_to_node: dict[tuple[int, int, int], AbstractNode],
    ) -> list[AbstractNode]:
        """Find abstract nodes near a position."""
        # Find the cluster containing this position
        cluster = next(
            (c for c in self._clusters if c.contains(pos)), None
        )
        if not cluster:
            return []

        # Return all nodes in this cluster
        return [
            node for node in pos_to_node.values() if node.cluster == cluster
        ]

    def _abstract_search(
        self,
        graph: dict[AbstractNode, list[tuple[AbstractNode, float]]],
        start: AbstractNode,
        goal: AbstractNode,
    ) -> list[AbstractNode] | None:
        """Run A* on abstract graph."""
        open_set = [(0, start)]
        came_from: dict[AbstractNode, AbstractNode] = {}
        g_score: dict[AbstractNode, float] = {start: 0}

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = [current]
                while current != start:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor, cost in graph.get(current, []):
                tentative_g = g_score[current] + cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self.heuristic.calculate(neighbor.position, goal.position)
                    f = tentative_g + h
                    heapq.heappush(open_set, (f, neighbor))

        return None

    def _estimate_path_cost(
        self,
        grid: "Grid",
        path: list[tuple[int, int, int]],
    ) -> float:
        """Estimate the cost of a path."""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += grid.get_cost(*path[i])
        return cost

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"HPAStar(cluster_size={self._cluster_size}, "
            f"heuristic={self.heuristic!r}, movement={self.movement!r})"
        )
