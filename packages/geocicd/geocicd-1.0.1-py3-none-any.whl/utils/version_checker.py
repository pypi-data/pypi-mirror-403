"""
Version Checker for CLI Version Enforcement

This module provides version checking functionality to ensure all team members
use the latest version of the CLI tool.

Requirements: 23.1-23.13
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from packaging import version as pkg_version

from utils.exceptions import VersionCheckError
from utils.logging_config import get_logger
from utils.registry_adapters import (
    PyPIAdapter,
    NexusAdapter,
    ArtifactoryAdapter,
    CustomAdapter
)

logger = get_logger(__name__)


@dataclass
class VersionCheckResult:
    """Result of a version check operation"""
    current_version: str
    latest_version: str
    update_required: bool
    registry_url: str
    checked_at: datetime


class VersionChecker:
    """
    CLI version enforcement system
    
    Checks if the CLI is up to date and blocks execution if a newer version is available.
    Supports multiple registry types: PyPI, Nexus, Artifactory, and custom HTTP endpoints.
    
    Requirements: 23.1-23.13
    """
    
    CACHE_FILE = Path.home() / '.geocicd' / 'version_check_cache.json'
    CACHE_DURATION = timedelta(hours=1)
    DEFAULT_REGISTRY = 'https://pypi.org'
    PACKAGE_NAME = 'geocicd'
    
    def __init__(self, current_version: str):
        """
        Initialize VersionChecker
        
        Args:
            current_version: Current installed version of the CLI
        """
        self.current_version = current_version
        self.adapters = {
            'pypi': PyPIAdapter(),
            'nexus': NexusAdapter(),
            'artifactory': ArtifactoryAdapter(),
            'custom': CustomAdapter()
        }
    
    def check_version(self, registry_url: Optional[str] = None, skip_check: bool = False) -> VersionCheckResult:
        """
        Check if CLI is up to date
        
        Args:
            registry_url: Optional custom registry URL (overrides config)
            skip_check: If True, skip version check (for emergency use)
            
        Returns:
            VersionCheckResult with current, latest, and update_required
            
        Raises:
            VersionCheckError: If check fails due to auth issues
        """
        if skip_check:
            logger.warning("Version check skipped via --skip-version-check flag")
            return VersionCheckResult(
                current_version=self.current_version,
                latest_version=self.current_version,
                update_required=False,
                registry_url='skipped',
                checked_at=datetime.now()
            )
        
        # Check cache first
        cached_result = self.get_cached_result()
        if cached_result:
            logger.debug("Using cached version check result")
            return cached_result
        
        # Get registry URL
        if not registry_url:
            registry_url = self.get_registry_url()
        
        logger.info(f"Checking for CLI updates from: {registry_url}")
        
        try:
            # Get latest version
            latest_version = self.get_latest_version(registry_url, self.PACKAGE_NAME)
            
            # Compare versions
            update_required = self.compare_versions(self.current_version, latest_version)
            
            # Create result
            result = VersionCheckResult(
                current_version=self.current_version,
                latest_version=latest_version,
                update_required=update_required,
                registry_url=registry_url,
                checked_at=datetime.now()
            )
            
            # Cache result
            self.cache_version_check(result)
            
            return result
            
        except VersionCheckError as e:
            # Check if it's an authentication error (strict handling)
            if 'Authentication failed' in str(e):
                logger.error(f"Version check failed: {e}")
                raise
            else:
                # Network or other errors (graceful handling)
                logger.warning(f"Version check failed, continuing execution: {e}")
                return VersionCheckResult(
                    current_version=self.current_version,
                    latest_version=self.current_version,
                    update_required=False,
                    registry_url=registry_url,
                    checked_at=datetime.now()
                )
    
    def get_latest_version(self, registry_url: str, package_name: str) -> str:
        """
        Query registry for latest version
        
        Args:
            registry_url: Registry URL (PyPI, Nexus, Artifactory, or custom)
            package_name: Package name to check
            
        Returns:
            Latest version string (e.g., "1.2.3")
            
        Raises:
            VersionCheckError: If registry is unreachable or auth fails
        """
        # Determine registry type from URL
        registry_type = self._detect_registry_type(registry_url)
        
        logger.debug(f"Detected registry type: {registry_type}")
        
        # Get appropriate adapter
        adapter = self.adapters.get(registry_type)
        if not adapter:
            raise VersionCheckError(f"Unsupported registry type: {registry_type}")
        
        # Get credentials from config if available
        credentials = self._get_credentials(registry_url)
        
        # Query registry
        return adapter.get_latest_version(package_name, registry_url, credentials)
    
    def compare_versions(self, current: str, latest: str) -> bool:
        """
        Compare versions using semantic versioning
        
        Args:
            current: Current installed version
            latest: Latest available version
            
        Returns:
            True if update required (latest > current), False otherwise
        """
        try:
            current_ver = pkg_version.parse(current)
            latest_ver = pkg_version.parse(latest)
            
            update_required = latest_ver > current_ver
            
            logger.debug(f"Version comparison: current={current}, latest={latest}, update_required={update_required}")
            
            return update_required
            
        except Exception as e:
            logger.warning(f"Error comparing versions: {e}. Assuming no update required.")
            return False
    
    def get_registry_url(self) -> str:
        """
        Get registry URL from environment or config
        
        Checks in order:
        1. GEOCICD_REGISTRY_URL environment variable
        2. ~/.geocicd/config.yaml
        3. Default PyPI
        
        Returns:
            Registry URL
        """
        # Check environment variable first
        env_url = os.environ.get('GEOCICD_REGISTRY_URL')
        if env_url:
            logger.debug(f"Using registry URL from environment: {env_url}")
            return env_url
        
        # Check config file
        config_file = Path.home() / '.geocicd' / 'config.yaml'
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'registry_url' in config:
                        logger.debug(f"Using registry URL from config: {config['registry_url']}")
                        return config['registry_url']
            except Exception as e:
                logger.warning(f"Error reading config file: {e}")
        
        # Use default
        logger.debug(f"Using default registry URL: {self.DEFAULT_REGISTRY}")
        return self.DEFAULT_REGISTRY
    
    def cache_version_check(self, result: VersionCheckResult) -> None:
        """
        Cache version check result for 1 hour
        
        Args:
            result: Version check result to cache
        """
        try:
            # Ensure cache directory exists
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare cache data
            cache_data = {
                'current_version': result.current_version,
                'latest_version': result.latest_version,
                'update_required': result.update_required,
                'registry_url': result.registry_url,
                'checked_at': result.checked_at.isoformat()
            }
            
            # Write cache file
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached version check result to: {self.CACHE_FILE}")
            
        except Exception as e:
            logger.warning(f"Failed to cache version check result: {e}")
    
    def get_cached_result(self) -> Optional[VersionCheckResult]:
        """
        Get cached version check result if valid
        
        Returns:
            Cached result or None if expired/missing
        """
        try:
            if not self.CACHE_FILE.exists():
                return None
            
            # Read cache file
            with open(self.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            # Parse checked_at timestamp
            checked_at = datetime.fromisoformat(cache_data['checked_at'])
            
            # Check if cache is still valid
            age = datetime.now() - checked_at
            if age > self.CACHE_DURATION:
                logger.debug(f"Cache expired (age: {age})")
                return None
            
            # Return cached result
            return VersionCheckResult(
                current_version=cache_data['current_version'],
                latest_version=cache_data['latest_version'],
                update_required=cache_data['update_required'],
                registry_url=cache_data['registry_url'],
                checked_at=checked_at
            )
            
        except Exception as e:
            logger.debug(f"Failed to read cache: {e}")
            return None
    
    def _detect_registry_type(self, registry_url: str) -> str:
        """
        Detect registry type from URL
        
        Args:
            registry_url: Registry URL
            
        Returns:
            Registry type: 'pypi', 'nexus', 'artifactory', or 'custom'
        """
        url_lower = registry_url.lower()
        
        if 'pypi.org' in url_lower or '/pypi/' in url_lower:
            return 'pypi'
        elif 'nexus' in url_lower or '/service/rest/' in url_lower:
            return 'nexus'
        elif 'artifactory' in url_lower or '/artifactory/' in url_lower:
            return 'artifactory'
        else:
            return 'custom'
    
    def _get_credentials(self, registry_url: str) -> Optional[Dict[str, str]]:
        """
        Get credentials for registry from config
        
        Args:
            registry_url: Registry URL
            
        Returns:
            Credentials dictionary or None
        """
        config_file = Path.home() / '.geocicd' / 'config.yaml'
        if not config_file.exists():
            return None
        
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                
                if not config or 'registries' not in config:
                    return None
                
                # Find matching registry
                for registry in config['registries']:
                    if registry.get('url') == registry_url:
                        return registry.get('credentials')
                
                return None
                
        except Exception as e:
            logger.warning(f"Error reading credentials from config: {e}")
            return None
