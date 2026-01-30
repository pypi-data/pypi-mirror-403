"""
Registry configuration helper for GitLab CI/CD Migration system.

This module provides utilities to access registry configurations per service and environment.
"""

import logging
from typing import Dict, Any, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


class RegistryConfigHelper:
    """
    Helper class to access registry configurations per service and environment.
    
    Supports:
    - npmServer
    - mavenServer
    - gradleServer
    - pypiServer
    - dockerServer
    - rawServer
    
    Each service can have different configurations per environment (dev, stg, ese).
    """
    
    @staticmethod
    def get_docker_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get Docker registry configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Docker registry configuration with pushUrl, pullUrl, credentials
            None if not configured
        """
        registry = config.get('registry', {})
        docker_server = registry.get('dockerServer', {})
        env_config = docker_server.get(environment)
        
        if env_config:
            logger.debug(f"Found Docker registry config for environment '{environment}'")
        else:
            logger.warning(f"No Docker registry config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_npm_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get NPM registry configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            NPM registry configuration with registryUrl, publishUrl, username, password
            None if not configured
        """
        registry = config.get('registry', {})
        npm_server = registry.get('npmServer', {})
        env_config = npm_server.get(environment)
        
        if env_config:
            logger.debug(f"Found NPM registry config for environment '{environment}'")
        else:
            logger.warning(f"No NPM registry config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_npm_registry_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get NPM registry URL for npm install operations.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            NPM registry URL or None
        """
        npm_config = RegistryConfigHelper.get_npm_config(config, environment)
        if not npm_config:
            return None
        
        # Support both old 'url' and new 'registryUrl' fields
        return npm_config.get('registryUrl') or npm_config.get('url')
    
    @staticmethod
    def get_npm_publish_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get NPM publish URL for npm publish operations.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            NPM publish URL or None (falls back to registryUrl if publishUrl not specified)
        """
        npm_config = RegistryConfigHelper.get_npm_config(config, environment)
        if not npm_config:
            return None
        
        # Use publishUrl if available, otherwise fall back to registryUrl or url
        return npm_config.get('publishUrl') or npm_config.get('registryUrl') or npm_config.get('url')
    
    @staticmethod
    def get_maven_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get Maven repository configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Maven repository configuration with repositoryUrl, publishUrl, username, password
            None if not configured
        """
        registry = config.get('registry', {})
        maven_server = registry.get('mavenServer', {})
        env_config = maven_server.get(environment)
        
        if env_config:
            logger.debug(f"Found Maven repository config for environment '{environment}'")
        else:
            logger.warning(f"No Maven repository config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_maven_repository_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Maven repository URL for downloading dependencies.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Maven repository URL or None (falls back to publishUrl if repositoryUrl not specified)
        """
        maven_config = RegistryConfigHelper.get_maven_config(config, environment)
        if not maven_config:
            return None
        
        # Use repositoryUrl if available, otherwise fall back to publishUrl
        return maven_config.get('repositoryUrl') or maven_config.get('publishUrl')
    
    @staticmethod
    def get_maven_releases_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Maven releases URL for publishing release artifacts.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Maven releases URL or None
        """
        maven_config = RegistryConfigHelper.get_maven_config(config, environment)
        return maven_config.get('publishUrl') if maven_config else None
    
    @staticmethod
    def get_gradle_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get Gradle repository configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Gradle repository configuration with repositoryUrl, publishUrl, username, password
            None if not configured
        """
        registry = config.get('registry', {})
        gradle_server = registry.get('gradleServer', {})
        env_config = gradle_server.get(environment)
        
        if env_config:
            logger.debug(f"Found Gradle repository config for environment '{environment}'")
        else:
            logger.warning(f"No Gradle repository config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_gradle_repository_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Gradle repository URL for downloading dependencies.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Gradle repository URL or None (falls back to publishUrl if repositoryUrl not specified)
        """
        gradle_config = RegistryConfigHelper.get_gradle_config(config, environment)
        if not gradle_config:
            return None
        
        # Use repositoryUrl if available, otherwise fall back to publishUrl
        return gradle_config.get('repositoryUrl') or gradle_config.get('publishUrl')
    
    @staticmethod
    def get_gradle_releases_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Gradle releases URL for publishing release artifacts.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Gradle releases URL or None
        """
        gradle_config = RegistryConfigHelper.get_gradle_config(config, environment)
        return gradle_config.get('publishUrl') if gradle_config else None
    
    @staticmethod
    def get_pypi_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get PyPI repository configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            PyPI repository configuration with url, username, password
            None if not configured
        """
        registry = config.get('registry', {})
        pypi_server = registry.get('pypiServer', {})
        env_config = pypi_server.get(environment)
        
        if env_config:
            logger.debug(f"Found PyPI repository config for environment '{environment}'")
        else:
            logger.warning(f"No PyPI repository config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_raw_config(config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get raw/generic artifacts repository configuration for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Raw repository configuration with url, username, password
            None if not configured
        """
        registry = config.get('registry', {})
        raw_server = registry.get('rawServer', {})
        env_config = raw_server.get(environment)
        
        if env_config:
            logger.debug(f"Found raw repository config for environment '{environment}'")
        else:
            logger.warning(f"No raw repository config found for environment '{environment}'")
        
        return env_config
    
    @staticmethod
    def get_docker_push_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Docker push URL for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Docker push URL or None
        """
        docker_config = RegistryConfigHelper.get_docker_config(config, environment)
        return docker_config.get('pushUrl') if docker_config else None
    
    @staticmethod
    def get_docker_pull_url(config: Dict[str, Any], environment: str) -> Optional[str]:
        """
        Get Docker pull URL for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Docker pull URL or None
        """
        docker_config = RegistryConfigHelper.get_docker_config(config, environment)
        return docker_config.get('pullUrl') if docker_config else None
    
    @staticmethod
    def get_docker_credentials(config: Dict[str, Any], environment: str) -> Dict[str, Optional[str]]:
        """
        Get Docker registry credentials for environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Dictionary with username, password, accessKeyId, secretAccessKey, region
        """
        docker_config = RegistryConfigHelper.get_docker_config(config, environment)
        
        if not docker_config:
            return {}
        
        # Standard credentials (username/password)
        credentials = {
            'username': docker_config.get('username'),
            'password': docker_config.get('password'),
        }
        
        # AWS ECR credentials
        if 'accessKeyId' in docker_config:
            credentials['accessKeyId'] = docker_config.get('accessKeyId')
            credentials['secretAccessKey'] = docker_config.get('secretAccessKey')
            credentials['region'] = docker_config.get('region')
        
        return credentials
