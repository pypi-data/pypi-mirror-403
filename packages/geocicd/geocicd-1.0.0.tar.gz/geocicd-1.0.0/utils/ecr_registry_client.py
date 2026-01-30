"""
AWS ECR Docker registry client implementation.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
import subprocess

from utils.registry_clients import RegistryClient, ArtifactResolverError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class ECRRegistryClient(RegistryClient):
    """Docker registry client for AWS ECR."""
    
    def __init__(self, registry_url: str, region: Optional[str] = None):
        """
        Initialize ECR registry client.
        
        Args:
            registry_url: ECR registry URL (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com)
            region: AWS region (extracted from URL if not provided)
        """
        self.registry_url = registry_url.rstrip('/')
        
        # Extract region from URL if not provided
        if region:
            self.region = region
        else:
            # ECR URL format: {account-id}.dkr.ecr.{region}.amazonaws.com
            match = re.search(r'\.ecr\.([^.]+)\.amazonaws\.com', registry_url)
            if match:
                self.region = match.group(1)
            else:
                self.region = 'us-east-1'
        
        logger.debug(f"Initialized ECRRegistryClient for {self.registry_url} in region {self.region}")
    
    def list_tags(self, image_name: str) -> List[str]:
        """
        List all tags for an image in ECR.
        
        Uses AWS CLI to query ECR.
        
        Args:
            image_name: Name of the image (repository name)
            
        Returns:
            List of tag names
            
        Raises:
            ArtifactResolverError: If listing tags fails
        """
        try:
            logger.debug(f"Listing tags for {image_name} in ECR region {self.region}")
            
            # Use AWS CLI to list images
            cmd = [
                'aws', 'ecr', 'describe-images',
                '--repository-name', image_name,
                '--region', self.region,
                '--output', 'json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                if 'RepositoryNotFoundException' in result.stderr:
                    logger.warning(f"Repository {image_name} not found in ECR")
                    return []
                raise ArtifactResolverError(
                    f"Failed to list ECR images: {result.stderr}",
                    registry_type="ecr",
                    registry_url=self.registry_url,
                )
            
            data = json.loads(result.stdout)
            images = data.get('imageDetails', [])
            
            # Extract all tags from all images
            tags = []
            for image in images:
                image_tags = image.get('imageTags', [])
                tags.extend(image_tags)
            
            logger.debug(f"Found {len(tags)} tags for {image_name} in ECR")
            return tags
            
        except subprocess.TimeoutExpired:
            raise ArtifactResolverError(
                f"Timeout while listing ECR images for {image_name}",
                registry_type="ecr",
                registry_url=self.registry_url,
            )
        except json.JSONDecodeError as e:
            raise ArtifactResolverError(
                f"Invalid JSON response from AWS CLI: {str(e)}",
                registry_type="ecr",
                registry_url=self.registry_url,
            )
        except FileNotFoundError:
            raise ArtifactResolverError(
                "AWS CLI not found. Please install AWS CLI to use ECR registry.",
                registry_type="ecr",
                registry_url=self.registry_url,
            )

    
    def get_tag_metadata(self, image_name: str, tag: str) -> Dict[str, Any]:
        """
        Get metadata for a specific image tag in ECR.
        
        Args:
            image_name: Name of the image
            tag: Tag name
            
        Returns:
            Dictionary with metadata
            
        Raises:
            ArtifactResolverError: If getting metadata fails
        """
        try:
            logger.debug(f"Getting metadata for {image_name}:{tag} in ECR")
            
            cmd = [
                'aws', 'ecr', 'describe-images',
                '--repository-name', image_name,
                '--image-ids', f'imageTag={tag}',
                '--region', self.region,
                '--output', 'json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise ArtifactResolverError(
                    f"Failed to get ECR image metadata: {result.stderr}",
                    registry_type="ecr",
                    registry_url=self.registry_url,
                )
            
            data = json.loads(result.stdout)
            images = data.get('imageDetails', [])
            
            if not images:
                raise ArtifactResolverError(
                    f"Tag {tag} not found for image {image_name}",
                    registry_type="ecr",
                    registry_url=self.registry_url,
                )
            
            image = images[0]
            return {
                'tag': tag,
                'digest': image.get('imageDigest', ''),
                'pushed_at': image.get('imagePushedAt', ''),
                'size': image.get('imageSizeInBytes', 0),
            }
            
        except subprocess.TimeoutExpired:
            raise ArtifactResolverError(
                f"Timeout while getting ECR metadata for {image_name}:{tag}",
                registry_type="ecr",
                registry_url=self.registry_url,
            )
        except json.JSONDecodeError as e:
            raise ArtifactResolverError(
                f"Invalid JSON response from AWS CLI: {str(e)}",
                registry_type="ecr",
                registry_url=self.registry_url,
            )
