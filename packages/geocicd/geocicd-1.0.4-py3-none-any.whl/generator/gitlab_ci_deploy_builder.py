"""
GitLabCIDeployBuilder module for deployment job generation.

This module handles the creation of deployment jobs for different environments.
"""

import logging
from typing import Any, Dict, List

from utils.constants import (
    STAGE_DEPLOY,
    DEPLOY_METHOD_KUBERNETES,
    DEPLOY_METHOD_DOCKER_COMPOSE,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GitLabCIDeployBuilder:
    """
    Builder for GitLab CI deployment jobs.
    
    This class generates deployment jobs for environments with:
    - Branch-based conditional execution
    - Dependencies on publish jobs
    - Deployment scripts based on deployMethod
    - Environment-specific configuration
    """
    
    def __init__(self):
        """Initialize deploy builder."""
        logger.debug("GitLabCIDeployBuilder initialized")
    
    def generate_deploy_jobs(
        self,
        environments: Dict[str, Dict[str, Any]],
        components: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate deploy jobs with branch conditions.
        
        Creates deploy jobs for each environment-component combination with:
        - Branch-based conditional execution
        - Dependencies on publish jobs
        - Deployment scripts based on deployMethod
        - Environment-specific configuration
        
        Args:
            environments: Environment configurations
            components: Component configurations
            
        Returns:
            Dictionary of deploy job definitions keyed by job name
        """
        logger.debug(
            f"Generating deploy jobs for {len(environments)} environment(s) "
            f"and {len(components)} component(s)"
        )
        
        deploy_jobs = {}
        
        for env_name, env_config in environments.items():
            for component in components:
                component_name = component.get('name')
                if not component_name:
                    continue
                
                job_name = f"deploy:{env_name}:{component_name}"
                deploy_jobs[job_name] = self.create_deploy_job(
                    component,
                    env_name,
                    env_config
                )
                logger.debug(f"Generated deploy job: {job_name}")
        
        return deploy_jobs
    
    def create_deploy_job(
        self,
        component: Dict[str, Any],
        env_name: str,
        env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create deploy job for a component in an environment.
        
        Args:
            component: Component configuration
            env_name: Environment name
            env_config: Environment configuration
            
        Returns:
            Deploy job definition
        """
        component_name = component.get('name')
        deploy_method = env_config.get('deployMethod', DEPLOY_METHOD_KUBERNETES)
        branches = env_config.get('branches', [])
        
        # Build deployment script based on deploy method
        if deploy_method == DEPLOY_METHOD_KUBERNETES:
            script = self.get_kubernetes_deploy_script(component, env_name, env_config)
            image = 'alpine/k8s:1.28.3'
        elif deploy_method == DEPLOY_METHOD_DOCKER_COMPOSE:
            script = self.get_docker_compose_deploy_script(component, env_name, env_config)
            image = 'docker:24.0.5'
        else:
            logger.warning(f"Unsupported deploy method: {deploy_method}, using placeholder")
            script = [
                f'echo "Deploy method {deploy_method} is not supported"',
                f'echo "Supported methods: {DEPLOY_METHOD_KUBERNETES}, {DEPLOY_METHOD_DOCKER_COMPOSE}"',
                'exit 1'
            ]
            image = 'alpine:3.18'
        
        # Build only rules for branch matching
        only_rules = []
        for branch in branches:
            # Convert wildcard patterns to regex
            if '*' in branch or '/' in branch:
                # Handle patterns like "develop-*", "feature/*", "release/*"
                pattern = branch.replace('*', '.*').replace('/', '\\/')
                only_rules.append(f'/{pattern}/')
            else:
                # Exact branch match
                only_rules.append(branch)
        
        # Build needs list with all publish jobs for this component
        needs = []
        build_config = component.get('build', {})
        outputs = build_config.get('outputs', [])
        
        if outputs:
            # Add dependency on all publish jobs for this component in this environment
            for output_type in outputs:
                needs.append(f'publish:{component_name}:{output_type}:{env_name}')
        else:
            # If no outputs, depend on build job
            needs.append(f'build:{component_name}')
        
        job = {
            'stage': STAGE_DEPLOY,
            'image': image,
            'script': script,
            'needs': needs,
            'only': {
                'refs': only_rules
            },
            'environment': {
                'name': env_name,
                'action': 'start'
            }
        }
        
        return job
    
    def get_kubernetes_deploy_script(
        self,
        component: Dict[str, Any],
        env_name: str,
        env_config: Dict[str, Any]
    ) -> List[str]:
        """
        Generate Kubernetes deployment script.
        
        Args:
            component: Component configuration
            env_name: Environment name
            env_config: Environment configuration
            
        Returns:
            List of script commands
        """
        component_name = component.get('name')
        
        # Get destination configuration
        destinations = env_config.get('destination', [])
        k8s_dest = next((d for d in destinations if d.get('type') == 'kubernetes'), {})
        
        namespace = k8s_dest.get('namespace', f'${{ORGANIZATION}}-${{PROJECT_NAME}}-{env_name}')
        context = k8s_dest.get('context', '')
        
        script = [
            f'# Deploy {component_name} to {env_name}',
            f'echo "Deploying to namespace: {namespace}"',
        ]
        
        # Add context flag if specified
        context_flag = f'--context {context}' if context else ''
        
        # Create namespace if it doesn't exist
        script.append(f'kubectl create namespace {namespace} {context_flag} --dry-run=client -o yaml | kubectl apply {context_flag} -f -')
        
        # Apply Kubernetes resources
        script.append(f'kubectl apply {context_flag} -n {namespace} -f k8s/{component_name}/')
        
        # Wait for deployment
        script.append(f'kubectl rollout status {context_flag} -n {namespace} deployment/{component_name}')
        
        return script
    
    def get_docker_compose_deploy_script(
        self,
        component: Dict[str, Any],
        env_name: str,
        env_config: Dict[str, Any]
    ) -> List[str]:
        """
        Generate Docker Compose deployment script.
        
        Args:
            component: Component configuration
            env_name: Environment name
            env_config: Environment configuration
            
        Returns:
            List of script commands
        """
        component_name = component.get('name')
        
        # Get docker-compose destination configuration
        destinations = env_config.get('destination', [])
        compose_dest = next((d for d in destinations if d.get('type') == 'dockerCompose'), {})
        
        # Get docker-compose configuration
        host = compose_dest.get('host', 'localhost')
        user = compose_dest.get('user', 'deployer')
        compose_path = compose_dest.get('composePath', f'/opt/apps/${{PROJECT_NAME}}')
        compose_file = compose_dest.get('composeFile', 'docker-compose.yml')
        service = compose_dest.get('service', component_name)
        
        script = [
            f'# Deploy {component_name} to {env_name} using Docker Compose',
            f'echo "Deploying to host: {host}"',
            f'echo "Compose path: {compose_path}"',
            f'echo "Service: {service}"',
            '',
            '# Install SSH client if not present',
            'apk add --no-cache openssh-client',
            '',
            '# Setup SSH key',
            'mkdir -p ~/.ssh',
            'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
            'chmod 600 ~/.ssh/id_rsa',
            f'ssh-keyscan -H {host} >> ~/.ssh/known_hosts',
            '',
            f'# Copy docker-compose file to remote host',
            f'scp {compose_file} {user}@{host}:{compose_path}/',
            '',
            f'# Deploy using docker-compose',
            f'ssh {user}@{host} "cd {compose_path} && docker-compose -f {compose_file} pull {service}"',
            f'ssh {user}@{host} "cd {compose_path} && docker-compose -f {compose_file} up -d {service}"',
            '',
            f'# Verify deployment',
            f'ssh {user}@{host} "cd {compose_path} && docker-compose -f {compose_file} ps {service}"',
        ]
        
        return script
