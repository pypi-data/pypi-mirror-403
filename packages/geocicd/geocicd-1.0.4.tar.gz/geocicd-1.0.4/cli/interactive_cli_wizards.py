"""
Configuration wizards for Interactive CLI.

Provides step-by-step wizards for creating configuration sections.
"""

import questionary
from typing import Dict, Any, List, Callable, Optional
from rich.console import Console
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

console = Console()


class BackException(Exception):
    """Exception raised when user wants to go back."""
    pass


def create_key_bindings():
    """Create custom key bindings with Ctrl+B for going back."""
    kb = KeyBindings()
    
    @kb.add('c-b')
    def _(event):
        """Handle Ctrl+B to go back."""
        raise BackException()
    
    return kb


class ConfigurationWizards:
    """Wizards for creating configuration sections."""
    
    def __init__(self, custom_style):
        """
        Initialize wizards.
        
        Args:
            custom_style: Questionary style for prompts
        """
        self.custom_style = custom_style
        self.key_bindings = create_key_bindings()
    
    def _ask_with_back(self, question_func: Callable, *args, **kwargs) -> Any:
        """
        Wrapper to add Ctrl+B support to any questionary question.
        
        Args:
            question_func: Questionary function (text, select, confirm, etc.)
            *args, **kwargs: Arguments to pass to the question function
            
        Returns:
            Answer from the question
            
        Raises:
            BackException: When user presses Ctrl+B
        """
        # Add key bindings to kwargs if not present
        if 'key_bindings' not in kwargs:
            kwargs['key_bindings'] = self.key_bindings
        
        try:
            return question_func(*args, **kwargs).ask()
        except BackException:
            raise
        except KeyboardInterrupt:
            raise
    
    def wizard_project_info(self) -> Dict[str, Any]:
        """Wizard for project information."""
        console.print("[dim]Premi Ctrl+B per tornare alla domanda precedente[/dim]\n")
        
        questions = []
        answers = {}
        current_idx = 0
        
        # Define all questions
        question_defs = [
            ('name', 'text', "Nome progetto (kebab-case):", "my-project", 
             lambda x: len(x) > 0 or "Il nome del progetto è obbligatorio"),
            ('organization', 'text', "Nome organizzazione:", "my-org",
             lambda x: len(x) > 0 or "Il nome dell'organizzazione è obbligatorio"),
            ('version', 'text', "Versione progetto:", "1.0.0",
             lambda x: len(x) > 0 or "La versione è obbligatoria"),
        ]
        
        while current_idx < len(question_defs):
            key, q_type, prompt, default, validate = question_defs[current_idx]
            
            try:
                if q_type == 'text':
                    answer = self._ask_with_back(
                        questionary.text,
                        prompt,
                        default=default,
                        style=self.custom_style,
                        validate=validate
                    )
                    answers[key] = answer
                    current_idx += 1
            except BackException:
                if current_idx > 0:
                    current_idx -= 1
                    console.print("[yellow]← Torno indietro...[/yellow]")
                else:
                    console.print("[yellow]Sei già alla prima domanda[/yellow]")
        
        return answers
    
    def wizard_components(self) -> List[Dict[str, Any]]:
        """Wizard for components configuration."""
        console.print("[dim]Premi Ctrl+B per tornare alla domanda precedente[/dim]\n")
        
        components = []
        
        while True:
            console.print(f"\n[bold]Componente {len(components) + 1}[/bold]")
            
            component = self._wizard_single_component(len(components))
            
            if component is None:  # User went back from first question
                if len(components) > 0:
                    console.print("[yellow]← Rimuovo l'ultimo componente e torno indietro...[/yellow]")
                    components.pop()
                    continue
                else:
                    console.print("[yellow]Nessun componente da rimuovere[/yellow]")
                    # Ask if they want to cancel or continue
                    try:
                        choice = self._ask_with_back(
                            questionary.select,
                            "Cosa vuoi fare?",
                            choices=['Continua ad aggiungere componenti', 'Annulla wizard'],
                            style=self.custom_style
                        )
                        if choice == 'Annulla wizard':
                            raise BackException()
                        continue
                    except BackException:
                        raise
            
            components.append(component)
            
            # Ask if user wants to add more components
            try:
                add_more = self._ask_with_back(
                    questionary.confirm,
                    "Aggiungere un altro componente?",
                    default=False,
                    style=self.custom_style
                )
                
                if not add_more:
                    break
            except BackException:
                console.print("[yellow]← Rimuovo l'ultimo componente...[/yellow]")
                components.pop()
                continue
        
        return components
    
    def _wizard_single_component(self, component_num: int) -> Optional[Dict[str, Any]]:
        """
        Wizard for a single component.
        
        Returns:
            Component dict or None if user went back from first question
        """
        questions_data = []
        current_idx = 0
        component = {}
        
        # Question 1: Component name
        while current_idx == 0:
            try:
                name = self._ask_with_back(
                    questionary.text,
                    "Nome componente:",
                    default=f"component-{component_num + 1}",
                    style=self.custom_style,
                    validate=lambda x: len(x) > 0 or "Il nome del componente è obbligatorio"
                )
                component['name'] = name
                current_idx = 1
            except BackException:
                return None  # Signal to go back
        
        # Question 2: Component type
        while current_idx == 1:
            try:
                comp_type = self._ask_with_back(
                    questionary.select,
                    "Tipo componente:",
                    choices=['vue', 'maven', 'npm', 'gradle', 'python'],
                    style=self.custom_style
                )
                component['type'] = comp_type
                current_idx = 2
            except BackException:
                current_idx = 0
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Question 3: Component path
        while current_idx == 2:
            try:
                path = self._ask_with_back(
                    questionary.text,
                    "Percorso componente:",
                    default=f"./{component['name']}",
                    style=self.custom_style
                )
                component['path'] = path
                current_idx = 3
            except BackException:
                current_idx = 1
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Build configuration based on type
        if component['type'] in ['npm', 'vue']:
            # Question 4: Node version
            while current_idx == 3:
                try:
                    node_version = self._ask_with_back(
                        questionary.text,
                        "Versione Node.js:",
                        default="18",
                        style=self.custom_style
                    )
                    component['nodeVersion'] = node_version
                    current_idx = 4
                except BackException:
                    current_idx = 2
                    console.print("[yellow]← Torno indietro...[/yellow]")
            
            # Question 5+: Install commands
            install_commands = []
            cmd_num = 1
            while current_idx >= 4:
                try:
                    default_cmd = ""
                    if cmd_num == 1:
                        default_cmd = "npm install"
                    
                    if cmd_num == 1:
                        console.print("\n[cyan]Comandi di installazione (uno per riga, riga vuota per finire):[/cyan]")
                    
                    cmd = self._ask_with_back(
                        questionary.text,
                        f"Comando installazione {cmd_num}:",
                        default=default_cmd,
                        style=self.custom_style
                    )
                    
                    if not cmd:
                        if len(install_commands) == 0:
                            console.print("[yellow]Almeno un comando di installazione è consigliato[/yellow]")
                        current_idx = 100  # Move to build command
                        break
                    
                    install_commands.append(cmd)
                    cmd_num += 1
                    
                except BackException:
                    if len(install_commands) > 0:
                        install_commands.pop()
                        cmd_num -= 1
                        console.print("[yellow]← Rimosso ultimo comando di installazione[/yellow]")
                    else:
                        current_idx = 3
                        console.print("[yellow]← Torno indietro...[/yellow]")
                        break
            
            # Question N: Build command
            while current_idx == 100:
                try:
                    build_command = self._ask_with_back(
                        questionary.text,
                        "Comando di build:",
                        default="npm run build",
                        style=self.custom_style,
                        validate=lambda x: len(x) > 0 or "Il comando di build è obbligatorio"
                    )
                    
                    # Combine all commands
                    all_commands = install_commands + [build_command]
                    
                    if all_commands:
                        component['build'] = {
                            'enabled': True,
                            'commands': all_commands
                        }
                    
                    current_idx = 101
                except BackException:
                    current_idx = 4
                    console.print("[yellow]← Torno ai comandi di installazione...[/yellow]")
            
            # Question N+1: Cache configuration
            while current_idx == 101:
                try:
                    use_cache = self._ask_with_back(
                        questionary.confirm,
                        "Abilitare cache di build?",
                        default=True,
                        style=self.custom_style
                    )
                    
                    if use_cache:
                        component['build']['cache'] = {
                            'paths': ['node_modules/', '.npm/']
                        }
                    
                    current_idx = 200  # Move to Docker config
                except BackException:
                    current_idx = 100
                    console.print("[yellow]← Torno indietro...[/yellow]")
        else:
            current_idx = 200  # Skip npm-specific questions
        
        # Docker configuration
        while current_idx == 200:
            try:
                use_docker = self._ask_with_back(
                    questionary.confirm,
                    "Creare immagine Docker?",
                    default=True,
                    style=self.custom_style
                )
                
                if use_docker:
                    current_idx = 201
                else:
                    return component  # Done
                    
            except BackException:
                if component['type'] in ['npm', 'vue']:
                    current_idx = 101
                else:
                    current_idx = 2
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Docker: Dockerfile path
        while current_idx == 201:
            try:
                dockerfile = self._ask_with_back(
                    questionary.text,
                    "Percorso Dockerfile:",
                    default=f"{component['path']}/Dockerfile",
                    style=self.custom_style
                )
                
                current_idx = 202
            except BackException:
                current_idx = 200
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Docker: Image name
        while current_idx == 202:
            try:
                image_name = self._ask_with_back(
                    questionary.text,
                    "Nome immagine Docker:",
                    default=component['name'],
                    style=self.custom_style
                )
                
                if 'build' not in component:
                    component['build'] = {'enabled': True}
                
                component['build']['artifacts'] = {
                    'type': 'docker',
                    'docker': {
                        'dockerfile': dockerfile,
                        'context': component['path']
                    }
                }
                
                current_idx = 203
            except BackException:
                current_idx = 201
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Docker: Outputs selection
        while current_idx == 203:
            try:
                outputs = self._ask_with_back(
                    questionary.checkbox,
                    "Seleziona gli output desiderati:",
                    choices=[
                        questionary.Choice('docker', checked=True),
                        questionary.Choice('artifact', checked=False),
                        questionary.Choice('helm', checked=False)
                    ],
                    style=self.custom_style
                )
                
                if not outputs:
                    console.print("[red]Devi selezionare almeno un output![/red]")
                    continue
                
                component['build']['outputs'] = outputs
                
                return component  # Done
                
            except BackException:
                current_idx = 202
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        return component
    
    def wizard_environments(self) -> Dict[str, Any]:
        """Wizard for environments configuration."""
        console.print("[dim]Premi Ctrl+B per tornare alla domanda precedente[/dim]\n")
        
        environments = {}
        default_envs = ['dev', 'stg', 'ese']
        env_idx = 0
        
        while env_idx < len(default_envs):
            env_name = default_envs[env_idx]
            console.print(f"\n[bold]Environment: {env_name}[/bold]")
            
            env_config = self._wizard_single_environment(env_name)
            
            if env_config is None:  # User went back
                if env_idx > 0:
                    env_idx -= 1
                    # Remove previous environment
                    prev_env = default_envs[env_idx]
                    if prev_env in environments:
                        del environments[prev_env]
                    console.print(f"[yellow]← Torno a {prev_env}...[/yellow]")
                else:
                    console.print("[yellow]Sei già al primo environment[/yellow]")
            elif env_config == 'skip':
                env_idx += 1
            else:
                environments[env_name] = env_config
                env_idx += 1
        
        return environments
    
    def _wizard_single_environment(self, env_name: str) -> Optional[Dict[str, Any]]:
        """
        Wizard for a single environment.
        
        Returns:
            Environment config dict, 'skip' to skip this env, or None to go back
        """
        current_idx = 0
        
        # Question 1: Configure this environment?
        while current_idx == 0:
            try:
                configure = self._ask_with_back(
                    questionary.confirm,
                    f"Configurare environment {env_name}?",
                    default=True,
                    style=self.custom_style
                )
                
                if not configure:
                    return 'skip'
                
                current_idx = 1
            except BackException:
                return None
        
        # Default branch patterns
        if env_name == 'dev':
            default_branches = ['develop', 'develop-*']
        elif env_name == 'stg':
            default_branches = ['staging', 'stage']
        else:
            default_branches = ['main', 'master']
        
        # Question 2: Branch patterns
        branches = None
        while current_idx == 1:
            try:
                branches_str = self._ask_with_back(
                    questionary.text,
                    "Pattern branch (separati da virgola):",
                    default=','.join(default_branches),
                    style=self.custom_style
                )
                
                branches = [b.strip() for b in branches_str.split(',')]
                current_idx = 2
            except BackException:
                current_idx = 0
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Question 3: Kubernetes namespace
        namespace = None
        while current_idx == 2:
            try:
                namespace = self._ask_with_back(
                    questionary.text,
                    "Namespace Kubernetes:",
                    default=f"my-org-my-project-{env_name}",
                    style=self.custom_style
                )
                current_idx = 3
            except BackException:
                current_idx = 1
                console.print("[yellow]← Torno indietro...[/yellow]")
        
        # Question 4: Kubernetes cluster
        cluster = None
        while current_idx == 3:
            try:
                cluster = self._ask_with_back(
                    questionary.text,
                    "URL cluster Kubernetes:",
                    default="https://kubernetes.default.svc",
                    style=self.custom_style
                )
                
                return {
                    'branches': branches,
                    'autoSync': True,
                    'deployMethod': 'kubernetes',
                    'destination': [{
                        'type': 'kubernetes',
                        'cluster': cluster,
                        'namespace': namespace
                    }]
                }
            except BackException:
                current_idx = 2
                console.print("[yellow]← Torno indietro...[/yellow]")
    
    def wizard_sonarqube(self) -> Dict[str, Any]:
        """Wizard for SonarQube configuration."""
        console.print("[dim]Premi Ctrl+B per tornare alla domanda precedente[/dim]\n")
        
        current_idx = 0
        server = None
        project_key = None
        
        # Question 1: Server URL
        while current_idx == 0:
            try:
                server = self._ask_with_back(
                    questionary.text,
                    "URL server SonarQube:",
                    default="https://sonarqube.example.com",
                    style=self.custom_style
                )
                current_idx = 1
            except BackException:
                raise  # Propagate to caller
        
        # Question 2: Project key
        while current_idx == 1:
            try:
                project_key = self._ask_with_back(
                    questionary.text,
                    "Chiave progetto SonarQube:",
                    default="my-project",
                    style=self.custom_style
                )
                
                return {
                    'enabled': True,
                    'server': server,
                    'projectKey': project_key,
                    'token': '${SONAR_TOKEN}',
                    'qualityGates': {
                        'coverage': {
                            'enabled': True,
                            'threshold': 80,
                            'operator': 'LT'
                        },
                        'bugs': {
                            'enabled': True,
                            'threshold': 0,
                            'operator': 'GT'
                        }
                    }
                }
            except BackException:
                current_idx = 0
                console.print("[yellow]← Torno indietro...[/yellow]")
    
    def wizard_change_detection(self) -> Dict[str, Any]:
        """Wizard for change detection configuration."""
        return {
            'enabled': True,
            'strategy': {
                'dev': {
                    'enabled': False
                },
                'stg': {
                    'enabled': True,
                    'compareWith': 'develop',
                    'useLastSuccessful': True
                },
                'ese': {
                    'enabled': True,
                    'compareWith': 'staging',
                    'useLastSuccessful': True
                }
            }
        }
