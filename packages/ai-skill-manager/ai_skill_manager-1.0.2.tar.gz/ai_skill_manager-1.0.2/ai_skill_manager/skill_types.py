"""Type definitions for AI Skill Manager Python package."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional

# Model type definition
ModelType = Literal[
    'github-copilot',
    'claude',
    'antigravity',
    'codex',
    'cursor',
    'codeium',
    'tabnine',
    'kite'
]

# Dependency manager types
DependencyManagerType = Literal['uv', 'pip', 'auto']


@dataclass
class SelectiveDownloadOptions:
    """Options for selective skill download."""
    skill_name: Optional[str] = None
    use_shallow_clone: bool = True
    install_dependencies: bool = True
    dependency_manager: DependencyManagerType = 'auto'
    timeout: int = 300  # 5 minutes default
    retry_attempts: int = 3


@dataclass
class SkillDownloadRequest:
    """Request for downloading a skill."""
    repo_url: str
    skill_path: str
    model: ModelType
    options: Optional[SelectiveDownloadOptions] = None


@dataclass
class DownloadResult:
    """Result of a skill download operation."""
    success: bool
    skill_name: str
    model: ModelType
    error: Optional[str] = None
    downloaded_files: List[str] = field(default_factory=list)
    installed_dependencies: Optional[List[str]] = None

    def __post_init__(self) -> None:
        pass


@dataclass
class RepositoryInfo:
    """Information about a git repository."""
    url: str
    default_branch: str
    available_skills: List[str]
    last_updated: datetime
    size: int


@dataclass
class DependencyFile:
    """Information about a dependency file."""
    path: str
    type: Literal['requirements.txt', 'pyproject.toml', 'package.json']
    content: str


@dataclass
class SkillInfo:
    """Information about an installed skill."""
    name: str
    path: str
    model: ModelType
    size: int
    modified: datetime


# Configuration types
@dataclass
class GitConfig:
    """Git-specific configuration options."""
    timeout: int = 300
    retry_attempts: int = 3
    shallow_clone: bool = True
    use_sparse_checkout: bool = True


@dataclass
class DependencyConfig:
    """Dependency management configuration."""
    preferred_manager: DependencyManagerType = 'auto'
    install_timeout: int = 600  # 10 minutes
    respect_virtual_env: bool = True


@dataclass
class SkillManagerConfig:
    """Overall skill manager configuration."""
    project_root: str = "."
    temp_directory: Optional[str] = None
    git_config: GitConfig = field(default_factory=lambda: GitConfig())
    dependency_config: DependencyConfig = field(default_factory=lambda: DependencyConfig())

    def __post_init__(self) -> None:
        pass


# Error types
class SkillManagerError(Exception):
    """Base exception for skill manager errors."""
    pass


class GitError(SkillManagerError):
    """Git operation related errors."""
    pass


class DependencyError(SkillManagerError):
    """Dependency installation related errors."""
    pass


class ValidationError(SkillManagerError):
    """Input validation related errors."""
    pass


class NetworkError(SkillManagerError):
    """Network operation related errors."""
    pass
