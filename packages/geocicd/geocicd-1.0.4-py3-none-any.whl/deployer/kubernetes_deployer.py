"""
KubernetesDeployer module for GitLab CI/CD Migration system.

This module provides Kubernetes deployment orchestration including:
- Integration with HelmGenerator and ArgocdGenerator
- Support for both ArgoCD and direct deployment modes
- Deployment workflow coordination
"""

import logging
import os
import subprocess
from typing import Any, Dict, Optional

from generator.helm_generator import HelmGenerator
from deployer.argocd_generator import ArgocdGenerator
from deployer.kubernetes_resource_manager import KubernetesResourceManager
from utils.logging_config import get_logger, OperationLogger
from utils.exceptions import DeploymentError

logger = get_logger(__name__)


class KubernetesDeployer:
    """
    Deployer for Kubernetes applications.
    
    This class orchestrates the complete deployment workflow:
    - Generate Helm charts
    - Create ConfigMaps from files
    - Create SSL secrets with auto-discovery
    - Manage namespaces
    - Deploy via ArgoCD or direct kubectl/helm
    
    Responsibilities:
    - Orchestrate full deployment workflow
    - Integrate HelmGenerator, ArgocdGenerator, and KubernetesResourceManager
    - Support both ArgoCD and direct deployment modes
    """
    
    def __init__(self):
        """Initialize Kubernetes deployer."""
        self.helm_generator = HelmGenerator()
        self.argocd_generator = ArgocdGenerator()
        self.resource_manager = KubernetesResourceManager()
        logger.debug("KubernetesDeployer initialized")
    
    def deploy(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy component to Kubernetes.
        
        Orchestrates the complete deployment workflow:
        1. Determine deployment mode (ArgoCD vs direct)
        2. Get environment and destination configuration
        3. Ensure namespace exists
        4. Create ConfigMaps from files
        5. Create SSL secrets if configured
        6. Generate Helm chart
        7. Deploy via ArgoCD or direct helm/kubectl
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            Dictionary with deployment results including:
            - status: 'success' or 'failed'
            - component: Component name
            - environment: Environment name
            - deployment_mode: 'argocd' or 'direct'
            - namespace: Target namespace
            - chart_path: Path to generated Helm chart
            
        Raises:
            DeploymentError: If deployment fails at any step
            ValueError: If required configuration is missing
            
        Examples:
            >>> deployer = KubernetesDeployer()
            >>> result = deployer.deploy(component, "stg", config)
            >>> print(result['status'])
            'success'
        """
        component_name = component.get('name')
        
        with OperationLogger(
            logger,
            f"deploy {component_name} to {environment}",
            component=component_name,
            environment=environment
        ):
            if not component_name:
                raise ValueError("Component must have a name")
            
            # Get environment configuration
            env_config = config.get('environments', {}).get(environment, {})
            if not env_config:
                raise ValueError(
                    f"Environment '{environment}' not found in configuration"
                )
            
            # Get destination configuration
            destinations = env_config.get('destination', [])
            if not destinations:
                raise ValueError(
                    f"No destination configured for environment '{environment}'"
                )
            
            # Use first destination for Kubernetes deployment
            destination = destinations[0]
            namespace = destination.get('namespace')
            context = destination.get('context')
            
            if not namespace:
                # Generate default namespace
                project_config = config.get('project', {})
                organization = project_config.get('organization', 'default')
                project_name = project_config.get('name', 'default')
                namespace = f"{organization}-{project_name}-{environment}"
                logger.info(f"Using default namespace: {namespace}")
            
            # Determine deployment mode
            argocd_config = env_config.get('argocd', {})
            use_argocd = argocd_config.get('enabled', False)
            deployment_mode = 'argocd' if use_argocd else 'direct'
            
            logger.info(
                f"Deploying {component_name} to {environment} "
                f"(mode: {deployment_mode}, namespace: {namespace})"
            )
            
            try:
                # Step 1: Ensure namespace exists
                self.resource_manager.ensure_namespace_exists(namespace, context)
                
                # Step 2: Create ConfigMaps
                k8s_config = component.get('kubernetes', {})
                configmaps = k8s_config.get('configMaps', [])
                if configmaps:
                    self.resource_manager.create_configmaps(configmaps, namespace, context)
                
                # Step 3: Create SSL secret if configured
                ssl_secret_config = k8s_config.get('sslSecret', {})
                if ssl_secret_config.get('enabled', False):
                    ssl_dir = os.path.join(component.get('path', '.'), 'ssl')
                    secret_name = ssl_secret_config.get('name', f"{component_name}-tls")
                    self.resource_manager.create_ssl_secret(ssl_dir, secret_name, namespace, context)
                
                # Step 4: Generate Helm chart
                chart_path = self.helm_generator.generate(
                    component,
                    environment,
                    config
                )
                logger.info(f"Generated Helm chart at: {chart_path}")
                
                # Step 5: Deploy based on mode
                if use_argocd:
                    # Deploy via ArgoCD
                    argocd_result = self.argocd_generator.deploy_with_argocd(
                        component,
                        environment,
                        config,
                        chart_path
                    )
                    
                    result = {
                        'status': 'success',
                        'component': component_name,
                        'environment': environment,
                        'deployment_mode': 'argocd',
                        'namespace': namespace,
                        'chart_path': chart_path,
                        'application_name': argocd_result.get('application_name'),
                        'argocd_result': argocd_result
                    }
                else:
                    # Direct deployment using helm
                    self._deploy_with_helm(
                        component_name,
                        chart_path,
                        namespace,
                        context
                    )
                    
                    result = {
                        'status': 'success',
                        'component': component_name,
                        'environment': environment,
                        'deployment_mode': 'direct',
                        'namespace': namespace,
                        'chart_path': chart_path
                    }
                
                logger.info(
                    f"Successfully deployed {component_name} to {environment}"
                )
                
                return result
                
            except Exception as e:
                error_msg = f"Failed to deploy {component_name} to {environment}: {str(e)}"
                logger.error(error_msg)
                
                if isinstance(e, DeploymentError):
                    raise
                
                raise DeploymentError(
                    error_msg,
                    component=component_name,
                    environment=environment,
                    namespace=namespace,
                    context=context
                )
    
    def _deploy_with_helm(
        self,
        component_name: str,
        chart_path: str,
        namespace: str,
        context: Optional[str] = None
    ) -> None:
        """
        Deploy Helm chart directly using helm upgrade --install.
        
        Args:
            component_name: Component name (used as release name)
            chart_path: Path to Helm chart directory
            namespace: Target namespace
            context: Optional Kubernetes context
            
        Raises:
            DeploymentError: If helm command fails
        """
        with OperationLogger(
            logger,
            f"deploy Helm chart for {component_name}",
            namespace=namespace
        ):
            # Build helm command
            release_name = component_name
            cmd = [
                'helm', 'upgrade', '--install',
                release_name,
                chart_path,
                '--namespace', namespace,
                '--create-namespace'
            ]
            
            # Add context if specified
            if context:
                cmd.extend(['--kube-context', context])
            
            logger.debug(f"Executing helm: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(
                    f"Deployed Helm release: {release_name} in namespace {namespace}"
                )
                if result.stdout:
                    logger.debug(f"helm output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to deploy Helm chart for {component_name}: {e.stderr}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    component=component_name,
                    namespace=namespace,
                    context=context,
                    helm_error=e.stderr
                )
