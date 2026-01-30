"""
Validator module for GitLab CI/CD Migration system.

This module provides configuration validation against JSON schema
and custom validation rules for branch patterns and other constraints.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import Draft7Validator, validators

from utils.exceptions import ValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Validator:
    """
    Validates configuration against JSON schema and custom rules.
    
    This class provides comprehensive validation including:
    - JSON schema validation
    - Branch pattern syntax validation
    - Custom business rule validation
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize validator with JSON schema.
        
        Args:
            schema_path: Path to JSON schema file. If None, uses default schema.
        """
        self.schema_path = schema_path or "schemas/ci-config.schema.json"
        self.schema = self._load_schema()
        self.validator = self._create_validator()
    
    def _load_schema(self) -> Dict[str, Any]:
        """
        Load JSON schema from file.
        
        Returns:
            Parsed JSON schema dictionary
            
        Raises:
            ValidationError: If schema file cannot be loaded
        """
        schema_file = Path(self.schema_path)
        
        if not schema_file.exists():
            raise ValidationError(
                f"Schema file not found: {self.schema_path}",
                file_path=self.schema_path,
                suggested_fix="Ensure the schema file exists in the schemas/ directory"
            )
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.debug(f"Loaded schema from {self.schema_path}")
            return schema
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON in schema file: {e}",
                file_path=self.schema_path,
                line_number=e.lineno,
                column_number=e.colno,
                suggested_fix="Fix JSON syntax errors in schema file"
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to load schema: {e}",
                file_path=self.schema_path
            )
    
    def _create_validator(self) -> Draft7Validator:
        """
        Create JSON schema validator with custom error handling.
        
        Returns:
            Configured Draft7Validator instance
        """
        # Extend validator to provide better error messages
        def set_defaults(validator, properties, instance, schema):
            """Set default values for missing properties."""
            for property, subschema in properties.items():
                if "default" in subschema:
                    instance.setdefault(property, subschema["default"])
            
            # Continue with normal validation
            for error in validators.Draft7Validator.VALIDATORS["properties"](
                validator, properties, instance, schema
            ):
                yield error
        
        # Create validator with extended functionality
        all_validators = dict(Draft7Validator.VALIDATORS)
        all_validators["properties"] = set_defaults
        
        ValidatorWithDefaults = validators.create(
            meta_schema=Draft7Validator.META_SCHEMA,
            validators=all_validators
        )
        
        return ValidatorWithDefaults(self.schema)
    
    def validate(self, config: Dict[str, Any], config_file: Optional[str] = None) -> None:
        """
        Validate configuration against JSON schema.
        
        Args:
            config: Configuration dictionary to validate
            config_file: Optional path to config file for error reporting
            
        Raises:
            ValidationError: If configuration is invalid with detailed error messages
        """
        logger.info("Validating configuration against JSON schema")
        
        # Collect all validation errors
        errors = list(self.validator.iter_errors(config))
        
        if not errors:
            logger.info("Configuration passed JSON schema validation")
            return
        
        # Format all validation errors
        violations = []
        for error in errors:
            # Build path to the error location
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
            
            # Format error message
            violation = f"{path}: {error.message}"
            violations.append(violation)
            
            # Log each violation
            logger.error(f"Validation error at {path}: {error.message}")
        
        # Raise comprehensive validation error
        raise ValidationError(
            f"Configuration validation failed with {len(violations)} error(s)",
            file_path=config_file,
            violations=violations,
            suggested_fix="Review the configuration against the schema requirements"
        )
    
    def validate_branch_patterns(self, patterns: List[str]) -> None:
        """
        Validate branch pattern syntax.
        
        Supports:
        - Exact matches: "develop", "main"
        - Wildcard suffix: "develop-*", "feature-*"
        - Path patterns: "release/*", "hotfix/*"
        
        Args:
            patterns: List of branch patterns to validate
            
        Raises:
            ValidationError: If any pattern has invalid syntax
        """
        logger.debug(f"Validating {len(patterns)} branch patterns")
        
        invalid_patterns = []
        
        for pattern in patterns:
            if not self._is_valid_branch_pattern(pattern):
                invalid_patterns.append(pattern)
                logger.error(f"Invalid branch pattern: {pattern}")
        
        if invalid_patterns:
            raise ValidationError(
                f"Invalid branch pattern syntax",
                violations=[f"Invalid pattern: {p}" for p in invalid_patterns],
                suggested_fix=(
                    "Branch patterns must be:\n"
                    "  - Exact: 'develop', 'main'\n"
                    "  - Wildcard suffix: 'develop-*', 'feature-*'\n"
                    "  - Path pattern: 'release/*', 'hotfix/*'"
                )
            )
        
        logger.debug("All branch patterns are valid")
    
    def _is_valid_branch_pattern(self, pattern: str) -> bool:
        """
        Check if a branch pattern has valid syntax.
        
        Args:
            pattern: Branch pattern to check
            
        Returns:
            True if pattern is valid, False otherwise
        """
        if not pattern or not isinstance(pattern, str):
            return False
        
        # Pattern must not be empty or only whitespace
        if not pattern.strip():
            return False
        
        # Pattern must not contain invalid characters
        # Valid characters: alphanumeric, dash, underscore, slash, asterisk
        if not re.match(r'^[a-zA-Z0-9\-_/*]+$', pattern):
            return False
        
        # Asterisk can only appear at the end or after a slash
        asterisk_positions = [i for i, c in enumerate(pattern) if c == '*']
        for pos in asterisk_positions:
            # Must be at end or followed by nothing
            if pos != len(pattern) - 1:
                return False
            # If not at start, must be preceded by dash or slash
            if pos > 0 and pattern[pos - 1] not in ['-', '/']:
                return False
        
        # Multiple consecutive slashes not allowed
        if '//' in pattern:
            return False
        
        # Pattern must not start or end with slash
        if pattern.startswith('/') or pattern.endswith('/'):
            return False
        
        return True
    
    def validate_component_types(self, components: List[Dict[str, Any]]) -> None:
        """
        Validate that all components have valid types.
        
        Args:
            components: List of component configurations
            
        Raises:
            ValidationError: If any component has invalid type
        """
        valid_types = {
            'vue', 'angular', 'react', 'npm', 'nginx',
            'maven', 'gradle', 'python', 'php', 'docker',
            'cordova', 'phoenix', 'ramani',
            'fastapi', 'django', 'flask',
            'go', 'rust', 'dotnet'
        }
        
        invalid_components = []
        
        for component in components:
            comp_type = component.get('type')
            if comp_type and comp_type not in valid_types:
                invalid_components.append({
                    'name': component.get('name', 'unknown'),
                    'type': comp_type
                })
        
        if invalid_components:
            violations = [
                f"Component '{c['name']}' has invalid type '{c['type']}'"
                for c in invalid_components
            ]
            raise ValidationError(
                "Invalid component types found",
                violations=violations,
                suggested_fix=f"Valid types are: {', '.join(sorted(valid_types))}"
            )
    
    def validate_environment_names(self, environments: Dict[str, Any]) -> None:
        """
        Validate environment names.
        
        Args:
            environments: Dictionary of environment configurations
            
        Raises:
            ValidationError: If any environment name is invalid
        """
        valid_environments = {'dev', 'stg', 'ese'}
        invalid_envs = [env for env in environments.keys() if env not in valid_environments]
        
        if invalid_envs:
            raise ValidationError(
                "Invalid environment names found",
                violations=[f"Invalid environment: {env}" for env in invalid_envs],
                suggested_fix=f"Valid environments are: {', '.join(sorted(valid_environments))}"
            )
    
    def validate_registry_urls(self, config: Dict[str, Any]) -> None:
        """
        Validate registry URLs in configuration.
        
        Args:
            config: Full configuration dictionary
            
        Raises:
            ValidationError: If any registry URL is invalid
        """
        invalid_urls = []
        
        # Check registry configuration for valid URLs
        registry_config = config.get('registry', {})
        
        for service_name, service_config in registry_config.items():
            if isinstance(service_config, dict):
                for env_name, env_config in service_config.items():
                    if isinstance(env_config, dict):
                        # Check pushUrl
                        push_url = env_config.get('pushUrl', '')
                        if push_url and not self._is_valid_url(push_url):
                            invalid_urls.append({
                                'service': service_name,
                                'environment': env_name,
                                'field': 'pushUrl',
                                'url': push_url
                            })
                        
                        # Check pullUrl
                        pull_url = env_config.get('pullUrl', '')
                        if pull_url and not self._is_valid_url(pull_url):
                            invalid_urls.append({
                                'service': service_name,
                                'environment': env_name,
                                'field': 'pullUrl',
                                'url': pull_url
                            })
                        
                        # Check url (for artifact servers)
                        url = env_config.get('url', '')
                        if url and not self._is_valid_url(url):
                            invalid_urls.append({
                                'service': service_name,
                                'environment': env_name,
                                'field': 'url',
                                'url': url
                            })
        
        if invalid_urls:
            violations = [
                f"Registry '{u['service']}' environment '{u['environment']}' has invalid {u['field']}: {u['url']}"
                for u in invalid_urls
            ]
            raise ValidationError(
                "Invalid registry URLs found",
                violations=violations,
                suggested_fix="Registry URLs must start with http://, https://, or be valid ECR URLs"
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        # Also accept ECR URLs
        ecr_pattern = re.compile(
            r'^\d{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com$'
        )
        
        return bool(url_pattern.match(url) or ecr_pattern.match(url))
    
    def validate_all(self, config: Dict[str, Any], config_file: Optional[str] = None) -> None:
        """
        Run all validation checks on configuration.
        
        Args:
            config: Configuration dictionary to validate
            config_file: Optional path to config file for error reporting
            
        Raises:
            ValidationError: If any validation check fails
        """
        logger.info("Running comprehensive configuration validation")
        
        # JSON schema validation
        self.validate(config, config_file)
        
        # Component type validation
        if 'components' in config:
            self.validate_component_types(config['components'])
        
        # Environment name validation
        if 'environments' in config:
            self.validate_environment_names(config['environments'])
        
        # Branch pattern validation
        if 'environments' in config:
            for env_name, env_config in config['environments'].items():
                if 'branches' in env_config:
                    try:
                        self.validate_branch_patterns(env_config['branches'])
                    except ValidationError as e:
                        # Add environment context to error
                        e.details['environment'] = env_name
                        raise
        
        # Registry URL validation
        self.validate_registry_urls(config)
        
        logger.info("All validation checks passed")
