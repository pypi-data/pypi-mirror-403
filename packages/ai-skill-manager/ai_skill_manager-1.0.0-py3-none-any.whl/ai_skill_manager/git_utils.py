"""Git command execution utilities for Python."""

import platform
import re
import subprocess
from dataclasses import dataclass
from typing import NamedTuple, Optional


@dataclass
class GitCommandResult:
    """Result of a git command execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int


class GitVersion(NamedTuple):
    """Git version information."""
    major: int
    minor: int
    patch: int
    full: str


class GitUtils:
    """Utilities for git command execution and version management."""

    MIN_GIT_VERSION = GitVersion(2, 25, 0, "2.25.0")

    @classmethod
    def execute_git_command(cls, args: list[str], cwd: Optional[str] = None, timeout: int = 30) -> GitCommandResult:
        """Execute a git command and return the result.

        Args:
            args: Git command arguments
            cwd: Working directory for the command
            timeout: Command timeout in seconds

        Returns:
            GitCommandResult with execution details
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return GitCommandResult(
                success=result.returncode == 0,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return GitCommandResult(
                success=False,
                stdout="",
                stderr=f"Git command timed out after {timeout} seconds",
                exit_code=124
            )
        except FileNotFoundError:
            return GitCommandResult(
                success=False,
                stdout="",
                stderr="Git command not found. Please install git.",
                exit_code=127
            )
        except Exception as e:
            return GitCommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=1
            )

    @classmethod
    def is_git_available(cls) -> bool:
        """Check if git is available on the system.

        Returns:
            True if git is available, False otherwise
        """
        try:
            result = cls.execute_git_command(['--version'])
            return result.success
        except Exception:
            return False

    @classmethod
    def get_git_version(cls) -> Optional[GitVersion]:
        """Get the installed git version.

        Returns:
            GitVersion object or None if git is not available
        """
        try:
            result = cls.execute_git_command(['--version'])

            if not result.success:
                return None

            # Parse version from output like "git version 2.34.1"
            version_match = re.search(r'git version (\d+)\.(\d+)\.(\d+)', result.stdout)

            if not version_match:
                return None

            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            patch = int(version_match.group(3))

            return GitVersion(major, minor, patch, result.stdout)

        except Exception:
            return None

    @classmethod
    def is_git_version_supported(cls) -> bool:
        """Check if the installed git version supports sparse-checkout.

        Returns:
            True if version is supported, False otherwise
        """
        version = cls.get_git_version()

        if not version:
            return False

        min_version = cls.MIN_GIT_VERSION

        if version.major > min_version.major:
            return True

        if version.major == min_version.major and version.minor > min_version.minor:
            return True

        if (version.major == min_version.major and
            version.minor == min_version.minor and
            version.patch >= min_version.patch):
            return True

        return False

    @classmethod
    def is_valid_repository_url(cls, url: str) -> bool:
        """Validate a git repository URL.

        Args:
            url: Repository URL to validate

        Returns:
            True if URL appears to be a valid git repository URL
        """
        patterns = [
            # GitHub patterns
            r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            r'^git@github\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            # GitLab patterns
            r'^https://gitlab\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            r'^git@gitlab\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            # Bitbucket patterns
            r'^https://bitbucket\.org/[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            r'^git@bitbucket\.org:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
            # Generic git URL patterns
            r'^https://[\w\-\.]+/[\w\-\./]+(?:\.git)?$',
            r'^git@[\w\-\.]+:[\w\-\./]+(?:\.git)?$'
        ]

        return any(re.match(pattern, url) for pattern in patterns)

    @classmethod
    def get_git_installation_guidance(cls) -> str:
        """Get installation guidance message for git.

        Returns:
            Platform-specific installation instructions
        """
        system = platform.system().lower()

        if system == 'darwin':
            return ('Install git using Homebrew: brew install git\n'
                   'Or download from: https://git-scm.com/download/mac')
        elif system == 'windows':
            return 'Download Git for Windows from: https://git-scm.com/download/win'
        elif system == 'linux':
            return ('Install git using your package manager:\n'
                   '  Ubuntu/Debian: sudo apt-get install git\n'
                   '  CentOS/RHEL: sudo yum install git\n'
                   '  Fedora: sudo dnf install git')
        else:
            return 'Install git from: https://git-scm.com/downloads'

    @classmethod
    def get_version_upgrade_guidance(cls, current_version: GitVersion) -> str:
        """Get version upgrade guidance message.

        Args:
            current_version: Currently installed git version

        Returns:
            Upgrade guidance message
        """
        min_version = cls.MIN_GIT_VERSION
        return (f'Git version {current_version.full} detected.\n'
               f'Sparse-checkout requires git >= {min_version.major}.{min_version.minor}.{min_version.patch}\n'
               'Please upgrade git to use selective skill download functionality.\n'
               f'{cls.get_git_installation_guidance()}')
