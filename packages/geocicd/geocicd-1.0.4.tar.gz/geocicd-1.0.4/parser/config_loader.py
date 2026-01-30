"""
Configuration file loading for GitLab CI/CD Migration system.

This module handles YAML file loading and import resolution.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from parser.merger import Merger
from parser.server_resolver import ServerResolver
from utils.exceptions_base import ValidationError, ImportError as ConfigImportError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """
    Configuration file loader with import resolution.
    
    This class provides:
    - YAML file parsing
    - Import resolution
    - Circular import detection
    - Server reference resolution
    """
    
    def __init__(self):
        """Initialize configuration loader."""
        self.merger = Merger()
        self.server_resolver = ServerResolver()
        self._import_stack: List[str] = []
        logger.debug("ConfigLoader initialized")
    
    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML as dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If YAML is invalid
        """
        yaml_file = Path(file_path)
        
        if not yaml_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise ValidationError(
                    "Configuration file is empty",
                    file_path=file_path
                )
            
            if not isinstance(config, dict):
                raise ValidationError(
                    "Configuration must be a YAML object/dictionary",
                    file_path=file_path
                )
            
            logger.debug(f"Loaded YAML from {file_path}")
            return config
        
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            raise ValidationError(
                f"Invalid YAML syntax: {e}",
                file_path=file_path,
                line_number=line.line + 1 if line else None,
                column_number=line.column + 1 if line else None,
                suggested_fix="Fix YAML syntax errors"
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to load configuration: {e}",
                file_path=file_path
            )
    
    def load_imports(self, config: Dict[str, Any], config_file: str) -> Dict[str, Any]:
        """
        Load and merge imported configuration files.
        
        Supports recursive imports with circular reference detection.
        
        Args:
            config: Configuration with imports section
            config_file: Path to current config file (for resolving relative paths)
            
        Returns:
            Configuration with imports merged
            
        Raises:
            ConfigImportError: If import fails or circular reference detected
        """
        logger.info("Resolving configuration imports")
        
        imports = config.get('imports', [])
        if not imports:
            return config
        
        # Get base directory for resolving relative paths
        base_dir = Path(config_file).parent
        
        # Track current file in import stack
        abs_config_file = str(Path(config_file).resolve())
        if abs_config_file in self._import_stack:
            raise ConfigImportError(
                f"Circular import detected: {config_file}",
                import_path=config_file,
                import_chain=self._import_stack + [abs_config_file]
            )
        
        self._import_stack.append(abs_config_file)
        
        try:
            # Load all imported configurations
            imported_configs = []
            
            for import_spec in imports:
                import_path = import_spec.get('path')
                import_alias = import_spec.get('as')
                
                if not import_path:
                    raise ConfigImportError(
                        "Import specification missing 'path' field",
                        referenced_from=config_file
                    )
                
                # Resolve relative path
                abs_import_path = base_dir / import_path
                
                if not abs_import_path.exists():
                    raise ConfigImportError(
                        f"Import file not found: {import_path}",
                        import_path=str(abs_import_path),
                        referenced_from=config_file,
                        suggested_fix=f"Ensure the file exists at {abs_import_path}"
                    )
                
                logger.debug(f"Loading import: {import_path} as {import_alias}")
                
                # Load imported config
                imported_config = self.load_yaml(str(abs_import_path))
                
                # Recursively resolve imports in the imported file
                if 'imports' in imported_config:
                    imported_config = self.load_imports(imported_config, str(abs_import_path))
                
                # Store with alias if provided
                if import_alias:
                    imported_configs.append({import_alias: imported_config})
                else:
                    imported_configs.append(imported_config)
            
            # Merge imports with base config
            result = self.merger.merge_imports(config, imported_configs)
            
            # Remove imports section from result
            if 'imports' in result:
                del result['imports']
            
            logger.info(f"Resolved {len(imports)} import(s)")
            return result
        
        finally:
            # Remove from import stack
            self._import_stack.pop()
    
    def resolve_servers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve server references in configuration.
        
        Args:
            config: Configuration with server references
            
        Returns:
            Configuration with resolved server references
        """
        return self.server_resolver.resolve_registry_config(config)
