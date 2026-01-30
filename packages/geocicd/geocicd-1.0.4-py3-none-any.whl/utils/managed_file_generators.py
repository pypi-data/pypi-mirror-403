"""
Managed file content generators for GitLab CI/CD Migration system.

This module provides content generation functions for various managed files
including .npmrc, Maven settings.xml, AWS credentials, Docker daemon config, etc.
"""

import base64
import json
import logging
from typing import Any, Dict

from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class ManagedFileGenerators:
    """
    Content generators for managed configuration files.
    
    This class provides static methods to generate content for:
    - .npmrc for NPM registry configuration
    - Maven settings.xml for Maven repository configuration
    - AWS credentials and config files
    - Docker daemon.json for insecure registries
    - kubeconfig for multi-cluster Kubernetes access
    """
    
    @staticmethod
    def generate_npmrc(config: Dict[str, Any]) -> str:
        """
        Generate .npmrc file content from configuration.
        
        Creates NPM registry configuration with:
        - Registry URL (for npm install)
        - Publish URL (for npm publish)
        - Authentication token or credentials
        - Scope-specific registries
        
        Args:
            config: NPM configuration dictionary with keys:
                - registryUrl: Registry URL for npm install (required)
                - publishUrl: Publish URL for npm publish (optional, defaults to registryUrl)
                - token: Authentication token (optional)
                - username: Username for basic auth (optional)
                - password: Password for basic auth (optional)
                - email: Email for registry (optional)
                - scopes: Dict of scope to registry mappings (optional)
        
        Returns:
            .npmrc file content as string
        """
        with OperationLogger(logger, "generate .npmrc file"):
            lines = []
            
            # Main registry URL (for npm install)
            registry_url = config.get('registryUrl') or config.get('registry')
            if registry_url:
                lines.append(f"registry={registry_url}")
            
            # Publish URL (for npm publish) - if different from registry
            publish_url = config.get('publishUrl')
            if publish_url and publish_url != registry_url:
                publish_host = ManagedFileGenerators._extract_host_from_url(publish_url)
                lines.append(f"# Publish registry")
                lines.append(f"publishConfig.registry={publish_url}")
            
            # Authentication
            token = config.get('token')
            if token:
                # Token-based authentication
                registry_host = ManagedFileGenerators._extract_host_from_url(registry_url) if registry_url else 'registry.npmjs.org'
                lines.append(f"//{registry_host}/:_authToken={token}")
                
                # Add auth for publish URL if different
                if publish_url and publish_url != registry_url:
                    publish_host = ManagedFileGenerators._extract_host_from_url(publish_url)
                    lines.append(f"//{publish_host}/:_authToken={token}")
            else:
                # Basic authentication
                username = config.get('username')
                password = config.get('password')
                email = config.get('email', 'user@example.com')
                
                if username and password:
                    registry_host = ManagedFileGenerators._extract_host_from_url(registry_url) if registry_url else 'registry.npmjs.org'
                    # Encode credentials in base64
                    auth_string = f"{username}:{password}"
                    auth_base64 = base64.b64encode(auth_string.encode()).decode()
                    lines.append(f"//{registry_host}/:_auth={auth_base64}")
                    lines.append(f"//{registry_host}/:email={email}")
                    
                    # Add auth for publish URL if different
                    if publish_url and publish_url != registry_url:
                        publish_host = ManagedFileGenerators._extract_host_from_url(publish_url)
                        lines.append(f"//{publish_host}/:_auth={auth_base64}")
                        lines.append(f"//{publish_host}/:email={email}")
            
            # Scope-specific registries
            scopes = config.get('scopes', {})
            for scope, scope_registry in scopes.items():
                lines.append(f"@{scope}:registry={scope_registry}")
            
            # Additional settings
            if config.get('alwaysAuth'):
                lines.append("always-auth=true")
            
            if config.get('strictSSL') is False:
                lines.append("strict-ssl=false")
            
            content = '\n'.join(lines) + '\n'
            logger.debug(f"Generated .npmrc with {len(lines)} lines")
            return content
    
    @staticmethod
    def generate_maven_settings(config: Dict[str, Any]) -> str:
        """
        Generate Maven settings.xml file content from configuration.
        
        Creates Maven settings with:
        - Repository for downloads (repositoryUrl)
        - Distribution management for releases (publishUrl)
        - Server authentication
        - Profiles and activation
        
        Args:
            config: Maven configuration dictionary with keys:
                - repositoryUrl: URL for downloading dependencies
                - publishUrl: URL for publishing releases (maven deploy)
                - username: Username for authentication
                - password: Password for authentication
                - servers: List of additional server configurations (optional)
                - mirrors: List of mirror configurations (optional)
                - profiles: List of profile configurations (optional)
                - activeProfiles: List of active profile IDs (optional)
        
        Returns:
            settings.xml file content as string
        """
        with OperationLogger(logger, "generate Maven settings.xml"):
            lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            lines.append('<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"')
            lines.append('          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
            lines.append('          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0')
            lines.append('                              http://maven.apache.org/xsd/settings-1.0.0.xsd">')
            
            # Servers section
            servers = config.get('servers', [])
            
            # Add default servers for repository and publish URLs if provided
            repository_url = config.get('repositoryUrl')
            publish_url = config.get('publishUrl')
            username = config.get('username')
            password = config.get('password')
            
            default_servers = []
            if repository_url and username and password:
                default_servers.append({
                    'id': 'nexus-repository',
                    'username': username,
                    'password': password
                })
            
            if publish_url and username and password and publish_url != repository_url:
                default_servers.append({
                    'id': 'nexus-releases',
                    'username': username,
                    'password': password
                })
            
            all_servers = default_servers + servers
            
            if all_servers:
                lines.append('  <servers>')
                for server in all_servers:
                    lines.append('    <server>')
                    lines.append(f'      <id>{server.get("id")}</id>')
                    
                    if server.get('username'):
                        lines.append(f'      <username>{server.get("username")}</username>')
                    if server.get('password'):
                        lines.append(f'      <password>{server.get("password")}</password>')
                    if server.get('privateKey'):
                        lines.append(f'      <privateKey>{server.get("privateKey")}</privateKey>')
                    if server.get('passphrase'):
                        lines.append(f'      <passphrase>{server.get("passphrase")}</passphrase>')
                    
                    lines.append('    </server>')
                lines.append('  </servers>')
            
            # Mirrors section
            mirrors = config.get('mirrors', [])
            if mirrors:
                lines.append('  <mirrors>')
                for mirror in mirrors:
                    lines.append('    <mirror>')
                    lines.append(f'      <id>{mirror.get("id")}</id>')
                    lines.append(f'      <name>{mirror.get("name", mirror.get("id"))}</name>')
                    lines.append(f'      <url>{mirror.get("url")}</url>')
                    lines.append(f'      <mirrorOf>{mirror.get("mirrorOf", "central")}</mirrorOf>')
                    lines.append('    </mirror>')
                lines.append('  </mirrors>')
            
            # Profiles section
            profiles = config.get('profiles', [])
            
            # Add default profile for repository URL if provided
            default_profiles = []
            if repository_url:
                default_profiles.append({
                    'id': 'nexus',
                    'repositories': [{
                        'id': 'nexus-repository',
                        'url': repository_url,
                        'releases': {'enabled': True},
                        'snapshots': {'enabled': False}
                    }],
                    'pluginRepositories': [{
                        'id': 'nexus-repository',
                        'url': repository_url
                    }]
                })
            
            all_profiles = default_profiles + profiles
            
            if all_profiles:
                lines.append('  <profiles>')
                for profile in all_profiles:
                    lines.append('    <profile>')
                    lines.append(f'      <id>{profile.get("id")}</id>')
                    
                    # Repositories
                    repositories = profile.get('repositories', [])
                    if repositories:
                        lines.append('      <repositories>')
                        for repo in repositories:
                            lines.append('        <repository>')
                            lines.append(f'          <id>{repo.get("id")}</id>')
                            lines.append(f'          <url>{repo.get("url")}</url>')
                            
                            releases = repo.get('releases', {})
                            if releases:
                                lines.append('          <releases>')
                                lines.append(f'            <enabled>{str(releases.get("enabled", True)).lower()}</enabled>')
                                lines.append('          </releases>')
                            
                            snapshots = repo.get('snapshots', {})
                            if snapshots:
                                lines.append('          <snapshots>')
                                lines.append(f'            <enabled>{str(snapshots.get("enabled", False)).lower()}</enabled>')
                                lines.append('          </snapshots>')
                            
                            lines.append('        </repository>')
                        lines.append('      </repositories>')
                    
                    # Plugin repositories
                    plugin_repositories = profile.get('pluginRepositories', [])
                    if plugin_repositories:
                        lines.append('      <pluginRepositories>')
                        for repo in plugin_repositories:
                            lines.append('        <pluginRepository>')
                            lines.append(f'          <id>{repo.get("id")}</id>')
                            lines.append(f'          <url>{repo.get("url")}</url>')
                            lines.append('        </pluginRepository>')
                        lines.append('      </pluginRepositories>')
                    
                    lines.append('    </profile>')
                lines.append('  </profiles>')
            
            # Active profiles section
            active_profiles = config.get('activeProfiles', [])
            
            # Add default active profile if repository URL is configured
            if repository_url and 'nexus' not in active_profiles:
                active_profiles = ['nexus'] + active_profiles
            
            if active_profiles:
                lines.append('  <activeProfiles>')
                for profile_id in active_profiles:
                    lines.append(f'    <activeProfile>{profile_id}</activeProfile>')
                lines.append('  </activeProfiles>')
            
            lines.append('</settings>')
            
            content = '\n'.join(lines) + '\n'
            logger.debug(f"Generated Maven settings.xml with {len(lines)} lines")
            return content
    
    @staticmethod
    def generate_aws_credentials(config: Dict[str, Any]) -> str:
        """
        Generate AWS credentials file content from configuration.
        
        Creates AWS credentials file with:
        - Access key ID
        - Secret access key
        - Session token (optional)
        - Multiple profiles
        
        Args:
            config: AWS credentials configuration with keys:
                - profiles: Dict of profile name to credentials
        
        Returns:
            AWS credentials file content as string
        """
        with OperationLogger(logger, "generate AWS credentials file"):
            lines = []
            
            profiles = config.get('profiles', {})
            for profile_name, credentials in profiles.items():
                lines.append(f"[{profile_name}]")
                
                if credentials.get('accessKeyId'):
                    lines.append(f"aws_access_key_id = {credentials.get('accessKeyId')}")
                if credentials.get('secretAccessKey'):
                    lines.append(f"aws_secret_access_key = {credentials.get('secretAccessKey')}")
                if credentials.get('sessionToken'):
                    lines.append(f"aws_session_token = {credentials.get('sessionToken')}")
                
                lines.append('')  # Empty line between profiles
            
            content = '\n'.join(lines)
            logger.debug(f"Generated AWS credentials file with {len(profiles)} profile(s)")
            return content
    
    @staticmethod
    def generate_aws_config(config: Dict[str, Any]) -> str:
        """
        Generate AWS config file content from configuration.
        
        Creates AWS config file with:
        - Region
        - Output format
        - Multiple profiles
        
        Args:
            config: AWS config configuration with keys:
                - profiles: Dict of profile name to config
        
        Returns:
            AWS config file content as string
        """
        with OperationLogger(logger, "generate AWS config file"):
            lines = []
            
            profiles = config.get('profiles', {})
            for profile_name, profile_config in profiles.items():
                if profile_name == 'default':
                    lines.append('[default]')
                else:
                    lines.append(f"[profile {profile_name}]")
                
                if profile_config.get('region'):
                    lines.append(f"region = {profile_config.get('region')}")
                if profile_config.get('output'):
                    lines.append(f"output = {profile_config.get('output')}")
                
                lines.append('')  # Empty line between profiles
            
            content = '\n'.join(lines)
            logger.debug(f"Generated AWS config file with {len(profiles)} profile(s)")
            return content
    
    @staticmethod
    def generate_docker_daemon_config(config: Dict[str, Any]) -> str:
        """
        Generate Docker daemon.json file content from configuration.
        
        Creates Docker daemon configuration with:
        - Insecure registries
        - Registry mirrors
        - Storage driver settings
        
        Args:
            config: Docker daemon configuration with keys:
                - insecureRegistries: List of insecure registry URLs
                - registryMirrors: List of registry mirror URLs
                - storageDriver: Storage driver name
        
        Returns:
            daemon.json file content as string
        """
        with OperationLogger(logger, "generate Docker daemon.json"):
            daemon_config = {}
            
            insecure_registries = config.get('insecureRegistries', [])
            if insecure_registries:
                daemon_config['insecure-registries'] = insecure_registries
            
            registry_mirrors = config.get('registryMirrors', [])
            if registry_mirrors:
                daemon_config['registry-mirrors'] = registry_mirrors
            
            storage_driver = config.get('storageDriver')
            if storage_driver:
                daemon_config['storage-driver'] = storage_driver
            
            content = json.dumps(daemon_config, indent=2) + '\n'
            logger.debug(f"Generated Docker daemon.json with {len(daemon_config)} setting(s)")
            return content
    
    @staticmethod
    def generate_kubeconfig(config: Dict[str, Any]) -> str:
        """
        Generate kubeconfig file content from configuration.
        
        Creates kubeconfig with:
        - Multiple clusters
        - Multiple contexts
        - User credentials
        
        Args:
            config: Kubeconfig configuration with keys:
                - clusters: List of cluster configurations
                - contexts: List of context configurations
                - users: List of user configurations
                - currentContext: Current context name
        
        Returns:
            kubeconfig file content as string (YAML)
        """
        with OperationLogger(logger, "generate kubeconfig file"):
            kubeconfig = {
                'apiVersion': 'v1',
                'kind': 'Config',
                'clusters': config.get('clusters', []),
                'contexts': config.get('contexts', []),
                'users': config.get('users', []),
                'current-context': config.get('currentContext', '')
            }
            
            import yaml
            content = yaml.dump(kubeconfig, default_flow_style=False, sort_keys=False)
            logger.debug(f"Generated kubeconfig with {len(config.get('clusters', []))} cluster(s)")
            return content
    
    @staticmethod
    def _extract_host_from_url(url: str) -> str:
        """
        Extract host from URL.
        
        Args:
            url: Full URL
        
        Returns:
            Host portion of URL
        """
        # Remove protocol
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # Remove path
        if '/' in url:
            url = url.split('/', 1)[0]
        
        return url
