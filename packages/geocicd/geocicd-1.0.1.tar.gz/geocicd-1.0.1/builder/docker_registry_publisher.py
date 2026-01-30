"""
DockerRegistryPublisher module for GitLab CI/CD Migration system.

This module provides Docker image publishing functionality with support for
multiple registry types (Nexus, AWS ECR, DockerHub) and authentication methods.
"""

import logging
from typing import Any, Dict

from builder.docker_registry_auth import DockerRegistryAuth
from builder.docker_registry_operations import DockerRegistryOperations
from utils.exceptions_build import PublishError
from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class DockerRegistryPublisher:
    """
    Publisher for Docker images to registries.
    
    This class handles Docker image publishing with:
    - Multiple registry types (Nexus, AWS ECR, DockerHub)
    - Username/password authentication
    - AWS ECR authentication with aws ecr get-login-password
    - Multiple tags per destination
    - ECR lifecycle policy configuration
    
    Responsibilities:
    - Authenticate with Docker registries
    - Push images to registries
    - Apply destination-specific tags
    - Configure ECR lifecycle policies
    - Handle authentication and push failures
    """
    
    def __init__(self):
        """Initialize Docker registry publisher."""
        logger.debug("DockerRegistryPublisher initialized")
    
    def publish(
        self,
        component: Dict[str, Any],
        destination: Dict[str, Any],
        config: Dict[str, Any],
        source_image: str
    ) -> None:
        """
        Publish Docker image to registry.
        
        This method:
        1. Authenticates with the registry
        2. Tags the image for the destination
        3. Pushes all configured tags
        4. Configures lifecycle policies (ECR only)
        
        Args:
            component: Component configuration
            destination: Registry destination configuration
            config: Full configuration for context
            source_image: Source image tag to publish (e.g., "myapp:abc123")
            
        Raises:
            PublishError: If authentication or push fails
        """
        component_name = component.get('name')
        dest_type = destination.get('type', 'dockerRegistry')
        dest_name = destination.get('name', 'unknown')
        
        with OperationLogger(
            logger,
            f"publish {component_name} to {dest_name} ({dest_type})"
        ):
            # Get registry configuration
            registry_url = destination.get('url', '')
            image_name = destination.get('imageName', component_name)
            tags = destination.get('tags', ['latest'])
            credentials_name = destination.get('credentials')
            
            if not registry_url:
                raise PublishError(
                    f"Destination {dest_name} missing 'url' field",
                    component=component_name,
                    destination=dest_name
                )
            
            # Authenticate with registry
            DockerRegistryAuth.login(
                registry_url=registry_url,
                credentials_name=credentials_name,
                dest_type=dest_type
            )
            
            # Tag and push for each configured tag
            for tag in tags:
                full_image = f"{registry_url}/{image_name}:{tag}"
                
                # Tag the source image
                logger.debug(f"Tagging {source_image} as {full_image}")
                DockerRegistryOperations.tag_image(source_image, full_image)
                
                # Push the image
                logger.info(f"Pushing {full_image}")
                DockerRegistryOperations.push_image(full_image, component_name)
            
            # Configure ECR lifecycle policy if applicable
            if dest_type == 'awsEcr':
                lifecycle_policy = destination.get('lifecyclePolicy', {})
                if lifecycle_policy.get('enabled', False):
                    DockerRegistryOperations.configure_ecr_lifecycle(
                        registry_url=registry_url,
                        image_name=image_name,
                        lifecycle_policy=lifecycle_policy,
                        component_name=component_name
                    )
            
            logger.info(
                f"Successfully published {component_name} to {dest_name} "
                f"with {len(tags)} tag(s)"
            )
