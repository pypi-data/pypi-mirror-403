"""
GitLabCIJobsBuilder module for build and publish job generation.

This module handles the creation of build and publish jobs for components.
"""

import logging
from typing import Any, Dict, List

from utils.constants import (
    STAGE_BUILD,
    STAGE_PUBLISH,
    DEFAULT_DOCKER_IMAGE,
)
from utils.logging_config import get_logger
from utils.managed_file_handler import ManagedFileHandler

logger = get_logger(__name__)


class GitLabCIJobsBuilder:
    """
    Builder for GitLab CI build and publish jobs.
    
    This class generates build and publish jobs for components with:
    - Appropriate Docker images based on component type
    - Build commands from configuration
    - Change detection conditional logic
    - Artifact storage
    - Registry publishing
    """
    
    def __init__(self):
        """Initialize jobs builder."""
        self.managed_file_handler = ManagedFileHandler()
        logger.debug("GitLabCIJobsBuilder initialized")
    
    def generate_build_jobs(self, components: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Generate build jobs for all components.
        
        Creates a build job for each component with:
        - Appropriate Docker image based on component type
        - Build commands from configuration
        - Change detection conditional logic
        - Artifact storage
        
        Args:
            components: List of component configurations
            
        Returns:
            Dictionary of build job definitions keyed by job name
        """
        logger.debug(f"Generating build jobs for {len(components)} component(s)")
        
        build_jobs = {}
        
        for component in components:
            component_name = component.get('name')
            if not component_name:
                logger.warning("Skipping component without name")
                continue
            
            job_name = f"build:{component_name}"
            build_jobs[job_name] = self.create_build_job(component)
            logger.debug(f"Generated build job: {job_name}")
        
        return build_jobs
    
    def create_build_job(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create build job for a component.
        
        Args:
            component: Component configuration
            
        Returns:
            Build job definition
        """
        component_name = component.get('name')
        component_type = component.get('type', 'docker')
        component_path = component.get('path', '.')
        
        # Determine Docker image based on component type
        image = self.get_build_image(component_type)
        
        # Get build commands
        build_config = component.get('build', {})
        commands = build_config.get('commands', [])
        
        # Build script
        script = []
        
        # Add managed file environment exports if configured
        managed_files = component.get('managedFiles', {})
        if managed_files:
            env_exports = self.managed_file_handler.generate_env_exports(managed_files)
            if env_exports:
                script.append('# Setup managed files')
                script.extend(env_exports)
                script.append('')
        
        # Change to component directory if specified
        if component_path and component_path != '.':
            script.append(f'cd {component_path}')
        
        # Add build commands
        if commands:
            script.extend(commands)
        else:
            # Default build commands based on type
            script.extend(self.get_default_build_commands(component_type))
        
        # Build Docker image if artifacts type is docker
        artifacts = build_config.get('artifacts', {})
        if artifacts.get('type') == 'docker':
            docker_config = artifacts.get('docker', {})
            dockerfile = docker_config.get('dockerfile', 'Dockerfile')
            context = docker_config.get('context', '.')
            build_args = docker_config.get('buildArgs', [])
            
            # Construct docker build command
            docker_cmd = f'docker build -f {dockerfile} -t ${{PROJECT_NAME}}-{component_name}:${{CI_COMMIT_SHORT_SHA}}'
            
            # Add build args
            for arg in build_args:
                docker_cmd += f' --build-arg {arg}'
            
            docker_cmd += f' {context}'
            script.append(docker_cmd)
        
        # Create job definition
        job = {
            'stage': STAGE_BUILD,
            'image': image,
            'services': ['docker:24.0.5-dind'] if artifacts.get('type') == 'docker' else None,
            'script': script,
            'needs': []
        }
        
        # Add ConfigMap volumes for managed files if configured
        if managed_files:
            volumes = []
            for file_type, file_config in managed_files.items():
                if file_config.get('configMapName'):
                    mount_path = file_config.get('path')
                    configmap_name = file_config.get('configMapName')
                    if mount_path and configmap_name:
                        volumes.append({
                            'name': configmap_name,
                            'mountPath': mount_path,
                            'subPath': mount_path.split('/')[-1]
                        })
            
            if volumes:
                job['volumes'] = volumes
        
        # Add change detection dependency if enabled
        if self.is_change_detection_enabled_for_component(component):
            job['needs'].append('detect:changes')
            # Add conditional execution based on change detection
            job['rules'] = [
                {
                    'if': f'$CHANGED_COMPONENTS =~ /{component_name}/',
                    'when': 'always'
                },
                {
                    'when': 'never'
                }
            ]
        else:
            job['needs'].append('validate:config')
        
        # Remove None values
        job = {k: v for k, v in job.items() if v is not None}
        
        return job
    
    def generate_publish_jobs(self, components: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Generate publish jobs for all components.
        
        Args:
            components: List of component configurations
            
        Returns:
            Dictionary of publish job definitions
        """
        logger.debug(f"Generating publish jobs for {len(components)} component(s)")
        
        publish_jobs = {}
        
        for component in components:
            component_name = component.get('name')
            if not component_name:
                continue
            
            # Get destinations
            build_config = component.get('build', {})
            destinations = build_config.get('destination', [])
            
            # Create publish job for each destination
            for idx, destination in enumerate(destinations):
                dest_type = destination.get('type', 'dockerRegistry')
                dest_name = destination.get('name', f'dest{idx}')
                
                job_name = f"publish:{component_name}:{dest_name}"
                publish_jobs[job_name] = self.create_publish_job(
                    component,
                    destination,
                    dest_name
                )
                logger.debug(f"Generated publish job: {job_name}")
        
        return publish_jobs
    
    def create_publish_job(
        self,
        component: Dict[str, Any],
        destination: Dict[str, Any],
        dest_name: str
    ) -> Dict[str, Any]:
        """
        Create publish job for a component destination.
        
        Args:
            component: Component configuration
            destination: Destination configuration
            dest_name: Destination name
            
        Returns:
            Publish job definition
        """
        component_name = component.get('name')
        registry_url = destination.get('url', '')
        image_name = destination.get('imageName', component_name)
        tags = destination.get('tags', ['latest'])
        
        script = [
            f'# Login to registry',
            f'echo "$REGISTRY_PASSWORD" | docker login {registry_url} -u "$REGISTRY_USERNAME" --password-stdin',
            f'# Tag and push image',
        ]
        
        # Tag and push for each tag
        for tag in tags:
            full_image = f'{registry_url}/{image_name}:{tag}'
            script.append(f'docker tag ${{PROJECT_NAME}}-{component_name}:${{CI_COMMIT_SHORT_SHA}} {full_image}')
            script.append(f'docker push {full_image}')
        
        job = {
            'stage': STAGE_PUBLISH,
            'image': DEFAULT_DOCKER_IMAGE,
            'services': ['docker:24.0.5-dind'],
            'script': script,
            'needs': [f'build:{component_name}']
        }
        
        return job
    
    def get_build_image(self, component_type: str) -> str:
        """
        Get appropriate Docker image for component type.
        
        Args:
            component_type: Component type (vue, maven, npm, etc.)
            
        Returns:
            Docker image name
        """
        image_map = {
            'vue': 'node:18-alpine',
            'npm': 'node:18-alpine',
            'maven': 'maven:3.9-eclipse-temurin-17',
            'gradle': 'gradle:8.4-jdk17',
            'python': 'python:3.11-slim',
            'docker': DEFAULT_DOCKER_IMAGE,
        }
        
        return image_map.get(component_type, DEFAULT_DOCKER_IMAGE)
    
    def get_default_build_commands(self, component_type: str) -> List[str]:
        """
        Get default build commands for component type.
        
        Args:
            component_type: Component type
            
        Returns:
            List of build commands
        """
        commands_map = {
            'vue': [
                'npm ci',
                'npm run build',
            ],
            'npm': [
                'npm ci',
                'npm run build',
            ],
            'maven': [
                'mvn clean package -DskipTests',
            ],
            'gradle': [
                'gradle clean build -x test',
            ],
            'python': [
                'pip install -r requirements.txt',
                'python setup.py build',
            ],
        }
        
        return commands_map.get(component_type, ['echo "No default build commands"'])
    
    def is_change_detection_enabled_for_component(self, component: Dict[str, Any]) -> bool:
        """
        Check if change detection is enabled for a component.
        
        Args:
            component: Component configuration
            
        Returns:
            True if change detection is enabled for this component
        """
        change_detection = component.get('changeDetection', {})
        return change_detection.get('enabled', False)
