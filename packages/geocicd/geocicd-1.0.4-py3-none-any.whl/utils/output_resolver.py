"""
Output resolver for build artifacts.

This module maps build outputs to registry servers based on component type and environment.
"""

import logging
from typing import Dict, Any, List, Optional

from utils.registry_config_helper import RegistryConfigHelper
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OutputResolver:
    """
    Resolve build outputs to physical registry servers.
    
    Maps output types (docker, artifact, helm) to appropriate registry servers
    based on component type and target environment.
    
    Examples:
        >>> resolver = OutputResolver()
        >>> servers = resolver.resolve_outputs(
        ...     component={'type': 'java', 'build': {'outputs': ['docker', 'artifact']}},
        ...     environment='ese',
        ...     config=config
        ... )
        >>> # Returns: [
        >>> #   {'output': 'docker', 'server': 'dockerServer', 'config': {...}},
        >>> #   {'output': 'artifact', 'server': 'mavenServer', 'config': {...}}
        >>> # ]
    """
    
    # Mapping: component type → artifact server type
    ARTIFACT_SERVER_MAP = {
        'java': 'mavenServer',
        'spring': 'mavenServer',
        'maven': 'mavenServer',
        'gradle': 'gradleServer',
        'npm': 'npmServer',
        'node': 'npmServer',
        'python': 'pypiServer',
        'vue': 'npmServer',
        'react': 'npmServer',
        'angular': 'npmServer',
    }
    
    def resolve_outputs(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Resolve build outputs to registry servers.
        
        Args:
            component: Component configuration
            environment: Target environment (dev, stg, ese)
            config: Full configuration with registry settings
            
        Returns:
            List of resolved outputs with server configurations:
            [
                {
                    'output': 'docker',
                    'server': 'dockerServer',
                    'config': { pushUrl, pullUrl, username, password, ... }
                },
                {
                    'output': 'artifact',
                    'server': 'mavenServer',
                    'config': { repositoryUrl, publishUrl, username, password }
                }
            ]
            
        Raises:
            ValueError: If output type is invalid or server not configured
        """
        component_type = component.get('type', 'unknown')
        build_config = component.get('build', {})
        outputs = build_config.get('outputs', [])
        
        if not outputs:
            logger.warning(f"Component {component.get('name')} has no outputs defined")
            return []
        
        resolved = []
        
        for output in outputs:
            if output == 'docker':
                server_config = self._resolve_docker(environment, config)
                resolved.append({
                    'output': 'docker',
                    'server': 'dockerServer',
                    'config': server_config
                })
            
            elif output == 'artifact':
                server_type, server_config = self._resolve_artifact(
                    component_type, environment, config
                )
                resolved.append({
                    'output': 'artifact',
                    'server': server_type,
                    'config': server_config
                })
            
            elif output == 'helm':
                server_config = self._resolve_helm(environment, config)
                resolved.append({
                    'output': 'helm',
                    'server': 'helmServer',
                    'config': server_config
                })
            
            else:
                raise ValueError(
                    f"Unknown output type '{output}' for component {component.get('name')}. "
                    f"Valid types: docker, artifact, helm"
                )
        
        logger.info(
            f"Resolved {len(resolved)} output(s) for component {component.get('name')} "
            f"in environment {environment}"
        )
        
        return resolved
    
    def resolve_output(
        self,
        output_type: str,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a single output type to registry server.
        
        Args:
            output_type: Output type (docker, artifact, helm)
            component: Component configuration
            environment: Target environment (dev, stg, ese)
            config: Full configuration with registry settings
            
        Returns:
            Resolved server configuration dictionary
            
        Raises:
            ValueError: If output type is invalid or server not configured
        """
        component_type = component.get('type', 'unknown')
        
        if output_type == 'docker':
            return self._resolve_docker(environment, config)
        
        elif output_type == 'artifact':
            server_type, server_config = self._resolve_artifact(
                component_type, environment, config
            )
            return server_config
        
        elif output_type == 'helm':
            return self._resolve_helm(environment, config)
        
        else:
            raise ValueError(
                f"Unknown output type '{output_type}' for component {component.get('name')}. "
                f"Valid types: docker, artifact, helm"
            )
    
    def _resolve_docker(
        self,
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve Docker output to dockerServer.
        
        Args:
            environment: Target environment
            config: Full configuration
            
        Returns:
            Docker server configuration
            
        Raises:
            ValueError: If dockerServer not configured for environment
        """
        docker_config = RegistryConfigHelper.get_docker_config(config, environment)
        
        if not docker_config:
            raise ValueError(
                f"No dockerServer configured for environment '{environment}'. "
                f"Add registry.dockerServer.{environment} to your configuration."
            )
        
        return docker_config
    
    def _resolve_artifact(
        self,
        component_type: str,
        environment: str,
        config: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Resolve artifact output to appropriate server based on component type.
        
        Args:
            component_type: Component type (java, npm, python, etc.)
            environment: Target environment
            config: Full configuration
            
        Returns:
            Tuple of (server_type, server_config)
            
        Raises:
            ValueError: If component type not supported or server not configured
        """
        # Determine server type from component type
        server_type = self.ARTIFACT_SERVER_MAP.get(component_type)
        
        if not server_type:
            raise ValueError(
                f"Component type '{component_type}' does not support artifact output. "
                f"Supported types: {', '.join(self.ARTIFACT_SERVER_MAP.keys())}"
            )
        
        # Get server configuration
        if server_type == 'mavenServer':
            server_config = RegistryConfigHelper.get_maven_config(config, environment)
        elif server_type == 'gradleServer':
            server_config = RegistryConfigHelper.get_gradle_config(config, environment)
        elif server_type == 'npmServer':
            server_config = RegistryConfigHelper.get_npm_config(config, environment)
        elif server_type == 'pypiServer':
            server_config = RegistryConfigHelper.get_pypi_config(config, environment)
        else:
            raise ValueError(f"Unknown server type: {server_type}")
        
        if not server_config:
            raise ValueError(
                f"No {server_type} configured for environment '{environment}'. "
                f"Add registry.{server_type}.{environment} to your configuration."
            )
        
        return server_type, server_config
    
    def _resolve_helm(
        self,
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve Helm output to helmServer.
        
        Args:
            environment: Target environment
            config: Full configuration
            
        Returns:
            Helm server configuration
            
        Raises:
            ValueError: If helmServer not configured for environment
        """
        # For now, Helm charts can be stored in raw server or dedicated helm server
        # Try helmServer first, fallback to rawServer
        registry = config.get('registry', {})
        helm_server = registry.get('helmServer', {})
        helm_config = helm_server.get(environment)
        
        if helm_config:
            return helm_config
        
        # Fallback to rawServer
        raw_config = RegistryConfigHelper.get_raw_config(config, environment)
        if raw_config:
            logger.info(f"Using rawServer for Helm charts in environment {environment}")
            return raw_config
        
        raise ValueError(
            f"No helmServer or rawServer configured for environment '{environment}'. "
            f"Add registry.helmServer.{environment} or registry.rawServer.{environment} "
            f"to your configuration."
        )
