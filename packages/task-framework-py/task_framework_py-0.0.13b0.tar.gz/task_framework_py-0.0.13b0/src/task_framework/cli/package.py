#!/usr/bin/env python
"""CLI tool for packaging task definitions into deployable zip files.

Usage:
    uv run python -m task_framework.cli.package --task-dir ./my-task --output my-task.zip
    
    # Or with verbose output:
    uv run python -m task_framework.cli.package --task-dir ./my-task -o my-task.zip -v
"""

import argparse
import json
import sys
from pathlib import Path

from task_framework.utils.task_packaging import TaskPackager, TaskPackageError


def main():
    """Main entry point for the packaging CLI."""
    parser = argparse.ArgumentParser(
        prog="task_framework.cli.package",
        description="Package a task definition directory into a deployable zip file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --task-dir ./my-task --output my-task.zip
    %(prog)s -t ./my-task -o my-task-v1.0.0.zip -v
    
Required Files:
    The task directory must contain:
    - task_metadata.json: Task metadata (name, version, entry_point, etc.)
    - pyproject.toml or requirements.txt: Dependencies
    - Task source code (Python files)
    
task_metadata.json Format:
    {
        "name": "my-task",
        "version": "1.0.0",
        "description": "Description of what the task does",
        "entry_point": "task:main_function",
        "input_schemas": [],
        "output_schemas": [],
        "sdk_version": "auto-injected by packager"
    }
""",
    )
    
    parser.add_argument(
        "-t", "--task-dir",
        required=True,
        help="Path to the task directory containing task source code and metadata",
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output path for the zip file",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the task directory without creating the zip file",
    )
    
    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Display the task metadata after validation",
    )
    
    args = parser.parse_args()
    
    task_dir = Path(args.task_dir)
    output_path = Path(args.output)
    
    if args.verbose:
        print(f"Task directory: {task_dir}")
        print(f"Output path: {output_path}")
    
    # Check task directory exists
    if not task_dir.exists():
        print(f"Error: Task directory does not exist: {task_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not task_dir.is_dir():
        print(f"Error: Not a directory: {task_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create packager
    packager = TaskPackager(str(task_dir))
    
    # Validate
    print("Validating task directory...")
    is_valid, error = packager.validate_for_packaging()
    
    if not is_valid:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
    
    print("✓ Validation passed")
    
    # Show metadata if requested
    if args.show_metadata or args.verbose:
        metadata_file = task_dir / "task_metadata.json"
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            print("\nTask Metadata:")
            print(f"  Name: {metadata.get('name', 'N/A')}")
            print(f"  Version: {metadata.get('version', 'N/A')}")
            print(f"  Description: {metadata.get('description', 'N/A')}")
            print(f"  Entry Point: {metadata.get('entry_point', 'N/A')}")
        except Exception as e:
            print(f"Warning: Could not read metadata: {e}", file=sys.stderr)
    
    # If validate-only, stop here
    if args.validate_only:
        print("\nValidation only mode - no zip file created")
        sys.exit(0)
    
    # Create package
    print(f"\nCreating package: {output_path}")
    try:
        result_path = packager.create_package(str(output_path))
        print(f"✓ Package created: {result_path}")
        
        # Show package info
        result_file = Path(result_path)
        size_kb = result_file.stat().st_size / 1024
        print(f"  Size: {size_kb:.2f} KB")
        
    except TaskPackageError as e:
        print(f"Packaging failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("\nDone! The package can now be uploaded via:")
    print(f"  - Admin API: POST /admin/tasks with the zip file")
    print(f"  - Place in task_definitions/ folder for auto-discovery on server restart")


if __name__ == "__main__":
    main()

