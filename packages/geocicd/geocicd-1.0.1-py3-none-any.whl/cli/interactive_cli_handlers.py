"""
Action handlers for Interactive CLI.

Handles user actions like create, edit, validate, generate, deploy.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
import yaml

from parser.config_parser import ConfigParser
from generator.gitlab_ci_generator import GitLabCIGenerator
from deployer.kubernetes_deployer import KubernetesDeployer
from cli.interactive_cli_wizards import ConfigurationWizards

console = Console()


class InteractiveCLIHandlers:
    """Handlers for CLI actions."""
    
    def __init__(self, config_file: str, output_file: str, custom_style):
        """
        Initialize handlers.
        
        Args:
            config_file: Path to configuration file
            output_file: Path to output pipeline file
            custom_style: Questionary style for prompts
        """
        self.config_file = config_file
        self.output_file = output_file
        self.custom_style = custom_style
        self.wizards = ConfigurationWizards(custom_style)
    
    def handle_create_configuration(self) -> None:
        """Handle configuration creation wizard."""
        console.print("\n[bold cyan]📝 Create New Configuration[/bold cyan]\n")
        
        # Check if config file already exists
        if Path(self.config_file).exists():
            overwrite = questionary.confirm(
                f"Configuration file '{self.config_file}' already exists. Overwrite?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if not overwrite:
                console.print("[yellow]Operation cancelled[/yellow]\n")
                return
            
            # Create backup
            backup_file = f"{self.config_file}.backup"
            shutil.copy(self.config_file, backup_file)
            console.print(f"[green]✓[/green] Backup created: {backup_file}\n")
        
        # Run configuration wizard
        config = self.create_configuration_wizard()
        
        if config:
            # Save configuration
            self.save_configuration(config, self.config_file)
            console.print(f"\n[green]✓[/green] Configuration saved to: [cyan]{self.config_file}[/cyan]\n")
            
            # Offer to generate pipeline
            generate = questionary.confirm(
                "Would you like to generate .gitlab-ci.yml now?",
                default=True,
                style=self.custom_style
            ).ask()
            
            if generate:
                self.handle_generate()
    
    def handle_edit_configuration(self) -> None:
        """Handle configuration editing."""
        console.print("\n[bold cyan]✏️  Edit Configuration[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] Configuration file '{self.config_file}' not found\n")
            return
        
        config = self.edit_configuration(self.config_file)
        
        if config:
            # Save configuration
            self.save_configuration(config, self.config_file)
            console.print(f"\n[green]✓[/green] Configuration updated: [cyan]{self.config_file}[/cyan]\n")
    
    def handle_validate(self) -> None:
        """Handle configuration validation."""
        console.print("\n[bold cyan]✓ Validate Configuration[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] Configuration file '{self.config_file}' not found\n")
            return
        
        self.validate_and_report(self.config_file)
    
    def handle_generate(self) -> None:
        """Handle pipeline generation."""
        console.print("\n[bold cyan]⚙️  Generate Pipeline[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] Configuration file '{self.config_file}' not found\n")
            return
        
        self.generate_pipeline(self.config_file, self.output_file)
    
    def handle_deploy(self) -> None:
        """Handle interactive deployment."""
        console.print("\n[bold cyan]🚀 Deploy to Environment[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] Configuration file '{self.config_file}' not found\n")
            return
        
        self.deploy_interactive(self.config_file)
    
    def handle_view_configuration(self) -> None:
        """Handle viewing current configuration."""
        console.print("\n[bold cyan]👁️  View Configuration[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] Configuration file '{self.config_file}' not found\n")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
            console.print()
            
        except Exception as e:
            console.print(f"[red]✗[/red] Error reading configuration: {e}\n")
    
    def create_configuration_wizard(self) -> Dict[str, Any]:
        """
        Guide user through configuration creation.
        
        Returns:
            Complete configuration dictionary
        """
        console.print("[bold]Let's create your pipeline configuration step by step.[/bold]\n")
        
        config = {}
        
        # Project information
        console.print("[bold cyan]Project Information[/bold cyan]")
        config['project'] = self.wizards.wizard_project_info()
        console.print()
        
        # Components
        console.print("[bold cyan]Components[/bold cyan]")
        config['components'] = self.wizards.wizard_components()
        console.print()
        
        # Environments
        console.print("[bold cyan]Environments[/bold cyan]")
        config['environments'] = self.wizards.wizard_environments()
        console.print()
        
        # SonarQube (optional)
        console.print("[bold cyan]Quality Analysis[/bold cyan]")
        enable_sonar = questionary.confirm(
            "Enable SonarQube quality analysis?",
            default=True,
            style=self.custom_style
        ).ask()
        
        if enable_sonar:
            config['sonarqube'] = self.wizards.wizard_sonarqube()
        console.print()
        
        # Change Detection (optional)
        console.print("[bold cyan]Change Detection[/bold cyan]")
        enable_change_detection = questionary.confirm(
            "Enable intelligent change detection?",
            default=True,
            style=self.custom_style
        ).ask()
        
        if enable_change_detection:
            config['changeDetection'] = self.wizards.wizard_change_detection()
        console.print()
        
        return config
    
    def edit_configuration(self, config_file: str) -> Optional[Dict[str, Any]]:
        """
        Interactive configuration editor.
        
        Args:
            config_file: Path to existing configuration
            
        Returns:
            Updated configuration dictionary or None if cancelled
        """
        try:
            # Load existing configuration
            parser = ConfigParser()
            config = parser.parse(config_file)
            
            console.print("[green]✓[/green] Configuration loaded successfully\n")
            
            # Show what can be edited
            choices = [
                questionary.Choice("📋 Project information", value="project"),
                questionary.Choice("📦 Components", value="components"),
                questionary.Choice("🌍 Environments", value="environments"),
                questionary.Choice("🔍 SonarQube settings", value="sonarqube"),
                questionary.Choice("🔄 Change detection", value="changeDetection"),
                questionary.Separator(),
                questionary.Choice("💾 Save and exit", value="save"),
                questionary.Choice("❌ Cancel", value="cancel"),
            ]
            
            while True:
                section = questionary.select(
                    "What would you like to edit?",
                    choices=choices,
                    style=self.custom_style
                ).ask()
                
                if section == "save":
                    return config
                elif section == "cancel":
                    return None
                elif section == "project":
                    config['project'] = self.wizards.wizard_project_info()
                elif section == "components":
                    config['components'] = self.wizards.wizard_components()
                elif section == "environments":
                    config['environments'] = self.wizards.wizard_environments()
                elif section == "sonarqube":
                    config['sonarqube'] = self.wizards.wizard_sonarqube()
                elif section == "changeDetection":
                    config['changeDetection'] = self.wizards.wizard_change_detection()
                
                console.print("[green]✓[/green] Section updated\n")
        
        except Exception as e:
            console.print(f"[red]✗[/red] Error loading configuration: {e}\n")
            return None
    
    def validate_and_report(self, config_file: str) -> bool:
        """
        Validate configuration and display results.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parser = ConfigParser()
            config = parser.parse(config_file)
            
            # Show success message
            console.print("[green]✓[/green] Configuration is valid!\n")
            
            # Show summary
            table = Table(title="Configuration Summary", border_style="green")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            
            table.add_row("Project", config.get('project', {}).get('name', 'N/A'))
            table.add_row("Organization", config.get('project', {}).get('organization', 'N/A'))
            table.add_row("Version", config.get('project', {}).get('version', 'N/A'))
            table.add_row("Components", str(len(config.get('components', []))))
            table.add_row("Environments", str(len(config.get('environments', {}))))
            
            # Show component details
            components = config.get('components', [])
            if components:
                table.add_row("", "")
                for comp in components:
                    table.add_row(f"  └─ {comp['name']}", f"Type: {comp['type']}, Path: {comp['path']}")
            
            console.print(table)
            console.print()
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Validation failed:\n")
            console.print(Panel(
                str(e),
                title="[red]Error Details[/red]",
                border_style="red",
                padding=(1, 2)
            ))
            console.print()
            return False
    
    def generate_pipeline(self, config_file: str, output_file: str) -> None:
        """
        Generate .gitlab-ci.yml from configuration.
        
        Args:
            config_file: Path to configuration
            output_file: Path for generated pipeline
        """
        try:
            # Parse configuration
            console.print("[cyan]Parsing configuration...[/cyan]")
            parser = ConfigParser()
            config = parser.parse(config_file)
            console.print("[green]✓[/green] Configuration parsed successfully\n")
            
            # Generate pipeline
            console.print("[cyan]Generating pipeline...[/cyan]")
            generator = GitLabCIGenerator()
            pipeline_yaml = generator.generate(config)
            console.print("[green]✓[/green] Pipeline generated successfully\n")
            
            # Write output file
            console.print(f"[cyan]Writing to {output_file}...[/cyan]")
            with open(output_file, 'w') as f:
                f.write(pipeline_yaml)
            console.print(f"[green]✓[/green] Pipeline written to: [cyan]{output_file}[/cyan]\n")
            
            # Show preview
            show_preview = questionary.confirm(
                "Would you like to see a preview?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if show_preview:
                console.print()
                syntax = Syntax(pipeline_yaml, "yaml", theme="monokai", line_numbers=True)
                console.print(syntax)
                console.print()
            
        except Exception as e:
            console.print(f"[red]✗[/red] Generation failed:\n")
            console.print(Panel(
                str(e),
                title="[red]Error Details[/red]",
                border_style="red",
                padding=(1, 2)
            ))
            console.print()
    
    def deploy_interactive(self, config_file: str) -> None:
        """
        Interactive deployment with environment selection.
        
        Args:
            config_file: Path to configuration
        """
        try:
            # Parse configuration
            parser = ConfigParser()
            config = parser.parse(config_file)
            
            # Get available environments
            environments = list(config.get('environments', {}).keys())
            if not environments:
                console.print("[red]✗[/red] No environments configured\n")
                return
            
            # Select environment
            environment = questionary.select(
                "Select target environment:",
                choices=environments,
                style=self.custom_style
            ).ask()
            
            # Get components
            components = config.get('components', [])
            component_names = [c['name'] for c in components]
            component_names.append("All components")
            
            # Select component
            selected = questionary.select(
                "Select component to deploy:",
                choices=component_names,
                style=self.custom_style
            ).ask()
            
            # Determine which components to deploy
            if selected == "All components":
                deploy_components = components
            else:
                deploy_components = [c for c in components if c['name'] == selected]
            
            # Confirm deployment
            console.print()
            console.print(Panel(
                f"[bold]Deployment Summary[/bold]\n\n"
                f"[cyan]Environment:[/cyan] {environment}\n"
                f"[cyan]Components:[/cyan] {', '.join([c['name'] for c in deploy_components])}\n",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            confirm = questionary.confirm(
                "Proceed with deployment?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if not confirm:
                console.print("[yellow]Deployment cancelled[/yellow]\n")
                return
            
            # Deploy
            console.print()
            deployer = KubernetesDeployer()
            
            for comp in deploy_components:
                console.print(f"[bold]Deploying {comp['name']}...[/bold]")
                deployer.deploy(comp, environment, config)
                console.print(f"[green]✓[/green] {comp['name']} deployed successfully\n")
            
            console.print("[green]✓[/green] Deployment completed successfully\n")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Deployment failed:\n")
            console.print(Panel(
                str(e),
                title="[red]Error Details[/red]",
                border_style="red",
                padding=(1, 2)
            ))
            console.print()
    
    def save_configuration(self, config: Dict[str, Any], output_file: str) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration dictionary
            output_file: Output file path
        """
        try:
            with open(output_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save configuration: {e}")
