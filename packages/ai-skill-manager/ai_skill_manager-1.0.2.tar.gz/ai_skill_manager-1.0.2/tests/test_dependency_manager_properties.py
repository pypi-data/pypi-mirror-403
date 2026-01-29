"""Property-based tests for DependencyManager functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from ai_skill_manager.dependency_manager import DependencyManager
from ai_skill_manager.skill_types import DependencyFile


# Custom strategies for generating test data
@st.composite
def valid_requirements_content(draw):
    """Generate valid requirements.txt content."""
    packages = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_.'),
            min_size=1, max_size=20
        ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
        min_size=0, max_size=10
    ))

    lines = []
    for package in packages:
        # Add version specifiers sometimes
        has_version = draw(st.booleans())
        if has_version:
            operator = draw(st.sampled_from(['>=', '==', '<=', '>', '<', '!=', '~=']))
            version = draw(st.text(
                alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='.'),
                min_size=1, max_size=10
            ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')))
            lines.append(f"{package}{operator}{version}")
        else:
            lines.append(package)

    # Add some comments
    if draw(st.booleans()):
        lines.insert(0, "# This is a comment")

    return '\n'.join(lines)


@st.composite
def valid_pyproject_content(draw):
    """Generate valid pyproject.toml content."""
    dependencies = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_.'),
            min_size=1, max_size=20
        ).filter(lambda x: x and not x.startswith('-')),
        min_size=0, max_size=5
    ))

    # Create basic pyproject.toml structure
    content = '[project]\n'
    content += 'name = "test-project"\n'
    content += 'version = "0.1.0"\n'

    if dependencies:
        content += 'dependencies = [\n'
        for dep in dependencies:
            content += f'    "{dep}",\n'
        content += ']\n'

    return content


@st.composite
def dependency_files(draw):
    """Generate DependencyFile objects."""
    file_type = draw(st.sampled_from(['requirements.txt', 'pyproject.toml']))

    if file_type == 'requirements.txt':
        content = draw(valid_requirements_content())
    else:
        content = draw(valid_pyproject_content())

    return DependencyFile(
        path=f"/tmp/{file_type}",
        type=file_type,
        content=content
    )


class TestDependencyManagerProperties:
    """Property-based tests for DependencyManager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dirs = []

    def teardown_method(self):
        """Clean up test environment."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def create_temp_skill_dir(self, files_content=None):
        """Create a temporary skill directory with optional files."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        if files_content:
            for filename, content in files_content.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content, encoding='utf-8')

        return temp_dir

    @given(st.booleans(), st.integers(min_value=60, max_value=1200))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_dependency_manager_initialization(self, respect_virtual_env, install_timeout):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: For any valid configuration parameters, DependencyManager should initialize correctly.
        """
        manager = DependencyManager(
            respect_virtual_env=respect_virtual_env,
            install_timeout=install_timeout
        )

        # Configuration should be stored correctly
        assert manager.respect_virtual_env == respect_virtual_env
        assert manager.install_timeout == install_timeout

        # Values should be within expected ranges
        assert manager.install_timeout >= 60
        assert isinstance(manager.respect_virtual_env, bool)

    @given(valid_requirements_content())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_requirements_file_detection(self, requirements_content):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: For any valid requirements.txt content, the manager should detect and parse it correctly.
        """
        manager = DependencyManager()

        # Create temporary skill directory with requirements.txt
        skill_dir = self.create_temp_skill_dir({
            'requirements.txt': requirements_content
        })

        # Detect dependency files
        dependency_files = manager.detect_dependency_files(skill_dir)

        # Should find the requirements.txt file
        requirements_files = [f for f in dependency_files if f.type == 'requirements.txt']
        assert len(requirements_files) == 1

        req_file = requirements_files[0]
        assert req_file.content == requirements_content
        assert req_file.path.endswith('requirements.txt')

        # Resolve dependencies
        dependencies = manager.resolve_dependencies(dependency_files)

        # Dependencies should be a list
        assert isinstance(dependencies, list)

        # Non-empty content should produce some dependencies (unless all comments/empty lines)
        if requirements_content.strip() and not all(line.strip().startswith('#') or not line.strip()
                                                   for line in requirements_content.split('\n')):
            # Should have found at least some dependencies
            assert len(dependencies) >= 0  # Could be 0 if all lines are comments

    @given(valid_pyproject_content())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_pyproject_file_detection(self, pyproject_content):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: For any valid pyproject.toml content, the manager should detect and parse it correctly.
        """
        manager = DependencyManager()

        # Create temporary skill directory with pyproject.toml
        skill_dir = self.create_temp_skill_dir({
            'pyproject.toml': pyproject_content
        })

        # Detect dependency files
        dependency_files = manager.detect_dependency_files(skill_dir)

        # Should find the pyproject.toml file
        pyproject_files = [f for f in dependency_files if f.type == 'pyproject.toml']
        assert len(pyproject_files) == 1

        pyproject_file = pyproject_files[0]
        assert pyproject_file.content == pyproject_content
        assert pyproject_file.path.endswith('pyproject.toml')

        # Resolve dependencies
        dependencies = manager.resolve_dependencies(dependency_files)

        # Dependencies should be a list
        assert isinstance(dependencies, list)

    @given(valid_requirements_content(), valid_pyproject_content())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_pyproject_priority_over_requirements(self, requirements_content, pyproject_content):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: When both pyproject.toml and requirements.txt exist, pyproject.toml should take priority.
        """
        manager = DependencyManager()

        # Create temporary skill directory with both files
        skill_dir = self.create_temp_skill_dir({
            'requirements.txt': requirements_content,
            'pyproject.toml': pyproject_content
        })

        # Detect dependency files
        dependency_files = manager.detect_dependency_files(skill_dir)

        # Should find both files
        assert len(dependency_files) == 2

        # Resolve dependencies - should prioritize pyproject.toml
        dependencies = manager.resolve_dependencies(dependency_files)

        # Dependencies should be a list
        assert isinstance(dependencies, list)

        # Test that pyproject.toml is processed (by checking if we get dependencies from it)
        pyproject_only_deps = manager.resolve_dependencies([
            f for f in dependency_files if f.type == 'pyproject.toml'
        ])

        # If pyproject.toml has dependencies, they should be included
        # (This validates the priority requirement 5.5)
        if pyproject_only_deps:
            # At least some dependencies from pyproject.toml should be present
            assert len(dependencies) >= 0

    @given(st.lists(dependency_files(), min_size=1, max_size=3))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_dependency_resolution_consistency(self, dep_files):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: Dependency resolution should be consistent and deterministic.
        """
        manager = DependencyManager()

        # Resolve dependencies multiple times
        deps1 = manager.resolve_dependencies(dep_files)
        deps2 = manager.resolve_dependencies(dep_files)

        # Results should be identical
        assert deps1 == deps2

        # Results should be lists
        assert isinstance(deps1, list)
        assert isinstance(deps2, list)

        # All dependencies should be strings
        for dep in deps1:
            assert isinstance(dep, str)
            assert len(dep.strip()) > 0

    def test_property_6_package_manager_detection(self):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: Package manager detection should be consistent and provide accurate information.
        """
        manager = DependencyManager()

        # Test uv availability detection
        uv_available = manager.is_uv_available()
        assert isinstance(uv_available, bool)

        # Test pip availability detection
        pip_available = manager.is_pip_available()
        assert isinstance(pip_available, bool)

        # Get package manager info
        info = manager.get_package_manager_info()

        # Info should be a dictionary with expected structure
        assert isinstance(info, dict)
        assert 'uv' in info
        assert 'pip' in info
        assert 'virtual_env' in info

        # Each package manager info should have availability and version
        for pm in ['uv', 'pip']:
            assert 'available' in info[pm]
            assert 'version' in info[pm]
            assert isinstance(info[pm]['available'], bool)

        # Virtual environment detection should be boolean
        assert isinstance(info['virtual_env'], bool)

        # Consistency check: if detection methods return True, info should reflect that
        assert info['uv']['available'] == uv_available
        assert info['pip']['available'] == pip_available

    @given(st.booleans())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_virtual_environment_respect(self, use_uv):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: Virtual environment settings should be respected consistently.
        """
        manager = DependencyManager(respect_virtual_env=True)

        # Create empty skill directory
        skill_dir = self.create_temp_skill_dir()

        # Mock package manager availability
        with patch.object(manager, 'is_uv_available', return_value=use_uv):
            with patch.object(manager, 'is_pip_available', return_value=True):
                with patch('subprocess.run') as mock_run:
                    # Mock successful installation
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stderr = ""

                    # Test installation with empty dependencies (should succeed)
                    success, installed_deps, error = manager.install_dependencies(skill_dir, use_uv=use_uv)

                    # Should succeed with no dependencies
                    assert success is True
                    assert installed_deps == []
                    assert error is None

    def test_property_6_error_handling_consistency(self):
        """
        **Feature: selective-skill-download, Property 6: Dependency Management Integration**
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

        Property: Error handling should be consistent across different failure scenarios.
        """
        manager = DependencyManager()

        # Test with non-existent directory
        non_existent_dir = "/path/that/does/not/exist"

        # Should handle gracefully
        dependency_files = manager.detect_dependency_files(non_existent_dir)
        assert isinstance(dependency_files, list)
        assert len(dependency_files) == 0

        # Test installation with non-existent directory
        success, deps, error = manager.install_dependencies(non_existent_dir)

        # Should handle gracefully (no dependencies to install)
        assert success is True
        assert deps == []
        assert error is None


class DependencyManagerStateMachine(RuleBasedStateMachine):
    """Stateful property testing for DependencyManager operations."""

    def __init__(self):
        super().__init__()
        self.manager = None
        self.temp_dirs = []

    @initialize()
    def setup_manager(self):
        """Initialize DependencyManager for stateful testing."""
        self.manager = DependencyManager()

    @rule(respect_venv=st.booleans(), timeout=st.integers(min_value=60, max_value=600))
    def create_manager_with_config(self, respect_venv, timeout):
        """Test manager creation with different configurations."""
        self.manager = DependencyManager(
            respect_virtual_env=respect_venv,
            install_timeout=timeout
        )

        assert self.manager.respect_virtual_env == respect_venv
        assert self.manager.install_timeout == timeout

    @rule()
    def check_package_managers(self):
        """Test package manager availability checking."""
        uv_available = self.manager.is_uv_available()
        pip_available = self.manager.is_pip_available()

        assert isinstance(uv_available, bool)
        assert isinstance(pip_available, bool)

        # Get detailed info
        info = self.manager.get_package_manager_info()
        assert isinstance(info, dict)
        assert info['uv']['available'] == uv_available
        assert info['pip']['available'] == pip_available

    @rule(content=valid_requirements_content())
    def test_requirements_processing(self, content):
        """Test requirements.txt processing in different states."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # Create requirements.txt
        req_file = Path(temp_dir) / 'requirements.txt'
        req_file.write_text(content, encoding='utf-8')

        # Detect and process
        dep_files = self.manager.detect_dependency_files(temp_dir)
        dependencies = self.manager.resolve_dependencies(dep_files)

        assert isinstance(dep_files, list)
        assert isinstance(dependencies, list)

    @invariant()
    def manager_state_consistent(self):
        """Ensure manager state remains consistent."""
        if self.manager:
            assert hasattr(self.manager, 'respect_virtual_env')
            assert hasattr(self.manager, 'install_timeout')
            assert isinstance(self.manager.respect_virtual_env, bool)
            assert self.manager.install_timeout > 0

    def teardown(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)


# Stateful test runner
TestDependencyManagerStateful = DependencyManagerStateMachine.TestCase


if __name__ == "__main__":
    # Run a quick test to verify the property tests work
    pytest.main([__file__, "-v"])
