"""
Registry client implementations for different Docker registries.

Provides abstract base class and concrete implementations for Nexus, ECR, and DockerHub.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import requests
from requests.auth import HTTPBasicAuth
import subprocess

from utils.exceptions import CICDMigrationError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class ArtifactResolverError(CICDMigrationError):
    """Exception raised when artifact resolution fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        registry_type: Optional[str] = None,
        registry_url: Optional[str] = None,
    ):
        """
        Initialize artifact resolver error.
        
        Args:
            message: Error message
            component: Component name
            registry_type: Type of registry (docker, ecr, dockerhub)
            registry_url: Registry URL
        """
        details = {}
        if component:
            details["component"] = component
        if registry_type:
            details["registry_type"] = registry_type
        if registry_url:
            details["registry_url"] = registry_url
        
        super().__init__(message, details)
        self.component = component
        self.registry_type = registry_type
        self.registry_url = registry_url


class RegistryClient(ABC):
    """Abstract base class for Docker registry API clients."""
    
    @abstractmethod
    def list_tags(self, image_name: str) -> List[str]:
        """
        List all tags for an image in the registry.
        
        Args:
            image_name: Name of the image (without registry URL)
            
        Returns:
            List of tag names
            
        Raises:
            ArtifactResolverError: If listing tags fails
        """
        pass
    
    @abstractmethod
    def get_tag_metadata(self, image_name: str, tag: str) -> Dict[str, Any]:
        """
        Get metadata for a specific image tag.
        
        Args:
            image_name: Name of the image
            tag: Tag name
            
        Returns:
            Dictionary with metadata (created_at, digest, etc.)
            
        Raises:
            ArtifactResolverError: If getting metadata fails
        """
        pass
