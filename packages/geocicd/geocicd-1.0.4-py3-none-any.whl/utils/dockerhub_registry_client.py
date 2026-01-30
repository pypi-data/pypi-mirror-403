"""
DockerHub registry client implementation.
"""

import logging
from typing import List, Dict, Any, Optional
import requests

from utils.registry_clients import RegistryClient, ArtifactResolverError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class DockerHubRegistryClient(RegistryClient):
    """Docker registry client for DockerHub."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize DockerHub registry client.
        
        Args:
            username: DockerHub username for authentication
            password: DockerHub password or token for authentication
        """
        self.registry_url = "https://hub.docker.com"
        self.api_url = "https://hub.docker.com/v2"
        self.username = username
        self.password = password
        self.token = None
        
        logger.debug("Initialized DockerHubRegistryClient")
    
    def _authenticate(self) -> None:
        """
        Authenticate with DockerHub and get access token.
        
        Raises:
            ArtifactResolverError: If authentication fails
        """
        if not self.username or not self.password:
            logger.debug("No credentials provided, using anonymous access")
            return
        
        try:
            url = f"{self.api_url}/users/login"
            data = {
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            self.token = response.json().get('token')
            logger.debug("Successfully authenticated with DockerHub")
            
        except requests.exceptions.RequestException as e:
            raise ArtifactResolverError(
                f"Failed to authenticate with DockerHub: {str(e)}",
                registry_type="dockerhub",
                registry_url=self.registry_url,
            )

    
    def list_tags(self, image_name: str) -> List[str]:
        """
        List all tags for an image in DockerHub.
        
        Args:
            image_name: Name of the image (format: namespace/repository or library/repository)
            
        Returns:
            List of tag names
            
        Raises:
            ArtifactResolverError: If listing tags fails
        """
        # Ensure authentication if credentials provided
        if self.username and self.password and not self.token:
            self._authenticate()
        
        # Parse image name (handle library/ prefix for official images)
        if '/' not in image_name:
            image_name = f"library/{image_name}"
        
        try:
            logger.debug(f"Listing tags for {image_name} from DockerHub")
            
            url = f"{self.api_url}/repositories/{image_name}/tags"
            headers = {}
            if self.token:
                headers['Authorization'] = f"Bearer {self.token}"
            
            tags = []
            page = 1
            page_size = 100
            
            while True:
                params = {'page': page, 'page_size': page_size}
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                tags.extend([result['name'] for result in results])
                
                # Check if there are more pages
                if not data.get('next'):
                    break
                
                page += 1
            
            logger.debug(f"Found {len(tags)} tags for {image_name} in DockerHub")
            return tags
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Image {image_name} not found in DockerHub")
                return []
            raise ArtifactResolverError(
                f"Failed to list tags for {image_name}: HTTP {e.response.status_code}",
                registry_type="dockerhub",
                registry_url=self.registry_url,
            )
        except requests.exceptions.RequestException as e:
            raise ArtifactResolverError(
                f"Failed to connect to DockerHub: {str(e)}",
                registry_type="dockerhub",
                registry_url=self.registry_url,
            )

    
    def get_tag_metadata(self, image_name: str, tag: str) -> Dict[str, Any]:
        """
        Get metadata for a specific image tag in DockerHub.
        
        Args:
            image_name: Name of the image
            tag: Tag name
            
        Returns:
            Dictionary with metadata
            
        Raises:
            ArtifactResolverError: If getting metadata fails
        """
        # Ensure authentication if credentials provided
        if self.username and self.password and not self.token:
            self._authenticate()
        
        # Parse image name
        if '/' not in image_name:
            image_name = f"library/{image_name}"
        
        try:
            logger.debug(f"Getting metadata for {image_name}:{tag} from DockerHub")
            
            url = f"{self.api_url}/repositories/{image_name}/tags/{tag}"
            headers = {}
            if self.token:
                headers['Authorization'] = f"Bearer {self.token}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'tag': tag,
                'digest': data.get('digest', ''),
                'last_updated': data.get('last_updated', ''),
                'full_size': data.get('full_size', 0),
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ArtifactResolverError(
                    f"Tag {tag} not found for image {image_name}",
                    registry_type="dockerhub",
                    registry_url=self.registry_url,
                )
            raise ArtifactResolverError(
                f"Failed to get metadata for {image_name}:{tag}: HTTP {e.response.status_code}",
                registry_type="dockerhub",
                registry_url=self.registry_url,
            )
        except requests.exceptions.RequestException as e:
            raise ArtifactResolverError(
                f"Failed to connect to DockerHub: {str(e)}",
                registry_type="dockerhub",
                registry_url=self.registry_url,
            )
