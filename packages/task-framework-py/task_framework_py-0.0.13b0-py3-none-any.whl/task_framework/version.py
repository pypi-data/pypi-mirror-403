"""Task Framework version information."""

from importlib.metadata import version, PackageNotFoundError
import tomllib
from pathlib import Path

def _get_version():
    # Priority 1: Read from pyproject.toml (Development mode / Source)
    try:
        # Look for pyproject.toml in project root (2 levels up from src/task_framework)
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                ver = data.get("project", {}).get("version")
                if ver:
                    return ver
    except Exception:
        pass

    # Priority 2: Installed package version
    try:
        return version("task-framework-py")
    except PackageNotFoundError:
        pass

    # Priority 3: Fallback
    return "dev"

__version__ = _get_version()

# Export version string
VERSION = __version__


def get_version_info() -> dict:
    """Get version information dictionary.
    
    Returns:
        Dictionary with version details
    """
    return {
        "version": __version__,
        "name": "task-framework",
    }
