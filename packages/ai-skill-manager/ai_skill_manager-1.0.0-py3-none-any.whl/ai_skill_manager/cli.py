"""Command-line interface for AI Skill Manager."""

import json
from typing import List, Optional, cast

import click

from .manager import SkillManager
from .skill_types import ModelType, SelectiveDownloadOptions, SkillDownloadRequest


@click.group()
@click.version_option()
def cli() -> None:
    """AI Skill Manager - Manage skills for different AI coding assistants."""
    pass


@cli.command()
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.argument('url')
@click.option('--name', help='Custom name for the skill')
def download(model: Optional[str], url: str, name: Optional[str]) -> None:
    """Download a skill from a URL."""
    manager = SkillManager()

    if not model:
        model = manager.detect_model()
        if model:
            click.echo(f"Auto-detected model: {model}")
        else:
            click.echo("Could not auto-detect model. Please specify with --model")
            return

    try:
        manager.download_skill_from_url(url, model, name)
        click.echo(f"✓ Downloaded skill to {model}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)


@cli.command()
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.argument('repo')
@click.argument('path')
@click.option('--name', help='Custom name for the skill')
def github(model: Optional[str], repo: str, path: str, name: Optional[str]) -> None:
    """Download skill from GitHub repository."""
    manager = SkillManager()

    if not model:
        model = manager.detect_model()
        if model:
            click.echo(f"Auto-detected model: {model}")
        else:
            click.echo("Could not auto-detect model. Please specify with --model")
            return

    try:
        manager.download_github_skill(repo, path, model, name)
        click.echo(f"✓ Downloaded skill from GitHub to {model}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)


@cli.command()
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.option('--all', is_flag=True, help='List skills for all models')
def list(model: Optional[str], all: bool) -> None:
    """List skills."""
    manager = SkillManager()

    if all:
        for model_name in SkillManager.MODEL_DIRECTORIES.keys():
            skills = manager.list_skills(model_name)
            if skills:
                click.echo(f"\n{model_name}:")
                for skill in skills:
                    click.echo(f"  - {skill}")
    else:
        if not model:
            model = manager.detect_model()
            if model:
                click.echo(f"Auto-detected model: {model}")
            else:
                click.echo("Could not auto-detect model. Please specify with --model")
                return

        skills = manager.list_skills(model)
        if skills:
            click.echo(f"Skills for {model}:")
            for skill in skills:
                click.echo(f"  - {skill}")
        else:
            click.echo(f"No skills found for {model}")


@cli.command()
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.argument('skill_name')
def remove(model: Optional[str], skill_name: str) -> None:
    """Remove a skill."""
    manager = SkillManager()

    if not model:
        model = manager.detect_model()
        if model:
            click.echo(f"Auto-detected model: {model}")
        else:
            click.echo("Could not auto-detect model. Please specify with --model")
            return

    if manager.remove_skill(model, skill_name):
        click.echo(f"✓ Removed skill '{skill_name}' from {model}")
    else:
        click.echo(f"✗ Skill '{skill_name}' not found in {model}")


@cli.command()
@click.argument('skill_name')
@click.option('--from', 'source_model', required=True,
              type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Source model')
@click.option('--to', 'target_model', required=True,
              type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target model')
def copy(skill_name: str, source_model: str, target_model: str) -> None:
    """Copy skill between models."""
    manager = SkillManager()

    if manager.copy_skill(source_model, target_model, skill_name):
        click.echo(f"✓ Copied skill '{skill_name}' from {source_model} to {target_model}")
    else:
        click.echo(f"✗ Skill '{skill_name}' not found in {source_model}")


@cli.command()
def detect() -> None:
    """Detect which AI model is being used."""
    manager = SkillManager()
    detected = manager.detect_model()
    if detected:
        click.echo(f"Detected AI model: {detected}")
    else:
        click.echo("No AI model detected in current project")


@cli.command()
def models() -> None:
    """List all supported AI models."""
    manager = SkillManager()
    click.echo("Supported AI models:")
    for model in manager.get_supported_models():
        click.echo(f"  - {model}")


@cli.command('download-selective')
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.argument('repo_url')
@click.argument('skill_path')
@click.option('--name', help='Custom name for the skill')
@click.option('--no-deps', is_flag=True, help='Skip dependency installation')
@click.option('--shallow/--no-shallow', default=True, help='Use shallow clone (default: True)')
@click.option('--timeout', type=int, default=300, help='Timeout in seconds (default: 300)')
@click.option('--retries', type=int, default=3, help='Number of retry attempts (default: 3)')
def download_selective(
    model: Optional[str],
    repo_url: str,
    skill_path: str,
    name: Optional[str],
    no_deps: bool,
    shallow: bool,
    timeout: int,
    retries: int
) -> None:
    """Download a specific skill from a git repository using sparse-checkout."""
    manager = SkillManager()

    if not model:
        model = manager.detect_model()
        if model:
            click.echo(f"Auto-detected model: {model}")
        else:
            click.echo("Could not auto-detect model. Please specify with --model")
            return

    try:
        options = SelectiveDownloadOptions(
            skill_name=name,
            use_shallow_clone=shallow,
            install_dependencies=not no_deps,
            timeout=timeout,
            retry_attempts=retries
        )

        click.echo(f"Downloading skill '{skill_path}' from {repo_url}...")
        result = manager.download_skill_selective(repo_url, skill_path, cast(ModelType, model), options)

        if result.success:
            click.echo(f"✓ Downloaded skill to {model}")
            if result.installed_dependencies:
                click.echo(f"  Installed {len(result.installed_dependencies)} dependencies")
        else:
            click.echo(f"✗ {result.error or 'Unknown error'}", err=True)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)


@cli.command('download-batch')
@click.option('--model', '-m', type=click.Choice(SkillManager.MODEL_DIRECTORIES.keys()),
              help='Target AI model (auto-detected if not specified)')
@click.argument('config_file', type=click.Path(exists=True))
def download_batch(model: Optional[str], config_file: str) -> None:
    """Download multiple skills from a configuration file."""
    try:
        # Parse and validate config file first
        with open(config_file) as f:
            config = json.load(f)

        if 'skills' not in config:
            click.echo("✗ Configuration file must contain 'skills' array", err=True)
            return

        # Now handle model detection
        manager = SkillManager()

        if not model:
            model = manager.detect_model()
            if model:
                click.echo(f"Auto-detected model: {model}")
            else:
                click.echo("Could not auto-detect model. Please specify with --model")
                return

        requests: List[SkillDownloadRequest] = []
        for skill_config in config['skills']:
            if 'repoUrl' not in skill_config or 'skillPath' not in skill_config:
                click.echo("✗ Each skill must have 'repoUrl' and 'skillPath'", err=True)
                return

            options_dict = skill_config.get('options', {})
            # Map camelCase JSON keys to snake_case Python attributes
            if options_dict:
                mapped_options = {
                    'skill_name': options_dict.get('skillName'),
                    'use_shallow_clone': options_dict.get('useShallowClone', True),
                    'install_dependencies': options_dict.get('installDependencies', True),
                    'timeout': options_dict.get('timeout', 300),
                    'retry_attempts': options_dict.get('retryAttempts', 3)
                }
                # Remove None values
                mapped_options = {k: v for k, v in mapped_options.items() if v is not None}
                options = SelectiveDownloadOptions(**mapped_options)
            else:
                options = None

            request = SkillDownloadRequest(
                repo_url=skill_config['repoUrl'],
                skill_path=skill_config['skillPath'],
                model=cast(ModelType, model),
                options=options
            )
            requests.append(request)

        click.echo(f"Downloading {len(requests)} skills...")
        results = manager.download_multiple_skills(requests)

        success_count = sum(1 for r in results if r.success)
        click.echo(f"✓ Successfully downloaded {success_count}/{len(results)} skills")

        for result in results:
            if not result.success:
                click.echo(f"  ✗ {result.skill_name}: {result.error or 'Unknown error'}")

    except json.JSONDecodeError:
        click.echo("✗ Invalid JSON in configuration file", err=True)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)


@cli.command('explore')
@click.argument('repo_url')
@click.option('--branch', default='main', help='Branch to explore (default: main)')
def explore(repo_url: str, branch: str) -> None:
    """Explore a repository to list available skills."""
    manager = SkillManager()

    try:
        click.echo(f"Exploring repository: {repo_url}")
        skills = manager.list_repository_skills(repo_url)

        if skills:
            click.echo(f"Available skills in {repo_url}:")
            for skill in skills:
                click.echo(f"  - {skill}")
        else:
            click.echo("No skills found in repository")

    except Exception as e:
        click.echo(f"✗ {e}", err=True)


def main() -> None:
    """Entry point for the CLI."""
    cli()
