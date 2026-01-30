"""
Docker registry operations module for GitLab CI/CD Migration system.

This module provides Docker image operations including tagging, pushing,
and ECR lifecycle policy configuration.
"""

import json
import logging
import subprocess
from typing import Any, Dict

from utils.exceptions_build import PublishError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DockerRegistryOperations:
    """
    Operations handler for Docker images and registries.
    
    This class handles:
    - Image tagging
    - Image pushing to registries
    - ECR lifecycle policy configuration
    
    Responsibilities:
    - Tag Docker images
    - Push images to registries
    - Configure ECR lifecycle policies
    - Handle operation failures
    """
    
    @staticmethod
    def tag_image(source_image: str, target_image: str) -> None:
        """
        Tag Docker image.
        
        Args:
            source_image: Source image tag
            target_image: Target image tag
            
        Raises:
            PublishError: If tagging fails
        """
        try:
            result = subprocess.run(
                ['docker', 'tag', source_image, target_image],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise PublishError(
                    f"Failed to tag image {source_image} as {target_image}",
                    exit_code=result.returncode,
                    command=f"docker tag {source_image} {target_image}",
                    error=result.stderr,
                    suggested_fix="Ensure source image exists"
                )
                
        except FileNotFoundError:
            raise PublishError(
                "Docker command not found",
                suggested_fix="Ensure Docker is installed and in PATH"
            )
    
    @staticmethod
    def push_image(image: str, component_name: str) -> None:
        """
        Push Docker image to registry.
        
        Args:
            image: Full image name with registry and tag
            component_name: Component name for error messages
            
        Raises:
            PublishError: If push fails
        """
        try:
            result = subprocess.run(
                ['docker', 'push', image],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Log output
            if result.stdout:
                logger.debug(f"Docker push output:\n{result.stdout}")
            
            if result.stderr:
                logger.debug(f"Docker push stderr:\n{result.stderr}")
            
            if result.returncode != 0:
                raise PublishError(
                    f"Failed to push image {image}",
                    component=component_name,
                    image=image,
                    exit_code=result.returncode,
                    command=f"docker push {image}",
                    output=result.stdout,
                    error=result.stderr,
                    suggested_fix="Verify registry authentication and network connectivity"
                )
            
            logger.info(f"Successfully pushed {image}")
            
        except FileNotFoundError:
            raise PublishError(
                "Docker command not found",
                suggested_fix="Ensure Docker is installed and in PATH"
            )
    
    @staticmethod
    def configure_ecr_lifecycle(
        registry_url: str,
        image_name: str,
        lifecycle_policy: Dict[str, Any],
        component_name: str
    ) -> None:
        """
        Configure ECR lifecycle policy.
        
        Args:
            registry_url: ECR registry URL
            image_name: Image name (repository name)
            lifecycle_policy: Lifecycle policy configuration
            component_name: Component name for logging
            
        Raises:
            PublishError: If policy configuration fails
        """
        keep_last_images = lifecycle_policy.get('keepLastImages', 10)
        
        logger.info(
            f"Configuring ECR lifecycle policy for {image_name}: "
            f"keep last {keep_last_images} images"
        )
        
        # Extract region from ECR URL
        region = DockerRegistryOperations._extract_ecr_region(registry_url)
        if not region:
            logger.warning(f"Cannot extract region from ECR URL: {registry_url}")
            return
        
        # Create lifecycle policy JSON
        policy = {
            "rules": [
                {
                    "rulePriority": 1,
                    "description": f"Keep last {keep_last_images} images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": keep_last_images
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }
        
        policy_json = json.dumps(policy)
        
        # Apply lifecycle policy
        try:
            result = subprocess.run(
                [
                    'aws', 'ecr', 'put-lifecycle-policy',
                    '--repository-name', image_name,
                    '--lifecycle-policy-text', policy_json,
                    '--region', region
                ],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                # Log warning but don't fail the publish
                logger.warning(
                    f"Failed to configure ECR lifecycle policy for {image_name}: "
                    f"{result.stderr}"
                )
            else:
                logger.info(f"Successfully configured ECR lifecycle policy for {image_name}")
                
        except FileNotFoundError:
            logger.warning("AWS CLI not found, skipping lifecycle policy configuration")
        except Exception as e:
            logger.warning(f"Error configuring ECR lifecycle policy: {e}")
    
    @staticmethod
    def _extract_ecr_region(registry_url: str) -> str:
        """
        Extract AWS region from ECR registry URL.
        
        Args:
            registry_url: ECR registry URL
            
        Returns:
            AWS region string or empty string if extraction fails
        """
        # Format: <account-id>.dkr.ecr.<region>.amazonaws.com
        parts = registry_url.split('.')
        if len(parts) >= 4 and 'ecr' in parts:
            return parts[3]
        return ""
