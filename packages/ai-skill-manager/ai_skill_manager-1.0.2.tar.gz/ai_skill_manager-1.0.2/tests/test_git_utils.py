"""Tests for GitUtils functionality."""

from ai_skill_manager.git_utils import GitUtils


class TestGitUtils:
    """Test cases for GitUtils class."""

    def test_is_valid_repository_url_github_https(self):
        """Test GitHub HTTPS URL validation."""
        assert GitUtils.is_valid_repository_url('https://github.com/user/repo')
        assert GitUtils.is_valid_repository_url('https://github.com/user/repo.git')

    def test_is_valid_repository_url_github_ssh(self):
        """Test GitHub SSH URL validation."""
        assert GitUtils.is_valid_repository_url('git@github.com:user/repo')
        assert GitUtils.is_valid_repository_url('git@github.com:user/repo.git')

    def test_is_valid_repository_url_gitlab(self):
        """Test GitLab URL validation."""
        assert GitUtils.is_valid_repository_url('https://gitlab.com/user/repo')
        assert GitUtils.is_valid_repository_url('git@gitlab.com:user/repo')

    def test_is_valid_repository_url_invalid(self):
        """Test invalid URL rejection."""
        assert not GitUtils.is_valid_repository_url('not-a-url')
        assert not GitUtils.is_valid_repository_url('https://example.com')
        assert not GitUtils.is_valid_repository_url('')

    def test_get_git_installation_guidance(self):
        """Test git installation guidance."""
        guidance = GitUtils.get_git_installation_guidance()
        assert isinstance(guidance, str)
        assert len(guidance) > 0
        assert 'git' in guidance.lower()

    def test_is_git_available(self):
        """Test git availability check."""
        is_available = GitUtils.is_git_available()
        assert isinstance(is_available, bool)

    def test_get_git_version(self):
        """Test git version retrieval."""
        is_available = GitUtils.is_git_available()
        if is_available:
            version = GitUtils.get_git_version()
            assert version is not None
            assert version.major > 0
            assert version.minor >= 0
            assert version.patch >= 0
            assert 'git version' in version.full

    def test_is_git_version_supported(self):
        """Test git version support check."""
        is_supported = GitUtils.is_git_version_supported()
        assert isinstance(is_supported, bool)
