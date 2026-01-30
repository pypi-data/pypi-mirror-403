"""
Configuration defaults application for GitLab CI/CD Migration system.

This module applies default values and patterns to configuration.
"""

import logging
from typing import Any, Dict

from parser.merger import Merger
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigDefaults:
    """
    Configuration defaults applicator.
    
    This class provides:
    - Default value application
    - Branch pattern defaults
    - Comparison branch defaults
    """
    
    def __init__(self):
        """Initialize configuration defaults applicator."""
        self.merger = Merger()
        logger.debug("ConfigDefaults initialized")
    
    def apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values for missing configuration.
        
        This method:
        1. Applies global defaults to all components
        2. Applies environment-specific defaults
        3. Sets sensible defaults for missing fields
        
        Args:
            config: Parsed configuration
            
        Returns:
            Configuration with defaults applied
        """
        logger.info("Applying default values")
        
        result = config.copy()
        
        # Ensure required sections exist
        if 'defaults' not in result:
            result['defaults'] = {}
        
        if 'environments' not in result:
            result['environments'] = {}
        
        if 'components' not in result:
            result['components'] = []
        
        # Apply defaults to components
        if result['components']:
            component_defaults = result['defaults'].get('build', {})
            result['components'] = self.merger.apply_component_defaults(
                result['components'],
                component_defaults
            )
        
        # Apply default branch patterns to environments
        result = self._apply_default_branch_patterns(result)
        
        # Apply default comparison branches
        result = self._apply_default_compare_branches(result)
        
        logger.info("Default values applied")
        return result
    
    def _apply_default_branch_patterns(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default branch patterns to environments without explicit patterns.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with default branch patterns
        """
        from utils.constants import DEFAULT_BRANCH_PATTERNS
        
        for env_name in ['dev', 'stg', 'ese']:
            if env_name in config['environments']:
                env_config = config['environments'][env_name]
                
                # Apply default patterns if not specified
                if 'branches' not in env_config or not env_config['branches']:
                    default_patterns = DEFAULT_BRANCH_PATTERNS.get(env_name, [])
                    env_config['branches'] = default_patterns
                    logger.debug(f"Applied default branch patterns for {env_name}: {default_patterns}")
        
        return config
    
    def _apply_default_compare_branches(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default comparison branches for change detection.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with default comparison branches
        """
        from utils.constants import DEFAULT_COMPARE_BRANCHES
        
        # Ensure changeDetection section exists
        if 'changeDetection' not in config:
            config['changeDetection'] = {}
        
        if 'strategy' not in config['changeDetection']:
            config['changeDetection']['strategy'] = {}
        
        # Apply default comparison branches
        for env_name, default_branch in DEFAULT_COMPARE_BRANCHES.items():
            if env_name not in config['changeDetection']['strategy']:
                config['changeDetection']['strategy'][env_name] = {}
            
            env_strategy = config['changeDetection']['strategy'][env_name]
            
            if 'compareWith' not in env_strategy and default_branch:
                env_strategy['compareWith'] = default_branch
                logger.debug(f"Applied default compareWith branch for {env_name}: {default_branch}")
        
        return config
