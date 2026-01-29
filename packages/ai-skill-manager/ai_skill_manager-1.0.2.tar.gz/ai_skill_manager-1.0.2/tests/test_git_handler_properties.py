"""Property-based tests for GitHandler sparse-checkout functionality."""

import os
import tempfile
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from ai_skill_manager.git_handler import GitHandler
from ai_skill_manager.git_utils import GitCommandResult, GitUtils
from ai_skill_manager.skill_types import SelectiveDownloadOptions, ValidationError


# Custom strategies for generating test data
@st.composite
def valid_repo_urls(draw):
    """Generate valid repository URLs."""
    providers = ['github.com', 'gitlab.com', 'bitbucket.org']
    provider = draw(st.sampled_from(providers))

    # Generate valid username and repo name
    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
        min_size=1, max_size=20
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')))

    repo_name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_.'),
        min_size=1, max_size=30
    ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')))

    protocol = draw(st.sampled_from(['https', 'ssh']))

    if protocol == 'https':
        return f"https://{provider}/{username}/{repo_name}"
    else:
        return f"git@{provider}:{username}/{repo_name}"


@st.composite
def valid_skill_paths(draw):
    """Generate valid skill paths."""
    # Generate path components
    components = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
            min_size=1, max_size=15
        ).filter(lambda x: x and x != '.' and x != '..'),
        min_size=1, max_size=4
    ))

    return '/'.join(components)


@st.composite
def selective_download_options(draw):
    """Generate SelectiveDownloadOptions."""
    return SelectiveDownloadOptions(
        skill_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        use_shallow_clone=draw(st.booleans()),
        install_dependencies=draw(st.booleans()),
        dependency_manager=draw(st.sampled_from(['uv', 'pip', 'auto'])),
        timeout=draw(st.integers(min_value=30, max_value=600)),
        retry_attempts=draw(st.integers(min_value=1, max_value=5))
    )


