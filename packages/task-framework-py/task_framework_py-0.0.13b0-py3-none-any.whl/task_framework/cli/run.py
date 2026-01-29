"""CLI tool for running tasks in development mode.

This module provides a simple way to run a task locally with a development server.
It handles all the boilerplate: loading metadata, setting up the framework, and starting the server.

Usage:
    from task_framework.cli.run import run_task
    
    # In your task.py file:
    async def my_task_function(context):
        # Your task implementation
        pass
    
    if __name__ == "__main__":
        run_task()
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional


def load_task_metadata(task_dir: Path) -> dict:
    """Load and validate task metadata.
    
    Supports both task_metadata.json and task.yaml formats.
    If task.yaml exists and is newer (or task_metadata.json doesn't exist),
    auto-generates task_metadata.json from task.yaml.
    
    Args:
        task_dir: Path to the task directory
        
    Returns:
        Parsed task metadata dictionary
        
    Raises:
        FileNotFoundError: If neither task_metadata.json nor task.yaml exist
        ValueError: If metadata is invalid
    """
    metadata_file = task_dir / "task_metadata.json"
    yaml_file = task_dir / "task.yaml"
    
    # Auto-generate task_metadata.json from task.yaml if needed
    if yaml_file.exists():
        should_generate = (
            not metadata_file.exists() or 
            yaml_file.stat().st_mtime > metadata_file.stat().st_mtime
        )
        if should_generate:
            try:
                import yaml
                with open(yaml_file, "r") as f:
                    yaml_data = yaml.safe_load(f)
                with open(metadata_file, "w") as f:
                    json.dump(yaml_data, f, indent=2)
            except ImportError:
                pass  # pyyaml not installed, fall through to JSON check
            except Exception:
                pass  # Failed to generate, fall through to JSON check
    
    if not metadata_file.exists():
        raise FileNotFoundError(
            f"task_metadata.json not found in {task_dir}\n"
            "Create a task.yaml or task_metadata.json with: name, version, entry_point, description"
        )
    
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Validate required fields
    required_fields = ["name", "version", "entry_point"]
    missing = [f for f in required_fields if f not in metadata]
    if missing:
        raise ValueError(f"task_metadata.json missing required fields: {missing}")
    
    # Validate entry_point format
    entry_point = metadata["entry_point"]
    if ":" not in entry_point:
        raise ValueError(
            f"Invalid entry_point format: '{entry_point}'\n"
            "Expected format: 'module:function_name' (e.g., 'task:sample_task_function')"
        )
    
    return metadata


def load_task_function(task_dir: Path, entry_point: str) -> Callable:
    """Dynamically load the task function from the entry point.
    
    Args:
        task_dir: Path to the task directory
        entry_point: Entry point in format 'module:function_name'
        
    Returns:
        The loaded task function callable
        
    Raises:
        ImportError: If module cannot be loaded
        AttributeError: If function not found in module
    """
    module_name, func_name = entry_point.rsplit(":", 1)
    
    # Add task directory to path for imports
    task_dir_str = str(task_dir)
    if task_dir_str not in sys.path:
        sys.path.insert(0, task_dir_str)
    
    # Find the module file
    module_path = task_dir / f"{module_name.replace('.', '/')}.py"
    if not module_path.exists():
        # Try as a package
        module_path = task_dir / module_name.replace(".", "/") / "__init__.py"
    
    if not module_path.exists():
        raise ImportError(f"Module '{module_name}' not found at {module_path}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for '{module_name}'")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    # Get the function
    if not hasattr(module, func_name):
        raise AttributeError(f"Function '{func_name}' not found in module '{module_name}'")
    
    task_function = getattr(module, func_name)
    
    if not callable(task_function):
        raise TypeError(f"'{func_name}' is not callable")
    
    return task_function


def ensure_dependencies():
    """Ensure required dependencies are installed."""
    # Check for python-multipart
    try:
        import multipart
    except ImportError:
        print("Installing python-multipart (required for file uploads)...")
        try:
            subprocess.run(
                ["uv", "pip", "install", "python-multipart", "--quiet"],
                capture_output=True,
                text=True,
                check=True
            )
            print("  ✓ python-multipart installed")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ⚠ Warning: Failed to install python-multipart: {e}")
            print("  You may need to install it manually: uv pip install python-multipart")
    
    # Install task-framework in editable mode from parent directory
    print("Installing task-framework dependencies...")
    try:
        # Find project root (go up from examples/sample_task_package)
        # This assumes we're running from a task directory
        task_dir = Path.cwd()
        project_root = task_dir.parent.parent
        
        # Check if we're in the actual framework directory
        if (project_root / "src" / "task_framework").exists():
            subprocess.run(
                ["uv", "pip", "install", "-e", str(project_root), "--quiet"],
                capture_output=True,
                text=True,
                check=True
            )
            print("  ✓ task-framework installed")
        else:
            # Framework is already installed via package manager
            print("  ✓ task-framework already available")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Warning: Failed to install task-framework")
        print(f"  Error: {e.stderr if e.stderr else 'Unknown error'}")
        print("  You may need to install it manually:")
        print(f"    cd {project_root}")
        print("    uv pip install -e .")
        print()


def run_task(
    task_dir: Optional[Path] = None,
    task_function: Optional[Callable] = None,
    entry_point: Optional[str] = None,
    port: Optional[int] = None,
    test: bool = False,
) -> None:
    """Run a task in development mode with UI.
    
    This function handles all the boilerplate:
    - Loading task metadata
    - Loading the task function (if not provided)
    - Setting up database and storage
    - Initializing the framework
    - Starting the development server
    
    Args:
        task_dir: Optional path to the task directory. Defaults to the directory
                  containing the calling script (__file__).
        task_function: Optional task function to use directly. If provided, entry_point
                       and task_dir are only used for metadata.
        entry_point: Optional entry point override. If not provided, uses entry_point
                     from task_metadata.json.
        port: Optional port number for the server. If not provided, uses PORT environment
              variable or defaults to 3000.
        test: If True, starts the server with the task registered and ready to test via UI.
              The task is automatically available - no packaging needed.
    
    Examples:
        # Simple usage - auto-detects everything from task_metadata.json:
        run_task()
        
        # With explicit task function:
        async def my_task(context):
            pass
        
        run_task(task_function=my_task)
        
        # With custom directory:
        run_task(task_dir=Path("./my-task"))
        
        # With custom port:
        run_task(port=8080)
        
        # Start server with task ready for testing via UI:
        run_task(test=True)
    """
    print("=" * 70)
    print("Task Framework - Local Development Server")
    print("=" * 70)
    print()
    
    # Ensure required dependencies are installed
    ensure_dependencies()
    
    # Determine task directory
    if task_dir is None:
        # Try to get the caller's file location
        import inspect
        try:
            frame = inspect.currentframe()
            if frame is not None and frame.f_back is not None:
                caller_frame = frame.f_back
                caller_file = caller_frame.f_globals.get("__file__")
                if caller_file:
                    task_dir = Path(caller_file).parent.resolve()
                else:
                    task_dir = Path.cwd()
            else:
                task_dir = Path.cwd()
        except Exception:
            # Fallback to current working directory
            task_dir = Path.cwd()
    
    task_dir = Path(task_dir).resolve()
    
    print(f"Task directory: {task_dir}")
    print()
    
    # Load task metadata
    try:
        print("Loading task metadata...")
        metadata = load_task_metadata(task_dir)
        print(f"  Name: {metadata['name']}")
        print(f"  Version: {metadata['version']}")
        print(f"  Entry Point: {metadata['entry_point']}")
        print(f"  Description: {metadata.get('description', 'N/A')}")
        print()
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Load task function if not provided
    if task_function is None:
        entry_point_to_use = entry_point or metadata["entry_point"]
        try:
            print("Loading task function...")
            task_function = load_task_function(task_dir, entry_point_to_use)
            print(f"  Loaded: {task_function.__name__}")
            print()
        except (ImportError, AttributeError, TypeError) as e:
            print(f"ERROR: Failed to load task function: {e}")
            sys.exit(1)
    
    # Get configuration from environment
    api_keys = os.getenv("API_KEYS", "dev-key").split(",")
    admin_api_keys = os.getenv("ADMIN_API_KEYS", "admin-key").split(",")
    # Use provided port, or environment variable, or default to 3000
    if port is None:
        port = int(os.getenv("PORT", "3000"))
    
    # Filter out empty strings
    api_keys = [key.strip() for key in api_keys if key.strip()]
    admin_api_keys = [key.strip() for key in admin_api_keys if key.strip()]
    
    # Import framework components after ensuring dependencies
    # This allows ensure_dependencies() to install task-framework if needed
    from task_framework import TaskFramework
    from task_framework.repositories.file_db import FileDatabase
    from task_framework.scheduler.scheduler import Scheduler
    from task_framework.storage.local import LocalFileStorage
    import uvicorn
    
    # Initialize database and storage
    print("Initializing database and storage...")
    # Use test-data folder to keep all generated files organized
    test_data_dir = task_dir / "test-data"
    data_dir = test_data_dir / "data"
    database = FileDatabase(base_path=str(data_dir))
    file_storage = LocalFileStorage(base_path=str(data_dir / "storage"))
    scheduler = Scheduler()
    
    print(f"  Test data directory: {test_data_dir}")
    print(f"  Data directory: {data_dir}")
    print()
    
    # Initialize framework
    print("Initializing Task Framework...")
    framework = TaskFramework(
        api_keys=api_keys,
        admin_api_keys=admin_api_keys,
        database=database,
        file_storage=file_storage,
        scheduler=scheduler,
        base_path=str(test_data_dir),  # Use test-data as base path
    )
    
    # Deploy the task from source directory using async deploy_dev_task
    import asyncio
    
    print("Deploying task from source...")
    
    async def deploy_and_run():
        try:
            task_def = await framework.deploy_dev_task(str(task_dir))
            print(f"  ✓ Task deployed: {task_def.task_id}:{task_def.version}")
            return task_def
        except Exception as e:
            print(f"ERROR: Deployment failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(deploy_and_run())
    print()
    
    # Print server info
    print("=" * 70)
    print("Local Development Server Started!")
    print("=" * 70)
    print()
    print(f"  Server URL:  http://localhost:{port}")
    print(f"  Web UI:      http://localhost:{port}/ui")
    print(f"  API Docs:    http://localhost:{port}/docs")
    print(f"  Health:      http://localhost:{port}/health")
    print(f"  Metrics:     http://localhost:{port}/metrics")
    print()
    print("Authentication:")
    print(f"  API Key:     {api_keys[0]}")
    print(f"  Admin Key:   {admin_api_keys[0]}")
    print()
    print("✓ Task deployed and ready to test!")
    
    print("Quick Test via API:")
    print(f'  curl -X POST http://localhost:{port}/threads \\')
    print(f'    -H "X-API-Key: {api_keys[0]}" \\')
    print('    -H "X-User-Id: dev-user" \\')
    print('    -H "X-App-Id: local-dev" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"mode": "sync", "inputs": [{"kind": "text", "text": "Hello World"}]}\'')
    print()
    print("Or open the Web UI to test your task:")
    print(f"  → http://localhost:{port}/ui")
    print()
    
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Create and run the FastAPI server
    from task_framework.server import create_server
    app = create_server(framework, port=port)
    uvicorn.run(app, host="0.0.0.0", port=port)

