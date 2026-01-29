"""Property-based tests for CLI argument processing functionality."""

import json
import os
import tempfile
from unittest.mock import Mock, patch

from click.testing import CliRunner
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from ai_skill_manager.cli import cli
from ai_skill_manager.skill_types import SelectiveDownloadOptions


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
        ).filter(lambda x: x and x != '.' and x != '..' and not x.startswith('-')),
        min_size=1, max_size=3
    ))

    return '/'.join(components)


@st.composite
def valid_cli_options(draw):
    """Generate valid CLI options."""
    return {
        'name': draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        'no_deps': draw(st.booleans()),
        'shallow': draw(st.booleans()),
        'timeout': draw(st.integers(min_value=30, max_value=3600)),
        'retries': draw(st.integers(min_value=1, max_value=10))
    }


@st.composite
def valid_batch_config(draw):
    """Generate valid batch configuration."""
    skills = draw(st.lists(
        st.fixed_dictionaries({
            'repoUrl': valid_repo_urls(),
            'skillPath': valid_skill_paths(),
            'options': st.one_of(st.none(), st.fixed_dictionaries({
                'skillName': st.one_of(st.none(), st.text(min_size=1, max_size=50)),
                'useShallowClone': st.booleans(),
                'installDependencies': st.booleans(),
                'timeout': st.integers(min_value=30, max_value=3600),
                'retryAttempts': st.integers(min_value=1, max_value=10)
            }))
        }),
        min_size=1, max_size=5
    ))

    return {'skills': skills}


