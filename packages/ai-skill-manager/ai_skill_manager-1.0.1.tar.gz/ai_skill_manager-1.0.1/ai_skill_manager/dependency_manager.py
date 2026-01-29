"""Dependency management for AI skills."""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tomllib

from .skill_types import DependencyFile

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages Python dependencies for AI skills."""

    def __init__(self, respect_virtual_env: bool = True, install_timeout: int = 600):
        """Initialize the dependency manager.

        Args:
            respect_virtual_env: Whether to respect existing virtual environments
            install_timeout: Timeout for dependency installation in seconds
        """
        self.respect_virtual_env = respect_virtual_env
        self.install_timeout = install_timeout

    def is_uv_available(self) -> bool:
        """Check if uv package manager is available.

        Returns:
            True if uv is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['uv', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def is_pip_available(self) -> bool:
        """Check if pip is available.

        Returns:
            True if pip is available, False otherwise
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def detect_dependency_files(self, skill_path: str) -> List[DependencyFile]:
        """Detect dependency files in a skill directory.

        Args:
            skill_path: Path to the skill directory

        Returns:
            List of detected dependency files
        """
        skill_dir = Path(skill_path)
        dependency_files = []

        # Check for requirements.txt
        requirements_path = skill_dir / 'requirements.txt'
        if requirements_path.exists():
            try:
                content = requirements_path.read_text(encoding='utf-8')
                dependency_files.append(DependencyFile(
                    path=str(requirements_path),
                    type='requirements.txt',
                    content=content
                ))
            except Exception as e:
                logger.warning(f"Failed to read requirements.txt: {e}")

        # Check for pyproject.toml
        pyproject_path = skill_dir / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding='utf-8')
                dependency_files.append(DependencyFile(
                    path=str(pyproject_path),
                    type='pyproject.toml',
                    content=content
                ))
            except Exception as e:
                logger.warning(f"Failed to read pyproject.toml: {e}")

        return dependency_files

    def resolve_dependencies(self, files: List[DependencyFile]) -> List[str]:
        """Resolve dependencies from dependency files.

        Args:
            files: List of dependency files

        Returns:
            List of resolved dependency specifications
        """
        dependencies = []

        # Prioritize pyproject.toml over requirements.txt as per requirement 5.5
        pyproject_files = [f for f in files if f.type == 'pyproject.toml']
        requirements_files = [f for f in files if f.type == 'requirements.txt']

        if pyproject_files:
            # Process pyproject.toml files
            for dep_file in pyproject_files:
                try:
                    parsed_toml = tomllib.loads(dep_file.content)

                    # Extract dependencies from different sections
                    project_deps = parsed_toml.get('project', {}).get('dependencies', [])
                    dependencies.extend(project_deps)

                    # Extract optional dependencies
                    optional_deps = parsed_toml.get('project', {}).get('optional-dependencies', {})
                    for group_deps in optional_deps.values():
                        dependencies.extend(group_deps)

                    # Extract build system requirements
                    build_deps = parsed_toml.get('build-system', {}).get('requires', [])
                    dependencies.extend(build_deps)

                except Exception as e:
                    logger.warning(f"Failed to parse pyproject.toml: {e}")

        elif requirements_files:
            # Process requirements.txt files only if no pyproject.toml
            for dep_file in requirements_files:
                try:
                    lines = dep_file.content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            dependencies.append(line)
                except Exception as e:
                    logger.warning(f"Failed to parse requirements.txt: {e}")

        return dependencies

    def _is_in_virtual_env(self) -> bool:
        """Check if currently running in a virtual environment.

        Returns:
            True if in virtual environment, False otherwise
        """
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None
        )

    def _get_install_command(self, dependencies: List[str], use_uv: bool) -> List[str]:
        """Get the appropriate install command.

        Args:
            dependencies: List of dependencies to install
            use_uv: Whether to use uv or pip

        Returns:
            Command list for subprocess execution
        """
        if use_uv:
            cmd = ['uv', 'pip', 'install']
        else:
            cmd = [sys.executable, '-m', 'pip', 'install']

        # Add user flag if not in virtual environment and respect_virtual_env is True
        if not use_uv and self.respect_virtual_env and not self._is_in_virtual_env():
            cmd.append('--user')

        cmd.extend(dependencies)
        return cmd

    def install_dependencies(self, skill_path: str, use_uv: Optional[bool] = None) -> Tuple[bool, List[str], Optional[str]]:
        """Install dependencies for a skill.

        Args:
            skill_path: Path to the skill directory
            use_uv: Whether to use uv (None for auto-detection)

        Returns:
            Tuple of (success, installed_dependencies, error_message)
        """
        # Detect dependency files
        dependency_files = self.detect_dependency_files(skill_path)
        if not dependency_files:
            logger.info("No dependency files found")
            return True, [], None

        # Resolve dependencies
        dependencies = self.resolve_dependencies(dependency_files)
        if not dependencies:
            logger.info("No dependencies to install")
            return True, [], None

        # Determine package manager to use
        if use_uv is None:
            use_uv = self.is_uv_available()
            if not use_uv and not self.is_pip_available():
                error_msg = "Neither uv nor pip is available for dependency installation"
                logger.error(error_msg)
                return False, [], error_msg
        elif use_uv and not self.is_uv_available():
            logger.warning("uv requested but not available, falling back to pip")
            use_uv = False
            if not self.is_pip_available():
                error_msg = "pip is not available for dependency installation"
                logger.error(error_msg)
                return False, [], error_msg

        # Install dependencies
        try:
            cmd = self._get_install_command(dependencies, use_uv)
            logger.info(f"Installing dependencies with command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.install_timeout,
                cwd=skill_path
            )

            if result.returncode == 0:
                logger.info("Dependencies installed successfully")
                return True, dependencies, None
            else:
                error_msg = f"Dependency installation failed: {result.stderr}"
                logger.error(error_msg)
                return False, [], error_msg

        except subprocess.TimeoutExpired:
            error_msg = f"Dependency installation timed out after {self.install_timeout} seconds"
            logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Dependency installation failed: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def get_package_manager_info(self) -> Dict[str, Any]:
        """Get information about available package managers.

        Returns:
            Dictionary with package manager availability and versions
        """
        info: Dict[str, Any] = {
            'uv': {'available': False, 'version': None},
            'pip': {'available': False, 'version': None},
            'virtual_env': self._is_in_virtual_env()
        }

        # Check uv
        if self.is_uv_available():
            try:
                result = subprocess.run(
                    ['uv', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    info['uv']['available'] = True
                    info['uv']['version'] = result.stdout.strip()
            except Exception:
                pass

        # Check pip
        if self.is_pip_available():
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    info['pip']['available'] = True
                    info['pip']['version'] = result.stdout.strip()
            except Exception:
                pass

        return info
