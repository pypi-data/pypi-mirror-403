"""
ManagedFileHandler module for GitLab CI/CD Migration system.

This module provides handling of managed files (configuration files that need to be
mounted or configured in CI/CD jobs).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from utils.managed_file_generators import ManagedFileGenerators
from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class ManagedFileHandler:
    """
    Handler for managed files in GitLab CI/CD pipelines.
    
    This class coordinates managed file operations including:
    - Generating file content via ManagedFileGenerators
    - Creating ConfigMap definitions for file mounting
    - Generating environment variable exports
    - Supporting multiple file types and formats
    
    Responsibilities:
    - Coordinate file content generation
    - Create ConfigMap mount configurations
    - Generate environment variable exports
    """
    
    def __init__(self):
        """Initialize managed file handler."""
        logger.debug("ManagedFileHandler initialized")
        self.generators = ManagedFileGenerators()
    
    def generate_npmrc(self, config: Dict[str, Any]) -> str:
        """
        Generate .npmrc file content from configuration.
        
        Args:
            config: NPM configuration dictionary
        
        Returns:
            .npmrc file content as string
        """
        return self.generators.generate_npmrc(config)
    
    def generate_maven_settings(self, config: Dict[str, Any]) -> str:
        """
        Generate Maven settings.xml file content from configuration.
        
        Args:
            config: Maven configuration dictionary
        
        Returns:
            settings.xml file content as string
        """
        return self.generators.generate_maven_settings(config)
    
    def generate_aws_credentials(self, config: Dict[str, Any]) -> str:
        """
        Generate AWS credentials file content from configuration.
        
        Args:
            config: AWS credentials configuration
        
        Returns:
            AWS credentials file content as string
        """
        return self.generators.generate_aws_credentials(config)
    
    def generate_aws_config(self, config: Dict[str, Any]) -> str:
        """
        Generate AWS config file content from configuration.
        
        Args:
            config: AWS config configuration
        
        Returns:
            AWS config file content as string
        """
        return self.generators.generate_aws_config(config)
    
    def generate_docker_daemon_config(self, config: Dict[str, Any]) -> str:
        """
        Generate Docker daemon.json file content from configuration.
        
        Args:
            config: Docker daemon configuration
        
        Returns:
            daemon.json file content as string
        """
        return self.generators.generate_docker_daemon_config(config)
    
    def generate_kubeconfig(self, config: Dict[str, Any]) -> str:
        """
        Generate kubeconfig file content from configuration.
        
        Args:
            config: Kubeconfig configuration
        
        Returns:
            kubeconfig file content as string (YAML)
        """
        return self.generators.generate_kubeconfig(config)
    
    def generate_configmap_mount(
        self,
        file_type: str,
        file_path: str,
        configmap_name: str
    ) -> Dict[str, Any]:
        """
        Generate ConfigMap mount configuration for GitLab CI job.
        
        Args:
            file_type: Type of file (.npmrc, settings.xml, etc.)
            file_path: Path where file should be mounted in container
            configmap_name: Name of the ConfigMap
        
        Returns:
            ConfigMap mount configuration dictionary
        """
        mount_config = {
            'name': configmap_name,
            'mountPath': file_path,
            'subPath': Path(file_path).name
        }
        
        logger.debug(f"Generated ConfigMap mount for {file_type} at {file_path}")
        return mount_config
    
    def generate_env_exports(self, managed_files: Dict[str, Any]) -> List[str]:
        """
        Generate environment variable export commands for managed files.
        
        Args:
            managed_files: Dictionary of managed file configurations
        
        Returns:
            List of export commands as strings
        """
        with OperationLogger(logger, "generate environment variable exports"):
            exports = []
            
            # NPM config
            if 'npmrc' in managed_files:
                npmrc_path = managed_files['npmrc'].get('path', '/root/.npmrc')
                exports.append(f"export NPM_CONFIG_USERCONFIG={npmrc_path}")
            
            # Maven settings
            if 'mavenSettings' in managed_files:
                settings_path = managed_files['mavenSettings'].get('path', '/root/.m2/settings.xml')
                exports.append(f"export MAVEN_SETTINGS={settings_path}")
            
            # AWS credentials
            if 'awsCredentials' in managed_files:
                creds_path = managed_files['awsCredentials'].get('path', '/root/.aws/credentials')
                exports.append(f"export AWS_SHARED_CREDENTIALS_FILE={creds_path}")
            
            # AWS config
            if 'awsConfig' in managed_files:
                config_path = managed_files['awsConfig'].get('path', '/root/.aws/config')
                exports.append(f"export AWS_CONFIG_FILE={config_path}")
            
            # Kubeconfig
            if 'kubeconfig' in managed_files:
                kubeconfig_path = managed_files['kubeconfig'].get('path', '/root/.kube/config')
                exports.append(f"export KUBECONFIG={kubeconfig_path}")
            
            # Docker config
            if 'dockerDaemon' in managed_files:
                docker_config_path = managed_files['dockerDaemon'].get('path', '/etc/docker/daemon.json')
                exports.append(f"export DOCKER_CONFIG_FILE={docker_config_path}")
            
            logger.debug(f"Generated {len(exports)} environment variable export(s)")
            return exports
