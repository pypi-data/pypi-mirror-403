"""
GeoCICD CLI - Main entry point

This module provides the command-line interface for the GitLab CI/CD Migration system.
It includes version enforcement to ensure all team members use the latest version.

Requirements: 21.1-21.12, 23.1-23.13
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from utils.version_checker import VersionChecker
from utils.logging_config import get_logger

# Get version from pyproject.toml
__version__ = "1.0.2"

logger = get_logger(__name__)
console = Console()


def check_version_and_enforce(skip_check: bool = False) -> None:
    """
    Check CLI version and enforce update if needed
    
    This function runs at startup before any other operations.
    If a newer version is available, it blocks execution and displays
    an upgrade message.
    
    Args:
        skip_check: If True, skip version check (emergency use only)
    
    Requirements: 23.1-23.5, 23.7-23.8, 23.10
    """
    if skip_check:
        console.print("[yellow]⚠️  Version check skipped (--skip-version-check flag)[/yellow]")
        return
    
    try:
        # Create version checker
        checker = VersionChecker(current_version=__version__)
        
        # Check version
        result = checker.check_version(skip_check=skip_check)
        
        # If update required, block execution
        if result.update_required:
            console.print()
            console.print(Panel(
                Text.from_markup(
                    f"[bold red]⚠️  CLI Update Required[/bold red]\n\n"
                    f"[yellow]Current version:[/yellow] {result.current_version}\n"
                    f"[green]Latest version:[/green]  {result.latest_version}\n\n"
                    f"[bold]Please update to the latest version:[/bold]\n"
                    f"[cyan]pip install --upgrade geocicd[/cyan]\n\n"
                    f"[dim]Registry: {result.registry_url}[/dim]"
                ),
                title="Update Required",
                border_style="red",
                padding=(1, 2)
            ))
            console.print()
            
            logger.error(f"CLI version {result.current_version} is outdated. Latest: {result.latest_version}")
            sys.exit(1)
        
        # Log successful check
        logger.debug(f"Version check passed: {result.current_version} is up to date")
        
    except Exception as e:
        # This should only happen for authentication errors (strict handling)
        # Network errors are handled gracefully in VersionChecker
        logger.error(f"Version check failed: {e}")
        console.print(f"[red]Error checking version: {e}[/red]")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option('--skip-version-check', is_flag=True, hidden=True,
              help='Skip version check (emergency use only)')
@click.option('--version', is_flag=True, help='Show version and exit')
@click.pass_context
def cli(ctx: click.Context, skip_version_check: bool, version: bool) -> None:
    """
    GeoCICD - GitLab CI/CD Pipeline Generator
    
    Automated generation of GitLab CI/CD pipelines from declarative configuration.
    Supports multi-environment deployments, change detection, quality gates, and
    Kubernetes deployment via ArgoCD.
    """
    # Show version and exit
    if version:
        console.print(f"GeoCICD version {__version__}")
        sys.exit(0)
    
    # Check version before any operations (unless skipped)
    if not skip_version_check:
        check_version_and_enforce(skip_check=False)
    else:
        check_version_and_enforce(skip_check=True)
    
    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@cli.command()
@click.argument('config_file', type=click.Path(exists=True), default='ci-config.yaml')
def validate(config_file: str) -> None:
    """
    Validate configuration file
    
    Checks the configuration file for syntax errors, schema violations,
    and undefined variables.
    
    Args:
        config_file: Path to ci-config.yaml (default: ci-config.yaml)
    """
    from parser.config_parser import ConfigParser
    from rich.table import Table
    
    console.print(f"\n[bold]Validating configuration:[/bold] {config_file}\n")
    
    try:
        parser = ConfigParser()
        config = parser.parse(config_file)
        
        # Show success message
        console.print("[green]✓[/green] Configuration is valid!\n")
        
        # Show summary
        table = Table(title="Configuration Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Project", config.get('project', {}).get('name', 'N/A'))
        table.add_row("Organization", config.get('project', {}).get('organization', 'N/A'))
        table.add_row("Components", str(len(config.get('components', []))))
        table.add_row("Environments", str(len(config.get('environments', {}))))
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗[/red] Validation failed:\n")
        console.print(f"[red]{e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True), default='ci-config.yaml')
@click.option('--output', '-o', default='.gitlab-ci.yml',
              help='Output file path (default: .gitlab-ci.yml)')
def generate(config_file: str, output: str) -> None:
    """
    Generate .gitlab-ci.yml from configuration
    
    Parses the configuration file and generates a complete GitLab CI/CD
    pipeline definition.
    
    Args:
        config_file: Path to ci-config.yaml (default: ci-config.yaml)
        output: Output file path (default: .gitlab-ci.yml)
    """
    from parser.config_parser import ConfigParser
    from generator.gitlab_ci_generator import GitLabCIGenerator
    
    console.print(f"\n[bold]Generating pipeline from:[/bold] {config_file}\n")
    
    try:
        # Parse configuration
        parser = ConfigParser()
        config = parser.parse(config_file)
        
        console.print("[green]✓[/green] Configuration parsed successfully")
        
        # Generate pipeline
        generator = GitLabCIGenerator()
        pipeline_yaml = generator.generate(config)
        
        console.print("[green]✓[/green] Pipeline generated successfully")
        
        # Write output file
        with open(output, 'w') as f:
            f.write(pipeline_yaml)
        
        console.print(f"[green]✓[/green] Pipeline written to: [cyan]{output}[/cyan]\n")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Generation failed:\n")
        console.print(f"[red]{e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True), default='ci-config.yaml')
@click.argument('environment', type=str)
@click.argument('component', type=str, required=False)
def deploy(config_file: str, environment: str, component: Optional[str]) -> None:
    """
    Deploy to Kubernetes environment
    
    Deploys one or all components to the specified environment using
    Helm and ArgoCD.
    
    Args:
        config_file: Path to ci-config.yaml (default: ci-config.yaml)
        environment: Target environment (dev, stg, ese)
        component: Optional component name (deploys all if not specified)
    """
    from parser.config_parser import ConfigParser
    from deployer.kubernetes_deployer import KubernetesDeployer
    
    console.print(f"\n[bold]Deploying to environment:[/bold] {environment}\n")
    
    if component:
        console.print(f"[bold]Component:[/bold] {component}\n")
    else:
        console.print("[bold]Component:[/bold] All components\n")
    
    try:
        # Parse configuration
        parser = ConfigParser()
        config = parser.parse(config_file)
        
        console.print("[green]✓[/green] Configuration parsed successfully")
        
        # Get components to deploy
        components = config.get('components', [])
        if component:
            components = [c for c in components if c['name'] == component]
            if not components:
                console.print(f"[red]✗[/red] Component '{component}' not found in configuration\n")
                sys.exit(1)
        
        # Deploy each component
        deployer = KubernetesDeployer()
        for comp in components:
            console.print(f"\n[bold]Deploying {comp['name']}...[/bold]")
            deployer.deploy(comp, environment, config)
            console.print(f"[green]✓[/green] {comp['name']} deployed successfully")
        
        console.print(f"\n[green]✓[/green] Deployment completed successfully\n")
        
    except Exception as e:
        console.print(f"\n[red]✗[/red] Deployment failed:\n")
        console.print(f"[red]{e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True), default='ci-config.yaml')
@click.argument('environment', type=str)
def detect_changes(config_file: str, environment: str) -> None:
    """
    Detect changed components
    
    Analyzes Git history to determine which components have been modified
    since the comparison branch for the specified environment.
    
    Args:
        config_file: Path to ci-config.yaml (default: ci-config.yaml)
        environment: Target environment (dev, stg, ese)
    """
    from parser.config_parser import ConfigParser
    from utils.change_detector import ChangeDetector
    from rich.table import Table
    
    console.print(f"\n[bold]Detecting changes for environment:[/bold] {environment}\n")
    
    try:
        # Parse configuration
        parser = ConfigParser()
        config = parser.parse(config_file)
        
        console.print("[green]✓[/green] Configuration parsed successfully")
        
        # Detect changes
        detector = ChangeDetector()
        changed_components = detector.get_changed_components(environment, config)
        
        # Show results
        table = Table(title="Change Detection Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        
        all_components = [c['name'] for c in config.get('components', [])]
        for comp_name in all_components:
            if comp_name in changed_components:
                table.add_row(comp_name, "[yellow]Changed (will build)[/yellow]")
            else:
                table.add_row(comp_name, "[green]Unchanged (will reuse)[/green]")
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗[/red] Change detection failed:\n")
        console.print(f"[red]{e}[/red]\n")
        sys.exit(1)


@cli.command()
def interactive() -> None:
    """
    Launch interactive CLI
    
    Provides a user-friendly menu-driven interface for creating configurations,
    validating, generating pipelines, and deploying to environments.
    
    Requirements: 21.1-21.12
    """
    from cli.interactive_cli import InteractiveCLI
    
    try:
        interactive_cli = InteractiveCLI(current_version=__version__)
        interactive_cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive mode cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception("Error in interactive CLI")
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def version_info() -> None:
    """
    Show detailed version information
    
    Displays current version, latest available version, and registry information.
    """
    from rich.table import Table
    
    console.print(f"\n[bold]GeoCICD Version Information[/bold]\n")
    
    try:
        # Create version checker
        checker = VersionChecker(current_version=__version__)
        
        # Check version (don't enforce)
        result = checker.check_version(skip_check=False)
        
        # Show information
        table = Table()
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Current Version", result.current_version)
        table.add_row("Latest Version", result.latest_version)
        table.add_row("Update Required", "Yes" if result.update_required else "No")
        table.add_row("Registry", result.registry_url)
        table.add_row("Checked At", result.checked_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(table)
        console.print()
        
        if result.update_required:
            console.print("[yellow]⚠️  Update available! Run:[/yellow] [cyan]pip install --upgrade geocicd[/cyan]\n")
        else:
            console.print("[green]✓ You are using the latest version[/green]\n")
        
    except Exception as e:
        console.print(f"[red]Error checking version: {e}[/red]\n")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the CLI
    
    This function is called when the geocicd command is executed.
    It sets up the CLI and handles version enforcement.
    """
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error in CLI")
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
