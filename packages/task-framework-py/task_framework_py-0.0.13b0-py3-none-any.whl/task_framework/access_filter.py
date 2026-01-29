"""Access control filtering for resources based on authentication metadata."""

from typing import Any, Dict, List, Optional

from task_framework.dependencies import AuthenticatedRequest


class AccessFilter:
    """Utility class for filtering resources based on authentication metadata."""

    @staticmethod
    def filter_resources(
        resources: List[Dict[str, Any]],
        auth: AuthenticatedRequest,
    ) -> List[Dict[str, Any]]:
        """Filter resources based on authentication context.

        Admin keys bypass all filtering and return all resources.
        Regular keys only return resources matching their user_id and app_id metadata.

        Args:
            resources: List of resource dictionaries (e.g., Thread, Schedule, Run)
            auth: AuthenticatedRequest context with key_type, user_id, app_id

        Returns:
            Filtered list of resources matching the authentication context
        """
        # Admin keys bypass all filtering
        if auth.key_type == "admin":
            from task_framework.logging import logger

            logger.info(
                "access_control.filtered",
                key_type=auth.key_type,
                user_id=auth.user_id,
                app_id=auth.app_id,
                filtered_count=len(resources),
                total_count=len(resources),
            )
            return resources

        # Regular keys: filter by metadata
        filtered: List[Dict[str, Any]] = []
        for resource in resources:
            # Extract metadata from resource (Thread.metadata or similar)
            metadata: Optional[Dict[str, Any]] = resource.get("metadata", {})
            if not isinstance(metadata, dict):
                # Skip resources without proper metadata dict
                continue

            resource_user_id = metadata.get("user_id")
            resource_app_id = metadata.get("app_id")

            # Match if both user_id and app_id match
            if resource_user_id == auth.user_id and resource_app_id == auth.app_id:
                filtered.append(resource)

        # Log filtering results
        from task_framework.logging import logger

        logger.info(
            "access_control.filtered",
            key_type=auth.key_type,
            user_id=auth.user_id,
            app_id=auth.app_id,
            filtered_count=len(filtered),
            total_count=len(resources),
        )

        return filtered

    @staticmethod
    def check_resource_access(
        resource: Dict[str, Any],
        auth: AuthenticatedRequest,
    ) -> bool:
        """Check if authenticated request can access a specific resource.

        Admin keys can access any resource (returns True).
        Regular keys can only access resources matching their metadata.

        Args:
            resource: Resource dictionary with metadata
            auth: AuthenticatedRequest context

        Returns:
            True if access is allowed, False otherwise
        """
        # Admin keys can access any resource
        if auth.key_type == "admin":
            return True

        # Regular keys: check metadata match
        metadata: Optional[Dict[str, Any]] = resource.get("metadata", {})
        if not isinstance(metadata, dict):
            return False

        resource_user_id = metadata.get("user_id")
        resource_app_id = metadata.get("app_id")

        return resource_user_id == auth.user_id and resource_app_id == auth.app_id

