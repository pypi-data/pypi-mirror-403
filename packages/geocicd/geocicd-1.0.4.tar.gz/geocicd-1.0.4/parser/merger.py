"""
Merger module for GitLab CI/CD Migration system.

This module provides deep merging of configuration dictionaries with
support for precedence rules and list merging strategies.
"""

import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


class MergeStrategy:
    """Enumeration of list merge strategies."""
    REPLACE = "replace"  # Replace entire list
    APPEND = "append"    # Append items to list
    MERGE = "merge"      # Merge lists by index


class Merger:
    """
    Merges configuration dictionaries with precedence rules.
    
    This class provides deep merging with support for:
    - Nested dictionary merging
    - List merging strategies (replace, append, merge)
    - Precedence rules (environment > defaults > base)
    - Type preservation
    """
    
    def __init__(self, list_strategy: str = MergeStrategy.REPLACE):
        """
        Initialize merger with list merge strategy.
        
        Args:
            list_strategy: Strategy for merging lists (replace, append, merge)
        """
        self.list_strategy = list_strategy
        logger.debug(f"Initialized Merger with list_strategy={list_strategy}")
    
    def merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries with override taking precedence.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary (takes precedence)
            
        Returns:
            Merged configuration dictionary
        """
        logger.debug("Merging configurations")
        
        # Deep copy base to avoid modifying original
        result = deepcopy(base)
        
        # Merge override into result
        self._merge_recursive(result, override)
        
        logger.debug("Configuration merge completed")
        return result
    
    def _merge_recursive(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source into target.
        
        Args:
            target: Target dictionary (modified in place)
            source: Source dictionary to merge from
        """
        for key, source_value in source.items():
            if key in target:
                target_value = target[key]
                
                # Both are dictionaries - merge recursively
                if isinstance(target_value, dict) and isinstance(source_value, dict):
                    self._merge_recursive(target_value, source_value)
                
                # Both are lists - apply list merge strategy
                elif isinstance(target_value, list) and isinstance(source_value, list):
                    target[key] = self._merge_lists(target_value, source_value)
                
                # Different types or primitives - override wins
                else:
                    target[key] = deepcopy(source_value)
            
            else:
                # Key doesn't exist in target - add it
                target[key] = deepcopy(source_value)
    
    def _merge_lists(self, base_list: List[Any], override_list: List[Any]) -> List[Any]:
        """
        Merge two lists according to the configured strategy.
        
        Args:
            base_list: Base list
            override_list: Override list
            
        Returns:
            Merged list
        """
        if self.list_strategy == MergeStrategy.REPLACE:
            # Replace entire list with override
            return deepcopy(override_list)
        
        elif self.list_strategy == MergeStrategy.APPEND:
            # Append override items to base
            result = deepcopy(base_list)
            result.extend(deepcopy(override_list))
            return result
        
        elif self.list_strategy == MergeStrategy.MERGE:
            # Merge lists by index
            result = deepcopy(base_list)
            
            for i, item in enumerate(override_list):
                if i < len(result):
                    # Merge with existing item
                    if isinstance(result[i], dict) and isinstance(item, dict):
                        self._merge_recursive(result[i], item)
                    else:
                        result[i] = deepcopy(item)
                else:
                    # Append new item
                    result.append(deepcopy(item))
            
            return result
        
        else:
            # Unknown strategy - default to replace
            logger.warning(f"Unknown list merge strategy: {self.list_strategy}, using replace")
            return deepcopy(override_list)
    
    def merge_multiple(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configurations with later configs taking precedence.
        
        Args:
            *configs: Variable number of configuration dictionaries
            
        Returns:
            Merged configuration dictionary
        """
        if not configs:
            return {}
        
        if len(configs) == 1:
            return deepcopy(configs[0])
        
        logger.debug(f"Merging {len(configs)} configurations")
        
        # Start with first config
        result = deepcopy(configs[0])
        
        # Merge each subsequent config
        for config in configs[1:]:
            self._merge_recursive(result, config)
        
        logger.debug("Multiple configuration merge completed")
        return result
    
    def merge_with_defaults(
        self,
        config: Dict[str, Any],
        defaults: Dict[str, Any],
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge configuration with defaults, applying environment-specific overrides.
        
        Precedence order (highest to lowest):
        1. Environment-specific configuration
        2. Component/top-level configuration
        3. Environment-specific defaults
        4. Global defaults
        
        Args:
            config: Main configuration
            defaults: Default configuration
            environment: Optional environment name for environment-specific defaults
            
        Returns:
            Merged configuration
        """
        logger.debug(f"Merging configuration with defaults (environment={environment})")
        
        # Start with global defaults
        result = deepcopy(defaults)
        
        # Apply environment-specific defaults if available
        if environment and 'environments' in defaults:
            env_defaults = defaults.get('environments', {}).get(environment, {})
            if env_defaults:
                logger.debug(f"Applying environment-specific defaults for {environment}")
                self._merge_recursive(result, env_defaults)
        
        # Apply main configuration (highest precedence)
        self._merge_recursive(result, config)
        
        logger.debug("Configuration merged with defaults")
        return result
    
    def merge_component_with_defaults(
        self,
        component: Dict[str, Any],
        defaults: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge a component configuration with default values.
        
        Args:
            component: Component configuration
            defaults: Default configuration for components
            
        Returns:
            Component with defaults applied
        """
        logger.debug(f"Merging component '{component.get('name', 'unknown')}' with defaults")
        
        # Start with defaults
        result = deepcopy(defaults)
        
        # Merge component configuration
        self._merge_recursive(result, component)
        
        return result
    
    def merge_environment_config(
        self,
        base_config: Dict[str, Any],
        environment: str,
        env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge environment-specific configuration with base configuration.
        
        Args:
            base_config: Base configuration
            environment: Environment name
            env_config: Environment-specific configuration
            
        Returns:
            Merged configuration for the environment
        """
        logger.debug(f"Merging environment configuration for {environment}")
        
        # Start with base config
        result = deepcopy(base_config)
        
        # Apply environment-specific overrides
        self._merge_recursive(result, env_config)
        
        # Add environment name to result
        result['_environment'] = environment
        
        logger.debug(f"Environment configuration merged for {environment}")
        return result
    
    def apply_component_defaults(
        self,
        components: List[Dict[str, Any]],
        defaults: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply default values to all components.
        
        Args:
            components: List of component configurations
            defaults: Default configuration to apply
            
        Returns:
            List of components with defaults applied
        """
        logger.debug(f"Applying defaults to {len(components)} components")
        
        result = []
        for component in components:
            merged = self.merge_component_with_defaults(component, defaults)
            result.append(merged)
        
        logger.debug("Defaults applied to all components")
        return result
    
    def merge_imports(
        self,
        base_config: Dict[str, Any],
        imported_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge imported configurations with base configuration.
        
        Precedence: base_config > imported_configs (in order)
        
        Args:
            base_config: Base configuration (highest precedence)
            imported_configs: List of imported configurations (in import order)
            
        Returns:
            Merged configuration
        """
        logger.debug(f"Merging base config with {len(imported_configs)} imports")
        
        # Start with empty config
        result = {}
        
        # Merge imports in order (later imports override earlier ones)
        for imported in imported_configs:
            self._merge_recursive(result, imported)
        
        # Finally merge base config (highest precedence)
        self._merge_recursive(result, base_config)
        
        logger.debug("Import merge completed")
        return result
    
    def get_effective_config(
        self,
        component: Dict[str, Any],
        environment: str,
        global_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get the effective configuration for a component in an environment.
        
        This applies all precedence rules:
        1. Component-specific configuration
        2. Environment-specific defaults
        3. Global defaults
        
        Args:
            component: Component configuration
            environment: Environment name
            global_config: Global configuration with defaults and environments
            
        Returns:
            Effective configuration for the component in the environment
        """
        logger.debug(
            f"Computing effective config for component '{component.get('name')}' "
            f"in environment '{environment}'"
        )
        
        # Start with global defaults
        result = {}
        if 'defaults' in global_config:
            result = deepcopy(global_config['defaults'])
        
        # Apply environment-specific defaults
        if 'environments' in global_config:
            env_config = global_config['environments'].get(environment, {})
            if env_config:
                self._merge_recursive(result, env_config)
        
        # Apply component configuration (highest precedence)
        self._merge_recursive(result, component)
        
        # Add metadata
        result['_component'] = component.get('name')
        result['_environment'] = environment
        
        logger.debug("Effective configuration computed")
        return result
    
    def remove_null_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove all null/None values from configuration recursively.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with null values removed
        """
        result = {}
        
        for key, value in config.items():
            if value is None:
                continue
            
            if isinstance(value, dict):
                cleaned = self.remove_null_values(value)
                if cleaned:  # Only add if not empty
                    result[key] = cleaned
            
            elif isinstance(value, list):
                cleaned_list = [
                    self.remove_null_values(item) if isinstance(item, dict) else item
                    for item in value
                    if item is not None
                ]
                if cleaned_list:  # Only add if not empty
                    result[key] = cleaned_list
            
            else:
                result[key] = value
        
        return result
