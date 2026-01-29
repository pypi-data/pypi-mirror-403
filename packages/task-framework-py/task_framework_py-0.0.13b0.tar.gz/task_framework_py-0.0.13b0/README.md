# Task Framework

A Python library for building and executing task-based workflows with built-in support for scheduling, webhooks, artifact management, and observability.

## Features

- **Multi-Task Server**: Deploy multiple task definitions to a single server, each with isolated execution environments
- **Thread Execution**: Run tasks synchronously or asynchronously with full state management
- **Artifact Management**: Track inputs and outputs with support for JSON, text, and file artifacts
- **File Storage**: Pluggable file storage interface with local filesystem and pre-signed URL support
- **Scheduling**: Cron-based scheduling with APScheduler integration
- **Webhooks**: Event-driven notifications with automatic retry and delivery tracking
- **Observability**: Built-in Prometheus metrics and structured logging
- **OpenAPI 3.1.0**: Auto-generated API documentation at `/docs`

## Installation

```bash
pip install task-framework-py
```

Or with uv:

```bash
uv add task-framework-py
```

## Quick Start

### Multi-Task Server

The Task Framework runs as a server that can host multiple task definitions. Each task is packaged as a zip file with its code and metadata.

**Start a task server:**

```bash
# Start server with auto-discovery from task_definitions/ directory
task-framework serve --host 0.0.0.0 --port 3000

# Or for development, load a task from source
task-framework serve --dev-task /path/to/my-task/
```

**Deploy a task via API:**

```bash
curl -X POST http://localhost:3000/admin/tasks \
  -H "X-API-Key: your-admin-key" \
  -F "file=@my-task-1.0.0.zip"
```

**Task Zip Structure:**

```
my-task-1.0.0.zip/
  task_metadata.json    # Task metadata and schemas
  task.py              # Task implementation
  pyproject.toml       # Dependencies (optional)
```

**Example Task Function:**

```python
async def my_task(context):
    # Get input artifacts
    inputs = await context.get_input_artifacts()
    
    # Process inputs
    result = {"message": "Task completed", "input_count": len(inputs)}
    
    # Publish output
    from task_framework.models.artifact import Artifact
    await context.publish_output_artifacts([
        Artifact(kind="json", value=result, media_type="application/json")
    ])

## API Usage

### Create a Thread (Execute Task)

```bash
curl -X POST http://localhost:3000/threads \
  -H "X-API-Key: your-api-key" \
  -H "X-User-Id: user123" \
  -H "X-App-Id: app456" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "sync",
    "inputs": [{"kind": "json", "value": {"data": "test"}}]
  }'
```

In multi-task mode, add `?task_id=my-task&version=1.0.0` query parameters.

### List Threads

```bash
curl http://localhost:3000/threads \
  -H "X-API-Key: your-api-key" \
  -H "X-User-Id: user123" \
  -H "X-App-Id: app456"
```

### Health Check

```bash
curl http://localhost:3000/health
```

## Task Package Format

A task package is a zip file containing:

```
my-task-1.0.0.zip/
  task_metadata.json    # Task metadata
  task.py              # Task implementation
  pyproject.toml       # Dependencies
```

Example `task_metadata.json`:

```json
{
  "name": "my-task",
  "version": "1.0.0",
  "description": "My task description",
  "entry_point": "task:my_task_function",
  "input_schemas": [
    {"kind": "json", "media_type": "application/json", "required": true}
  ],
  "output_schemas": [
    {"kind": "json", "media_type": "application/json"}
  ]
}
```

## Documentation

- **API Documentation**: Start the server and visit `/docs` for interactive Swagger UI
- **User Guide**: See `docs/user/` for getting started guides
- **Architecture**: See `docs/architecture/` for system design documentation
- **Feature Documentation**: See `docs/features/` for detailed feature documentation

## Authentication

The framework uses API key authentication via the `X-API-Key` header:

- **Regular API Keys**: Require `user_id` and `app_id` metadata for access control
- **Admin API Keys**: Full access to all endpoints including `/admin/*` routes

Public endpoints (no authentication required):
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /task/metadata` - Task metadata discovery

## Requirements

- Python 3.13+
- FastAPI
- Pydantic 2.x
- uvicorn

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see the development documentation in `docs/developer/` for setup instructions.
