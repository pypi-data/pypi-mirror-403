"""Load balancing strategies for selecting target servers."""

import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from task_framework.proxy_registry import ServerEntry, TaskTypeGroup


class LoadBalancer(ABC):
    """Abstract base class for load balancing strategies."""

    @abstractmethod
    def select_server(
        self,
        servers: List[ServerEntry],
        task_type: str,
        sticky_key: Optional[str] = None,
    ) -> Optional[ServerEntry]:
        """Select a server from the list.

        Args:
            servers: List of available servers
            task_type: Task type identifier
            sticky_key: Optional sticky routing key (for sticky strategies)

        Returns:
            Selected ServerEntry or None if no servers available
        """
        pass


class RoundRobinBalancer(LoadBalancer):
    """Round-robin load balancing strategy."""

    def __init__(self) -> None:
        """Initialize round-robin balancer."""
        self._counters: Dict[str, int] = {}  # task_type -> counter

    def select_server(
        self,
        servers: List[ServerEntry],
        task_type: str,
        sticky_key: Optional[str] = None,
    ) -> Optional[ServerEntry]:
        """Select next server in round-robin order.

        Args:
            servers: List of available servers
            task_type: Task type identifier
            sticky_key: Ignored for round-robin

        Returns:
            Selected ServerEntry or None if no servers available
        """
        # Filter to healthy, non-draining servers
        available = [s for s in servers if s.status == "healthy" and s.status != "draining"]
        if not available:
            return None
        
        # Get or initialize counter for this task type
        counter = self._counters.get(task_type, 0)
        
        # Select server at counter position
        selected = available[counter % len(available)]
        
        # Increment counter
        self._counters[task_type] = counter + 1
        
        return selected


class LeastConnectionsBalancer(LoadBalancer):
    """Least-connections load balancing strategy."""

    def __init__(self) -> None:
        """Initialize least-connections balancer."""
        self._active_connections: Dict[str, int] = {}  # server_id -> active connections

    def select_server(
        self,
        servers: List[ServerEntry],
        task_type: str,
        sticky_key: Optional[str] = None,
    ) -> Optional[ServerEntry]:
        """Select server with fewest active connections.

        Args:
            servers: List of available servers
            task_type: Task type identifier
            sticky_key: Ignored for least-connections

        Returns:
            Selected ServerEntry or None if no servers available
        """
        # Filter to healthy, non-draining servers
        available = [s for s in servers if s.status == "healthy" and s.status != "draining"]
        if not available:
            return None
        
        # Respect max_concurrent if set
        candidates = []
        for server in available:
            active = self._active_connections.get(server.id, 0)
            if server.max_concurrent is None or active < server.max_concurrent:
                candidates.append((server, active))
        
        if not candidates:
            return None
        
        # Select server with minimum active connections
        selected_server, _ = min(candidates, key=lambda x: x[1])
        return selected_server

    def increment_connections(self, server_id: str) -> None:
        """Increment active connection count for a server.

        Args:
            server_id: Server identifier
        """
        self._active_connections[server_id] = self._active_connections.get(server_id, 0) + 1

    def decrement_connections(self, server_id: str) -> None:
        """Decrement active connection count for a server.

        Args:
            server_id: Server identifier
        """
        current = self._active_connections.get(server_id, 0)
        if current > 0:
            self._active_connections[server_id] = current - 1


class RandomBalancer(LoadBalancer):
    """Random load balancing strategy."""

    def select_server(
        self,
        servers: List[ServerEntry],
        task_type: str,
        sticky_key: Optional[str] = None,
    ) -> Optional[ServerEntry]:
        """Select a random server.

        Args:
            servers: List of available servers
            task_type: Task type identifier
            sticky_key: Ignored for random

        Returns:
            Selected ServerEntry or None if no servers available
        """
        # Filter to healthy, non-draining servers
        available = [s for s in servers if s.status == "healthy" and s.status != "draining"]
        if not available:
            return None
        
        return random.choice(available)


class StickyBalancer(LoadBalancer):
    """Sticky load balancing strategy using a routing key."""

    def __init__(self) -> None:
        """Initialize sticky balancer."""
        self._sticky_map: Dict[str, str] = {}  # sticky_key -> server_id

    def select_server(
        self,
        servers: List[ServerEntry],
        task_type: str,
        sticky_key: Optional[str] = None,
    ) -> Optional[ServerEntry]:
        """Select server based on sticky key.

        Args:
            servers: List of available servers
            task_type: Task type identifier
            sticky_key: Sticky routing key (e.g., client ID)

        Returns:
            Selected ServerEntry or None if no servers available
        """
        # Filter to healthy, non-draining servers
        available = [s for s in servers if s.status == "healthy" and s.status != "draining"]
        if not available:
            return None
        
        # If sticky key provided, try to use previously assigned server
        if sticky_key:
            assigned_id = self._sticky_map.get(sticky_key)
            if assigned_id:
                assigned = next((s for s in available if s.id == assigned_id), None)
                if assigned:
                    return assigned
        
        # No sticky assignment or assigned server unavailable - select new one
        # Use round-robin as fallback
        selected = available[0]  # Simple selection
        
        # Store sticky mapping
        if sticky_key:
            self._sticky_map[sticky_key] = selected.id
        
        return selected


class LoadBalancerFactory:
    """Factory for creating load balancer instances."""

    @staticmethod
    def create(strategy: str) -> LoadBalancer:
        """Create a load balancer instance.

        Args:
            strategy: Strategy name (round-robin, least-connections, random, sticky)

        Returns:
            LoadBalancer instance

        Raises:
            ValueError: If strategy is not recognized
        """
        strategies = {
            "round-robin": RoundRobinBalancer,
            "least-connections": LeastConnectionsBalancer,
            "random": RandomBalancer,
            "sticky": StickyBalancer,
        }
        
        balancer_class = strategies.get(strategy)
        if not balancer_class:
            raise ValueError(f"Unknown load balancing strategy: {strategy}")
        
        return balancer_class()

