"""
Change detection helper functions for GitLab CI/CD Migration system.

This module provides helper functions for change detection including
environment strategy resolution and comparison branch determination.
"""

import logging
from typing import Any, Dict, List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ChangeDetectionHelpers:
    """
    Helper functions for change detection.
    
    This class provides:
    - Environment strategy resolution
    - Comparison branch determination
    - Component list extraction
    """
    
    @staticmethod
    def get_all_component_names(config: Dict[str, Any]) -> List[str]:
        """
        Get list of all component names from configuration.
        
        Args:
            config: Full configuration dictionary
            
        Returns:
            List of all component names
        """
        components = config.get('components', [])
        return [component.get('name', 'unknown') for component in components]
    
    @staticmethod
    def get_environment_strategy(
        environment: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get change detection strategy for specific environment.
        
        Args:
            environment: Environment name
            config: Full configuration dictionary
            
        Returns:
            Strategy configuration dictionary
        """
        change_detection_config = config.get('changeDetection', {})
        strategies = change_detection_config.get('strategy', {})
        
        # Get environment-specific strategy
        strategy = strategies.get(environment, {})
        
        logger.debug(f"Strategy for environment '{environment}': {strategy}")
        return strategy
    
    @staticmethod
    def get_comparison_branch(
        environment: str,
        strategy: Dict[str, Any],
    ) -> Optional[str]:
        """
        Get comparison branch for environment.
        
        Uses environment-specific defaults if not explicitly configured:
        - dev: None (always build)
        - stg: origin/develop
        - ese: origin/staging
        
        Args:
            environment: Environment name
            strategy: Strategy configuration for environment
            
        Returns:
            Comparison branch name or None for always build
        """
        # Check if explicitly configured
        comparison_branch = strategy.get('compareWith')
        
        if comparison_branch:
            logger.debug(
                f"Using configured comparison branch for '{environment}': {comparison_branch}"
            )
            return comparison_branch
        
        # Apply environment-specific defaults
        default_branches = {
            'dev': None,  # Always build
            'stg': 'origin/develop',
            'ese': 'origin/staging',
        }
        
        default_branch = default_branches.get(environment)
        
        if default_branch:
            logger.debug(
                f"Using default comparison branch for '{environment}': {default_branch}"
            )
        else:
            logger.debug(
                f"No default comparison branch for '{environment}', will build all components"
            )
        
        return default_branch
    
    @staticmethod
    def get_component_patterns(component: Dict[str, Any]) -> tuple:
        """
        Get include and exclude patterns for component.
        
        Args:
            component: Component configuration dictionary
            
        Returns:
            Tuple of (include_patterns, exclude_patterns)
        """
        component_path = component.get('path', '')
        change_detection = component.get('changeDetection', {})
        
        # Get include patterns (default to component path if not specified)
        include_patterns = change_detection.get('paths', [])
        if not include_patterns:
            # Default pattern: match all files in component path
            if component_path:
                # Normalize path and create pattern
                normalized_path = component_path.rstrip('/').replace('\\', '/')
                include_patterns = [f"{normalized_path}/**"]
            else:
                # No path specified, match all files
                include_patterns = ["**"]
        
        # Get exclude patterns
        exclude_patterns = change_detection.get('excludePaths', [])
        
        return include_patterns, exclude_patterns
