"""Centralized ID generation utilities.

This module provides unique ID generators for all entity types in the framework.
All IDs use full UUID4 (32 hex characters) to avoid collision risk.

ID Format: {prefix}_{32 hex chars}
Example: thread_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6

Entropy: ~122 bits (collision-safe for billions of IDs)
"""

import uuid


def generate_thread_id() -> str:
    """Generate a unique thread ID.
    
    Returns:
        Thread ID in format: thread_{32 hex chars}
    """
    return f"thread_{uuid.uuid4().hex}"


def generate_artifact_id() -> str:
    """Generate a unique artifact ID.
    
    Returns:
        Artifact ID in format: artifact_{32 hex chars}
    """
    return f"artifact_{uuid.uuid4().hex}"


def generate_schedule_id() -> str:
    """Generate a unique schedule ID.
    
    Returns:
        Schedule ID in format: schedule_{32 hex chars}
    """
    return f"schedule_{uuid.uuid4().hex}"


def generate_webhook_id() -> str:
    """Generate a unique webhook ID.
    
    Returns:
        Webhook ID in format: webhook_{32 hex chars}
    """
    return f"webhook_{uuid.uuid4().hex}"


def generate_delivery_id() -> str:
    """Generate a unique delivery ID.
    
    Returns:
        Delivery ID in format: delivery_{32 hex chars}
    """
    return f"delivery_{uuid.uuid4().hex}"


def generate_file_ref() -> str:
    """Generate a unique file reference ID.
    
    Returns:
        File reference in format: file_{32 hex chars}
    """
    return f"file_{uuid.uuid4().hex}"
