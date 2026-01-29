"""Task loader service for dynamic task function loading using uv."""

import asyncio
import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from task_framework.logging import logger
from task_framework.models.task_definition import TaskDefinition, TaskMetadata
from task_framework.repositories.file_db import FileDatabase
from task_framework.repositories.task_storage import TaskStorage
from task_framework.storage.local import LocalFileStorage
from task_framework.utils.task_packaging import (
    TaskPackageError,
    TaskPackageValidator,
    extract_zip_async,
    calculate_zip_hash_async,
)


class TaskLoaderError(Exception):
    """Exception raised for task loading errors."""
    pass


class TaskLoader:
    """Service for loading task functions from deployed code.
    
    Handles:
    - Zip extraction
    - Virtual environment creation using uv
    - Dependency installation
    - Dynamic task function loading
    """
    
    def __init__(self, task_storage: TaskStorage, framework_path: Optional[str] = None) -> None:
        """Initialize TaskLoader.
        
        Args:
            task_storage: TaskStorage repository for path management
            framework_path: Optional path to local task-framework source for development.
                           If provided, task-framework will be installed from this path
                           instead of PyPI.
        """
        self.task_storage = task_storage
        self.framework_path = framework_path
    
    async def load_from_zip(self, zip_path: str) -> TaskDefinition:
        """Load a task from a zip file.
        
        This is the main entry point for loading a new task.
        
        Args:
            zip_path: Path to the task definition zip file
            
        Returns:
            TaskDefinition with loaded task function
            
        Raises:
            TaskLoaderError: If loading fails at any step
        """
        zip_path = Path(zip_path)
        
        # Validate zip package
        validator = TaskPackageValidator(str(zip_path))
        is_valid, error = validator.validate()
        if not is_valid:
            raise TaskLoaderError(f"Invalid task package: {error}")
        
        # Get metadata
        try:
            metadata = validator.get_metadata()
        except TaskPackageError as e:
            raise TaskLoaderError(f"Failed to read metadata: {e}")
        
        task_id = metadata.name
        version = metadata.version
        
        logger.info(
            "task_loader.loading",
            zip_path=str(zip_path),
            task_id=task_id,
            version=version,
        )
        
        # Create directories
        paths = await self.task_storage.create_task_directories(task_id, version)
        code_path = paths["code_path"]
        venv_path = paths["venv_path"]
        data_path = paths["data_path"]
        storage_path = paths["storage_path"]
        
        # Extract zip to code directory
        await extract_zip_async(str(zip_path), code_path)
        
        # Create virtual environment
        await self._create_venv(venv_path)
        
        # Install dependencies
        await self._install_dependencies(code_path, venv_path)
        
        # Calculate zip hash
        zip_hash = await calculate_zip_hash_async(str(zip_path))
        
        # Create TaskDefinition
        task_def = TaskDefinition.from_metadata(
            metadata=metadata,
            base_path=Path(paths["base_path"]),
            zip_path=str(zip_path),
            zip_hash=zip_hash,
        )
        
        # Load task function
        task_function = await self._load_task_function(code_path, metadata.entry_point)
        task_def.set_task_function(task_function)
        
        # Note: Database and file storage are now managed at the framework level,
        # not per-task. Tasks share the same storage.
        
        logger.info(
            "task_loader.loaded",
            task_id=task_id,
            version=version,
            entry_point=metadata.entry_point,
        )
        
        return task_def
    
    async def load_existing(
        self,
        task_id: str,
        version: str,
        metadata: TaskMetadata,
        deployed_at: Optional[datetime] = None,
    ) -> TaskDefinition:
        """Load an already-deployed task (for server restart).
        
        Args:
            task_id: Task identifier
            version: Task version
            metadata: TaskMetadata from stored metadata
            deployed_at: Optional deployment timestamp to preserve
            
        Returns:
            TaskDefinition with loaded task function
            
        Raises:
            TaskLoaderError: If loading fails
        """
        base_path = self.task_storage.get_task_base_path(task_id, version)
        code_path = self.task_storage.get_code_path(task_id, version)
        data_path = self.task_storage.get_data_path(task_id, version)
        storage_path = self.task_storage.get_storage_path(task_id, version)
        
        # Check if code exists
        if not await self.task_storage.code_exists(task_id, version):
            raise TaskLoaderError(f"Task code not found for {task_id}:{version}")
        
        # Create TaskDefinition with preserved deployed_at
        task_def = TaskDefinition.from_metadata(
            metadata=metadata,
            base_path=base_path,
            deployed_at=deployed_at,
        )
        
        # Load task function
        task_function = await self._load_task_function(str(code_path), metadata.entry_point)
        task_def.set_task_function(task_function)
        
        # Note: Database and file storage are now managed at the framework level,
        # not per-task. Tasks share the same storage.
        
        logger.info(
            "task_loader.loaded_existing",
            task_id=task_id,
            version=version,
        )
        
        return task_def
    
    async def _create_venv(self, venv_path: str) -> None:
        """Create a virtual environment using uv.
        
        Args:
            venv_path: Path for the virtual environment
            
        Raises:
            TaskLoaderError: If venv creation fails
        """
        venv_path = Path(venv_path)
        
        # Skip if venv already exists
        if (venv_path / "bin" / "python").exists():
            logger.debug(
                "task_loader.venv_exists",
                venv_path=str(venv_path),
            )
            return
        
        logger.info(
            "task_loader.creating_venv",
            venv_path=str(venv_path),
        )
        
        try:
            process = await asyncio.create_subprocess_exec(
                "uv", "venv", str(venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise TaskLoaderError(
                    f"Failed to create venv: {stderr.decode()}"
                )
            
            logger.info(
                "task_loader.venv_created",
                venv_path=str(venv_path),
            )
            
        except FileNotFoundError:
            raise TaskLoaderError("uv not found. Please install uv: https://docs.astral.sh/uv/")
        except Exception as e:
            raise TaskLoaderError(f"Failed to create venv: {e}")
    
    async def _install_dependencies(self, code_path: str, venv_path: str) -> None:
        """Install dependencies using uv.
        
        Args:
            code_path: Path to the extracted code
            venv_path: Path to the virtual environment
            
        Raises:
            TaskLoaderError: If installation fails
        """
        # Resolve to absolute paths - required because subprocess may change cwd
        code_path = Path(code_path).resolve()
        venv_path = Path(venv_path).resolve()
        
        # Check for pyproject.toml or requirements.txt
        pyproject = code_path / "pyproject.toml"
        requirements = code_path / "requirements.txt"
        uv_lock = code_path / "uv.lock"
        
        if pyproject.exists():
            # Use uv pip install with pyproject.toml
            if uv_lock.exists():
                # Use uv sync for reproducible installs
                cmd = ["uv", "sync", "--directory", str(code_path)]
            else:
                # Install from pyproject.toml
                cmd = ["uv", "pip", "install", "-e", str(code_path), "--python", str(venv_path / "bin" / "python")]
        elif requirements.exists():
            # Install from requirements.txt
            cmd = ["uv", "pip", "install", "-r", str(requirements), "--python", str(venv_path / "bin" / "python")]
        else:
            logger.warning(
                "task_loader.no_dependencies",
                code_path=str(code_path),
            )
            return
        
        logger.info(
            "task_loader.installing_dependencies",
            code_path=str(code_path),
            command=" ".join(cmd),
        )
        
        try:
            # If framework_path is set, install task-framework from local source FIRST
            # This allows uv to resolve task-framework when installing task dependencies
            if self.framework_path:
                logger.info(
                    "task_loader.installing_local_framework",
                    framework_path=self.framework_path,
                )
                framework_cmd = [
                    "uv", "pip", "install", "-e", self.framework_path,
                    "--python", str(venv_path / "bin" / "python")
                ]
                process = await asyncio.create_subprocess_exec(
                    *framework_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(code_path),
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise TaskLoaderError(
                        f"Failed to install local task-framework: {stderr.decode()}"
                    )
            
            # Now install task dependencies
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(code_path),
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise TaskLoaderError(
                    f"Failed to install dependencies: {stderr.decode()}"
                )
            
            logger.info(
                "task_loader.dependencies_installed",
                code_path=str(code_path),
            )
            
        except FileNotFoundError:
            raise TaskLoaderError("uv not found. Please install uv: https://docs.astral.sh/uv/")
        except Exception as e:
            raise TaskLoaderError(f"Failed to install dependencies: {e}")
    
    async def _load_task_function(self, code_path: str, entry_point: str) -> Callable:
        """Dynamically load the task function from code.
        
        Args:
            code_path: Path to the extracted code directory
            entry_point: Entry point in format 'module:function'
            
        Returns:
            The loaded task function
            
        Raises:
            TaskLoaderError: If loading fails
        """
        if ":" not in entry_point:
            raise TaskLoaderError(f"Invalid entry_point format: {entry_point}. Expected 'module:function'")
        
        module_path, func_name = entry_point.rsplit(":", 1)
        code_path = Path(code_path)
        
        # Add code path to sys.path temporarily
        code_path_str = str(code_path)
        if code_path_str not in sys.path:
            sys.path.insert(0, code_path_str)
        
        try:
            # Convert module path to file path
            module_parts = module_path.split(".")
            module_file = code_path / "/".join(module_parts[:-1] if len(module_parts) > 1 else []) / f"{module_parts[-1]}.py"
            
            if not module_file.exists():
                # Try as a package
                module_file = code_path / "/".join(module_parts) / "__init__.py"
            
            if not module_file.exists():
                # Try direct path
                module_file = code_path / f"{module_path.replace('.', '/')}.py"
            
            if not module_file.exists():
                raise TaskLoaderError(f"Module file not found: {module_path}")
            
            # Load module
            spec = importlib.util.spec_from_file_location(module_path, module_file)
            if spec is None or spec.loader is None:
                raise TaskLoaderError(f"Could not load module spec: {module_path}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)
            
            # Get function
            if not hasattr(module, func_name):
                raise TaskLoaderError(f"Function '{func_name}' not found in module '{module_path}'")
            
            task_function = getattr(module, func_name)
            
            if not callable(task_function):
                raise TaskLoaderError(f"'{func_name}' is not callable")
            
            # Validate signature
            import inspect
            sig = inspect.signature(task_function)
            if len(sig.parameters) < 1:
                raise TaskLoaderError(f"Task function must accept at least one parameter (context)")
            
            logger.info(
                "task_loader.function_loaded",
                entry_point=entry_point,
                module_path=str(module_file),
            )
            
            return task_function
            
        except TaskLoaderError:
            raise
        except Exception as e:
            raise TaskLoaderError(f"Failed to load task function: {e}")
        finally:
            # Don't remove from sys.path as the module may need imports
            pass
    
    async def unload_task(self, task_def: TaskDefinition) -> None:
        """Unload a task and cleanup.
        
        Args:
            task_def: TaskDefinition to unload
        """
        # Remove module from sys.modules if loaded
        module_path = task_def.entry_point.rsplit(":", 1)[0] if ":" in task_def.entry_point else None
        if module_path and module_path in sys.modules:
            del sys.modules[module_path]
        
        logger.info(
            "task_loader.unloaded",
            task_id=task_def.task_id,
            version=task_def.version,
        )
    
    async def verify_dependencies(self, task_def: TaskDefinition) -> Tuple[bool, Optional[str]]:
        """Verify that task dependencies are properly installed.
        
        Args:
            task_def: TaskDefinition to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        venv_python = Path(task_def.venv_path) / "bin" / "python"
        
        if not venv_python.exists():
            return False, "Virtual environment not found"
        
        # Try importing the task module
        try:
            process = await asyncio.create_subprocess_exec(
                str(venv_python), "-c",
                f"import {task_def.entry_point.rsplit(':', 1)[0]}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return False, f"Import failed: {stderr.decode()}"
            
            return True, None
            
        except Exception as e:
            return False, f"Verification failed: {e}"

