"""
ArtifactTagger module for GitLab CI/CD Migration system.

This module provides artifact tagging functionality.
"""

import os
from typing import Any, Dict, List

from utils.git_utils import GitUtils
from utils.logging_config import get_logger, OperationLogger
from utils.version_extractor import VersionExtractor

logger = get_logger(__name__)


class ArtifactTagger:
    """
    Tagger for Docker artifacts and other build outputs.
    
    This class generates artifact tags using:
    - Version from configuration or project files
    - Branch name from Git
    - Build number from CI environment
    - Git commit SHA
    
    Tag patterns:
    - {version}.{branch}.{build_number}
    - {branch}-latest
    - {version}
    
    Responsibilities:
    - Generate artifact tags based on patterns
    - Include Git commit SHA in image labels
    - Support multiple tag formats
    - Provide consistent tagging across components
    """
    
    def __init__(self):
        """Initialize artifact tagger."""
        self.git_utils = GitUtils()
        self.version_extractor = VersionExtractor()
        logger.debug("ArtifactTagger initialized")
    
    def generate_tags(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any],
        environment: str = None
    ) -> List[str]:
        """
        Generate artifact tags for a component.
        
        Generates multiple tags:
        1. {version}.{branch}.{build_number} - Full versioned tag
        2. {branch}-latest - Latest for branch
        3. {version} - Version only (optional)
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
            environment: Target environment (optional)
        
        Returns:
            List of tag strings
        """
        with OperationLogger(logger, f"generate tags for {component.get('name')}"):
            tags = []
            
            # Extract version
            version = self.version_extractor.extract_version(component, config)
            
            # Get branch name
            branch = self.git_utils.get_current_branch()
            branch_safe = self._sanitize_tag_component(branch)
            
            # Get build number from CI environment
            build_number = self._get_build_number()
            
            # Generate full versioned tag: {version}.{branch}.{build_number}
            full_tag = f"{version}.{branch_safe}.{build_number}"
            tags.append(full_tag)
            logger.debug(f"Generated full tag: {full_tag}")
            
            # Generate branch-latest tag: {branch}-latest
            branch_latest_tag = f"{branch_safe}-latest"
            tags.append(branch_latest_tag)
            logger.debug(f"Generated branch-latest tag: {branch_latest_tag}")
            
            # Generate version-only tag (optional, for releases)
            if self._is_release_branch(branch):
                version_tag = version
                tags.append(version_tag)
                logger.debug(f"Generated version tag: {version_tag}")
            
            logger.info(f"Generated {len(tags)} tag(s) for {component.get('name')}")
            return tags
    
    def generate_image_labels(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate Docker image labels including Git commit SHA.
        
        Labels include:
        - git.commit.sha: Full Git commit SHA
        - git.commit.short: Short Git commit SHA
        - git.branch: Branch name
        - version: Component version
        - build.timestamp: Build timestamp
        - component.name: Component name
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
        
        Returns:
            Dictionary of label key-value pairs
        """
        with OperationLogger(logger, f"generate image labels for {component.get('name')}"):
            labels = {}
            
            # Git information
            commit_sha = self.git_utils.get_commit_sha()
            commit_short = self.git_utils.get_commit_short()
            branch = self.git_utils.get_current_branch()
            
            labels['git.commit.sha'] = commit_sha
            labels['git.commit.short'] = commit_short
            labels['git.branch'] = branch
            
            # Version information
            version = self.version_extractor.extract_version(component, config)
            labels['version'] = version
            
            # Build information
            labels['build.timestamp'] = self._get_build_timestamp()
            labels['build.number'] = self._get_build_number()
            
            # Component information
            labels['component.name'] = component.get('name', '')
            labels['component.type'] = component.get('type', '')
            
            # Project information
            project = config.get('project', {})
            if project.get('name'):
                labels['project.name'] = project['name']
            if project.get('organization'):
                labels['project.organization'] = project['organization']
            
            logger.debug(f"Generated {len(labels)} image label(s)")
            return labels
    
    def generate_build_args(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Generate Docker build args including version and Git info.
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
        
        Returns:
            List of build arg strings in format "KEY=VALUE"
        """
        with OperationLogger(logger, "generate Docker build args"):
            build_args = []
            
            # Version
            version = self.version_extractor.extract_version(component, config)
            build_args.append(f"VERSION={version}")
            
            # Git information
            commit_sha = self.git_utils.get_commit_sha()
            commit_short = self.git_utils.get_commit_short()
            branch = self.git_utils.get_current_branch()
            
            build_args.append(f"GIT_COMMIT={commit_sha}")
            build_args.append(f"GIT_COMMIT_SHORT={commit_short}")
            build_args.append(f"GIT_BRANCH={branch}")
            
            # Build information
            build_args.append(f"BUILD_TIMESTAMP={self._get_build_timestamp()}")
            build_args.append(f"BUILD_NUMBER={self._get_build_number()}")
            
            # Add custom build args from component configuration
            custom_build_args = component.get('build', {}).get('artifacts', {}).get('docker', {}).get('buildArgs', [])
            for arg in custom_build_args:
                if '=' in arg:
                    build_args.append(arg)
                else:
                    logger.warning(f"Invalid build arg format (expected KEY=VALUE): {arg}")
            
            logger.debug(f"Generated {len(build_args)} build arg(s)")
            return build_args
    
    def _sanitize_tag_component(self, component: str) -> str:
        """
        Sanitize a tag component to be Docker-compatible.
        
        Docker tags must:
        - Be lowercase
        - Contain only [a-z0-9._-]
        - Not start with . or -
        
        Args:
            component: Tag component to sanitize
        
        Returns:
            Sanitized tag component
        """
        # Convert to lowercase
        component = component.lower()
        
        # Replace invalid characters with dash
        import re
        component = re.sub(r'[^a-z0-9._-]', '-', component)
        
        # Remove leading dots and dashes
        component = component.lstrip('.-')
        
        # Collapse multiple dashes
        component = re.sub(r'-+', '-', component)
        
        return component
    
    def _get_build_number(self) -> str:
        """
        Get build number from CI environment.
        
        Checks multiple CI environment variables:
        - CI_PIPELINE_IID (GitLab)
        - BUILD_NUMBER (Jenkins)
        - GITHUB_RUN_NUMBER (GitHub Actions)
        
        Returns:
            Build number or "0" if not in CI environment
        """
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
    
    def _get_build_timestamp(self) -> str:
        """
        Get current build timestamp in ISO format.
        
        Returns:
            ISO format timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def _is_release_branch(self, branch: str) -> bool:
        """
        Check if branch is a release branch.
        
        Release branches:
        - main
        - master
        - release/*
        - v*.*.*
        
        Args:
            branch: Branch name
        
        Returns:
            True if release branch, False otherwise
        """
        release_patterns = [
            'main',
            'master',
        ]
        
        # Exact match
        if branch in release_patterns:
            return True
        
        # Pattern match
        if branch.startswith('release/'):
            return True
        
        # Version tag pattern
        import re
        if re.match(r'^v?\d+\.\d+\.\d+', branch):
            return True
        
        return False
