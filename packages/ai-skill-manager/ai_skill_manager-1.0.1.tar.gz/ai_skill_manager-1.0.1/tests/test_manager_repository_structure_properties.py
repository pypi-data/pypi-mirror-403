"""Property-based tests for SkillManager repository structure handling."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from ai_skill_manager.git_utils import GitUtils
from ai_skill_manager.manager import SkillManager
from ai_skill_manager.skill_types import (
    SkillDownloadRequest,
    ValidationError,
)


# Custom strategies for generating test data
@st.composite
def valid_repo_urls(draw):
    """Generate valid repository URLs."""
    providers = ['github.com', 'gitlab.com', 'bitbucket.org']
    provider = draw(st.sampled_from(providers))

    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
        min_size=1, max_size=20
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')))

    repo_name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_.'),
        min_size=1, max_size=30
    ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')))

    return f"https://{provider}/{username}/{repo_name}"


@st.composite
def skill_directory_structures(draw):
    """Generate skill directory structures with multiple levels."""
    # Generate nested directory structures
    depth = draw(st.integers(min_value=1, max_value=4))
    components = []

    for _ in range(depth):
        component = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
            min_size=1, max_size=15
        ).filter(lambda x: x and x != '.' and x != '..'))
        components.append(component)

    return '/'.join(components)


@st.composite
def multi_skill_repositories(draw):
    """Generate repositories with multiple skill directories."""
    num_skills = draw(st.integers(min_value=2, max_value=5))
    skills = []

    for _ in range(num_skills):
        skill_path = draw(skill_directory_structures())
        skills.append(skill_path)

    # Ensure unique skill paths
    return list(set(skills))


@st.composite
def model_types(draw):
    """Generate valid model types."""
    models = ['github-copilot', 'claude', 'antigravity', 'codex', 'cursor', 'codeium', 'tabnine', 'kite']
    return draw(st.sampled_from(models))


class TestSkillManagerRepositoryStructure:
    """Property-based tests for SkillManager repository structure handling."""

    def setup_method(self):
        """Set up test environment."""
        # Mock git availability for all tests
        self.git_available_patcher = patch.object(GitUtils, 'is_git_available', return_value=True)
        self.git_version_supported_patcher = patch.object(GitUtils, 'is_git_version_supported', return_value=True)

        self.git_available_patcher.start()
        self.git_version_supported_patcher.start()

        # Create temporary project root
        self.temp_project_root = tempfile.mkdtemp()
        self.skill_manager = SkillManager(project_root=self.temp_project_root)

    def teardown_method(self):
        """Clean up test environment."""
        self.git_available_patcher.stop()
        self.git_version_supported_patcher.stop()

        # Clean up temporary directory
        if os.path.exists(self.temp_project_root):
            shutil.rmtree(self.temp_project_root, ignore_errors=True)

    @given(valid_repo_urls(), skill_directory_structures(), model_types())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_repository_structure_skill_path_targeting(self, repo_url, skill_path, model):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: For any repository containing multiple skill folders, the system should be able
        to download any specified skill path while preserving the complete directory subtree structure.
        """
        # Mock git operations to simulate successful download
        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            # Simulate downloaded files with proper directory structure
            mock_files = []
            if '/' in skill_path:
                # Multi-level directory structure
                parts = skill_path.split('/')
                for i, _part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Add some files in the final directory
                        mock_files.extend([
                            f"{'/'.join(parts[:i+1])}/main.py",
                            f"{'/'.join(parts[:i+1])}/config.json",
                            f"{'/'.join(parts[:i+1])}/README.md"
                        ])
                    else:
                        # Add intermediate directory marker
                        mock_files.append(f"{'/'.join(parts[:i+1])}/")
            else:
                # Single directory
                mock_files = [
                    f"{skill_path}/main.py",
                    f"{skill_path}/config.json",
                    f"{skill_path}/README.md"
                ]

            mock_clone.return_value = mock_files

            # Test selective download
            result = self.skill_manager.download_skill_selective(
                repo_url, skill_path, model
            )

            # Verify the download was successful
            assert result.success is True
            assert result.model == model
            assert result.skill_name == Path(skill_path).name
            assert len(result.downloaded_files) > 0

            # Verify git handler was called with correct parameters
            mock_clone.assert_called_once()
            call_args = mock_clone.call_args
            assert call_args[0][0] == repo_url  # repo_url
            assert call_args[0][1] == skill_path  # skill_path

            # Verify target directory structure
            target_dir = Path(call_args[0][2]).resolve()
            expected_skill_dir = (Path(self.temp_project_root) / self.skill_manager.MODEL_DIRECTORIES[model] / Path(skill_path).name).resolve()
            assert expected_skill_dir == target_dir

    @given(valid_repo_urls(), multi_skill_repositories(), model_types())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_repository_structure_multiple_skills_isolation(self, repo_url, skill_paths, model):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: When downloading multiple skills from the same repository, each skill should
        be isolated in its own directory structure.
        """
        assume(len(skill_paths) >= 2)  # Ensure we have multiple skills

        # Filter out skill paths that would result in duplicate names
        unique_names = set()
        filtered_paths = []
        for path in skill_paths:
            name = Path(path).name
            if name not in unique_names:
                unique_names.add(name)
                filtered_paths.append(path)

        assume(len(filtered_paths) >= 2)  # Ensure we still have multiple unique skills

        # Mock git operations
        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            # Create download requests for multiple skills
            requests = []
            for skill_path in filtered_paths[:3]:  # Limit to 3 skills for performance
                requests.append(SkillDownloadRequest(
                    repo_url=repo_url,
                    skill_path=skill_path,
                    model=model
                ))

            # Mock different file sets for each skill
            def mock_clone_side_effect(repo_url, skill_path, target_dir, options=None):
                return [
                    f"{skill_path}/main.py",
                    f"{skill_path}/config.json"
                ]

            mock_clone.side_effect = mock_clone_side_effect

            # Download multiple skills
            results = self.skill_manager.download_multiple_skills(requests)

            # Verify all downloads were successful
            assert len(results) == len(requests)
            for result in results:
                assert result.success is True
                assert result.model == model

            # Verify each skill has its own directory
            skill_names = [result.skill_name for result in results]
            assert len(set(skill_names)) == len(skill_names)  # All names should be unique

            # Verify git handler was called for each skill
            assert mock_clone.call_count == len(requests)

    @given(valid_repo_urls(), skill_directory_structures(), model_types())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_repository_structure_subdirectory_preservation(self, repo_url, skill_path, model):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: When a skill path contains subdirectories, the system should download
        the entire skill subtree while preserving directory structure.
        """
        # Create a complex directory structure
        assume('/' in skill_path)  # Ensure we have subdirectories

        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            # Simulate complex directory structure with nested files
            mock_files = []
            path_parts = skill_path.split('/')

            # Create files at different levels
            for i in range(len(path_parts)):
                current_path = '/'.join(path_parts[:i+1])
                mock_files.extend([
                    f"{current_path}/file_{i}.py",
                    f"{current_path}/config_{i}.json"
                ])

                # Add subdirectories
                if i < len(path_parts) - 1:
                    mock_files.append(f"{current_path}/subdir/nested_file.py")

            mock_clone.return_value = mock_files

            # Test download
            result = self.skill_manager.download_skill_selective(
                repo_url, skill_path, model
            )

            # Verify successful download
            assert result.success is True
            assert len(result.downloaded_files) > 0

            # Verify that files from different directory levels are included
            downloaded_files = result.downloaded_files

            # Should have files from multiple directory levels
            file_depths = [file_path.count('/') for file_path in downloaded_files]
            assert len(set(file_depths)) > 1  # Multiple directory levels

            # Verify directory structure is preserved in file paths
            for file_path in downloaded_files:
                # Each file should maintain its relative path structure
                assert not file_path.startswith('/')  # Should be relative paths
                assert '..' not in file_path  # No parent directory references

    @given(valid_repo_urls(), st.text(min_size=1, max_size=50), model_types())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much])
    def test_property_4_repository_structure_metadata_inclusion(self, repo_url, skill_path, model):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: Where skill metadata files exist (package.json, requirements.txt),
        the system should include them in the download.
        """
        # Filter out invalid skill paths
        assume(skill_path.strip() != "")
        assume(not skill_path.startswith('/'))
        assume('..' not in skill_path)
        # More lenient character filtering
        assume(all(c.isalnum() or c in '-_/.@' for c in skill_path))
        # Ensure reasonable length
        assume(len(skill_path) <= 30)

        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            # Simulate skill with metadata files
            metadata_files = [
                f"{skill_path}/package.json",
                f"{skill_path}/requirements.txt",
                f"{skill_path}/pyproject.toml",
                f"{skill_path}/main.py",
                f"{skill_path}/README.md"
            ]

            mock_clone.return_value = metadata_files

            # Test download
            result = self.skill_manager.download_skill_selective(
                repo_url, skill_path, model
            )

            # Verify successful download
            assert result.success is True
            assert len(result.downloaded_files) > 0

            # Verify metadata files are included
            downloaded_files = result.downloaded_files
            metadata_extensions = ['.json', '.txt', '.toml']

            has_metadata = any(
                any(file_path.endswith(ext) for ext in metadata_extensions)
                for file_path in downloaded_files
            )
            assert has_metadata  # Should include at least one metadata file

    @given(valid_repo_urls(), skill_directory_structures(), model_types())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_repository_structure_error_handling(self, repo_url, skill_path, model):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: When the specified skill path does not exist in the repository,
        the system should return a descriptive error message.
        """
        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            # Simulate skill path not found
            mock_clone.side_effect = ValidationError(f"Skill path '{skill_path}' not found in repository")

            # Test download
            result = self.skill_manager.download_skill_selective(
                repo_url, skill_path, model
            )

            # Verify error handling
            assert result.success is False
            assert result.error is not None
            assert skill_path in result.error or "not found" in result.error.lower()
            assert result.downloaded_files == []

    def test_property_4_repository_structure_forward_slash_separators(self):
        """
        **Feature: selective-skill-download, Property 4: Repository Structure Handling**
        **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

        Property: The system should support skill paths with forward slashes as directory separators.
        """
        repo_url = "https://github.com/test/repo"
        skill_paths = [
            "skills/python/auth",
            "tools/data/processors",
            "examples/web/api",
            "src/utils/helpers"
        ]
        model = "github-copilot"

        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            mock_clone.return_value = ["main.py", "config.json"]

            for skill_path in skill_paths:
                result = self.skill_manager.download_skill_selective(
                    repo_url, skill_path, model
                )

                # Verify successful handling of forward slash separators
                assert result.success is True
                assert result.skill_name == Path(skill_path).name

                # Verify the path was passed correctly to git handler
                mock_clone.assert_called()
                call_args = mock_clone.call_args
                assert call_args[0][1] == skill_path  # skill_path parameter


