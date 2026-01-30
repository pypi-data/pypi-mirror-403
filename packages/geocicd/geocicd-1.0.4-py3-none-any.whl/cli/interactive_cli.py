"""
Interactive CLI for GeoCICD

This module provides an interactive command-line interface that guides users
through pipeline configuration, validation, generation, and deployment.

Requirements: 21.1-21.12
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from cli.interactive_cli_handlers import InteractiveCLIHandlers
from utils.logging_config import get_logger

logger = get_logger(__name__)
console = Console()

# Custom style for questionary prompts
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#2196f3 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#2196f3'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


class InteractiveCLI:
    """
    Interactive command-line interface for GeoCICD
    
    Provides a user-friendly menu-driven interface for:
    - Creating new pipeline configurations
    - Editing existing configurations
    - Validating configurations
    - Generating .gitlab-ci.yml files
    - Deploying to environments
    - Viewing current configuration
    
    Requirements: 21.1-21.12
    """
    
    def __init__(self, current_version: str = "1.0.0"):
        """
        Initialize the interactive CLI
        
        Args:
            current_version: Current CLI version for version checking
        """
        self.current_version = current_version
        self.config_file = "ci-config.yaml"
        self.output_file = ".gitlab-ci.yml"
        self.handlers = InteractiveCLIHandlers(self.config_file, self.output_file, custom_style)
        
    def run(self) -> None:
        """
        Start interactive CLI session
        
        Displays main menu and handles user interactions.
        Includes version check at startup.
        
        Requirements: 21.1, 21.8, 23.1-23.13
        """
        # Display welcome banner
        self._display_welcome()
        
        # Main menu loop
        while True:
            try:
                action = self._show_main_menu()
                
                if action == "create":
                    self.handlers.handle_create_configuration()
                elif action == "edit":
                    self.handlers.handle_edit_configuration()
                elif action == "validate":
                    self.handlers.handle_validate()
                elif action == "generate":
                    self.handlers.handle_generate()
                elif action == "deploy":
                    self.handlers.handle_deploy()
                elif action == "view":
                    self.handlers.handle_view_configuration()
                elif action == "exit":
                    console.print("\n[cyan]👋 Arrivederci![/cyan]\n")
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Operazione annullata[/yellow]")
                continue
            except Exception as e:
                logger.exception("Error in interactive CLI")
                console.print(f"\n[red]Errore: {e}[/red]\n")
                continue
    
    def _display_welcome(self) -> None:
        """Display welcome banner"""
        console.print()
        console.print(Panel(
            Text.from_markup(
                "[bold cyan]GeoCICD CLI Interattiva[/bold cyan]\n\n"
                "[white]Generazione automatica di pipeline GitLab CI/CD da configurazione dichiarativa[/white]\n"
                "[dim]Versione: " + self.current_version + "[/dim]"
            ),
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()
    
    def _show_main_menu(self) -> str:
        """
        Display main menu and get user choice
        
        Returns:
            Selected action
        """
        choices = [
            questionary.Choice("📝 Crea nuova configurazione", value="create"),
            questionary.Choice("✏️  Modifica configurazione esistente", value="edit"),
            questionary.Choice("✓  Valida configurazione", value="validate"),
            questionary.Choice("⚙️  Genera .gitlab-ci.yml", value="generate"),
            questionary.Choice("🚀 Deploy su environment", value="deploy"),
            questionary.Choice("👁️  Visualizza configurazione corrente", value="view"),
            questionary.Separator(),
            questionary.Choice("❌ Esci", value="exit"),
        ]
        
        return questionary.select(
            "Cosa vuoi fare?",
            choices=choices,
            style=custom_style
        ).ask()
