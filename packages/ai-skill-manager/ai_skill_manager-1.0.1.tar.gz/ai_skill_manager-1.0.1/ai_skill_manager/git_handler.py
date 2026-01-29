"""Git Handler for selective skill download operations."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from .git_utils import GitUtils
from .skill_types import (
    GitError,
    NetworkError,
    RepositoryInfo,
    SelectiveDownloadOptions,
    ValidationError,
)


class GitHandler:
    """Handles git operations for selective skill downloads."""

    def __init__(self, timeout: int = 300, retry_attempts: int = 3):
        """Initialize the GitHandler.

        Args:
            timeout: Default timeout for git operations in seconds
            retry_attempts: Number of retry attempts for network operations
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        # Verify git availability and version
        if not GitUtils.is_git_available():
            raise GitError(GitUtils.get_git_installation_guidance())

        if not GitUtils.is_git_version_supported():
            version = GitUtils.get_git_version()
            if version:
                raise GitError(GitUtils.get_version_upgrade_guidance(version))
            else:
                raise GitError("Unable to determine git version")

    def is_valid_repository(self, url: str) -> bool:
        """Validate if a URL is a valid git repository.

        Args:
            url: Repository URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not GitUtils.is_valid_repository_url(url):
            return False

        # Additional validation by attempting to get repository info
        try:
            result = GitUtils.execute_git_command(
                ['ls-remote', '--heads', url],
                timeout=30
            )
            return result.success
        except Exception:
            return False

    def get_repository_info(self, url: str) -> RepositoryInfo:
        """Get information about a git repository.

        Args:
            url: Repository URL

        Returns:
            RepositoryInfo object with repository details

        Raises:
            GitError: If repository information cannot be retrieved
            ValidationError: If URL is invalid
        """
        if not self.is_valid_repository(url):
            raise ValidationError(f"Invalid repository URL: {url}")

        try:
            # Get remote branches to determine default branch
            result = GitUtils.execute_git_command(
                ['ls-remote', '--heads', url],
                timeout=self.timeout
            )

            if not result.success:
                raise GitError(f"Failed to access repository: {result.stderr}")

            # Parse branches from output
            branches = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        branch_ref = parts[1]
                        if branch_ref.startswith('refs/heads/'):
                            branch_name = branch_ref.replace('refs/heads/', '')
                            branches.append(branch_name)

            # Determine default branch (prefer main, then master, then first available)
            default_branch = 'main'
            if 'main' not in branches:
                if 'master' in branches:
                    default_branch = 'master'
                elif branches:
                    default_branch = branches[0]
                else:
                    default_branch = 'main'  # fallback

            # For now, we'll return basic info - skill detection would require cloning
            from datetime import datetime
            return RepositoryInfo(
                url=url,
                default_branch=default_branch,
                available_skills=[],  # Would need full clone to detect
                last_updated=datetime.now(),
                size=0  # Would need additional API calls to determine
            )

        except Exception as e:
            if isinstance(e, (GitError, ValidationError)):
                raise
            raise GitError(f"Failed to get repository information: {str(e)}") from e

    def initialize_sparse_checkout(self, repo_path: str) -> None:
        """Initialize sparse-checkout in a git repository.

        Args:
            repo_path: Path to the git repository

        Raises:
            GitError: If sparse-checkout initialization fails
        """
        try:
            # Enable sparse-checkout
            result = GitUtils.execute_git_command(
                ['config', 'core.sparseCheckout', 'true'],
                cwd=repo_path,
                timeout=self.timeout
            )

            if not result.success:
                raise GitError(f"Failed to enable sparse-checkout: {result.stderr}")

            # Initialize sparse-checkout
            result = GitUtils.execute_git_command(
                ['sparse-checkout', 'init'],
                cwd=repo_path,
                timeout=self.timeout
            )

            if not result.success:
                raise GitError(f"Failed to initialize sparse-checkout: {result.stderr}")

        except Exception as e:
            if isinstance(e, GitError):
                raise
            raise GitError(f"Failed to initialize sparse-checkout: {str(e)}") from e

    def configure_sparse_checkout(self, repo_path: str, skill_paths: List[str]) -> None:
        """Configure sparse-checkout patterns for specific skill paths.

        Args:
            repo_path: Path to the git repository
            skill_paths: List of skill paths to include in sparse-checkout

        Raises:
            GitError: If sparse-checkout configuration fails
        """
        try:
            # Set sparse-checkout patterns
            result = GitUtils.execute_git_command(
                ['sparse-checkout', 'set'] + skill_paths,
                cwd=repo_path,
                timeout=self.timeout
            )

            if not result.success:
                raise GitError(f"Failed to configure sparse-checkout: {result.stderr}")

        except Exception as e:
            if isinstance(e, GitError):
                raise
            raise GitError(f"Failed to configure sparse-checkout: {str(e)}") from e

    def clone_with_sparse_checkout(
        self,
        repo_url: str,
        skill_path: str,
        target_dir: str,
        options: Optional[SelectiveDownloadOptions] = None
    ) -> List[str]:
        """Clone a repository with sparse-checkout for a specific skill.

        Args:
            repo_url: Repository URL to clone
            skill_path: Path to the skill within the repository
            target_dir: Target directory for the skill files
            options: Optional download configuration

        Returns:
            List of downloaded file paths

        Raises:
            GitError: If clone operation fails
            ValidationError: If inputs are invalid
            NetworkError: If network operation fails
        """
        if not self.is_valid_repository(repo_url):
            raise ValidationError(f"Invalid repository URL: {repo_url}")

        if not skill_path or skill_path.startswith('/') or '..' in skill_path:
            raise ValidationError(f"Invalid skill path: {skill_path}")

        options = options or SelectiveDownloadOptions()
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        # Create temporary directory for git operations
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_repo_path = Path(temp_dir) / "repo"

            try:
                # Initialize empty repository
                result = GitUtils.execute_git_command(
                    ['init'],
                    cwd=str(temp_repo_path.parent),
                    timeout=self.timeout
                )

                if not result.success:
                    raise GitError(f"Failed to initialize repository: {result.stderr}")

                # Create the repo directory
                temp_repo_path.mkdir(exist_ok=True)

                # Add remote origin
                result = GitUtils.execute_git_command(
                    ['remote', 'add', 'origin', repo_url],
                    cwd=str(temp_repo_path),
                    timeout=self.timeout
                )

                if not result.success:
                    raise GitError(f"Failed to add remote origin: {result.stderr}")

                # Initialize and configure sparse-checkout
                self.initialize_sparse_checkout(str(temp_repo_path))
                self.configure_sparse_checkout(str(temp_repo_path), [skill_path])

                # Perform shallow clone with sparse-checkout
                repo_info = self.get_repository_info(repo_url)
                clone_args = ['pull', 'origin', repo_info.default_branch]

                if options.use_shallow_clone:
                    clone_args.extend(['--depth', '1'])

                # Retry logic for network operations
                last_error = None
                for attempt in range(self.retry_attempts):
                    try:
                        result = GitUtils.execute_git_command(
                            clone_args,
                            cwd=str(temp_repo_path),
                            timeout=self.timeout
                        )

                        if result.success:
                            break
                        else:
                            last_error = result.stderr

                    except Exception as e:
                        last_error = str(e)

                    if attempt < self.retry_attempts - 1:
                        # Exponential backoff
                        import time
                        time.sleep(2 ** attempt)
                else:
                    raise NetworkError(f"Failed to clone repository after {self.retry_attempts} attempts: {last_error}")

                # Verify skill path exists
                skill_source_path = temp_repo_path / skill_path
                if not skill_source_path.exists():
                    raise ValidationError(f"Skill path '{skill_path}' not found in repository")

                # Copy skill files to target directory
                downloaded_files = []

                if skill_source_path.is_file():
                    # Single file skill
                    target_file = target_path / skill_source_path.name
                    shutil.copy2(skill_source_path, target_file)
                    downloaded_files.append(str(target_file.relative_to(target_path)))
                else:
                    # Directory skill - copy entire subtree
                    for root, _dirs, files in os.walk(skill_source_path):
                        root_path = Path(root)
                        rel_root = root_path.relative_to(skill_source_path)

                        # Create directory structure
                        target_subdir = target_path / rel_root
                        target_subdir.mkdir(parents=True, exist_ok=True)

                        # Copy files
                        for file_name in files:
                            source_file = root_path / file_name
                            target_file = target_subdir / file_name
                            shutil.copy2(source_file, target_file)
                            downloaded_files.append(str(target_file.relative_to(target_path)))

                return downloaded_files

            except Exception as e:
                if isinstance(e, (GitError, ValidationError, NetworkError)):
                    raise
                raise GitError(f"Unexpected error during clone operation: {str(e)}") from e

    def list_repository_skills(self, repo_url: str) -> List[str]:
        """List available skills in a repository.

        Args:
            repo_url: Repository URL

        Returns:
            List of skill paths found in the repository

        Raises:
            GitError: If repository cannot be accessed
            ValidationError: If URL is invalid
        """
        if not self.is_valid_repository(repo_url):
            raise ValidationError(f"Invalid repository URL: {repo_url}")

        # For now, return empty list - full implementation would require
        # cloning the repository and scanning for skill directories
        # This is a placeholder for future enhancement
        return []

    def is_git_available(self) -> bool:
        """Check if git is available on the system.

        Returns:
            True if git is available and supported version
        """
        return GitUtils.is_git_available() and GitUtils.is_git_version_supported()

    def get_git_version(self) -> Optional[str]:
        """Get the git version string.

        Returns:
            Git version string or None if not available
        """
        version = GitUtils.get_git_version()
        return version.full if version else None
