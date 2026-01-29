"""Congestion-based cost function."""

from grid_pathfinding.costs.base import CostFunction


class CongestionCost(CostFunction):
    """Cost function based on agent congestion.

    Increases cost based on the number of nearby agents.
    This is useful for simulating crowded environments.

    Attributes:
        base_cost: Base movement cost.
        radius: Distance to check for other agents.
        agent_positions: Set of current agent positions.

    Examples:
        >>> cost_fn = CongestionCost(base_cost=1.0, radius=2)
        >>> cost_fn.add_agent((5, 5, 0))
        >>> cost_fn.calculate(grid, (4, 5, 0), (5, 5, 0))
        2.0  # Higher cost due to nearby agent
    """

    __slots__ = ("_base_cost", "_radius", "_agent_positions")

    def __init__(
        self,
        base_cost: float = 1.0,
        radius: int = 2,
    ) -> None:
        """Initialize the congestion cost function.

        Args:
            base_cost: Base movement cost (no congestion).
            radius: Distance to check for other agents.
        """
        if base_cost <= 0:
            raise ValueError(f"base_cost must be positive, got {base_cost}")
        if radius < 0:
            raise ValueError(f"radius must be non-negative, got {radius}")

        self._base_cost = base_cost
        self._radius = radius
        self._agent_positions: set[tuple[int, int, int]] = set()

    @property
    def agent_count(self) -> int:
        """Get the current number of agents."""
        return len(self._agent_positions)

    def add_agent(self, position: tuple[int, int, int]) -> None:
        """Add an agent at the given position.

        Args:
            position: Agent position (x, y, z).
        """
        self._agent_positions.add(position)

    def remove_agent(self, position: tuple[int, int, int]) -> None:
        """Remove an agent from the given position.

        Args:
            position: Agent position (x, y, z).
        """
        self._agent_positions.discard(position)

    def clear_agents(self) -> None:
        """Clear all agent positions."""
        self._agent_positions.clear()

    def _count_nearby_agents(
        self,
        position: tuple[int, int, int],
    ) -> int:
        """Count agents within radius of a position.

        Args:
            position: Center position (x, y, z).

        Returns:
            Number of nearby agents.
        """
        px, py, pz = position
        count = 0
        r = self._radius

        for ax, ay, az in self._agent_positions:
            dx = abs(ax - px)
            dy = abs(ay - py)
            dz = abs(az - pz)

            if dx <= r and dy <= r and dz <= r:
                count += 1

        return count

    def calculate(
        self,
        grid: "Grid",
        from_pos: tuple[int, int, int],
        to_pos: tuple[int, int, int],
    ) -> float:
        """Calculate the cost considering congestion.

        Args:
            grid: The grid (not used, but kept for interface).
            from_pos: Source position.
            to_pos: Target position.

        Returns:
            Movement cost multiplied by congestion factor.
        """
        # Get base cost from grid
        base = grid.get_cost(*to_pos)

        # Count nearby agents at destination
        nearby = self._count_nearby_agents(to_pos)

        # Cost increases with nearby agents
        # Formula: base * (1 + nearby * 0.5)
        congestion_multiplier = 1.0 + (nearby * 0.5)

        return base * congestion_multiplier

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CongestionCost(base_cost={self._base_cost}, "
            f"radius={self._radius}, agents={len(self._agent_positions)})"
        )
