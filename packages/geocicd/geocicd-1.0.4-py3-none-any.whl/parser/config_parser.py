"""
ConfigParser module for GitLab CI/CD Migration system.

This module provides the main entry point for parsing, validating,
and processing ci-config.yaml configuration files.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from parser.config_loader import ConfigLoader
from parser.config_defaults import ConfigDefaults
from parser.interpolator import Interpolator
from parser.merger import Merger
from parser.validator import Validator
from utils.exceptions_base import ValidationError, InterpolationError
from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class ConfigParser:
    """
    Main configuration parser that orchestrates validation, interpolation, and merging.
    
    This class provides:
    - YAML file parsing
    - JSON schema validation
    - Variable interpolation
    - Import resolution
    - Default value application
    - Circular import detection
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize configuration parser.
        
        Args:
            schema_path: Optional path to JSON schema file
        """
        self.validator = Validator(schema_path)
        self.interpolator = Interpolator()
        self.merger = Merger()
        self.loader = ConfigLoader()
        self.defaults = ConfigDefaults()
        logger.debug("ConfigParser initialized")

    def parse(self, config_file: str) -> Dict[str, Any]:
        """
        Parse configuration file and return validated config.
        
        This method orchestrates the complete parsing workflow:
        1. Load YAML file
        2. Resolve imports
        3. Resolve server references
        4. Apply defaults
        5. Resolve variable interpolations
        6. Validate against schema
        
        Args:
            config_file: Path to ci-config.yaml
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValidationError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist
            InterpolationError: If variable resolution fails
            ConfigImportError: If import resolution fails
        """
        with OperationLogger(logger, "parse configuration", file=config_file):
            # Load YAML file
            config = self.loader.load_yaml(config_file)
            
            # Resolve imports
            if 'imports' in config:
                config = self.loader.load_imports(config, config_file)
            
            # Resolve server references
            config = self.loader.resolve_servers(config)
            
            # Apply defaults
            config = self.defaults.apply_defaults(config)
            
            # Build interpolation context
            context = self.interpolator.build_context(config)
            
            # Check for undefined variables before resolving
            undefined_vars = self.interpolator.find_undefined_variables(config, context)
            if undefined_vars:
                raise InterpolationError(
                    f"Found {len(undefined_vars)} undefined variable(s)",
                    missing_variables=undefined_vars
                )
            
            # Resolve interpolations
            config = self.interpolator.resolve(config, context)
            
            # Validate against schema
            self.validator.validate_all(config, config_file)
            
            logger.info("Configuration parsed and validated successfully")
            return config

    def parse_dict(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse configuration from dictionary (for testing or programmatic use).
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration
            
        Raises:
            ValidationError: If configuration is invalid
            InterpolationError: If variable resolution fails
        """
        logger.info("Parsing configuration from dictionary")
        
        # Apply defaults
        config = self.defaults.apply_defaults(config)
        
        # Build interpolation context
        context = self.interpolator.build_context(config)
        
        # Check for undefined variables
        undefined_vars = self.interpolator.find_undefined_variables(config, context)
        if undefined_vars:
            raise InterpolationError(
                f"Found {len(undefined_vars)} undefined variable(s)",
                missing_variables=undefined_vars
            )
        
        # Resolve interpolations
        config = self.interpolator.resolve(config, context)
        
        # Validate against schema
        self.validator.validate_all(config)
        
        logger.info("Configuration parsed from dictionary successfully")
        return config
    
    def validate_only(self, config_file: str) -> None:
        """
        Validate configuration file without full parsing.
        
        This is useful for quick validation checks.
        
        Args:
            config_file: Path to ci-config.yaml
            
        Raises:
            ValidationError: If configuration is invalid
        """
        logger.info(f"Validating configuration file: {config_file}")
        
        # Load YAML
        config = self.loader.load_yaml(config_file)
        
        # Validate against schema
        self.validator.validate_all(config, config_file)
        
        logger.info("Configuration validation passed")
    
    def get_component_config(
        self,
        config: Dict[str, Any],
        component_name: str,
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get effective configuration for a specific component.
        
        Args:
            config: Full parsed configuration
            component_name: Name of component
            environment: Optional environment name for environment-specific config
            
        Returns:
            Component configuration with defaults and environment overrides applied
            
        Raises:
            ValueError: If component not found
        """
        # Find component
        component = None
        for comp in config.get('components', []):
            if comp.get('name') == component_name:
                component = comp
                break
        
        if not component:
            raise ValueError(f"Component not found: {component_name}")
        
        # Get effective config
        if environment:
            return self.merger.get_effective_config(component, environment, config)
        else:
            return component
    
    def get_environment_config(
        self,
        config: Dict[str, Any],
        environment: str
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific environment.
        
        Args:
            config: Full parsed configuration
            environment: Environment name (dev, stg, ese)
            
        Returns:
            Environment configuration
            
        Raises:
            ValueError: If environment not found
        """
        if environment not in config.get('environments', {}):
            raise ValueError(f"Environment not found: {environment}")
        
        return config['environments'][environment]
    
    def list_components(self, config: Dict[str, Any]) -> List[str]:
        """
        Get list of all component names.
        
        Args:
            config: Parsed configuration
            
        Returns:
            List of component names
        """
        return [comp.get('name') for comp in config.get('components', [])]
    
    def list_environments(self, config: Dict[str, Any]) -> List[str]:
        """
        Get list of all environment names.
        
        Args:
            config: Parsed configuration
            
        Returns:
            List of environment names
        """
        return list(config.get('environments', {}).keys())
    
    def serialize(self, config: Dict[str, Any]) -> str:
        """
        Serialize configuration back to YAML string.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            YAML string
        """
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    def save(self, config: Dict[str, Any], output_file: str) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration dictionary
            output_file: Path to output file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {output_file}")