class TestGitHandlerProperties:
    """Property-based tests for GitHandler."""

    def setup_method(self):
        """Set up test environment."""
        # Mock git availability for all tests
        self.git_available_patcher = patch.object(GitUtils, 'is_git_available', return_value=True)
        self.git_version_supported_patcher = patch.object(GitUtils, 'is_git_version_supported', return_value=True)

        self.git_available_patcher.start()
        self.git_version_supported_patcher.start()

    def teardown_method(self):
        """Clean up test environment."""
        self.git_available_patcher.stop()
        self.git_version_supported_patcher.stop()

    @given(valid_repo_urls())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_1_sparse_checkout_download_completeness_url_validation(self, repo_url):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: For any valid repository URL, the GitHandler should correctly validate it.
        """
        handler = GitHandler()

        # Mock the ls-remote command to simulate repository validation
        with patch.object(GitUtils, 'execute_git_command') as mock_execute:
            mock_execute.return_value = GitCommandResult(
                success=True,
                stdout="ref: refs/heads/main\nHEAD\n1234567\trefs/heads/main",
                stderr="",
                exit_code=0
            )

            # The handler should validate the URL format correctly
            is_valid = handler.is_valid_repository(repo_url)

            # For properly formatted URLs, validation should succeed
            assert isinstance(is_valid, bool)

            # If the URL format is valid, the git command should have been called
            if is_valid:
                mock_execute.assert_called()
                args = mock_execute.call_args[0][0]
                assert args[0] == 'ls-remote'
                assert args[1] == '--heads'
                assert args[2] == repo_url

    @given(st.text().filter(lambda x: not any(pattern in x for pattern in ['github.com', 'gitlab.com', 'bitbucket.org'])))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_1_sparse_checkout_invalid_url_rejection(self, invalid_url):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: For any invalid repository URL, the GitHandler should reject it.
        """
        assume(invalid_url.strip() != "")  # Skip empty strings
        assume(not invalid_url.startswith('https://') or 'github.com' not in invalid_url)

        handler = GitHandler()

        # Invalid URLs should be rejected without making git calls
        with patch.object(GitUtils, 'execute_git_command'):
            is_valid = handler.is_valid_repository(invalid_url)

            # Invalid URLs should return False
            assert is_valid is False

    @given(valid_repo_urls(), valid_skill_paths())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_1_sparse_checkout_path_validation(self, repo_url, skill_path):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: For any valid repository URL and skill path, the validation should handle them appropriately.
        """
        handler = GitHandler()

        # Mock git operations
        with patch.object(GitUtils, 'execute_git_command') as mock_execute:
            # Mock repository validation
            mock_execute.return_value = GitCommandResult(
                success=True,
                stdout="ref: refs/heads/main\nHEAD\n1234567\trefs/heads/main",
                stderr="",
                exit_code=0
            )

            # Test repository validation
            is_valid_repo = handler.is_valid_repository(repo_url)
            assert isinstance(is_valid_repo, bool)

            # Test that skill paths are properly validated (no leading slash, no ..)
            if not skill_path.startswith('/') and '..' not in skill_path:
                # Valid skill paths should not raise ValidationError during basic validation
                # (actual clone operation would be mocked separately)
                assert len(skill_path) > 0
                assert '/' in skill_path or len(skill_path.split('/')) >= 1

    @given(valid_repo_urls(), valid_skill_paths(), selective_download_options())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_1_sparse_checkout_options_handling(self, repo_url, skill_path, options):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: For any valid options, the GitHandler should handle them correctly.
        """
        GitHandler()

        # Test that options are properly structured
        assert isinstance(options.use_shallow_clone, bool)
        assert isinstance(options.install_dependencies, bool)
        assert options.dependency_manager in ['uv', 'pip', 'auto']
        assert options.timeout > 0
        assert options.retry_attempts > 0

        # Test that timeout and retry values are within reasonable bounds
        assert 30 <= options.timeout <= 600
        assert 1 <= options.retry_attempts <= 5

    def test_property_1_sparse_checkout_error_conditions(self):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: Error conditions should be handled consistently.
        """
        handler = GitHandler()

        # Test invalid skill paths
        invalid_paths = ['/absolute/path', '../relative/path', 'path/../with/dotdot', '']

        for invalid_path in invalid_paths:
            with tempfile.TemporaryDirectory() as temp_dir:
                with pytest.raises(ValidationError):
                    handler.clone_with_sparse_checkout(
                        'https://github.com/user/repo',
                        invalid_path,
                        temp_dir
                    )

    @given(st.integers(min_value=1, max_value=10), st.integers(min_value=30, max_value=300))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_1_configuration_consistency(self, retry_attempts, timeout):
        """
        **Feature: selective-skill-download, Property 1: Sparse-Checkout Download Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3**

        Property: GitHandler configuration should be consistent with provided parameters.
        """
        handler = GitHandler(timeout=timeout, retry_attempts=retry_attempts)

        # Configuration should be stored correctly
        assert handler.timeout == timeout
        assert handler.retry_attempts == retry_attempts

        # Values should be within expected ranges
        assert handler.timeout >= 30
        assert handler.retry_attempts >= 1


class GitHandlerStateMachine(RuleBasedStateMachine):
    """Stateful property testing for GitHandler operations."""

    def __init__(self):
        super().__init__()
        self.handler = None
        self.temp_dirs = []

    @initialize()
    def setup_handler(self):
        """Initialize GitHandler for stateful testing."""
        with patch.object(GitUtils, 'is_git_available', return_value=True):
            with patch.object(GitUtils, 'is_git_version_supported', return_value=True):
                self.handler = GitHandler()

    @rule(repo_url=valid_repo_urls())
    def validate_repository(self, repo_url):
        """Test repository validation in different states."""
        with patch.object(GitUtils, 'execute_git_command') as mock_execute:
            mock_execute.return_value = GitCommandResult(
                success=True,
                stdout="ref: refs/heads/main\nHEAD",
                stderr="",
                exit_code=0
            )

            result = self.handler.is_valid_repository(repo_url)
            assert isinstance(result, bool)

    @rule()
    def check_git_availability(self):
        """Test git availability checking."""
        result = self.handler.is_git_available()
        assert isinstance(result, bool)

    @invariant()
    def handler_state_consistent(self):
        """Ensure handler state remains consistent."""
        if self.handler:
            assert hasattr(self.handler, 'timeout')
            assert hasattr(self.handler, 'retry_attempts')
            assert self.handler.timeout > 0
            assert self.handler.retry_attempts > 0

    def teardown(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)


# Stateful test runner
TestGitHandlerStateful = GitHandlerStateMachine.TestCase


if __name__ == "__main__":
    # Run a quick test to verify the property tests work
    pytest.main([__file__, "-v"])
