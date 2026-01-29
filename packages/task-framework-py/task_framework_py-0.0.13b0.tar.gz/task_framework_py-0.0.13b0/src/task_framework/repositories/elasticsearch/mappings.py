"""Elasticsearch index mappings for all data types.

Defines the schema for each Elasticsearch index used by task-framework.
"""

# Thread index mappings
THREAD_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "name": {"type": "keyword"},
        "state": {"type": "keyword"},
        "mode": {"type": "keyword"},
        "created_at": {"type": "date"},
        "started_at": {"type": "date"},
        "finished_at": {"type": "date"},
        "schedule_id": {"type": "keyword"},
        "run_id": {"type": "keyword"},
        "parent_thread_id": {"type": "keyword"},
        "metadata": {
            "type": "object",
            "properties": {
                "app_id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "task_id": {"type": "keyword"},
                "task_version": {"type": "keyword"},
            }
        },
        "input": {"type": "object", "enabled": False},
        "output": {"type": "object", "enabled": False},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "keyword"},
                "message": {"type": "text"},
                "details": {"type": "object", "enabled": False},
            }
        },
    }
}

# Artifact index mappings
ARTIFACT_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "ref": {"type": "keyword"},
        "kind": {"type": "keyword"},
        "direction": {"type": "keyword"},
        "media_type": {"type": "keyword"},
        "size": {"type": "long"},
        "sha256": {"type": "keyword"},
        "file_ref": {"type": "keyword"},
        "filename": {"type": "keyword"},
        "created_at": {"type": "date"},
        "archived": {"type": "boolean"},
        "archived_at": {"type": "date"},
        "value": {"type": "object", "enabled": False},
        "labels": {"type": "object", "enabled": False},
    }
}

# Schedule index mappings
SCHEDULE_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "state": {"type": "keyword"},
        "cron": {"type": "keyword"},
        "timezone": {"type": "keyword"},
        "task_id": {"type": "keyword"},
        "task_version": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "last_run_at": {"type": "date"},
        "next_run_at": {"type": "date"},
        "run_count": {"type": "integer"},
        "input": {"type": "object", "enabled": False},
        "metadata": {"type": "object", "enabled": False},
    }
}

# Run index mappings
RUN_MAPPINGS = {
    "properties": {
        "run_id": {"type": "keyword"},
        "schedule_id": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "state": {"type": "keyword"},
        "scheduled_for_utc": {"type": "date"},
        "started_at": {"type": "date"},
        "finished_at": {"type": "date"},
        "error": {"type": "text"},
    }
}

# Webhook index mappings
WEBHOOK_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "url": {"type": "keyword"},
        "events": {"type": "object", "enabled": False},  # EventFilters nested object
        "data_filters": {"type": "object", "enabled": False},  # DataFilters nested object
        "scope": {"type": "object", "enabled": False},  # WebhookScope nested object - thread_ids, ad_hoc, etc
        "task_id": {"type": "keyword"},
        "task_version": {"type": "keyword"},
        "enabled": {"type": "boolean"},
        "secret": {"type": "keyword"},  # Encrypted
        "api_key": {"type": "keyword"},  # Optional API key for webhook delivery
        "timeout_seconds": {"type": "integer"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "created_by": {"type": "keyword"},
        "headers": {"type": "object", "enabled": False},
        "metadata": {"type": "object", "enabled": False},
    }
}

# Webhook delivery index mappings
DELIVERY_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "webhook_id": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "event": {"type": "keyword"},
        "status": {"type": "keyword"},
        "http_status": {"type": "integer"},
        "timestamp": {"type": "date"},
        "attempt": {"type": "integer"},
        "request": {"type": "object", "enabled": False},
        "response": {"type": "object", "enabled": False},
        "error": {"type": "text"},
        "duration_ms": {"type": "integer"},
    }
}

# Task definition index mappings
TASK_DEFINITION_MAPPINGS = {
    "properties": {
        "task_id": {"type": "keyword"},
        "version": {"type": "keyword"},
        "full_id": {"type": "keyword"},
        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "description": {"type": "text"},
        "registered_at": {"type": "date"},
        "is_latest": {"type": "boolean"},
        "code_path": {"type": "keyword"},
        "venv_path": {"type": "keyword"},
        "input_schema": {"type": "object", "enabled": False},
        "output_schema": {"type": "object", "enabled": False},
        "config_schema": {"type": "object", "enabled": False},
        "credentials": {"type": "keyword"},  # List of credential names
    }
}

# Deployment record index mappings
DEPLOYMENT_MAPPINGS = {
    "properties": {
        "zip_path": {"type": "keyword"},
        "zip_hash": {"type": "keyword"},
        "task_id": {"type": "keyword"},
        "version": {"type": "keyword"},
        "status": {"type": "keyword"},
        "deployed_at": {"type": "date"},
        "error": {"type": "text"},
    }
}

# Idempotency key index mappings
IDEMPOTENCY_MAPPINGS = {
    "properties": {
        "hash_key": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "created_at": {"type": "date"},
    }
}

# Credential index mappings (encrypted values)
CREDENTIAL_MAPPINGS = {
    "properties": {
        "name": {"type": "keyword"},
        "encrypted_value": {"type": "binary"},  # Encrypted at application level
        "description": {"type": "text"},
        "tags": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "expires_at": {"type": "date"},
    }
}

# Task configuration index mappings
CONFIG_MAPPINGS = {
    "properties": {
        "task_id": {"type": "keyword"},
        "encrypted_values": {"type": "binary"},  # Encrypted at application level
        "updated_at": {"type": "date"},
    }
}

# File metadata index mappings (standalone file uploads)
FILE_MAPPINGS = {
    "properties": {
        "file_ref": {"type": "keyword"},
        "filename": {"type": "keyword"},
        "media_type": {"type": "keyword"},
        "size": {"type": "long"},
        "sha256": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "created_by": {"type": "keyword"},  # user_id or app_id
        "labels": {"type": "object", "enabled": False},
    }
}

# Lock index mappings (for distributed locking)
LOCK_MAPPINGS = {
    "properties": {
        "owner": {"type": "keyword"},
        "acquired_at": {"type": "date"},
        "expires_at": {"type": "date"},
        "heartbeat_at": {"type": "date"},
        "context": {"type": "object", "enabled": False},
    }
}

# Index suffix constants
INDEX_SUFFIXES = {
    "threads": "threads",
    "artifacts": "artifacts",
    "schedules": "schedules",
    "runs": "runs",
    "webhooks": "webhooks",
    "deliveries": "deliveries",
    "tasks": "tasks",
    "deployments": "deployments",
    "idempotency": "idempotency",
    "credentials": "credentials",
    "config": "config",
    "files": "files",
    "locks": "locks",
}

# All mappings by index suffix
ALL_MAPPINGS = {
    "threads": THREAD_MAPPINGS,
    "artifacts": ARTIFACT_MAPPINGS,
    "schedules": SCHEDULE_MAPPINGS,
    "runs": RUN_MAPPINGS,
    "webhooks": WEBHOOK_MAPPINGS,
    "deliveries": DELIVERY_MAPPINGS,
    "tasks": TASK_DEFINITION_MAPPINGS,
    "deployments": DEPLOYMENT_MAPPINGS,
    "idempotency": IDEMPOTENCY_MAPPINGS,
    "credentials": CREDENTIAL_MAPPINGS,
    "config": CONFIG_MAPPINGS,
    "files": FILE_MAPPINGS,
    "locks": LOCK_MAPPINGS,
}
