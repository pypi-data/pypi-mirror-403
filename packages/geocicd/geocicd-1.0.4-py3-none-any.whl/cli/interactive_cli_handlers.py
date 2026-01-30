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
from cli.interactive_cli_wizards import ConfigurationWizards, BackException

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
        console.print("\n[bold cyan]📝 Crea Nuova Configurazione[/bold cyan]\n")
        
        # Check if config file already exists
        if Path(self.config_file).exists():
            overwrite = questionary.confirm(
                f"Il file di configurazione '{self.config_file}' esiste già. Sovrascrivere?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if not overwrite:
                console.print("[yellow]Operazione annullata[/yellow]\n")
                return
            
            # Create backup
            backup_file = f"{self.config_file}.backup"
            shutil.copy(self.config_file, backup_file)
            console.print(f"[green]✓[/green] Backup creato: {backup_file}\n")
        
        # Run configuration wizard
        config = self.create_configuration_wizard()
        
        if config:
            # Save configuration
            self.save_configuration(config, self.config_file)
            console.print(f"\n[green]✓[/green] Configurazione salvata in: [cyan]{self.config_file}[/cyan]\n")
            
            # Offer to generate pipeline
            generate = questionary.confirm(
                "Vuoi generare il .gitlab-ci.yml ora?",
                default=True,
                style=self.custom_style
            ).ask()
            
            if generate:
                self.handle_generate()
    
    def handle_edit_configuration(self) -> None:
        """Handle configuration editing."""
        console.print("\n[bold cyan]✏️  Modifica Configurazione[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] File di configurazione '{self.config_file}' non trovato\n")
            return
        
        config = self.edit_configuration(self.config_file)
        
        if config:
            # Save configuration
            self.save_configuration(config, self.config_file)
            console.print(f"\n[green]✓[/green] Configurazione aggiornata: [cyan]{self.config_file}[/cyan]\n")
    
    def handle_validate(self) -> None:
        """Handle configuration validation."""
        console.print("\n[bold cyan]✓ Valida Configurazione[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] File di configurazione '{self.config_file}' non trovato\n")
            return
        
        self.validate_and_report(self.config_file)
    
    def handle_generate(self) -> None:
        """Handle pipeline generation."""
        console.print("\n[bold cyan]⚙️  Genera Pipeline[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] File di configurazione '{self.config_file}' non trovato\n")
            return
        
        self.generate_pipeline(self.config_file, self.output_file)
    
    def handle_deploy(self) -> None:
        """Handle interactive deployment."""
        console.print("\n[bold cyan]🚀 Deploy su Environment[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] File di configurazione '{self.config_file}' non trovato\n")
            return
        
        self.deploy_interactive(self.config_file)
    
    def handle_view_configuration(self) -> None:
        """Handle viewing current configuration."""
        console.print("\n[bold cyan]👁️  Visualizza Configurazione[/bold cyan]\n")
        
        if not Path(self.config_file).exists():
            console.print(f"[red]✗[/red] File di configurazione '{self.config_file}' non trovato\n")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
            console.print()
            
        except Exception as e:
            console.print(f"[red]✗[/red] Errore nella lettura della configurazione: {e}\n")
    
    def create_configuration_wizard(self) -> Dict[str, Any]:
        """
        Guide user through configuration creation.
        
        Returns:
            Complete configuration dictionary
        """
        console.print("[bold]Creiamo la configurazione della pipeline passo dopo passo.[/bold]\n")
        console.print("[dim]Premi Ctrl+B in qualsiasi momento per tornare alla domanda precedente[/dim]\n")
        
        config = {}
        section_idx = 0
        sections = ['project', 'components', 'environments', 'sonarqube', 'changeDetection']
        
        while section_idx < len(sections):
            section = sections[section_idx]
            
            try:
                if section == 'project':
                    console.print("[bold cyan]Informazioni Progetto[/bold cyan]")
                    config['project'] = self.wizards.wizard_project_info()
                    console.print()
                    section_idx += 1
                    
                elif section == 'components':
                    console.print("[bold cyan]Componenti[/bold cyan]")
                    config['components'] = self.wizards.wizard_components()
                    console.print()
                    section_idx += 1
                    
                elif section == 'environments':
                    console.print("[bold cyan]Environments[/bold cyan]")
                    config['environments'] = self.wizards.wizard_environments()
                    console.print()
                    section_idx += 1
                    
                elif section == 'sonarqube':
                    console.print("[bold cyan]Analisi Qualità[/bold cyan]")
                    enable_sonar = self.wizards._ask_with_back(
                        questionary.confirm,
                        "Abilitare analisi qualità con SonarQube?",
                        default=True,
                        style=self.custom_style
                    )
                    
                    if enable_sonar:
                        config['sonarqube'] = self.wizards.wizard_sonarqube()
                    console.print()
                    section_idx += 1
                    
                elif section == 'changeDetection':
                    console.print("[bold cyan]Rilevamento Modifiche[/bold cyan]")
                    enable_change_detection = self.wizards._ask_with_back(
                        questionary.confirm,
                        "Abilitare rilevamento intelligente delle modifiche?",
                        default=True,
                        style=self.custom_style
                    )
                    
                    if enable_change_detection:
                        config['changeDetection'] = self.wizards.wizard_change_detection()
                    console.print()
                    section_idx += 1
                    
            except BackException:
                if section_idx > 0:
                    section_idx -= 1
                    prev_section = sections[section_idx]
                    console.print(f"[yellow]← Torno a {prev_section}...[/yellow]\n")
                    # Remove the section we're going back to so it can be re-entered
                    if prev_section in config:
                        del config[prev_section]
                else:
                    console.print("[yellow]Sei già alla prima sezione[/yellow]")
        
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
            
            console.print("[green]✓[/green] Configurazione caricata con successo\n")
            
            # Show what can be edited
            choices = [
                questionary.Choice("📋 Informazioni progetto", value="project"),
                questionary.Choice("📦 Componenti", value="components"),
                questionary.Choice("🌍 Environments", value="environments"),
                questionary.Choice("🔍 Impostazioni SonarQube", value="sonarqube"),
                questionary.Choice("🔄 Rilevamento modifiche", value="changeDetection"),
                questionary.Separator(),
                questionary.Choice("💾 Salva ed esci", value="save"),
                questionary.Choice("❌ Annulla", value="cancel"),
            ]
            
            while True:
                section = questionary.select(
                    "Cosa vuoi modificare?",
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
                
                console.print("[green]✓[/green] Sezione aggiornata\n")
        
        except Exception as e:
            console.print(f"[red]✗[/red] Errore nel caricamento della configurazione: {e}\n")
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
            console.print("[green]✓[/green] La configurazione è valida!\n")
            
            # Show summary
            table = Table(title="Riepilogo Configurazione", border_style="green")
            table.add_column("Proprietà", style="cyan", no_wrap=True)
            table.add_column("Valore", style="white")
            
            table.add_row("Progetto", config.get('project', {}).get('name', 'N/A'))
            table.add_row("Organizzazione", config.get('project', {}).get('organization', 'N/A'))
            table.add_row("Versione", config.get('project', {}).get('version', 'N/A'))
            table.add_row("Componenti", str(len(config.get('components', []))))
            table.add_row("Environments", str(len(config.get('environments', {}))))
            
            # Show component details
            components = config.get('components', [])
            if components:
                table.add_row("", "")
                for comp in components:
                    table.add_row(f"  └─ {comp['name']}", f"Tipo: {comp['type']}, Percorso: {comp['path']}")
            
            console.print(table)
            console.print()
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Validazione fallita:\n")
            console.print(Panel(
                str(e),
                title="[red]Dettagli Errore[/red]",
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
            console.print("[cyan]Analisi configurazione...[/cyan]")
            parser = ConfigParser()
            config = parser.parse(config_file)
            console.print("[green]✓[/green] Configurazione analizzata con successo\n")
            
            # Generate pipeline
            console.print("[cyan]Generazione pipeline...[/cyan]")
            generator = GitLabCIGenerator()
            pipeline_yaml = generator.generate(config)
            console.print("[green]✓[/green] Pipeline generata con successo\n")
            
            # Write output file
            console.print(f"[cyan]Scrittura in {output_file}...[/cyan]")
            with open(output_file, 'w') as f:
                f.write(pipeline_yaml)
            console.print(f"[green]✓[/green] Pipeline scritta in: [cyan]{output_file}[/cyan]\n")
            
            # Show preview
            show_preview = questionary.confirm(
                "Vuoi vedere un'anteprima?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if show_preview:
                console.print()
                syntax = Syntax(pipeline_yaml, "yaml", theme="monokai", line_numbers=True)
                console.print(syntax)
                console.print()
            
        except Exception as e:
            console.print(f"[red]✗[/red] Generazione fallita:\n")
            console.print(Panel(
                str(e),
                title="[red]Dettagli Errore[/red]",
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
                console.print("[red]✗[/red] Nessun environment configurato\n")
                return
            
            # Select environment
            environment = questionary.select(
                "Seleziona environment di destinazione:",
                choices=environments,
                style=self.custom_style
            ).ask()
            
            # Get components
            components = config.get('components', [])
            component_names = [c['name'] for c in components]
            component_names.append("Tutti i componenti")
            
            # Select component
            selected = questionary.select(
                "Seleziona componente da deployare:",
                choices=component_names,
                style=self.custom_style
            ).ask()
            
            # Determine which components to deploy
            if selected == "Tutti i componenti":
                deploy_components = components
            else:
                deploy_components = [c for c in components if c['name'] == selected]
            
            # Confirm deployment
            console.print()
            console.print(Panel(
                f"[bold]Riepilogo Deployment[/bold]\n\n"
                f"[cyan]Environment:[/cyan] {environment}\n"
                f"[cyan]Componenti:[/cyan] {', '.join([c['name'] for c in deploy_components])}\n",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            confirm = questionary.confirm(
                "Procedere con il deployment?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if not confirm:
                console.print("[yellow]Deployment annullato[/yellow]\n")
                return
            
            # Deploy
            console.print()
            deployer = KubernetesDeployer()
            
            for comp in deploy_components:
                console.print(f"[bold]Deploy di {comp['name']} in corso...[/bold]")
                deployer.deploy(comp, environment, config)
                console.print(f"[green]✓[/green] {comp['name']} deployato con successo\n")
            
            console.print("[green]✓[/green] Deployment completato con successo\n")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Deployment fallito:\n")
            console.print(Panel(
                str(e),
                title="[red]Dettagli Errore[/red]",
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