class SkillManagerRepositoryStateMachine(RuleBasedStateMachine):
    """Stateful property testing for SkillManager repository operations."""

    def __init__(self):
        super().__init__()
        self.skill_manager = None
        self.temp_project_root = None
        self.downloaded_skills = {}  # Track downloaded skills by model

    @initialize()
    def setup_manager(self):
        """Initialize SkillManager for stateful testing."""
        with patch.object(GitUtils, 'is_git_available', return_value=True):
            with patch.object(GitUtils, 'is_git_version_supported', return_value=True):
                self.temp_project_root = tempfile.mkdtemp()
                self.skill_manager = SkillManager(project_root=self.temp_project_root)

                # Initialize tracking for each model
                for model in self.skill_manager.get_supported_models():
                    self.downloaded_skills[model] = set()

    @rule(repo_url=valid_repo_urls(), skill_path=skill_directory_structures(), model=model_types())
    def download_skill(self, repo_url, skill_path, model):
        """Test skill download operations."""
        with patch.object(self.skill_manager.git_handler, 'clone_with_sparse_checkout') as mock_clone:
            mock_clone.return_value = [f"{skill_path}/main.py"]

            result = self.skill_manager.download_skill_selective(repo_url, skill_path, model)

            if result.success:
                self.downloaded_skills[model].add(result.skill_name)

            # Verify result structure
            assert isinstance(result.success, bool)
            assert isinstance(result.skill_name, str)
            assert result.model == model
            assert isinstance(result.downloaded_files, list)

    @rule(model=model_types())
    def list_skills(self, model):
        """Test skill listing operations."""
        # Mock the file system to return our tracked skills
        with patch.object(Path, 'iterdir') as mock_iterdir:
            mock_files = []
            for skill_name in self.downloaded_skills[model]:
                mock_file = Mock()
                mock_file.is_file.return_value = True
                mock_file.name = skill_name
                mock_files.append(mock_file)

            mock_iterdir.return_value = mock_files

            with patch.object(Path, 'exists', return_value=True):
                skills = self.skill_manager.list_skills(model)

                # Verify skills list structure
                assert isinstance(skills, list)
                for skill in skills:
                    assert isinstance(skill, str)

    @invariant()
    def manager_state_consistent(self):
        """Ensure manager state remains consistent."""
        if self.skill_manager:
            assert hasattr(self.skill_manager, 'project_root')
            assert hasattr(self.skill_manager, 'git_handler')
            assert hasattr(self.skill_manager, 'dependency_manager')

            # Verify supported models are consistent
            models = self.skill_manager.get_supported_models()
            assert isinstance(models, list)
            assert len(models) > 0

    def teardown(self):
        """Clean up temporary directories."""
        if self.temp_project_root and os.path.exists(self.temp_project_root):
            shutil.rmtree(self.temp_project_root, ignore_errors=True)


# Stateful test runner
TestSkillManagerRepositoryStateful = SkillManagerRepositoryStateMachine.TestCase


if __name__ == "__main__":
    # Run a quick test to verify the property tests work
    pytest.main([__file__, "-v"])