class TestCLIArgumentProcessing:
    """Property-based tests for CLI argument processing."""

    @given(
        repo_url=valid_repo_urls(),
        skill_path=valid_skill_paths(),
        options=valid_cli_options()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_download_selective_argument_processing(self, repo_url, skill_path, options):
        """
        **Feature: selective-skill-download, Property 2: CLI Argument Processing**
        **Validates: Requirements 2.1, 2.5**

        For any valid combination of repository URL, skill path, and command options,
        the CLI should successfully parse the arguments and initiate the appropriate download operation.
        """
        runner = CliRunner()

        # Mock the SkillManager to avoid actual git operations
        with patch('ai_skill_manager.cli.SkillManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.detect_model.return_value = 'github-copilot'
            mock_manager.download_skill_selective.return_value = {
                'success': True,
                'skillName': options.get('name', 'test-skill'),
                'model': 'github-copilot',
                'downloadedFiles': ['test.py'],
                'installedDependencies': [] if options['no_deps'] else ['requests']
            }

            # Build command arguments
            cmd_args = ['download-selective', repo_url, skill_path]

            if options['name']:
                cmd_args.extend(['--name', options['name']])
            if options['no_deps']:
                cmd_args.append('--no-deps')
            if not options['shallow']:
                cmd_args.append('--no-shallow')
            cmd_args.extend(['--timeout', str(options['timeout'])])
            cmd_args.extend(['--retries', str(options['retries'])])

            # Execute command
            result = runner.invoke(cli, cmd_args)

            # Verify command executed successfully
            assert result.exit_code == 0, f"Command failed with output: {result.output}"

            # Verify SkillManager was called with correct arguments
            mock_manager.download_skill_selective.assert_called_once()
            call_args = mock_manager.download_skill_selective.call_args

            assert call_args[0][0] == repo_url
            assert call_args[0][1] == skill_path
            assert call_args[0][2] == 'github-copilot'

            # Verify options were passed correctly
            passed_options = call_args[0][3]
            assert passed_options.use_shallow_clone == options['shallow']
            assert passed_options.install_dependencies == (not options['no_deps'])
            assert passed_options.timeout == options['timeout']
            assert passed_options.retry_attempts == options['retries']

            if options['name']:
                assert passed_options.skill_name == options['name']

    @given(config=valid_batch_config())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_download_batch_argument_processing(self, config):
        """
        **Feature: selective-skill-download, Property 2: CLI Argument Processing**
        **Validates: Requirements 2.1, 2.5**

        For any valid batch configuration file, the CLI should successfully parse
        the configuration and initiate batch download operations.
        """
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name

        try:
            # Mock the SkillManager to avoid actual git operations
            with patch('ai_skill_manager.cli.SkillManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                mock_manager.detect_model.return_value = 'github-copilot'

                # Mock successful results for all skills
                mock_results = []
                for skill in config['skills']:
                    options = skill.get('options') or {}
                    mock_results.append({
                        'success': True,
                        'skillName': options.get('skillName', 'test-skill'),
                        'model': 'github-copilot',
                        'downloadedFiles': ['test.py'],
                        'installedDependencies': []
                    })

                mock_manager.download_multiple_skills.return_value = mock_results

                # Execute command
                result = runner.invoke(cli, ['download-batch', config_file])

                # Verify command executed successfully
                assert result.exit_code == 0, f"Command failed with output: {result.output}"

                # Verify SkillManager was called with correct arguments
                mock_manager.download_multiple_skills.assert_called_once()
                call_args = mock_manager.download_multiple_skills.call_args[0][0]

                # Verify all skills were processed
                assert len(call_args) == len(config['skills'])

                for i, request in enumerate(call_args):
                    expected_skill = config['skills'][i]
                    assert request.repo_url == expected_skill['repoUrl']
                    assert request.skill_path == expected_skill['skillPath']
                    assert request.model == 'github-copilot'

                    # Handle None options correctly
                    expected_options = expected_skill.get('options')
                    if expected_options is not None:
                        assert request.options is not None
                        # Compare the options attributes
                        for key, value in expected_options.items():
                            # Map JSON keys to dataclass attributes
                            attr_map = {
                                'skillName': 'skill_name',
                                'useShallowClone': 'use_shallow_clone',
                                'installDependencies': 'install_dependencies',
                                'timeout': 'timeout',
                                'retryAttempts': 'retry_attempts'
                            }
                            attr_name = attr_map.get(key, key)
                            assert getattr(request.options, attr_name) == value
                    else:
                        assert request.options is None or request.options == SelectiveDownloadOptions()

        finally:
            os.unlink(config_file)

    @given(repo_url=valid_repo_urls())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_explore_argument_processing(self, repo_url):
        """
        **Feature: selective-skill-download, Property 2: CLI Argument Processing**
        **Validates: Requirements 2.1, 2.5**

        For any valid repository URL, the explore command should successfully
        parse the URL and initiate repository exploration.
        """
        runner = CliRunner()

        # Mock the SkillManager to avoid actual git operations
        with patch('ai_skill_manager.cli.SkillManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_repository_skills.return_value = ['skill1', 'skill2', 'skill3']

            # Execute command
            result = runner.invoke(cli, ['explore', repo_url])

            # Verify command executed successfully
            assert result.exit_code == 0, f"Command failed with output: {result.output}"

            # Verify SkillManager was called with correct arguments
            mock_manager.list_repository_skills.assert_called_once_with(repo_url)

            # Verify output contains expected skills
            assert 'skill1' in result.output
            assert 'skill2' in result.output
            assert 'skill3' in result.output

    def test_invalid_json_config_handling(self):
        """Test that invalid JSON configuration files are handled gracefully."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            config_file = f.name

        try:
            # Mock the SkillManager to avoid model detection issues
            with patch('ai_skill_manager.cli.SkillManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                mock_manager.detect_model.return_value = 'github-copilot'

                result = runner.invoke(cli, ['download-batch', config_file])

                # Should fail gracefully with appropriate error message
                assert result.exit_code == 0  # Click doesn't exit with error code for handled exceptions
                assert 'Invalid JSON' in result.output

        finally:
            os.unlink(config_file)

    def test_missing_skills_array_handling(self):
        """Test that configuration files without 'skills' array are handled gracefully."""
        runner = CliRunner()

        config = {'invalid': 'config'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name

        try:
            # Mock the SkillManager to avoid model detection issues
            with patch('ai_skill_manager.cli.SkillManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                mock_manager.detect_model.return_value = 'github-copilot'

                result = runner.invoke(cli, ['download-batch', config_file])

                # Should fail gracefully with appropriate error message
                assert result.exit_code == 0  # Click doesn't exit with error code for handled exceptions
                assert "must contain 'skills' array" in result.output

        finally:
            os.unlink(config_file)
