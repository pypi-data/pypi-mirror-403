"""
Generic Docker Registry client implementation.

Supports any Docker Registry V2 API compliant registry (Nexus, Harbor, GitLab Registry, etc.)
"""

import logging
import json
from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth

from utils.registry_clients import RegistryClient, ArtifactResolverError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class DockerRegistryClient(RegistryClient):
    """Generic Docker Registry client for any Docker Registry V2 API compliant registry."""
    
    def __init__(self, registry_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Docker Registry client.
        
        Args:
            registry_url: Registry URL (e.g., registry.example.com:5000)
            username: Username for authentication
            password: Password for authentication
        """
        self.registry_url = registry_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password) if username and password else None
        
        # Determine protocol (default to https)
        if not self.registry_url.startswith(('http://', 'https://')):
            self.registry_url = f"https://{self.registry_url}"
        
        logger.debug(f"Initialized DockerRegistryClient for {self.registry_url}")
    
    def list_tags(self, image_name: str) -> List[str]:
        """
        List all tags for an image in Docker registry.
        
        Uses Docker Registry HTTP API V2.
        
        Args:
            image_name: Name of the image
            
        Returns:
            List of tag names
            
        Raises:
            ArtifactResolverError: If listing tags fails
        """
        url = f"{self.registry_url}/v2/{image_name}/tags/list"
        
        try:
            logger.debug(f"Listing tags for {image_name} from {url}")
            response = requests.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tags = data.get('tags', [])
            
            logger.debug(f"Found {len(tags)} tags for {image_name}")
            return tags if tags else []
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Image {image_name} not found in registry")
                return []
            raise ArtifactResolverError(
                f"Failed to list tags for {image_name}: HTTP {e.response.status_code}",
                registry_type="docker",
                registry_url=self.registry_url,
            )
        except requests.exceptions.RequestException as e:
            raise ArtifactResolverError(
                f"Failed to connect to Docker registry: {str(e)}",
                registry_type="docker",
                registry_url=self.registry_url,
            )
        except (KeyError, json.JSONDecodeError) as e:
            raise ArtifactResolverError(
                f"Invalid response from Docker registry: {str(e)}",
                registry_type="docker",
                registry_url=self.registry_url,
            )

    
    def get_tag_metadata(self, image_name: str, tag: str) -> Dict[str, Any]:
        """
        Get metadata for a specific image tag in Docker registry.
        
        Args:
            image_name: Name of the image
            tag: Tag name
            
        Returns:
            Dictionary with metadata
            
        Raises:
            ArtifactResolverError: If getting metadata fails
        """
        url = f"{self.registry_url}/v2/{image_name}/manifests/{tag}"
        
        try:
            logger.debug(f"Getting metadata for {image_name}:{tag}")
            response = requests.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            # Get digest from response headers
            digest = response.headers.get('Docker-Content-Digest', '')
            
            return {
                'tag': tag,
                'digest': digest,
                'size': len(response.content),
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ArtifactResolverError(
                    f"Tag {tag} not found for image {image_name}",
                    registry_type="docker",
                    registry_url=self.registry_url,
                )
            raise ArtifactResolverError(
                f"Failed to get metadata for {image_name}:{tag}: HTTP {e.response.status_code}",
                registry_type="docker",
                registry_url=self.registry_url,
            )
        except requests.exceptions.RequestException as e:
            raise ArtifactResolverError(
                f"Failed to connect to Docker registry: {str(e)}",
                registry_type="docker",
                registry_url=self.registry_url,
            )
