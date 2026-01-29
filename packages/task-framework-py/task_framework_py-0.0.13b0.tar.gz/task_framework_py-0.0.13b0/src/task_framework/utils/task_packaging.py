"""Task packaging utilities for zip validation, extraction, and metadata parsing."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
from aiofiles import os as aios

from task_framework.logging import logger
from task_framework.models.task_definition import TaskMetadata


class TaskPackageError(Exception):
    """Exception raised for task package validation errors."""
    pass


class TaskPackageValidator:
    """Validator for task definition zip packages."""
    
    REQUIRED_FILES = ["task_metadata.json"]
    OPTIONAL_FILES = ["pyproject.toml", "requirements.txt", "uv.lock"]
    
    def __init__(self, zip_path: str) -> None:
        """Initialize validator with zip file path.
        
        Args:
            zip_path: Path to the zip file
        """
        self.zip_path = Path(zip_path)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the zip package structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not self.zip_path.exists():
            return False, f"Zip file not found: {self.zip_path}"
        
        # Check it's a valid zip file
        if not zipfile.is_zipfile(self.zip_path):
            return False, f"Not a valid zip file: {self.zip_path}"
        
        try:
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                file_names = zf.namelist()
                
                # Normalize paths (handle both root and nested structures)
                normalized_names = set()
                root_prefix = None
                
                for name in file_names:
                    # Skip directory entries
                    if name.endswith("/"):
                        continue
                    
                    parts = name.split("/")
                    if len(parts) > 1 and root_prefix is None:
                        # Check if all files are under a common root
                        potential_root = parts[0]
                        if all(n.startswith(f"{potential_root}/") or n == potential_root for n in file_names if not n.endswith("/")):
                            root_prefix = potential_root
                    
                    if root_prefix and name.startswith(f"{root_prefix}/"):
                        # Remove root prefix
                        normalized_names.add(name[len(root_prefix) + 1:])
                    else:
                        normalized_names.add(name)
                
                # Check for required files
                for required_file in self.REQUIRED_FILES:
                    if required_file not in normalized_names:
                        return False, f"Missing required file: {required_file}"
                
                # Check for at least one dependency file
                has_deps = any(f in normalized_names for f in ["pyproject.toml", "requirements.txt"])
                if not has_deps:
                    return False, "Package must contain pyproject.toml or requirements.txt"
                
                # Validate task_metadata.json
                metadata_name = f"{root_prefix}/task_metadata.json" if root_prefix else "task_metadata.json"
                if metadata_name not in file_names:
                    # Try without prefix
                    metadata_name = "task_metadata.json"
                    if metadata_name not in file_names:
                        return False, "task_metadata.json not found in archive"
                
                try:
                    with zf.open(metadata_name) as meta_file:
                        metadata_content = meta_file.read().decode("utf-8")
                        metadata_dict = json.loads(metadata_content)
                        
                        # Validate required fields
                        required_fields = ["name", "version", "entry_point"]
                        for field in required_fields:
                            if field not in metadata_dict:
                                return False, f"task_metadata.json missing required field: {field}"
                        
                        # Validate entry_point format
                        entry_point = metadata_dict["entry_point"]
                        if ":" not in entry_point:
                            return False, f"Invalid entry_point format: {entry_point}. Expected 'module:function'"
                        
                except json.JSONDecodeError as e:
                    return False, f"Invalid JSON in task_metadata.json: {e}"
                except Exception as e:
                    return False, f"Error reading task_metadata.json: {e}"
                
        except zipfile.BadZipFile:
            return False, f"Corrupted zip file: {self.zip_path}"
        except Exception as e:
            return False, f"Error validating zip file: {e}"
        
        return True, None
    
    def get_metadata(self) -> TaskMetadata:
        """Extract and parse task_metadata.json from the zip.
        
        Returns:
            TaskMetadata object
            
        Raises:
            TaskPackageError: If metadata cannot be read or parsed
        """
        try:
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                file_names = zf.namelist()
                
                # Find task_metadata.json (might be in a subdirectory)
                metadata_name = None
                for name in file_names:
                    if name.endswith("task_metadata.json"):
                        metadata_name = name
                        break
                
                if not metadata_name:
                    raise TaskPackageError("task_metadata.json not found in archive")
                
                with zf.open(metadata_name) as meta_file:
                    metadata_content = meta_file.read().decode("utf-8")
                    metadata_dict = json.loads(metadata_content)
                    return TaskMetadata(**metadata_dict)
                    
        except json.JSONDecodeError as e:
            raise TaskPackageError(f"Invalid JSON in task_metadata.json: {e}")
        except Exception as e:
            raise TaskPackageError(f"Error reading task_metadata.json: {e}")


def calculate_zip_hash(zip_path: str) -> str:
    """Calculate SHA-256 hash of a zip file.
    
    Args:
        zip_path: Path to the zip file
        
    Returns:
        SHA-256 hash prefixed with 'sha256:'
    """
    sha256_hash = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"


async def calculate_zip_hash_async(zip_path: str) -> str:
    """Calculate SHA-256 hash of a zip file asynchronously.
    
    Args:
        zip_path: Path to the zip file
        
    Returns:
        SHA-256 hash prefixed with 'sha256:'
    """
    sha256_hash = hashlib.sha256()
    async with aiofiles.open(zip_path, "rb") as f:
        while True:
            byte_block = await f.read(4096)
            if not byte_block:
                break
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"


def extract_zip(zip_path: str, target_dir: str) -> None:
    """Extract a zip file to a target directory.
    
    Handles both flat and nested zip structures.
    
    Args:
        zip_path: Path to the zip file
        target_dir: Target directory for extraction
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        file_names = zf.namelist()
        
        # Check if all files are under a common root directory
        root_prefix = None
        non_dir_files = [n for n in file_names if not n.endswith("/")]
        
        if non_dir_files:
            first_file = non_dir_files[0]
            if "/" in first_file:
                potential_root = first_file.split("/")[0]
                if all(n.startswith(f"{potential_root}/") for n in non_dir_files):
                    root_prefix = potential_root
        
        for member in zf.namelist():
            # Skip directory entries
            if member.endswith("/"):
                continue
            
            # Determine target path
            if root_prefix and member.startswith(f"{root_prefix}/"):
                # Remove root prefix
                relative_path = member[len(root_prefix) + 1:]
            else:
                relative_path = member
            
            if not relative_path:
                continue
            
            # Extract file
            target_file = target_path / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with zf.open(member) as source, open(target_file, "wb") as dest:
                shutil.copyfileobj(source, dest)
    
    logger.info(
        "task_packaging.extracted",
        zip_path=zip_path,
        target_dir=target_dir,
    )


