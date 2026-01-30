"""
ArtifactMetadata module for GitLab CI/CD Migration system.

This module provides artifact metadata storage and retrieval.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.git_utils import GitUtils
from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class ArtifactMetadata:
    """
    Storage and retrieval for artifact metadata.
    
    This class manages artifact information including:
    - Component name
    - Artifact tags
    - Git commit SHA
    - Build timestamp
    - Build number
    - Registry URL
    
    Metadata is stored in JSON format for:
    - Change detection
    - Artifact reuse
    - Build traceability
    
    Responsibilities:
    - Store artifact metadata to JSON file
    - Retrieve artifact metadata
    - Query artifacts by component and environment
    - Support artifact reuse in change detection
    """
    
    def __init__(self, metadata_file: str = "/tmp/artifact-metadata.json"):
        """
        Initialize artifact metadata handler.
        
        Args:
            metadata_file: Path to metadata JSON file
        """
        self.metadata_file = Path(metadata_file)
        self.git_utils = GitUtils()
        logger.debug(f"ArtifactMetadata initialized with file: {metadata_file}")
    
    def store_artifact(
        self,
        component_name: str,
        tags: List[str],
        registry_url: str,
        image_name: str,
        environment: str = None,
        additional_info: Dict[str, Any] = None
    ) -> None:
        """
        Store artifact metadata to JSON file.
        
        Args:
            component_name: Name of the component
            tags: List of artifact tags
            registry_url: Registry URL where artifact is stored
            image_name: Image name in registry
            environment: Target environment (optional)
            additional_info: Additional metadata (optional)
        """
        with OperationLogger(logger, f"store artifact metadata for {component_name}"):
            # Load existing metadata
            metadata = self._load_metadata()
            
            # Create artifact entry
            artifact_entry = {
                'component': component_name,
                'tags': tags,
                'registry': registry_url,
                'image': image_name,
                'fullImage': f"{registry_url}/{image_name}:{tags[0]}" if tags else f"{registry_url}/{image_name}",
                'environment': environment,
                'gitCommit': self.git_utils.get_commit_sha(),
                'gitCommitShort': self.git_utils.get_commit_short(),
                'gitBranch': self.git_utils.get_current_branch(),
                'buildTimestamp': datetime.utcnow().isoformat() + 'Z',
                'buildNumber': self._get_build_number(),
            }
            
            # Add additional info if provided
            if additional_info:
                artifact_entry.update(additional_info)
            
            # Add to metadata
            if component_name not in metadata:
                metadata[component_name] = []
            
            metadata[component_name].append(artifact_entry)
            
            # Save metadata
            self._save_metadata(metadata)
            logger.info(f"Stored artifact metadata for {component_name}")
    
    def get_artifact(
        self,
        component_name: str,
        environment: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve latest artifact metadata for a component.
        
        Args:
            component_name: Name of the component
            environment: Target environment (optional, filters by environment)
        
        Returns:
            Artifact metadata dictionary or None if not found
        """
        with OperationLogger(logger, f"retrieve artifact metadata for {component_name}"):
            metadata = self._load_metadata()
            
            if component_name not in metadata:
                logger.debug(f"No artifacts found for {component_name}")
                return None
            
            artifacts = metadata[component_name]
            
            # Filter by environment if specified
            if environment:
                artifacts = [a for a in artifacts if a.get('environment') == environment]
            
            if not artifacts:
                logger.debug(f"No artifacts found for {component_name} in environment {environment}")
                return None
            
            # Return latest artifact (last in list)
            latest_artifact = artifacts[-1]
            logger.debug(f"Found artifact: {latest_artifact.get('fullImage')}")
            return latest_artifact
    
    def get_artifact_by_commit(
        self,
        component_name: str,
        commit_sha: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve artifact metadata for a specific Git commit.
        
        Args:
            component_name: Name of the component
            commit_sha: Git commit SHA (full or short)
        
        Returns:
            Artifact metadata dictionary or None if not found
        """
        with OperationLogger(logger, f"retrieve artifact for commit {commit_sha}"):
            metadata = self._load_metadata()
            
            if component_name not in metadata:
                return None
            
            artifacts = metadata[component_name]
            
            # Search for matching commit
            for artifact in reversed(artifacts):  # Search from newest to oldest
                if artifact.get('gitCommit', '').startswith(commit_sha):
                    logger.debug(f"Found artifact for commit {commit_sha}")
                    return artifact
                if artifact.get('gitCommitShort') == commit_sha:
                    logger.debug(f"Found artifact for commit {commit_sha}")
                    return artifact
            
            logger.debug(f"No artifact found for commit {commit_sha}")
            return None
    
    def get_all_artifacts(
        self,
        component_name: str = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve all artifact metadata.
        
        Args:
            component_name: Optional component name to filter by
        
        Returns:
            Dictionary of component name to list of artifacts
        """
        metadata = self._load_metadata()
        
        if component_name:
            return {component_name: metadata.get(component_name, [])}
        
        return metadata
    
    def get_artifact_tag(
        self,
        component_name: str,
        environment: str = None
    ) -> Optional[str]:
        """
        Get full artifact tag (registry/image:tag) for a component.
        
        Args:
            component_name: Name of the component
            environment: Target environment (optional)
        
        Returns:
            Full artifact tag string or None if not found
        """
        artifact = self.get_artifact(component_name, environment)
        if artifact:
            return artifact.get('fullImage')
        return None
    
    def clear_metadata(self) -> None:
        """
        Clear all artifact metadata.
        
        This removes the metadata file.
        """
        with OperationLogger(logger, "clear artifact metadata"):
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                logger.info("Artifact metadata cleared")
            else:
                logger.debug("No metadata file to clear")
    
    def export_metadata(self, output_file: str) -> None:
        """
        Export metadata to a different file.
        
        Args:
            output_file: Path to output file
        """
        with OperationLogger(logger, f"export metadata to {output_file}"):
            metadata = self._load_metadata()
            output_path = Path(output_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata exported to {output_file}")
    
    def _load_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load metadata from JSON file.
        
        Returns:
            Metadata dictionary
        """
        if not self.metadata_file.exists():
            logger.debug("Metadata file does not exist, returning empty metadata")
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.debug(f"Loaded metadata with {len(metadata)} component(s)")
            return metadata
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    def _save_metadata(self, metadata: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Save metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary to save
        """
        # Ensure parent directory exists
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved metadata to {self.metadata_file}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
    
    def _get_build_number(self) -> str:
        """
        Get build number from CI environment.
        
        Returns:
            Build number or "0" if not in CI environment
        """
        import os
        
        # GitLab CI
        build_number = os.environ.get('CI_PIPELINE_IID')
        if build_number:
            return build_number
        
        # Jenkins
        build_number = os.environ.get('BUILD_NUMBER')
        if build_number:
            return build_number
        
        # GitHub Actions
        build_number = os.environ.get('GITHUB_RUN_NUMBER')
        if build_number:
            return build_number
        
        # Default for local builds
        return "0"
