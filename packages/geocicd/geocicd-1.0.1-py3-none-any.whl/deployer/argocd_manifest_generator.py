"""
ArgoCD Application manifest generation.

Handles generation of ArgoCD Application manifests.
"""

import logging
from typing import Any, Dict

from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class ArgocdManifestGenerator:
    """Generator for ArgoCD Application manifests."""
    
    def __init__(self):
        """Initialize manifest generator."""
        logger.debug("ArgocdManifestGenerator initialized")
    
    def generate(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate ArgoCD Application manifest.
        
        Creates a complete ArgoCD Application manifest with:
        - Correct repository URL and branch
        - Helm chart path
        - Destination cluster and namespace
        - Sync policy (autoSync, selfHeal, prune)
        - Project assignment
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            Application manifest as dictionary
            
        Raises:
            ValueError: If required configuration is missing
        """
        with OperationLogger(logger, f"generate ArgoCD Application for {component.get('name')}"):
            component_name = component.get('name')
            if not component_name:
                raise ValueError("Component must have a name")
            
            # Get environment configuration
            env_config = config.get('environments', {}).get(environment, {})
            if not env_config:
                raise ValueError(f"Environment '{environment}' not found in configuration")
            
            # Get ArgoCD configuration
            argocd_config = env_config.get('argocd', {})
            if not argocd_config.get('enabled', False):
                raise ValueError(f"ArgoCD is not enabled for environment '{environment}'")
            
            # Get project configuration
            project_config = config.get('project', {})
            organization = project_config.get('organization', 'default')
            project_name = project_config.get('name', 'default')
            
            # Get charts repository configuration
            charts_repo = argocd_config.get('chartsRepo', {})
            repo_url = charts_repo.get('url')
            repo_branch = charts_repo.get('branch', 'main')
            
            if not repo_url:
                raise ValueError(f"ArgoCD chartsRepo.url not configured for environment '{environment}'")
            
            # Get destination configuration
            destination = env_config.get('destination', [{}])[0]
            cluster_url = destination.get('cluster', 'https://kubernetes.default.svc')
            namespace = destination.get('namespace', f"{organization}-{project_name}-{environment}")
            
            # Get Application configuration
            app_config = argocd_config.get('application', {})
            auto_sync = app_config.get('autoSync', True)
            self_heal = app_config.get('selfHeal', True)
            prune = app_config.get('prune', True)
            
            # Determine ArgoCD project
            argocd_project = argocd_config.get('project', 'default')
            
            # Build chart path in repository
            chart_path = f"projects/{organization}/{project_name}/{environment}/{component_name}"
            
            # Build Application manifest
            application = {
                'apiVersion': 'argoproj.io/v1alpha1',
                'kind': 'Application',
                'metadata': {
                    'name': f"{project_name}-{component_name}-{environment}",
                    'namespace': 'argocd',
                    'labels': {
                        'app.kubernetes.io/name': component_name,
                        'app.kubernetes.io/instance': f"{component_name}-{environment}",
                        'app.kubernetes.io/part-of': project_name,
                        'environment': environment,
                    },
                    'finalizers': [
                        'resources-finalizer.argocd.argoproj.io'
                    ]
                },
                'spec': {
                    'project': argocd_project,
                    'source': {
                        'repoURL': repo_url,
                        'targetRevision': repo_branch,
                        'path': chart_path,
                        'helm': {
                            'releaseName': f"{component_name}-{environment}"
                        }
                    },
                    'destination': {
                        'server': cluster_url,
                        'namespace': namespace
                    },
                    'syncPolicy': {}
                }
            }
            
            # Configure sync policy
            if auto_sync:
                application['spec']['syncPolicy']['automated'] = {
                    'prune': prune,
                    'selfHeal': self_heal,
                    'allowEmpty': False
                }
                application['spec']['syncPolicy']['syncOptions'] = [
                    'CreateNamespace=true',
                    'PrunePropagationPolicy=foreground',
                    'PruneLast=true'
                ]
            
            logger.info(
                f"Generated ArgoCD Application manifest: "
                f"{application['metadata']['name']}"
            )
            logger.debug(f"Application spec: {application['spec']}")
            
            return application
    
    def get_argocd_server(self, environment: str, config: Dict[str, Any]) -> str:
        """
        Determine ArgoCD server URL for environment.
        
        Args:
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            ArgoCD server URL
            
        Raises:
            ValueError: If ArgoCD server not configured
        """
        env_config = config.get('environments', {}).get(environment, {})
        argocd_config = env_config.get('argocd', {})
        
        server = argocd_config.get('server')
        if not server:
            raise ValueError(
                f"ArgoCD server not configured for environment '{environment}'"
            )
        
        logger.debug(f"ArgoCD server for {environment}: {server}")
        return server