async def extract_zip_async(zip_path: str, target_dir: str) -> None:
    """Extract a zip file to a target directory asynchronously.
    
    Args:
        zip_path: Path to the zip file
        target_dir: Target directory for extraction
    """
    # Use sync extraction in executor for better performance
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, extract_zip, zip_path, target_dir)


def parse_pyproject_toml(pyproject_path: str) -> dict:
    """Parse pyproject.toml file.
    
    Args:
        pyproject_path: Path to pyproject.toml
        
    Returns:
        Dict with parsed TOML content
        
    Raises:
        TaskPackageError: If file cannot be parsed
    """
    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        try:
            import tomli as tomllib
        except ImportError:
            raise TaskPackageError("tomllib or tomli required for pyproject.toml parsing")
    
    try:
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise TaskPackageError(f"Error parsing pyproject.toml: {e}")


def get_task_dependencies(code_path: str) -> list:
    """Get task dependencies from pyproject.toml or requirements.txt.
    
    Args:
        code_path: Path to the extracted code directory
        
    Returns:
        List of dependency strings
    """
    code_path = Path(code_path)
    
    # Try pyproject.toml first
    pyproject_path = code_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            config = parse_pyproject_toml(str(pyproject_path))
            project = config.get("project", {})
            return project.get("dependencies", [])
        except Exception:
            pass
    
    # Fall back to requirements.txt
    requirements_path = code_path / "requirements.txt"
    if requirements_path.exists():
        try:
            with open(requirements_path, "r") as f:
                lines = f.readlines()
                return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
        except Exception:
            pass
    
    return []


