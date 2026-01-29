"""AI Skill Manager - Manage skills for different AI coding assistants."""

__version__ = "0.1.0"

from .dependency_manager import DependencyManager
from .git_handler import GitHandler
from .git_utils import GitUtils
from .manager import SkillManager
from .skill_types import (
    DependencyConfig,
    DependencyError,
    DependencyFile,
    DownloadResult,
    GitConfig,
    GitError,
    ModelType,
    NetworkError,
    RepositoryInfo,
    SelectiveDownloadOptions,
    SkillDownloadRequest,
    SkillInfo,
    SkillManagerConfig,
    SkillManagerError,
    ValidationError,
)

__all__ = [
    "SkillManager",
    "GitUtils",
    "GitHandler",
    "DependencyManager",
    "ModelType",
    "SelectiveDownloadOptions",
    "SkillDownloadRequest",
    "DownloadResult",
    "RepositoryInfo",
    "DependencyFile",
    "SkillInfo",
    "GitConfig",
    "DependencyConfig",
    "SkillManagerConfig",
    "SkillManagerError",
    "GitError",
    "DependencyError",
    "ValidationError",
    "NetworkError"
]
