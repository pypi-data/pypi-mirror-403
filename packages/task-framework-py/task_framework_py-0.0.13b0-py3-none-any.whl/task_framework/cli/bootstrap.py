"""Bootstrap module for running tasks.

This module provides a bootstrap entry point that can install task-framework
if needed, then delegate to the actual run_task function.
"""

import subprocess
import sys
from pathlib import Path


def find_project_root(start_path: Path) -> Path:
    """Find the task-framework project root by looking for src/task_framework."""
    current = start_path.resolve()
    
    # Check current directory and parents
    for _ in range(5):  # Limit search depth
        if (current / "src" / "task_framework").exists():
            return current
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent
    
    return None


def ensure_task_framework_installed(task_dir: Path) -> bool:
    """Ensure task-framework is installed, installing it if necessary.
    
    Args:
        task_dir: Path to the task directory
        
    Returns:
        True if task-framework is available, False otherwise
    """
    # First, check if it's already importable
    try:
        import task_framework.cli.run
        return True
    except ImportError:
        pass
    
    # Find project root
    project_root = find_project_root(task_dir)
    if not project_root:
        return False
    
    # Try to install
    print("Installing task-framework...")
    try:
        result = subprocess.run(
            ["uv", "pip", "install", "-e", str(project_root)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✓ task-framework installed")
            # Clear module cache and try importing again
            if 'task_framework' in sys.modules:
                del sys.modules['task_framework']
            if 'task_framework.cli' in sys.modules:
                del sys.modules['task_framework.cli']
            if 'task_framework.cli.run' in sys.modules:
                del sys.modules['task_framework.cli.run']
            return True
        else:
            print(f"Installation failed: {result.stderr or result.stdout}")
            return False
    except Exception as e:
        print(f"Failed to install task-framework: {e}")
        return False


def run_task_bootstrap(task_dir: Path = None):
    """Bootstrap function that ensures task-framework is installed, then runs the task.
    
    Args:
        task_dir: Optional path to task directory. Defaults to caller's directory.
    """
    import inspect
    
    # Determine task directory
    if task_dir is None:
        try:
            frame = inspect.currentframe()
            if frame is not None and frame.f_back is not None:
                caller_file = frame.f_back.f_globals.get("__file__")
                if caller_file:
                    task_dir = Path(caller_file).parent.resolve()
                else:
                    task_dir = Path.cwd()
            else:
                task_dir = Path.cwd()
        except Exception:
            task_dir = Path.cwd()
    
    task_dir = Path(task_dir).resolve()
    
    # Ensure task-framework is installed
    if not ensure_task_framework_installed(task_dir):
        print("=" * 70)
        print("ERROR: Could not install task-framework")
        print("=" * 70)
        print()
        print("Please install it manually:")
        project_root = find_project_root(task_dir)
        if project_root:
            print(f"  cd {project_root}")
            print(f"  uv pip install -e .")
        else:
            print("  uv pip install task-framework")
        print()
        sys.exit(1)
    
    # Now import and run the actual run_task function
    # Re-import to get the fresh module after installation
    from task_framework.cli.run import run_task
    run_task(task_dir=task_dir)