def validate_entry_point(code_path: str, entry_point: str) -> Tuple[bool, Optional[str]]:
    """Validate that the entry point module exists.
    
    Args:
        code_path: Path to the extracted code directory
        entry_point: Entry point in format 'module:function'
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if ":" not in entry_point:
        return False, f"Invalid entry_point format: {entry_point}. Expected 'module:function'"
    
    module_part, func_name = entry_point.rsplit(":", 1)
    
    # Convert module path to file path
    module_path = module_part.replace(".", "/")
    code_path = Path(code_path)
    
    # Check for module.py
    module_file = code_path / f"{module_path}.py"
    if module_file.exists():
        return True, None
    
    # Check for module/__init__.py
    package_init = code_path / module_path / "__init__.py"
    if package_init.exists():
        return True, None
    
    return False, f"Module not found: {module_part} (looked for {module_file} or {package_init})"


class TaskPackager:
    """Utility for creating task definition packages."""
    
    def __init__(self, task_dir: str) -> None:
        """Initialize packager with task directory.
        
        Args:
            task_dir: Path to the task source directory
        """
        self.task_dir = Path(task_dir)
    
    def validate_for_packaging(self) -> Tuple[bool, Optional[str]]:
        """Validate that the directory can be packaged.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.task_dir.exists():
            return False, f"Directory not found: {self.task_dir}"
        
        if not self.task_dir.is_dir():
            return False, f"Not a directory: {self.task_dir}"
        
        # Check for required files
        metadata_file = self.task_dir / "task_metadata.json"
        if not metadata_file.exists():
            return False, "Missing task_metadata.json"
        
        # Validate metadata
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            required_fields = ["name", "version", "entry_point"]
            for field in required_fields:
                if field not in metadata:
                    return False, f"task_metadata.json missing required field: {field}"
            
            # Validate entry point
            entry_point = metadata["entry_point"]
            valid, error = validate_entry_point(str(self.task_dir), entry_point)
            if not valid:
                return False, error
                
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in task_metadata.json: {e}"
        
        # Check for dependency file
        has_deps = (self.task_dir / "pyproject.toml").exists() or (self.task_dir / "requirements.txt").exists()
        if not has_deps:
            return False, "Missing pyproject.toml or requirements.txt"
        
        return True, None
    
    def create_package(self, output_path: str) -> str:
        """Create a zip package from the task directory.
        
        Args:
            output_path: Path for the output zip file
            
        Returns:
            Path to the created zip file
            
        Raises:
            TaskPackageError: If packaging fails
        """
        valid, error = self.validate_for_packaging()
        if not valid:
            raise TaskPackageError(error)
        
        output_path = Path(output_path)
        
        # Ensure .zip extension
        if not str(output_path).endswith(".zip"):
            output_path = output_path.with_suffix(".zip")
        
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get SDK version to inject into task_metadata.json
        sdk_version = self._get_sdk_version()
        
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.task_dir.rglob("*"):
                if file_path.is_file():
                    # Skip common ignore patterns
                    rel_path = file_path.relative_to(self.task_dir)
                    rel_str = str(rel_path)
                    
                    if self._should_ignore(rel_str):
                        continue
                    
                    # Special handling for pyproject.toml - strip [tool.uv.sources]
                    if rel_str == "pyproject.toml":
                        content = self._preprocess_pyproject(file_path)
                        zf.writestr(str(rel_path), content)
                    # Inject SDK version into task_metadata.json
                    elif rel_str == "task_metadata.json":
                        content = self._inject_sdk_version(file_path, sdk_version)
                        zf.writestr(str(rel_path), content)
                    else:
                        zf.write(file_path, rel_path)
        
        logger.info(
            "task_packaging.created",
            task_dir=str(self.task_dir),
            output_path=str(output_path),
            sdk_version=sdk_version,
        )
        
        return str(output_path)
    
    def _get_sdk_version(self) -> Optional[str]:
        """Get the task-framework-py SDK version.
        
        Returns:
            SDK version string, or None if not installed
        """
        try:
            from importlib.metadata import version
            return version("task-framework-py")
        except Exception:
            # Fallback to reading from package __version__
            try:
                import task_framework
                return getattr(task_framework, "__version__", None)
            except Exception:
                return None
    
    def _inject_sdk_version(self, metadata_path: Path, sdk_version: Optional[str]) -> str:
        """Inject SDK version into task_metadata.json content.
        
        Args:
            metadata_path: Path to task_metadata.json
            sdk_version: SDK version to inject
            
        Returns:
            Modified JSON content as string
        """
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        if sdk_version:
            metadata["sdk_version"] = sdk_version
        
        return json.dumps(metadata, indent=2)

    
    def _preprocess_pyproject(self, pyproject_path: Path) -> str:
        """Preprocess pyproject.toml to remove development-only sections.
        
        Strips [tool.uv.sources] section which contains local paths that
        don't work in deployment.
        
        Args:
            pyproject_path: Path to pyproject.toml
            
        Returns:
            Preprocessed content as string
        """
        with open(pyproject_path, "r") as f:
            lines = f.readlines()
        
        result_lines = []
        skip_section = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if we're entering [tool.uv.sources] section
            if stripped == "[tool.uv.sources]":
                skip_section = True
                continue
            
            # Check if we're exiting the section (new section starts)
            if skip_section and stripped.startswith("["):
                skip_section = False
            
            # Skip lines in the [tool.uv.sources] section
            if skip_section:
                continue
            
            result_lines.append(line)
        
        # Clean up any trailing blank lines that might accumulate
        content = "".join(result_lines)
        return content.rstrip() + "\n"
    
    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored when packaging.
        
        Args:
            path: Relative path within the task directory
            
        Returns:
            True if the path should be ignored
        """
        ignore_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".git",
            ".env",
            ".venv",
            "venv",
            ".idea",
            ".vscode",
            "*.egg-info",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            "test-data",  # Generated test data directory
            "uv.lock",    # Lock file - not needed for packaging
        ]
        
        path_lower = path.lower()
        for pattern in ignore_patterns:
            if pattern.startswith("*"):
                if path_lower.endswith(pattern[1:]):
                    return True
            elif pattern in path_lower:
                return True
        
        return False

