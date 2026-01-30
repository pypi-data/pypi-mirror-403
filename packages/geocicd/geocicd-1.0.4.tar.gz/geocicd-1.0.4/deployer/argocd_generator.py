"""
ArgocdGenerator module for GitLab CI/CD Migration system.

This module provides ArgoCD Application manifest generation and deployment
operations including repository management and Application deployment.
"""

import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional
import shutil

import yaml

from utils.logging_config import get_logger, OperationLogger
from utils.exceptions import DeploymentError
from deployer.argocd_manifest_generator import ArgocdManifestGenerator
from deployer.argocd_repo_manager import ArgocdRepoManager

logger = get_logger(__name__)


class ArgocdGenerator:
    """
    Generator for ArgoCD Application manifests and deployment operations.
    
    This class handles:
    - ArgoCD Application manifest generation
    - k8s-charts repository operations (clone, copy, commit, push)
    - Application deployment to Kubernetes cluster
    """
    
    def __init__(self):
        """Initialize ArgoCD generator."""
        self.manifest_generator = ArgocdManifestGenerator()
        self.repo_manager = ArgocdRepoManager()
        logger.debug("ArgocdGenerator initialized")
    
    def generate(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate ArgoCD Application manifest.
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            Application manifest as dictionary
        """
        return self.manifest_generator.generate(component, environment, config)
    
    def get_argocd_server(self, environment: str, config: Dict[str, Any]) -> str:
        """
        Determine ArgoCD server URL for environment.
        
        Args:
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            ArgoCD server URL
        """
        return self.manifest_generator.get_argocd_server(environment, config)
    
    def clone_charts_repository(
        self,
        repo_url: str,
        branch: str,
        credentials: Optional[Dict[str, Any]] = None,
        target_dir: Optional[str] = None
    ) -> str:
        """Clone k8s-charts repository."""
        return self.repo_manager.clone_charts_repository(
            repo_url, branch, credentials, target_dir
        )
    
    def copy_helm_chart(
        self,
        chart_path: str,
        repo_path: str,
        target_path: str
    ) -> str:
        """Copy Helm chart to k8s-charts repository."""
        return self.repo_manager.copy_helm_chart(chart_path, repo_path, target_path)
    
    def commit_and_push_chart(
        self,
        repo_path: str,
        component_name: str,
        environment: str,
        commit_message: Optional[str] = None
    ) -> None:
        """Commit and push Helm chart changes to repository."""
        return self.repo_manager.commit_and_push_chart(
            repo_path, component_name, environment, commit_message
        )
    
    def apply_argocd_application(
        self,
        manifest: Dict[str, Any],
        context: Optional[str] = None,
        skip_for_eks: bool = True
    ) -> None:
        """
        Apply ArgoCD Application manifest to Kubernetes cluster.
        
        Args:
            manifest: Application manifest dictionary
            context: Optional Kubernetes context
            skip_for_eks: If True, skip apply for EKS contexts
            
        Raises:
            DeploymentError: If kubectl apply fails
        """
        app_name = manifest.get('metadata', {}).get('name', 'unknown')
        
        with OperationLogger(logger, f"apply ArgoCD Application {app_name}"):
            # Check if we should skip for EKS
            if skip_for_eks and context and 'eks' in context.lower():
                logger.info(
                    f"Skipping Application apply for EKS context: {context}"
                )
                return
            
            # Write manifest to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.yaml',
                delete=False
            ) as f:
                yaml.dump(manifest, f, default_flow_style=False)
                manifest_file = f.name
            
            try:
                # Build kubectl command
                cmd = ['kubectl', 'apply', '-f', manifest_file]
                
                if context:
                    cmd.extend(['--context', context])
                
                logger.debug(f"Executing: {' '.join(cmd)}")
                
                # Execute kubectl apply
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Applied ArgoCD Application: {app_name}")
                if result.stdout:
                    logger.debug(f"kubectl output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to apply ArgoCD Application: {e.stderr}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    details={
                        'application': app_name,
                        'context': context,
                        'exit_code': e.returncode,
                        'stderr': e.stderr,
                        'stdout': e.stdout
                    }
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(manifest_file)
                except Exception:
                    pass
    
    def deploy_with_argocd(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any],
        chart_path: str
    ) -> Dict[str, Any]:
        """
        Complete ArgoCD deployment workflow.
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            chart_path: Path to generated Helm chart
            
        Returns:
            Dictionary with deployment results
            
        Raises:
            DeploymentError: If any step fails
        """
        component_name = component.get('name')
        
        with OperationLogger(
            logger,
            f"deploy {component_name} to {environment} with ArgoCD"
        ):
            # Get environment and ArgoCD configuration
            env_config = config.get('environments', {}).get(environment, {})
            argocd_config = env_config.get('argocd', {})
            charts_repo = argocd_config.get('chartsRepo', {})
            
            repo_url = charts_repo.get('url')
            repo_branch = charts_repo.get('branch', 'main')
            credentials = charts_repo.get('credentials')
            
            # Get project configuration
            project_config = config.get('project', {})
            organization = project_config.get('organization', 'default')
            project_name = project_config.get('name', 'default')
            
            # Get destination configuration
            destination = env_config.get('destination', [{}])[0]
            context = destination.get('context')
            
            # Build chart path in repository
            chart_repo_path = f"projects/{organization}/{project_name}/{environment}/{component_name}"
            
            repo_path = None
            try:
                # Step 1: Clone repository
                repo_path = self.clone_charts_repository(
                    repo_url,
                    repo_branch,
                    credentials
                )
                
                # Step 2: Copy chart
                copied_chart_path = self.copy_helm_chart(
                    chart_path,
                    repo_path,
                    chart_repo_path
                )
                
                # Step 3: Commit and push
                self.commit_and_push_chart(
                    repo_path,
                    component_name,
                    environment
                )
                
                # Step 4: Generate Application manifest
                application = self.generate(component, environment, config)
                
                # Step 5: Apply Application
                self.apply_argocd_application(
                    application,
                    context=context,
                    skip_for_eks=True
                )
                
                result = {
                    'status': 'success',
                    'component': component_name,
                    'environment': environment,
                    'application_name': application['metadata']['name'],
                    'chart_path': chart_repo_path,
                    'repository': repo_url
                }
                
                logger.info(
                    f"Successfully deployed {component_name} to {environment} "
                    f"via ArgoCD"
                )
                
                return result
                
            finally:
                # Clean up cloned repository
                if repo_path and os.path.exists(repo_path):
                    try:
                        shutil.rmtree(repo_path)
                        logger.debug(f"Cleaned up repository: {repo_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up repository: {e}")
