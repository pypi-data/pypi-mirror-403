"""Service registry for managing enrolled task servers."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ServerEntry(BaseModel):
    """Represents an enrolled task server."""

    id: str = Field(..., description="Unique server identifier")
    name: Optional[str] = Field(None, description="Human-friendly server name")
    base_url: str = Field(..., description="HTTP(s) base URL of the server")
    health_path: str = Field(default="/health", description="Health check endpoint path")
    task_types: List[str] = Field(default_factory=list, description="Task types this server serves")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Freeform metadata")
    status: str = Field(default="unknown", description="Server health status: unknown, healthy, unhealthy, draining")
    weight: Optional[int] = Field(None, ge=1, description="Weight for weighted load balancing")
    max_concurrent: Optional[int] = Field(None, ge=1, description="Maximum concurrent connections")
    last_checked_at: Optional[datetime] = Field(None, description="Timestamp of last health check")


class EnrollmentRequest(BaseModel):
    """Request model for enrolling a new server."""

    id: str = Field(..., description="Unique server identifier")
    base_url: str = Field(..., description="HTTP(s) base URL of the server")
    task_types: List[str] = Field(..., description="Task types this server serves")
    name: Optional[str] = Field(None, description="Human-friendly server name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Freeform metadata")
    weight: Optional[int] = Field(None, ge=1, description="Weight for weighted load balancing")
    max_concurrent: Optional[int] = Field(None, ge=1, description="Maximum concurrent connections")


class TaskTypeGroup(BaseModel):
    """Represents a task type group with load balancing configuration."""

    task_type: str = Field(..., description="Unique task type identifier")
    lb_strategy: str = Field(default="round-robin", description="Load balancing strategy")
    sticky_header_name: Optional[str] = Field(None, description="Header name for sticky routing")
    health_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "failure_threshold": 1,
            "recovery_threshold": 1,
            "interval_seconds": 10,
        },
        description="Health check policy configuration",
    )
    servers: List[str] = Field(default_factory=list, description="List of server IDs in this group")


class ServiceRegistry:
    """In-memory registry for managing enrolled servers and task type groups."""

    def __init__(self, persistence_file: Optional[str] = None) -> None:
        """Initialize service registry.

        Args:
            persistence_file: Optional path to JSON file for persistence
        """
        self._servers: Dict[str, ServerEntry] = {}
        self._task_type_groups: Dict[str, TaskTypeGroup] = {}
        self.persistence_file = persistence_file
        
        # Load from file if it exists
        if self.persistence_file:
            self.load_from_file()

    def add_server(self, server: ServerEntry) -> None:
        """Add or update a server entry.

        Args:
            server: ServerEntry to add or update

        Raises:
            ValueError: If server ID is invalid or conflicts exist
        """
        if not server.id:
            raise ValueError("Server ID is required")
        
        # Update task type groups when server is added/updated
        old_server = self._servers.get(server.id)
        if old_server:
            # Remove from old task types
            for task_type in old_server.task_types:
                if task_type in self._task_type_groups:
                    group = self._task_type_groups[task_type]
                    if server.id in group.servers:
                        group.servers.remove(server.id)
        
        # Add/update server
        self._servers[server.id] = server
        
        # Add to new task types
        for task_type in server.task_types:
            if task_type not in self._task_type_groups:
                self._task_type_groups[task_type] = TaskTypeGroup(
                    task_type=task_type,
                    lb_strategy="round-robin",
                )
            group = self._task_type_groups[task_type]
            if server.id not in group.servers:
                group.servers.append(server.id)
        
        # Persist if file is configured
        if self.persistence_file:
            self.save_to_file()

    def get_server(self, server_id: str) -> Optional[ServerEntry]:
        """Get a server entry by ID.

        Args:
            server_id: Server identifier

        Returns:
            ServerEntry if found, None otherwise
        """
        return self._servers.get(server_id)

    def list_servers(self) -> List[ServerEntry]:
        """List all enrolled servers.

        Returns:
            List of all ServerEntry instances
        """
        return list(self._servers.values())

    def update_server(self, server_id: str, updates: Dict[str, Any]) -> Optional[ServerEntry]:
        """Update a server entry.

        Args:
            server_id: Server identifier
            updates: Dictionary of fields to update

        Returns:
            Updated ServerEntry if found, None otherwise
        """
        server = self._servers.get(server_id)
        if not server:
            return None
        
        # Create updated server entry
        server_dict = server.model_dump()
        server_dict.update({k: v for k, v in updates.items() if v is not None})
        
        # Preserve fields that shouldn't be updated via this method
        updated_server = ServerEntry(**server_dict)
        
        # Use add_server to handle task type group updates
        # Note: add_server will call save_to_file, so we don't need to call it here
        self.add_server(updated_server)
        
        return updated_server

    def delete_server(self, server_id: str) -> bool:
        """Delete a server entry.

        Args:
            server_id: Server identifier

        Returns:
            True if deleted, False if not found
        """
        server = self._servers.get(server_id)
        if not server:
            return False
        
        # Remove from task type groups
        for task_type in server.task_types:
            if task_type in self._task_type_groups:
                group = self._task_type_groups[task_type]
                if server_id in group.servers:
                    group.servers.remove(server_id)
                # Clean up empty groups
                if not group.servers:
                    del self._task_type_groups[task_type]
        
        # Delete server
        del self._servers[server_id]
        
        # Persist if file is configured
        if self.persistence_file:
            self.save_to_file()
        
        return True
    
    def get_task_type_group(self, task_type: str) -> Optional[TaskTypeGroup]:
        """Get task type group for a specific task type.

        Args:
            task_type: Task type identifier

        Returns:
            TaskTypeGroup if found, None otherwise
        """
        return self._task_type_groups.get(task_type)
    
    def list_task_types(self) -> List[str]:
        """List all registered task types.

        Returns:
            List of task type identifiers
        """
        return list(self._task_type_groups.keys())

    def save_to_file(self) -> None:
        """Save registry state to persistence file.
        
        Raises:
            IOError: If file write fails
        """
        if not self.persistence_file:
            return
        
        try:
            # Prepare data for serialization
            data = {
                "servers": [server.model_dump(mode="json") for server in self._servers.values()],
                "task_type_groups": [group.model_dump(mode="json") for group in self._task_type_groups.values()],
            }
            
            # Write to file atomically
            temp_file = f"{self.persistence_file}.tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            # Atomic rename
            os.replace(temp_file, self.persistence_file)
            
        except Exception as e:
            from task_framework.logging import logger
            logger.error("proxy.registry.save_failed", file=self.persistence_file, error=str(e), exc_info=True)
            raise

    def load_from_file(self) -> None:
        """Load registry state from persistence file.
        
        Raises:
            IOError: If file read fails or data is invalid
        """
        if not self.persistence_file or not os.path.exists(self.persistence_file):
            return
        
        try:
            with open(self.persistence_file, "r") as f:
                data = json.load(f)
            
            # Load servers
            self._servers = {}
            for server_data in data.get("servers", []):
                # Convert datetime strings back to datetime objects
                if "last_checked_at" in server_data and server_data["last_checked_at"]:
                    server_data["last_checked_at"] = datetime.fromisoformat(server_data["last_checked_at"].replace("Z", "+00:00"))
                server = ServerEntry(**server_data)
                self._servers[server.id] = server
            
            # Load task type groups
            self._task_type_groups = {}
            for group_data in data.get("task_type_groups", []):
                group = TaskTypeGroup(**group_data)
                self._task_type_groups[group.task_type] = group
            
            from task_framework.logging import logger
            logger.info("proxy.registry.loaded", file=self.persistence_file, servers_count=len(self._servers))
            
        except Exception as e:
            from task_framework.logging import logger
            logger.error("proxy.registry.load_failed", file=self.persistence_file, error=str(e), exc_info=True)
            # Don't raise - allow registry to start empty if file is corrupted

