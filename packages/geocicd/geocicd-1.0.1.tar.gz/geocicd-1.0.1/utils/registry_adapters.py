"""
Registry adapters for version checking.

Provides adapters for different package registry types.
"""

import json
import re
from typing import Optional, Dict
import requests
from packaging import version as pkg_version

from utils.exceptions import VersionCheckError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RegistryAdapter:
    """Base class for registry adapters"""
    
    def get_latest_version(self, package_name: str, registry_url: str, credentials: Optional[Dict[str, str]] = None) -> str:
        """Get latest version from registry."""
        raise NotImplementedError("Subclasses must implement get_latest_version")


class PyPIAdapter(RegistryAdapter):
    """Adapter for PyPI (public and private) registries"""
    
    def get_latest_version(self, package_name: str, registry_url: str, credentials: Optional[Dict[str, str]] = None) -> str:
        """Get latest version from PyPI."""
        registry_url = registry_url.rstrip('/')
        api_url = f"{registry_url}/pypi/{package_name}/json"
        
        logger.debug(f"Querying PyPI registry: {api_url}")
        
        try:
            auth = None
            if credentials:
                auth = (credentials.get('username'), credentials.get('password'))
            
            response = requests.get(api_url, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            latest_version = data['info']['version']
            
            logger.debug(f"Latest version from PyPI: {latest_version}")
            return latest_version
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise VersionCheckError(f"Authentication failed for PyPI registry: {registry_url}")
            elif e.response.status_code == 404:
                raise VersionCheckError(f"Package '{package_name}' not found in PyPI registry: {registry_url}")
            else:
                raise VersionCheckError(f"HTTP error querying PyPI: {e}")
        except requests.exceptions.RequestException as e:
            raise VersionCheckError(f"Network error querying PyPI: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            raise VersionCheckError(f"Invalid response from PyPI registry: {e}")


class NexusAdapter(RegistryAdapter):
    """Adapter for Nexus Repository Manager"""
    
    def get_latest_version(self, package_name: str, registry_url: str, credentials: Optional[Dict[str, str]] = None) -> str:
        """Get latest version from Nexus."""
        registry_url = registry_url.rstrip('/')
        
        parts = registry_url.split('/repository/')
        if len(parts) > 1:
            base_url = parts[0]
            repository = parts[1]
        else:
            base_url = registry_url
            repository = 'pypi-hosted'
        
        api_url = f"{base_url}/service/rest/v1/search"
        params = {
            'repository': repository,
            'name': package_name,
            'sort': 'version',
            'direction': 'desc'
        }
        
        logger.debug(f"Querying Nexus registry: {api_url} with params: {params}")
        
        try:
            auth = None
            if credentials:
                auth = (credentials.get('username'), credentials.get('password'))
            
            response = requests.get(api_url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('items'):
                raise VersionCheckError(f"Package '{package_name}' not found in Nexus repository: {repository}")
            
            latest_version = data['items'][0]['version']
            
            logger.debug(f"Latest version from Nexus: {latest_version}")
            return latest_version
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise VersionCheckError(f"Authentication failed for Nexus registry: {registry_url}")
            else:
                raise VersionCheckError(f"HTTP error querying Nexus: {e}")
        except requests.exceptions.RequestException as e:
            raise VersionCheckError(f"Network error querying Nexus: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            raise VersionCheckError(f"Invalid response from Nexus registry: {e}")


class ArtifactoryAdapter(RegistryAdapter):
    """Adapter for JFrog Artifactory"""
    
    def get_latest_version(self, package_name: str, registry_url: str, credentials: Optional[Dict[str, str]] = None) -> str:
        """Get latest version from Artifactory."""
        registry_url = registry_url.rstrip('/')
        
        parts = registry_url.split('/artifactory/')
        if len(parts) > 1:
            base_url = parts[0] + '/artifactory'
            repository = parts[1]
        else:
            base_url = registry_url
            repository = 'pypi-local'
        
        api_url = f"{base_url}/api/pypi/{repository}/simple/{package_name}/"
        
        logger.debug(f"Querying Artifactory registry: {api_url}")
        
        try:
            auth = None
            headers = {}
            if credentials:
                if 'api_key' in credentials:
                    headers['X-JFrog-Art-Api'] = credentials['api_key']
                else:
                    auth = (credentials.get('username'), credentials.get('password'))
            
            response = requests.get(api_url, auth=auth, headers=headers, timeout=10)
            response.raise_for_status()
            
            html = response.text
            
            version_pattern = rf'{package_name}-(\d+\.\d+\.\d+[^"]*)'
            versions = re.findall(version_pattern, html)
            
            if not versions:
                raise VersionCheckError(f"No versions found for package '{package_name}' in Artifactory repository: {repository}")
            
            sorted_versions = sorted(versions, key=pkg_version.parse, reverse=True)
            latest_version = sorted_versions[0]
            
            logger.debug(f"Latest version from Artifactory: {latest_version}")
            return latest_version
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise VersionCheckError(f"Authentication failed for Artifactory registry: {registry_url}")
            elif e.response.status_code == 404:
                raise VersionCheckError(f"Package '{package_name}' not found in Artifactory repository: {repository}")
            else:
                raise VersionCheckError(f"HTTP error querying Artifactory: {e}")
        except requests.exceptions.RequestException as e:
            raise VersionCheckError(f"Network error querying Artifactory: {e}")
        except Exception as e:
            raise VersionCheckError(f"Error parsing Artifactory response: {e}")


class CustomAdapter(RegistryAdapter):
    """Adapter for custom HTTP endpoints"""
    
    def get_latest_version(self, package_name: str, registry_url: str, credentials: Optional[Dict[str, str]] = None) -> str:
        """Get latest version from custom HTTP endpoint."""
        registry_url = registry_url.rstrip('/')
        api_url = registry_url.replace('{package}', package_name)
        
        logger.debug(f"Querying custom registry: {api_url}")
        
        try:
            auth = None
            headers = {}
            if credentials:
                if 'headers' in credentials:
                    headers = credentials['headers']
                else:
                    auth = (credentials.get('username'), credentials.get('password'))
            
            response = requests.get(api_url, auth=auth, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            latest_version = None
            if 'version' in data:
                latest_version = data['version']
            elif 'latest' in data:
                latest_version = data['latest']
            elif 'data' in data and isinstance(data['data'], dict):
                if 'version' in data['data']:
                    latest_version = data['data']['version']
                elif 'latest' in data['data']:
                    latest_version = data['data']['latest']
            
            if not latest_version:
                raise VersionCheckError(f"Could not find version field in custom registry response. Response: {data}")
            
            logger.debug(f"Latest version from custom registry: {latest_version}")
            return latest_version
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise VersionCheckError(f"Authentication failed for custom registry: {registry_url}")
            else:
                raise VersionCheckError(f"HTTP error querying custom registry: {e}")
        except requests.exceptions.RequestException as e:
            raise VersionCheckError(f"Network error querying custom registry: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            raise VersionCheckError(f"Invalid response from custom registry: {e}")
