"""
Artifact resolution system for GitLab CI/CD Migration.

Queries Docker registries to find the last successful artifact for unchanged
components, supporting generic Docker Registry V2 API, AWS ECR, and DockerHub.
"""

import logging
from typing import List, Dict, Any, Optional

from utils.exceptions import ArtifactNotFoundError
from utils.registry_clients import RegistryClient, ArtifactResolverError
from utils.docker_registry_client import DockerRegistryClient
from utils.ecr_registry_client import ECRRegistryClient
from utils.dockerhub_registry_client import DockerHubRegistryClient
from utils.logging_config import get_logger
from utils.constants import (
    REGISTRY_TYPE_DOCKER,
    REGISTRY_TYPE_ECR,
    REGISTRY_TYPE_DOCKERHUB,
)


logger = get_logger(__name__)


class ArtifactResolver:
    """
    Resolve last successful artifacts from Docker registries.
    
    Queries registries to find the most recent successful artifact for
    unchanged components, supporting generic Docker Registry V2 API, AWS ECR, and DockerHub.
    
    Examples:
        >>> resolver = ArtifactResolver()
        >>> config = {
        ...     'registry': {
        ...         'dockerServer': {
        ...             'stg': {
        ...                 'pullUrl': 'nexus.example.com:8082',
        ...                 'username': 'admin',
        ...                 'password': 'secret'
        ...             }
        ...         }
        ...     }
        ... }
        >>> artifact = resolver.get_last_successful_artifact('frontend', 'stg', config)
        >>> print(f"Using artifact: {artifact}")
    """
    
    def __init__(self):
        """Initialize ArtifactResolver."""
        logger.debug("Initialized ArtifactResolver")
    
    def get_last_successful_artifact(
        self,
        component: str,
        environment: str,
        config: Dict[str, Any],
    ) -> str:
        """
        Retrieve last successful artifact tag for a component.
        
        Searches the configured registry for the most recent successful
        artifact tag. The tag format is expected to be:
        {version}.{branch}.{build_number} or {branch}-latest
        
        Args:
            component: Component name
            environment: Environment name
            config: Full configuration dictionary
            
        Returns:
            Full artifact tag (registry/image:tag)
            
        Raises:
            ArtifactNotFoundError: If no successful artifact exists
            ArtifactResolverError: If registry query fails
            
        Examples:
            >>> resolver = ArtifactResolver()
            >>> artifact = resolver.get_last_successful_artifact('backend', 'stg', config)
            >>> print(artifact)
        """
        logger.info(f"Resolving last successful artifact for component '{component}' in environment '{environment}'")
        
        # Get registry configuration for this environment
        registry_config = self._get_registry_config(config, environment)
        if not registry_config:
            raise ArtifactResolverError(
                f"No artifact registry configured for environment '{environment}'",
                component=component,
            )
        
        # Get component configuration
        component_config = self._get_component_config(component, config)
        if not component_config:
            raise ArtifactResolverError(
                f"Component '{component}' not found in configuration",
                component=component,
            )
        
        # Get image name from component configuration
        image_name = self._get_image_name(component_config, config)
        
        # Create registry client
        client = self._create_registry_client(registry_config)
        
        # List all tags for the image
        try:
            tags = client.list_tags(image_name)
        except ArtifactResolverError as e:
            raise ArtifactNotFoundError(
                f"Failed to list tags for component '{component}': {str(e)}",
                component=component,
                environment=environment,
                registry_url=registry_config.get('url'),
            )
        
        if not tags:
            raise ArtifactNotFoundError(
                f"No artifacts found for component '{component}' in registry",
                component=component,
                environment=environment,
                registry_url=registry_config.get('url'),
                searched_tags=[],
            )
        
        # Filter tags for the target environment/branch
        environment_branch = self._get_environment_branch(environment, config)
        matching_tags = self._filter_tags_by_branch(tags, environment_branch)
        
        if not matching_tags:
            raise ArtifactNotFoundError(
                f"No artifacts found for component '{component}' matching branch '{environment_branch}'",
                component=component,
                environment=environment,
                registry_url=registry_config.get('url'),
                searched_tags=tags,
            )
        
        # Get the most recent tag
        latest_tag = self._get_latest_tag(matching_tags)
        
        # Build full artifact reference
        registry_url = registry_config.get('url', '').rstrip('/')
        full_artifact = f"{registry_url}/{image_name}:{latest_tag}"
        
        logger.info(f"Resolved artifact for '{component}': {full_artifact}")
        
        return full_artifact

    
    def _get_registry_config(self, config: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Get artifact registry configuration from config.
        
        Uses the Docker pull URL from registry.dockerServer for the specified environment.
        
        Args:
            config: Full configuration dictionary
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Registry configuration or None if not configured
        """
        from utils.registry_config_helper import RegistryConfigHelper
        
        # Get Docker config for environment
        docker_config = RegistryConfigHelper.get_docker_config(config, environment)
        
        if not docker_config:
            logger.warning(f"No Docker registry config found for environment '{environment}'")
            return None
        
        # Build registry config for artifact resolution
        pull_url = docker_config.get('pullUrl')
        if not pull_url:
            logger.warning(f"No Docker pull URL configured for environment '{environment}'")
            return None
        
        # Determine registry type (ECR or standard Docker registry)
        registry_type = 'ecr' if 'ecr' in pull_url else 'dockerRegistry'
        
        registry_config = {
            'type': registry_type,
            'url': pull_url,
            'credentials': {}
        }
        
        # Add credentials
        if registry_type == REGISTRY_TYPE_ECR:
            registry_config['credentials'] = {
                'region': docker_config.get('region'),
                'accessKeyId': docker_config.get('accessKeyId'),
                'secretAccessKey': docker_config.get('secretAccessKey'),
            }
        else:
            registry_config['credentials'] = {
                'username': docker_config.get('username'),
                'password': docker_config.get('password'),
            }
        
        return registry_config
    
    def _get_component_config(self, component_name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get component configuration by name.
        
        Args:
            component_name: Name of the component
            config: Full configuration dictionary
            
        Returns:
            Component configuration or None if not found
        """
        components = config.get('components', [])
        for component in components:
            if component.get('name') == component_name:
                return component
        return None
    
    def _get_image_name(self, component_config: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Get Docker image name for component.
        
        Args:
            component_config: Component configuration
            config: Full configuration dictionary
            environment: Target environment (dev, stg, ese)
            
        Returns:
            Image name (without registry URL and tag)
        """
        # Construct from project and component name
        project_name = config.get('project', {}).get('name', 'unknown')
        component_name = component_config.get('name', 'unknown')
        
        return f"{project_name}/{component_name}"
    
    def _get_environment_branch(self, environment: str, config: Dict[str, Any]) -> str:
        """
        Get the primary branch for an environment.
        
        Args:
            environment: Environment name
            config: Full configuration dictionary
            
        Returns:
            Branch name (e.g., 'develop', 'staging', 'main')
        """
        environments = config.get('environments', {})
        env_config = environments.get(environment, {})
        branches = env_config.get('branches', [])
        
        if branches:
            # Return first branch (primary branch for environment)
            first_branch = branches[0]
            # Remove 'origin/' prefix if present
            return first_branch.replace('origin/', '')
        
        # Default branch mapping
        default_branches = {
            'dev': 'develop',
            'stg': 'develop',
            'ese': 'main',
        }
        
        return default_branches.get(environment, 'main')

    
    def _filter_tags_by_branch(self, tags: List[str], branch: str) -> List[str]:
        """
        Filter tags that match the specified branch.
        
        Tag format: {version}.{branch}.{build_number} or {branch}-latest
        
        Args:
            tags: List of all tags
            branch: Branch name to filter by
            
        Returns:
            List of tags matching the branch
        """
        matching_tags = []
        
        for tag in tags:
            # Check for {branch}-latest format
            if tag == f"{branch}-latest":
                matching_tags.append(tag)
                continue
            
            # Check for {version}.{branch}.{build_number} format
            parts = tag.split('.')
            if len(parts) >= 3:
                # Branch is the second-to-last part before build number
                tag_branch = parts[-2]
                if tag_branch == branch:
                    matching_tags.append(tag)
        
        logger.debug(f"Filtered {len(matching_tags)} tags matching branch '{branch}' from {len(tags)} total tags")
        return matching_tags
    
    def _get_latest_tag(self, tags: List[str]) -> str:
        """
        Get the most recent tag from a list of tags.
        
        Prioritizes tags with build numbers over -latest tags.
        For tags with build numbers, returns the one with the highest build number.
        
        Args:
            tags: List of tags
            
        Returns:
            Most recent tag
        """
        if not tags:
            raise ArtifactResolverError("No tags provided to get latest")
        
        # Separate versioned tags from -latest tags
        versioned_tags = []
        latest_tags = []
        
        for tag in tags:
            if tag.endswith('-latest'):
                latest_tags.append(tag)
            else:
                versioned_tags.append(tag)
        
        # Prefer versioned tags over -latest tags
        if versioned_tags:
            # Sort by build number (last part after splitting by '.')
            def get_build_number(tag: str) -> int:
                parts = tag.split('.')
                try:
                    return int(parts[-1])
                except (ValueError, IndexError):
                    return 0
            
            sorted_tags = sorted(versioned_tags, key=get_build_number, reverse=True)
            latest = sorted_tags[0]
            logger.debug(f"Selected latest versioned tag: {latest}")
            return latest
        
        # Fallback to -latest tag
        if latest_tags:
            latest = latest_tags[0]
            logger.debug(f"Selected latest tag: {latest}")
            return latest
        
        # Should not reach here, but return first tag as fallback
        return tags[0]
    
    def _create_registry_client(self, registry_config: Dict[str, Any]) -> RegistryClient:
        """
        Create appropriate registry client based on configuration.
        
        Args:
            registry_config: Registry configuration
            
        Returns:
            Registry client instance
            
        Raises:
            ArtifactResolverError: If registry type cannot be determined
        """
        registry_url = registry_config.get('pullUrl', registry_config.get('url', ''))
        credentials = registry_config.get('credentials', {})
        
        # Deduce registry type from URL
        registry_type = self._detect_registry_type(registry_url)
        
        if registry_type == REGISTRY_TYPE_DOCKER:
            username = credentials.get('username')
            password = credentials.get('password')
            return DockerRegistryClient(registry_url, username, password)
        
        elif registry_type == REGISTRY_TYPE_ECR:
            region = credentials.get('region', 'eu-south-1')
            return ECRRegistryClient(registry_url, region)
        
        elif registry_type == REGISTRY_TYPE_DOCKERHUB:
            username = credentials.get('username')
            password = credentials.get('password')
            return DockerHubRegistryClient(username, password)
        
        else:
            raise ArtifactResolverError(
                f"Cannot determine registry type from URL: {registry_url}",
                registry_url=registry_url,
            )
    
    def _detect_registry_type(self, registry_url: str) -> str:
        """
        Detect registry type from URL.
        
        Args:
            registry_url: Registry URL
            
        Returns:
            Registry type: REGISTRY_TYPE_DOCKER, REGISTRY_TYPE_ECR, or REGISTRY_TYPE_DOCKERHUB
        """
        url_lower = registry_url.lower()
        
        # Check for AWS ECR
        if '.amazonaws.com' in url_lower or 'ecr' in url_lower:
            return REGISTRY_TYPE_ECR
        
        # Check for DockerHub
        if 'docker.io' in url_lower or 'hub.docker.com' in url_lower:
            return REGISTRY_TYPE_DOCKERHUB
        
        # Default to generic Docker Registry V2 API
        # This works for Nexus, Harbor, GitLab Registry, and any other Docker Registry V2 compliant registry
        return REGISTRY_TYPE_DOCKER
