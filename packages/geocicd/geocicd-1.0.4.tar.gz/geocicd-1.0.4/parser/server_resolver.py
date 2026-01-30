"""
Server reference resolver for GitLab CI/CD Migration system.

This module resolves server references in configuration files to actual server configurations.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from utils.exceptions_base import ValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ServerResolver:
    """
    Resolve server references to actual server configurations.
    
    This class loads server definitions from config/servers.yaml and resolves
    references like `server: "nexus-geosystems"` to actual server configurations.
    """
    
    def __init__(self, servers_file: str = "config/servers.yaml"):
        """
        Initialize server resolver.
        
        Args:
            servers_file: Path to servers.yaml file
        """
        self.servers_file = servers_file
        self._servers: Optional[Dict[str, Any]] = None
        logger.debug(f"ServerResolver initialized with file: {servers_file}")
    
    def _load_servers(self) -> Dict[str, Any]:
        """
        Load server definitions from servers.yaml.
        
        Returns:
            Dictionary of server definitions
            
        Raises:
            FileNotFoundError: If servers.yaml doesn't exist
            ValidationError: If servers.yaml is invalid
        """
        if self._servers is not None:
            return self._servers
        
        servers_path = Path(self.servers_file)
        
        if not servers_path.exists():
            raise FileNotFoundError(
                f"Server definitions file not found: {self.servers_file}. "
                f"Create this file with server configurations."
            )
        
        try:
            with open(servers_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'servers' not in data:
                raise ValidationError(
                    "servers.yaml must contain a 'servers' section",
                    file_path=self.servers_file
                )
            
            self._servers = data['servers']
            logger.info(f"Loaded {len(self._servers)} server definition(s) from {self.servers_file}")
            return self._servers
        
        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML in servers file: {e}",
                file_path=self.servers_file
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to load servers file: {e}",
                file_path=self.servers_file
            )
    
    def resolve_server_reference(
        self,
        server_name: str,
        service_type: str
    ) -> Dict[str, Any]:
        """
        Resolve a server reference to actual configuration.
        
        Args:
            server_name: Name of the server (e.g., "nexus-geosystems")
            service_type: Type of service (e.g., "dockerServer", "npmServer")
            
        Returns:
            Server configuration dictionary
            
        Raises:
            ValidationError: If server or service type not found
        """
        servers = self._load_servers()
        
        if server_name not in servers:
            available = ', '.join(servers.keys())
            raise ValidationError(
                f"Server '{server_name}' not found in {self.servers_file}. "
                f"Available servers: {available}"
            )
        
        server_def = servers[server_name]
        
        if service_type not in server_def:
            available = ', '.join(server_def.keys())
            raise ValidationError(
                f"Service type '{service_type}' not found in server '{server_name}'. "
                f"Available services: {available}"
            )
        
        config = server_def[service_type]
        logger.debug(f"Resolved server '{server_name}' service '{service_type}'")
        return config
    
    def resolve_registry_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve all server references in registry configuration.
        
        This method walks through the registry configuration and replaces
        server references with actual server configurations.
        
        Args:
            config: Full configuration dictionary with registry section
            
        Returns:
            Configuration with resolved server references
        """
        if 'registry' not in config:
            return config
        
        registry = config['registry']
        resolved_registry = {}
        
        # Service types to resolve
        service_types = [
            'npmServer',
            'mavenServer',
            'gradleServer',
            'pypiServer',
            'dockerServer',
            'rawServer',
            'helmServer'
        ]
        
        for service_type in service_types:
            if service_type not in registry:
                continue
            
            service_config = registry[service_type]
            resolved_service = {}
            
            # Resolve for each environment (dev, stg, ese)
            for env in ['dev', 'stg', 'ese']:
                if env not in service_config:
                    continue
                
                env_config = service_config[env]
                
                # Check if it's a server reference
                if isinstance(env_config, dict) and 'server' in env_config:
                    server_name = env_config['server']
                    
                    # Resolve server reference
                    resolved_config = self.resolve_server_reference(
                        server_name,
                        service_type
                    )
                    resolved_service[env] = resolved_config
                    
                    logger.debug(
                        f"Resolved {service_type}.{env}: server '{server_name}'"
                    )
                else:
                    # Already a full configuration, keep as-is
                    resolved_service[env] = env_config
            
            if resolved_service:
                resolved_registry[service_type] = resolved_service
        
        # Replace registry section with resolved version
        result = config.copy()
        result['registry'] = resolved_registry
        
        logger.info("Resolved all server references in registry configuration")
        return result
