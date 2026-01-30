"""
Configuration wizards for Interactive CLI.

Provides step-by-step wizards for creating configuration sections.
"""

import questionary
from typing import Dict, Any, List
from rich.console import Console

console = Console()


class ConfigurationWizards:
    """Wizards for creating configuration sections."""
    
    def __init__(self, custom_style):
        """
        Initialize wizards.
        
        Args:
            custom_style: Questionary style for prompts
        """
        self.custom_style = custom_style
    
    def wizard_project_info(self) -> Dict[str, Any]:
        """Wizard for project information."""
        name = questionary.text(
            "Project name (kebab-case):",
            default="my-project",
            style=self.custom_style,
            validate=lambda x: len(x) > 0 or "Project name is required"
        ).ask()
        
        organization = questionary.text(
            "Organization name:",
            default="my-org",
            style=self.custom_style,
            validate=lambda x: len(x) > 0 or "Organization is required"
        ).ask()
        
        version = questionary.text(
            "Project version:",
            default="1.0.0",
            style=self.custom_style,
            validate=lambda x: len(x) > 0 or "Version is required"
        ).ask()
        
        return {
            'name': name,
            'organization': organization,
            'version': version
        }
    
    def wizard_components(self) -> List[Dict[str, Any]]:
        """Wizard for components configuration."""
        components = []
        
        while True:
            console.print(f"\n[bold]Component {len(components) + 1}[/bold]")
            
            name = questionary.text(
                "Component name:",
                default=f"component-{len(components) + 1}",
                style=self.custom_style,
                validate=lambda x: len(x) > 0 or "Component name is required"
            ).ask()
            
            comp_type = questionary.select(
                "Component type:",
                choices=['vue', 'maven', 'npm', 'gradle', 'python'],
                style=self.custom_style
            ).ask()
            
            path = questionary.text(
                "Component path:",
                default=f"./{name}",
                style=self.custom_style
            ).ask()
            
            # Docker configuration
            use_docker = questionary.confirm(
                "Build Docker image?",
                default=True,
                style=self.custom_style
            ).ask()
            
            component = {
                'name': name,
                'type': comp_type,
                'path': path
            }
            
            if use_docker:
                dockerfile = questionary.text(
                    "Dockerfile path:",
                    default=f"{path}/Dockerfile",
                    style=self.custom_style
                ).ask()
                
                image_name = questionary.text(
                    "Docker image name:",
                    default=name,
                    style=self.custom_style
                ).ask()
                
                component['build'] = {
                    'artifacts': {
                        'type': 'docker',
                        'docker': {
                            'dockerfile': dockerfile,
                            'context': path
                        }
                    },
                    'destination': [{
                        'type': 'dockerRegistry',
                        'url': 'registry.example.com',
                        'imageName': image_name,
                        'tags': ['{{ version }}.{{ branch }}.{{ build_number }}', '{{ branch }}-latest']
                    }]
                }
            
            components.append(component)
            
            # Ask if user wants to add more components
            add_more = questionary.confirm(
                "Add another component?",
                default=False,
                style=self.custom_style
            ).ask()
            
            if not add_more:
                break
        
        return components
    
    def wizard_environments(self) -> Dict[str, Any]:
        """Wizard for environments configuration."""
        environments = {}
        
        # Default environments
        default_envs = ['dev', 'stg', 'ese']
        
        for env_name in default_envs:
            console.print(f"\n[bold]Environment: {env_name}[/bold]")
            
            configure = questionary.confirm(
                f"Configure {env_name} environment?",
                default=True,
                style=self.custom_style
            ).ask()
            
            if not configure:
                continue
            
            # Branch patterns
            if env_name == 'dev':
                default_branches = ['develop', 'develop-*']
            elif env_name == 'stg':
                default_branches = ['staging', 'stage']
            else:
                default_branches = ['main', 'master']
            
            branches_str = questionary.text(
                "Branch patterns (comma-separated):",
                default=','.join(default_branches),
                style=self.custom_style
            ).ask()
            
            branches = [b.strip() for b in branches_str.split(',')]
            
            # Kubernetes configuration
            namespace = questionary.text(
                "Kubernetes namespace:",
                default=f"my-org-my-project-{env_name}",
                style=self.custom_style
            ).ask()
            
            cluster = questionary.text(
                "Kubernetes cluster URL:",
                default="https://kubernetes.default.svc",
                style=self.custom_style
            ).ask()
            
            environments[env_name] = {
                'branches': branches,
                'autoSync': True,
                'deployMethod': 'kubernetes',
                'destination': [{
                    'type': 'kubernetes',
                    'cluster': cluster,
                    'namespace': namespace
                }]
            }
        
        return environments
    
    def wizard_sonarqube(self) -> Dict[str, Any]:
        """Wizard for SonarQube configuration."""
        server = questionary.text(
            "SonarQube server URL:",
            default="https://sonarqube.example.com",
            style=self.custom_style
        ).ask()
        
        project_key = questionary.text(
            "SonarQube project key:",
            default="my-project",
            style=self.custom_style
        ).ask()
        
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
