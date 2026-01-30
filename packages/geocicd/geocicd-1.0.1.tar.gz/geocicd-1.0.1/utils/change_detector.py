"""
Change detection system for GitLab CI/CD Migration.

Identifies modified components to optimize builds by comparing file changes
against component path patterns and environment-specific comparison branches.
"""

import logging
from typing import List, Dict, Any, Optional

from utils.git_utils import GitUtils, GitUtilsError
from utils.pattern_matcher import PatternMatcher
from utils.change_detection_helpers import ChangeDetectionHelpers
from utils.exceptions_base import CICDMigrationError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class ChangeDetectorError(CICDMigrationError):
    """Exception raised when change detection fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        environment: Optional[str] = None,
        comparison_branch: Optional[str] = None,
    ):
        """
        Initialize change detector error.
        
        Args:
            message: Error message
            component: Component name
            environment: Environment name
            comparison_branch: Branch used for comparison
        """
        details = {}
        if component:
            details["component"] = component
        if environment:
            details["environment"] = environment
        if comparison_branch:
            details["comparison_branch"] = comparison_branch
        
        super().__init__(message, details)
        self.component = component
        self.environment = environment
        self.comparison_branch = comparison_branch


class ChangeDetector:
    """
    Detect which components have been modified for optimized builds.
    
    Uses GitUtils to get changed files and PatternMatcher to determine
    if components are affected. Supports environment-specific comparison
    branches for different build strategies.
    
    Environment-specific comparison logic:
    - dev: Always build (no comparison)
    - stg: Compare with develop branch
    - ese: Compare with staging branch
    
    Examples:
        >>> detector = ChangeDetector()
        >>> config = {
        ...     'components': [
        ...         {
        ...             'name': 'frontend',
        ...             'path': 'frontend/',
        ...             'changeDetection': {
        ...                 'enabled': True,
        ...                 'paths': ['frontend/**'],
        ...                 'excludePaths': ['frontend/node_modules/**']
        ...             }
        ...         }
        ...     ],
        ...     'changeDetection': {
        ...         'enabled': True,
        ...         'strategy': {
        ...             'stg': {
        ...                 'enabled': True,
        ...                 'compareWith': 'origin/develop'
        ...             }
        ...         }
        ...     }
        ... }
        >>> changed = detector.get_changed_components('stg', config)
        >>> print(f"Changed components: {changed}")
    """
    
    def __init__(self, repository_path: str = "."):
        """
        Initialize ChangeDetector with repository path.
        
        Args:
            repository_path: Path to Git repository (default: current directory)
            
        Raises:
            ChangeDetectorError: If Git repository initialization fails
        """
        try:
            self.git_utils = GitUtils(repository_path)
            self.helpers = ChangeDetectionHelpers()
            logger.debug(f"Initialized ChangeDetector for repository: {repository_path}")
        except GitUtilsError as e:
            raise ChangeDetectorError(
                f"Failed to initialize ChangeDetector: {str(e)}",
            )
    
    def get_changed_components(
        self,
        environment: str,
        config: Dict[str, Any],
    ) -> List[str]:
        """
        Determine which components have been modified.
        
        Uses environment-specific comparison strategy:
        - dev: Always returns all components (no comparison)
        - stg: Compares with develop branch
        - ese: Compares with staging branch
        - Custom: Uses configured compareWith branch
        
        Args:
            environment: Target environment name (dev, stg, ese)
            config: Full configuration dictionary
            
        Returns:
            List of changed component names
            
        Raises:
            ChangeDetectorError: If change detection fails
            
        Examples:
            >>> detector = ChangeDetector()
            >>> changed = detector.get_changed_components('stg', config)
            >>> print(f"Components to build: {changed}")
        """
        logger.info(f"Detecting changed components for environment: {environment}")
        
        # Check if change detection is enabled globally
        change_detection_config = config.get('changeDetection', {})
        if not change_detection_config.get('enabled', False):
            logger.info("Change detection is disabled globally, building all components")
            return self.helpers.get_all_component_names(config)
        
        # Get environment-specific strategy
        strategy = self.helpers.get_environment_strategy(environment, config)
        
        # If strategy is disabled for this environment, build all components
        if not strategy.get('enabled', True):
            logger.info(f"Change detection disabled for environment '{environment}', building all components")
            return self.helpers.get_all_component_names(config)
        
        # Get comparison branch
        comparison_branch = self.helpers.get_comparison_branch(environment, strategy)
        
        # If no comparison branch (e.g., dev environment), build all components
        if comparison_branch is None:
            logger.info(f"No comparison branch for environment '{environment}', building all components")
            return self.helpers.get_all_component_names(config)
        
        # Get changed files from Git
        try:
            changed_files = self.git_utils.get_changed_files(base_branch=comparison_branch)
            logger.info(
                f"Found {len(changed_files)} changed files compared to '{comparison_branch}'"
            )
        except GitUtilsError as e:
            raise ChangeDetectorError(
                f"Failed to get changed files: {str(e)}",
                environment=environment,
                comparison_branch=comparison_branch,
            )
        
        # Determine which components are affected
        changed_components = []
        components = config.get('components', [])
        
        for component in components:
            component_name = component.get('name', 'unknown')
            
            # Check if component has change detection enabled
            component_change_detection = component.get('changeDetection', {})
            if not component_change_detection.get('enabled', True):
                logger.debug(f"Change detection disabled for component '{component_name}', including in build")
                changed_components.append(component_name)
                continue
            
            # Check if component is changed
            if self.is_component_changed(component, changed_files):
                logger.info(f"Component '{component_name}' has changes")
                changed_components.append(component_name)
            else:
                logger.info(f"Component '{component_name}' has no changes")
        
        logger.info(
            f"Change detection complete: {len(changed_components)} of "
            f"{len(components)} components changed"
        )
        
        return changed_components
    
    def is_component_changed(
        self,
        component: Dict[str, Any],
        changed_files: List[str],
    ) -> bool:
        """
        Check if specific component has changes using pattern matching.
        
        A component is considered changed if any changed file:
        1. Matches at least one include pattern (or component path if no patterns)
        2. Does not match any exclude pattern
        
        Args:
            component: Component configuration dictionary
            changed_files: List of changed file paths
            
        Returns:
            True if component changed, False otherwise
            
        Examples:
            >>> detector = ChangeDetector()
            >>> component = {
            ...     'name': 'frontend',
            ...     'path': 'frontend/',
            ...     'changeDetection': {
            ...         'paths': ['frontend/**/*.js', 'frontend/**/*.vue'],
            ...         'excludePaths': ['frontend/node_modules/**']
            ...     }
            ... }
            >>> changed_files = ['frontend/src/main.js', 'backend/app.py']
            >>> detector.is_component_changed(component, changed_files)
            True
        """
        component_name = component.get('name', 'unknown')
        component_path = component.get('path', '')
        change_detection = component.get('changeDetection', {})
        
        # Get include and exclude patterns
        include_patterns, exclude_patterns = self.helpers.get_component_patterns(component)
        
        logger.debug(
            f"Checking component '{component_name}' with "
            f"{len(include_patterns)} include patterns and "
            f"{len(exclude_patterns)} exclude patterns"
        )
        
        # Create pattern matcher
        matcher = PatternMatcher(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        
        # Check if any changed file matches the component patterns
        for file_path in changed_files:
            if matcher.matches(file_path):
                logger.debug(
                    f"Component '{component_name}' changed: file '{file_path}' matches patterns"
                )
                return True
        
        logger.debug(f"Component '{component_name}' unchanged: no matching files")
        return False
    
    def get_changed_files_for_component(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any],
    ) -> List[str]:
        """
        Get list of changed files that affect a specific component.
        
        This is useful for logging and debugging to see exactly which
        files triggered a component rebuild.
        
        Args:
            component: Component configuration dictionary
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            List of changed file paths that match component patterns
            
        Raises:
            ChangeDetectorError: If change detection fails
            
        Examples:
            >>> detector = ChangeDetector()
            >>> component = {'name': 'frontend', 'path': 'frontend/'}
            >>> files = detector.get_changed_files_for_component(component, 'stg', config)
            >>> print(f"Changed files: {files}")
        """
        # Get environment strategy and comparison branch
        strategy = self.helpers.get_environment_strategy(environment, config)
        comparison_branch = self.helpers.get_comparison_branch(environment, strategy)
        
        if comparison_branch is None:
            logger.debug("No comparison branch, returning empty list")
            return []
        
        # Get changed files from Git
        try:
            changed_files = self.git_utils.get_changed_files(base_branch=comparison_branch)
        except GitUtilsError as e:
            raise ChangeDetectorError(
                f"Failed to get changed files: {str(e)}",
                component=component.get('name'),
                environment=environment,
                comparison_branch=comparison_branch,
            )
        
        # Get component patterns
        component_path = component.get('path', '')
        change_detection = component.get('changeDetection', {})
        
        include_patterns = change_detection.get('paths', [])
        if not include_patterns and component_path:
            normalized_path = component_path.rstrip('/').replace('\\', '/')
            include_patterns = [f"{normalized_path}/**"]
        
        exclude_patterns = change_detection.get('excludePaths', [])
        
        # Filter changed files using pattern matcher
        matcher = PatternMatcher(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        
        matching_files = matcher.filter_files(changed_files)
        
        logger.debug(
            f"Component '{component.get('name')}' has {len(matching_files)} "
            f"changed files out of {len(changed_files)} total changes"
        )
        
        return matching_files
    
    def should_build_component(
        self,
        component_name: str,
        environment: str,
        config: Dict[str, Any],
    ) -> bool:
        """
        Determine if a component should be built for the given environment.
        
        This is a convenience method that combines change detection logic
        into a single boolean decision.
        
        Args:
            component_name: Name of the component
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            True if component should be built, False otherwise
            
        Examples:
            >>> detector = ChangeDetector()
            >>> if detector.should_build_component('frontend', 'stg', config):
            ...     print("Building frontend component")
        """
        changed_components = self.get_changed_components(environment, config)
        should_build = component_name in changed_components
        
        logger.debug(
            f"Component '{component_name}' should {'be built' if should_build else 'be skipped'} "
            f"for environment '{environment}'"
        )
        
        return should_build
    
    def get_last_successful_artifact(
        self,
        component: str,
        environment: str,
        config: Dict[str, Any],
    ) -> str:
        """
        Retrieve last successful artifact tag for unchanged component.
        
        This method delegates to ArtifactResolver to query the configured
        registry for the most recent successful artifact.
        
        Args:
            component: Component name
            environment: Environment name
            config: Full configuration dictionary
            
        Returns:
            Full artifact tag (registry/image:tag)
            
        Raises:
            ArtifactNotFoundError: If no successful artifact exists
            ArtifactResolverError: If registry query fails
            
        Examples:
            >>> detector = ChangeDetector()
            >>> artifact = detector.get_last_successful_artifact('backend', 'stg', config)
            >>> print(f"Reusing artifact: {artifact}")
        """
        # Import here to avoid circular dependency
        from utils.artifact_resolver import ArtifactResolver
        
        logger.info(f"Retrieving last successful artifact for '{component}' in '{environment}'")
        
        resolver = ArtifactResolver()
        artifact = resolver.get_last_successful_artifact(component, environment, config)
        
        logger.info(f"Will reuse artifact: {artifact}")
        
        return artifact
