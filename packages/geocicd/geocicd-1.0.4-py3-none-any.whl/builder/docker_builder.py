"""
DockerBuilder module for GitLab CI/CD Migration system.

This module provides Docker image building functionality with support for
build args, multiple tags, and comprehensive error handling.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.exceptions import BuildError
from utils.logging_config import get_logger, OperationLogger
from utils.artifact_tagger import ArtifactTagger
from utils.artifact_metadata import ArtifactMetadata

logger = get_logger(__name__)


class DockerBuilder:
    """
    Builder for Docker images.
    
    This class handles Docker image building with:
    - Custom Dockerfile and context paths
    - Build arguments
    - Multiple image tags
    - Build output capture
    - Comprehensive error handling
    
    Responsibilities:
    - Execute docker build commands
    - Apply multiple tags to built images
    - Capture and log build output
    - Handle build failures with descriptive errors
    """
    
    def __init__(self):
        """Initialize Docker builder."""
        self.artifact_tagger = ArtifactTagger()
        self.artifact_metadata = ArtifactMetadata()
        logger.debug("DockerBuilder initialized")
    
    def build(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any],
        git_commit: Optional[str] = None
    ) -> str:
        """
        Build Docker image for component.
        
        This method:
        1. Extracts build configuration from component
        2. Constructs docker build command
        3. Executes build in component path
        4. Captures and logs output
        5. Returns the built image tag
        
        Args:
            component: Component configuration with build settings
            config: Full configuration for context (project info, etc.)
            git_commit: Optional Git commit SHA for tagging (defaults to 'latest')
            
        Returns:
            Image tag that was built (e.g., "project-component:abc123")
            
        Raises:
            BuildError: If docker build fails or configuration is invalid
        """
        component_name = component.get('name')
        if not component_name:
            raise BuildError(
                "Component missing 'name' field",
                component=component
            )
        
        with OperationLogger(logger, f"build Docker image for {component_name}"):
            # Get build configuration
            build_config = component.get('build', {})
            artifacts = build_config.get('artifacts', {})
            
            if artifacts.get('type') != 'docker':
                raise BuildError(
                    f"Component {component_name} does not have Docker artifacts configured",
                    component=component_name,
                    artifact_type=artifacts.get('type')
                )
            
            docker_config = artifacts.get('docker', {})
            
            # Extract Docker build parameters
            dockerfile = docker_config.get('dockerfile', 'Dockerfile')
            context = docker_config.get('context', '.')
            build_args = docker_config.get('buildArgs', [])
            component_path = component.get('path', '.')
            
            # Determine image name and tag
            project_name = config.get('project', {}).get('name', 'unknown')
            commit_tag = git_commit or 'latest'
            image_name = f"{project_name}-{component_name}"
            image_tag = f"{image_name}:{commit_tag}"
            
            # Build docker build command
            docker_cmd = self._build_docker_command(
                dockerfile=dockerfile,
                context=context,
                image_tag=image_tag,
                build_args=build_args
            )
            
            logger.info(f"Building Docker image: {image_tag}")
            logger.debug(f"Docker command: {' '.join(docker_cmd)}")
            logger.debug(f"Working directory: {component_path}")
            
            # Execute docker build
            try:
                result = subprocess.run(
                    docker_cmd,
                    cwd=component_path if component_path != '.' else None,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Log output
                if result.stdout:
                    logger.debug(f"Docker build output:\n{result.stdout}")
                
                if result.stderr:
                    logger.debug(f"Docker build stderr:\n{result.stderr}")
                
                # Check for errors
                if result.returncode != 0:
                    raise BuildError(
                        f"Docker build failed for {component_name}",
                        component=component_name,
                        exit_code=result.returncode,
                        command=' '.join(docker_cmd),
                        output=result.stdout,
                        error=result.stderr,
                        suggested_fix="Check Dockerfile syntax and build context"
                    )
                
                logger.info(f"Successfully built Docker image: {image_tag}")
                return image_tag
                
            except FileNotFoundError:
                raise BuildError(
                    "Docker command not found",
                    component=component_name,
                    suggested_fix="Ensure Docker is installed and in PATH"
                )
            except Exception as e:
                if isinstance(e, BuildError):
                    raise
                raise BuildError(
                    f"Unexpected error during Docker build: {e}",
                    component=component_name,
                    error=str(e)
                )
    
    def build_and_tag(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any],
        environment: str = None,
        store_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Build Docker image with automatic tagging and metadata storage.
        
        This method:
        1. Generates appropriate tags using ArtifactTagger
        2. Builds the Docker image
        3. Applies all generated tags
        4. Stores artifact metadata
        5. Returns build information
        
        Args:
            component: Component configuration
            config: Full configuration
            environment: Target environment (optional)
            store_metadata: Whether to store artifact metadata (default: True)
            
        Returns:
            Dictionary with build information:
                - image: Base image name
                - tags: List of applied tags
                - labels: Image labels
                - metadata_stored: Whether metadata was stored
                
        Raises:
            BuildError: If build or tagging fails
        """
        component_name = component.get('name')
        
        with OperationLogger(logger, f"build and tag Docker image for {component_name}"):
            # Generate tags
            tags = self.artifact_tagger.generate_tags(component, config, environment)
            logger.info(f"Generated {len(tags)} tag(s) for {component_name}: {tags}")
            
            # Generate image labels
            labels = self.artifact_tagger.generate_image_labels(component, config)
            logger.debug(f"Generated {len(labels)} label(s)")
            
            # Generate build args (includes version, git info, etc.)
            build_args = self.artifact_tagger.generate_build_args(component, config)
            
            # Update component build args with generated ones
            build_config = component.get('build', {})
            artifacts = build_config.get('artifacts', {})
            docker_config = artifacts.get('docker', {})
            
            # Merge build args
            existing_build_args = docker_config.get('buildArgs', [])
            all_build_args = existing_build_args + build_args
            
            # Create modified component with updated build args
            modified_component = component.copy()
            modified_component['build'] = build_config.copy()
            modified_component['build']['artifacts'] = artifacts.copy()
            modified_component['build']['artifacts']['docker'] = docker_config.copy()
            modified_component['build']['artifacts']['docker']['buildArgs'] = all_build_args
            
            # Build image with first tag
            primary_tag = tags[0] if tags else 'latest'
            base_image = self.build(modified_component, config, primary_tag)
            
            # Apply additional tags
            if len(tags) > 1:
                self.tag_image(base_image, tags[1:])
            
            # Store metadata if requested
            metadata_stored = False
            if store_metadata:
                # Get registry and image name from outputs
                outputs = build_config.get('outputs', [])
                
                if 'docker' in outputs:
                    from utils.output_resolver import OutputResolver
                    output_resolver = OutputResolver()
                    
                    try:
                        server_config = output_resolver.resolve_output(
                            output_type='docker',
                            component=component,
                            environment=environment,
                            config=config
                        )
                        
                        registry_url = server_config.get('pushUrl', '')
                        image_name = component_name
                        
                        self.artifact_metadata.store_artifact(
                            component_name=component_name,
                            tags=tags,
                            registry_url=registry_url,
                            image_name=image_name,
                            environment=environment,
                            additional_info={
                                'labels': labels,
                                'buildArgs': all_build_args
                            }
                        )
                        metadata_stored = True
                        logger.info(f"Stored artifact metadata for {component_name}")
                    except Exception as e:
                        logger.warning(f"Failed to store artifact metadata: {e}")
            
            return {
                'image': base_image,
                'tags': tags,
                'labels': labels,
                'metadata_stored': metadata_stored
            }
    
    def tag_image(self, source_image: str, tags: List[str]) -> None:
        """
        Tag image with multiple tags.
        
        This method applies multiple tags to an existing Docker image.
        Useful for creating version tags, environment tags, and latest tags.
        
        Args:
            source_image: Source image name with tag (e.g., "myapp:abc123")
            tags: List of tags to apply (e.g., ["1.0.0", "latest", "dev"])
            
        Raises:
            BuildError: If docker tag command fails
        """
        if not tags:
            logger.debug(f"No additional tags to apply to {source_image}")
            return
        
        with OperationLogger(logger, f"tag image {source_image} with {len(tags)} tag(s)"):
            # Extract image name without tag
            if ':' in source_image:
                image_name = source_image.rsplit(':', 1)[0]
            else:
                image_name = source_image
            
            for tag in tags:
                target_image = f"{image_name}:{tag}"
                
                logger.debug(f"Tagging {source_image} as {target_image}")
                
                try:
                    result = subprocess.run(
                        ['docker', 'tag', source_image, target_image],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.returncode != 0:
                        raise BuildError(
                            f"Failed to tag image {source_image} as {target_image}",
                            exit_code=result.returncode,
                            command=f"docker tag {source_image} {target_image}",
                            error=result.stderr,
                            suggested_fix="Ensure source image exists"
                        )
                    
                    logger.info(f"Tagged image as {target_image}")
                    
                except FileNotFoundError:
                    raise BuildError(
                        "Docker command not found",
                        suggested_fix="Ensure Docker is installed and in PATH"
                    )
                except Exception as e:
                    if isinstance(e, BuildError):
                        raise
                    raise BuildError(
                        f"Unexpected error during image tagging: {e}",
                        error=str(e)
                    )
    
    def _build_docker_command(
        self,
        dockerfile: str,
        context: str,
        image_tag: str,
        build_args: List[str]
    ) -> List[str]:
        """
        Build docker build command with all parameters.
        
        Args:
            dockerfile: Path to Dockerfile
            context: Build context path
            image_tag: Image name and tag
            build_args: List of build arguments
            
        Returns:
            List of command arguments for subprocess
        """
        cmd = ['docker', 'build']
        
        # Add dockerfile flag
        cmd.extend(['-f', dockerfile])
        
        # Add tag
        cmd.extend(['-t', image_tag])
        
        # Add build args
        for arg in build_args:
            cmd.extend(['--build-arg', arg])
        
        # Add context (must be last)
        cmd.append(context)
        
        return cmd
    
    def image_exists(self, image_tag: str) -> bool:
        """
        Check if Docker image exists locally.
        
        Args:
            image_tag: Image name and tag to check
            
        Returns:
            True if image exists, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', 'image', 'inspect', image_tag],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("Docker command not found")
            return False
        except Exception as e:
            logger.warning(f"Error checking if image exists: {e}")
            return False
    
    def remove_image(self, image_tag: str, force: bool = False) -> None:
        """
        Remove Docker image.
        
        Args:
            image_tag: Image name and tag to remove
            force: Force removal even if image is in use
            
        Raises:
            BuildError: If docker rmi command fails
        """
        logger.debug(f"Removing Docker image: {image_tag}")
        
        cmd = ['docker', 'rmi']
        if force:
            cmd.append('-f')
        cmd.append(image_tag)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise BuildError(
                    f"Failed to remove image {image_tag}",
                    exit_code=result.returncode,
                    command=' '.join(cmd),
                    error=result.stderr
                )
            
            logger.info(f"Removed Docker image: {image_tag}")
            
        except FileNotFoundError:
            raise BuildError(
                "Docker command not found",
                suggested_fix="Ensure Docker is installed and in PATH"
            )
        except Exception as e:
            if isinstance(e, BuildError):
                raise
            raise BuildError(
                f"Unexpected error during image removal: {e}",
                error=str(e)
            )
