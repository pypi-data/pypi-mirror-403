"""Core skill management functionality."""

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

from .dependency_manager import DependencyManager
from .git_handler import GitHandler
from .skill_types import (
    DownloadResult,
    ModelType,
    RepositoryInfo,
    SelectiveDownloadOptions,
    SkillDownloadRequest,
    ValidationError,
)


class SkillManager:
    """Manages skills for different AI coding assistants."""

    # Model-specific skill directory mappings
    MODEL_DIRECTORIES = {
        'github-copilot': '.github/skills',
        'claude': '.claude/skills',
        'antigravity': '.agent/skills',
        'codex': '.codex/skills',
        'cursor': '.cursor/skills',
        'codeium': '.codeium/skills',
        'tabnine': '.tabnine/skills',
        'kite': '.kite/skills'
    }

    def __init__(self, project_root: str = "."):
        """Initialize the skill manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.git_handler = GitHandler()
        self.dependency_manager = DependencyManager()

    def detect_model(self) -> Optional[str]:
        """Auto-detect which AI model is being used in the project.

        Returns:
            Detected model name or None if no model detected
        """
        detection_files = {
            'github-copilot': ['.github/copilot.yml', '.github/workflows'],
            'claude': ['.claude', 'claude.json'],
            'antigravity': ['.agent', 'agent.json'],
            'codex': ['.codex', 'codex.json'],
            'cursor': ['.cursor', 'cursor.json'],
            'codeium': ['.codeium', 'codeium.json'],
            'tabnine': ['.tabnine', 'tabnine.json'],
            'kite': ['.kite', 'kite.json']
        }

        for model, files in detection_files.items():
            for file_path in files:
                if (self.project_root / file_path).exists():
                    return model

        return None

    def get_skill_directory(self, model: str) -> Path:
        """Get the skill directory path for a specific model.

        Args:
            model: AI model name

        Returns:
            Path to the skill directory

        Raises:
            ValueError: If model is not supported
        """
        if model not in self.MODEL_DIRECTORIES:
            raise ValueError(f"Unsupported model: {model}")

        skill_dir = self.project_root / self.MODEL_DIRECTORIES[model]
        skill_dir.mkdir(parents=True, exist_ok=True)
        return skill_dir

    def download_skill_from_url(self, url: str, model: str, skill_name: Optional[str] = None) -> bool:
        """Download a skill from a URL.

        Args:
            url: URL to download from
            model: Target AI model
            skill_name: Custom name for the skill file

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Determine skill name from URL if not provided
            if not skill_name:
                parsed_url = urlparse(url)
                skill_name = Path(parsed_url.path).stem or "downloaded_skill"

            # Ensure proper file extension
            if not skill_name.endswith(('.py', '.js', '.md', '.json', '.yml', '.yaml')):
                # Try to detect from content-type or URL
                content_type = response.headers.get('content-type', '')
                if 'python' in content_type or url.endswith('.py'):
                    skill_name += '.py'
                elif 'javascript' in content_type or url.endswith('.js'):
                    skill_name += '.js'
                elif 'json' in content_type or url.endswith('.json'):
                    skill_name += '.json'
                else:
                    skill_name += '.md'  # Default to markdown

            skill_dir = self.get_skill_directory(model)
            skill_path = skill_dir / skill_name

            with open(skill_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            return True

        except Exception as e:
            raise Exception(f"Failed to download skill from {url}: {e}") from e

    def download_github_skill(self, repo: str, path: str, model: str, skill_name: Optional[str] = None) -> bool:
        """Download a skill from a GitHub repository.

        Args:
            repo: GitHub repository (owner/repo format)
            path: Path to skill file in repository
            model: Target AI model
            skill_name: Custom name for the skill file

        Returns:
            True if successful, False otherwise
        """
        # Convert GitHub repo URL to raw content URL
        if repo.startswith('https://github.com/'):
            repo = repo.replace('https://github.com/', '')

        raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"

        # Try main branch first, then master
        try:
            return self.download_skill_from_url(raw_url, model, skill_name)
        except Exception:
            raw_url = f"https://raw.githubusercontent.com/{repo}/master/{path}"
            return self.download_skill_from_url(raw_url, model, skill_name)

    def list_skills(self, model: str) -> List[str]:
        """List all skills for a specific model.

        Args:
            model: AI model name

        Returns:
            List of skill file names
        """
        skill_dir = self.get_skill_directory(model)
        if not skill_dir.exists():
            return []

        skills = []
        for file_path in skill_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                skills.append(file_path.name)

        return sorted(skills)

    def remove_skill(self, model: str, skill_name: str) -> bool:
        """Remove a skill from the specified model directory.

        Args:
            model: AI model name
            skill_name: Name of skill to remove

        Returns:
            True if successful, False otherwise
        """
        skill_dir = self.get_skill_directory(model)
        skill_path = skill_dir / skill_name

        if skill_path.exists():
            skill_path.unlink()
            return True
        else:
            return False

    def copy_skill(self, source_model: str, target_model: str, skill_name: str) -> bool:
        """Copy a skill from one model directory to another.

        Args:
            source_model: Source AI model
            target_model: Target AI model
            skill_name: Name of skill to copy

        Returns:
            True if successful, False otherwise
        """
        source_dir = self.get_skill_directory(source_model)
        target_dir = self.get_skill_directory(target_model)

        source_path = source_dir / skill_name
        target_path = target_dir / skill_name

        if not source_path.exists():
            return False

        shutil.copy2(source_path, target_path)
        return True

    def get_supported_models(self) -> List[str]:
        """Get list of supported AI models.

        Returns:
            List of supported model names
        """
        return list(self.MODEL_DIRECTORIES.keys())

    def download_skill_selective(
        self,
        repo_url: str,
        skill_path: str,
        model: ModelType,
        options: Optional[SelectiveDownloadOptions] = None
    ) -> DownloadResult:
        """Download a specific skill from a repository using sparse-checkout.

        Args:
            repo_url: Repository URL to download from
            skill_path: Path to the skill within the repository
            model: Target AI model
            options: Optional download configuration

        Returns:
            DownloadResult with download status and details
        """
        options = options or SelectiveDownloadOptions()

        try:
            # Validate inputs
            if model not in self.MODEL_DIRECTORIES:
                raise ValidationError(f"Unsupported model: {model}")

            # Get skill directory
            skill_dir = self.get_skill_directory(model)

            # Determine skill name
            skill_name = options.skill_name
            if not skill_name:
                skill_name = Path(skill_path).name
                if not skill_name:
                    skill_name = "downloaded_skill"

            # Create target directory for this skill
            target_dir = skill_dir / skill_name

            # Download using git handler
            downloaded_files = self.git_handler.clone_with_sparse_checkout(
                repo_url, skill_path, str(target_dir), options
            )

            # Install dependencies if requested
            installed_dependencies = []
            if options.install_dependencies:
                try:
                    success, deps, error = self.dependency_manager.install_dependencies(
                        str(target_dir),
                        use_uv=(options.dependency_manager == 'uv') if options.dependency_manager != 'auto' else None
                    )
                    if success:
                        installed_dependencies = deps
                    elif error:
                        # Log warning but don't fail the download
                        print(f"Warning: Dependency installation failed: {error}")
                except Exception as e:
                    print(f"Warning: Dependency installation failed: {str(e)}")

            return DownloadResult(
                success=True,
                skill_name=skill_name,
                model=model,
                downloaded_files=downloaded_files,
                installed_dependencies=installed_dependencies
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                skill_name=options.skill_name or Path(skill_path).name or "unknown",
                model=model,
                error=str(e),
                downloaded_files=[],
                installed_dependencies=[]
            )

    def download_multiple_skills(self, requests: List[SkillDownloadRequest]) -> List[DownloadResult]:
        """Download multiple skills in batch.

        Args:
            requests: List of skill download requests

        Returns:
            List of download results
        """
        results = []

        # Group requests by repository for efficiency (Requirement 7.2)
        repo_groups: Dict[str, List[SkillDownloadRequest]] = {}
        for request in requests:
            repo_url = request.repo_url
            if repo_url not in repo_groups:
                repo_groups[repo_url] = []
            repo_groups[repo_url].append(request)

        # Process each repository group
        for _repo_url, repo_requests in repo_groups.items():
            for request in repo_requests:
                result = self.download_skill_selective(
                    request.repo_url,
                    request.skill_path,
                    request.model,
                    request.options
                )
                results.append(result)

        return results

    def list_repository_skills(self, repo_url: str) -> List[str]:
        """List available skills in a repository.

        Args:
            repo_url: Repository URL to explore

        Returns:
            List of skill paths found in the repository

        Raises:
            GitError: If repository cannot be accessed
            ValidationError: If URL is invalid
        """
        return self.git_handler.list_repository_skills(repo_url)

    def get_repository_info(self, repo_url: str) -> RepositoryInfo:
        """Get information about a repository.

        Args:
            repo_url: Repository URL

        Returns:
            RepositoryInfo object with repository details

        Raises:
            GitError: If repository information cannot be retrieved
            ValidationError: If URL is invalid
        """
        return self.git_handler.get_repository_info(repo_url)
