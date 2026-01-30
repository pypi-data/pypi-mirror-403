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
    
    def generate_publish_jobs(self, components: List[Dict[str, Any]], environment: str, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Generate publish jobs for all components.
        
        Args:
            components: List of component configurations
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            Dictionary of publish job definitions
        """
        logger.debug(f"Generating publish jobs for {len(components)} component(s) in environment {environment}")
        
        from utils.output_resolver import OutputResolver
        output_resolver = OutputResolver()
        
        publish_jobs = {}
        
        for component in components:
            component_name = component.get('name')
            if not component_name:
                continue
            
            # Get outputs
            build_config = component.get('build', {})
            outputs = build_config.get('outputs', [])
            
            if not outputs:
                logger.debug(f"Component {component_name} has no outputs configured")
                continue
            
            # Resolve each output to registry server
            for output_type in outputs:
                try:
                    server_config = output_resolver.resolve_output(
                        output_type=output_type,
                        component=component,
                        environment=environment,
                        config=config
                    )
                    
                    job_name = f"publish:{component_name}:{output_type}:{environment}"
                    publish_jobs[job_name] = self.create_publish_job(
                        component,
                        output_type,
                        server_config,
                        environment
                    )
                    logger.debug(f"Generated publish job: {job_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to resolve output {output_type} for {component_name} in {environment}: {e}")
                    continue
        
        return publish_jobs
    
    def create_publish_job(
        self,
        component: Dict[str, Any],
        output_type: str,
        server_config: Dict[str, Any],
        environment: str
    ) -> Dict[str, Any]:
        """
        Create publish job for a component output.
        
        Args:
            component: Component configuration
            output_type: Output type (docker, artifact, helm)
            server_config: Resolved server configuration
            environment: Target environment
            
        Returns:
            Publish job definition
        """
        component_name = component.get('name')
        
        # Build script based on output type
        if output_type == 'docker':
            script = self._create_docker_publish_script(component, server_config)
            image = 'docker:24.0.5'
            services = ['docker:24.0.5-dind']
        elif output_type == 'artifact':
            script = self._create_artifact_publish_script(component, server_config)
            image = self.get_build_image(component.get('type', 'docker'))
            services = None
        elif output_type == 'helm':
            script = self._create_helm_publish_script(component, server_config)
            image = 'alpine/helm:3.13.0'
            services = None
        else:
            logger.warning(f"Unknown output type: {output_type}")
            script = [f'echo "Unknown output type: {output_type}"', 'exit 1']
            image = DEFAULT_DOCKER_IMAGE
            services = None
        
        job = {
            'stage': STAGE_PUBLISH,
            'image': image,
            'script': script,
            'needs': [f'build:{component_name}']
        }
        
        if services:
            job['services'] = services
        
        return job
    
    def _create_docker_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create Docker publish script."""
        component_name = component.get('name')
        push_url = server_config.get('pushUrl', '')
        credentials_user = server_config.get('credentialsUser', 'REGISTRY_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'REGISTRY_PASSWORD')
        image_name = component_name
        
        script = [
            f'# Login to Docker registry',
            f'echo "${{{credentials_password}}}" | docker login {push_url} -u "${{{credentials_user}}}" --password-stdin',
            f'# Tag and push image',
            f'docker tag ${{PROJECT_NAME}}-{component_name}:${{CI_COMMIT_SHORT_SHA}} {push_url}/{image_name}:${{CI_COMMIT_SHORT_SHA}}',
            f'docker push {push_url}/{image_name}:${{CI_COMMIT_SHORT_SHA}}',
        ]
        
        return script
    
    def _create_artifact_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create artifact publish script."""
        component_type = component.get('type', 'docker')
        
        if component_type in ['java', 'spring', 'maven']:
            return self._create_maven_publish_script(component, server_config)
        elif component_type == 'gradle':
            return self._create_gradle_publish_script(component, server_config)
        elif component_type in ['npm', 'node', 'vue', 'react', 'angular']:
            return self._create_npm_publish_script(component, server_config)
        elif component_type == 'python':
            return self._create_python_publish_script(component, server_config)
        else:
            return [
                f'echo "Artifact publish not implemented for type: {component_type}"',
                'exit 1'
            ]
    
    def _create_maven_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create Maven artifact publish script."""
        # Use publishUrl for maven deploy (releases only)
        publish_url = server_config.get('publishUrl') or server_config.get('url')
        credentials_user = server_config.get('credentialsUser', 'NEXUS_CREDENTIALS_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'NEXUS_CREDENTIALS_PASSWORD')
        
        script = [
            f'# Publish Maven artifact to releases repository',
            f'mvn deploy -DskipTests -DaltDeploymentRepository=nexus-releases::default::{publish_url} -Dusername="${{{credentials_user}}}" -Dpassword="${{{credentials_password}}}"',
        ]
        
        return script
    
    def _create_gradle_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create Gradle artifact publish script."""
        # Use publishUrl for gradle publish (releases only)
        publish_url = server_config.get('publishUrl') or server_config.get('url')
        credentials_user = server_config.get('credentialsUser', 'NEXUS_CREDENTIALS_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'NEXUS_CREDENTIALS_PASSWORD')
        
        script = [
            f'# Publish Gradle artifact to releases repository',
            f'export GRADLE_PUBLISH_URL={publish_url}',
            f'export GRADLE_PUBLISH_USERNAME="${{{credentials_user}}}"',
            f'export GRADLE_PUBLISH_PASSWORD="${{{credentials_password}}}"',
            f'gradle publish -Dorg.gradle.internal.publish.checksums.insecure=true',
        ]
        
        return script
    
    def _create_npm_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create NPM artifact publish script."""
        # Use publishUrl for npm publish, not registryUrl
        publish_url = server_config.get('publishUrl') or server_config.get('url')
        credentials_user = server_config.get('credentialsUser', 'NEXUS_CREDENTIALS_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'NEXUS_CREDENTIALS_PASSWORD')
        
        script = [
            f'# Configure NPM publish registry',
            f'npm config set registry {publish_url}',
            f'npm config set //{publish_url.replace("https://", "").replace("http://", "")}/:_authToken="${{{credentials_password}}}"',
            f'# Publish NPM package',
            f'npm publish',
        ]
        
        return script
    
    def _create_python_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create Python artifact publish script."""
        url = server_config.get('url', '')
        credentials_user = server_config.get('credentialsUser', 'NEXUS_CREDENTIALS_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'NEXUS_CREDENTIALS_PASSWORD')
        
        script = [
            f'# Publish Python package',
            f'pip install twine',
            f'python setup.py sdist bdist_wheel',
            f'twine upload --repository-url {url} -u "${{{credentials_user}}}" -p "${{{credentials_password}}}" dist/*',
        ]
        
        return script
    
    def _create_helm_publish_script(
        self,
        component: Dict[str, Any],
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Create Helm chart publish script."""
        component_name = component.get('name')
        url = server_config.get('url', '')
        credentials_user = server_config.get('credentialsUser', 'NEXUS_CREDENTIALS_USERNAME')
        credentials_password = server_config.get('credentialsPassword', 'NEXUS_CREDENTIALS_PASSWORD')
        
        script = [
            f'# Package Helm chart',
            f'helm package charts/{component_name}',
            f'# Publish Helm chart',
            f'curl -u "${{{credentials_user}}}:${{{credentials_password}}}" {url} --upload-file {component_name}-*.tgz',
        ]
        
        return script
    
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
