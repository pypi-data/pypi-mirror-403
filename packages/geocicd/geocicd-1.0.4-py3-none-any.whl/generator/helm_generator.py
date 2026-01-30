"""
HelmGenerator module for GitLab CI/CD Migration system.

This module provides Helm chart generation from Kubernetes configuration.
"""

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

from generator.helm_chart_manager import HelmChartManager
from generator.helm_values_generator import HelmValuesGenerator
from generator.helm_template_generator import HelmTemplateGenerator
from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class HelmGenerator:
    """
    Generator for Helm charts from Kubernetes configuration.
    
    This class orchestrates Helm chart generation by delegating to specialized modules:
    - HelmChartManager: Chart structure and base chart management
    - HelmValuesGenerator: values.yaml generation
    - HelmTemplateGenerator: Kubernetes resource template generation
    
    Responsibilities:
    - Orchestrate complete Helm chart generation
    - Coordinate between chart manager, values generator, and template generator
    - Write YAML files to disk
    """
    
    def __init__(self):
        """Initialize Helm generator with specialized modules."""
        self.chart_manager = HelmChartManager()
        self.values_generator = HelmValuesGenerator()
        self.template_generator = HelmTemplateGenerator()
        logger.debug("HelmGenerator initialized")
    
    def generate(self, component: Dict[str, Any], environment: str, config: Dict[str, Any]) -> str:
        """
        Generate complete Helm chart for a component.
        
        This method creates a complete Helm chart structure:
        1. Create chart directory
        2. Clone base chart if configured
        3. Generate Chart.yaml with metadata
        4. Generate values.yaml with component configuration
        5. Create .helmignore file
        6. Generate templates/ directory with resource templates
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            Path to generated chart directory
            
        Raises:
            ValueError: If component configuration is invalid
            OSError: If chart directory cannot be created
        """
        with OperationLogger(logger, f"generate Helm chart for {component.get('name')}"):
            component_name = component.get('name')
            if not component_name:
                raise ValueError("Component must have a name")
            
            # Determine chart directory path
            chart_dir = self.chart_manager.get_chart_directory(component_name, environment)
            
            # Check if base chart should be used
            k8s_config = component.get('kubernetes', {})
            helm_config = k8s_config.get('helm', {})
            base_chart_config = helm_config.get('baseChart', {})
            
            if base_chart_config.get('enabled', False):
                # Clone and use base chart
                self.chart_manager.setup_base_chart(chart_dir, base_chart_config, config)
                logger.info(f"Using base chart from {base_chart_config.get('repository')}")
            else:
                # Create chart directory structure from scratch
                self.chart_manager.create_chart_structure(chart_dir)
            
            # Generate Chart.yaml
            chart_yaml = self.chart_manager.generate_chart_yaml(component, config)
            self._write_yaml_file(chart_dir / "Chart.yaml", chart_yaml)
            logger.debug(f"Generated Chart.yaml for {component_name}")
            
            # Generate values.yaml (always update with project-specific values)
            values_yaml = self.values_generator.generate_values_yaml(component, environment, config)
            self._write_yaml_file(chart_dir / "values.yaml", values_yaml)
            logger.debug(f"Generated values.yaml for {component_name}")
            
            # Generate .helmignore if not using base chart
            if not base_chart_config.get('enabled', False):
                self.chart_manager.generate_helmignore(chart_dir)
                logger.debug(f"Generated .helmignore for {component_name}")
            
            # Generate templates if not using base chart
            if not base_chart_config.get('enabled', False):
                # Generate _helpers.tpl
                self.chart_manager.generate_helpers_template(chart_dir, component)
                
                # Generate resource templates
                templates_created = self.template_generator.generate_templates(
                    component, environment, config, chart_dir
                )
                logger.info(f"Generated {len(templates_created)} template(s) for {component_name}")
            else:
                logger.info(f"Using templates from base chart")
            
            logger.info(f"Helm chart generated at: {chart_dir}")
            return str(chart_dir)
    
    def generate_chart_yaml(self, component: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Chart.yaml metadata.
        
        Delegates to HelmChartManager.
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
            
        Returns:
            Chart.yaml content as dictionary
        """
        return self.chart_manager.generate_chart_yaml(component, config)
    
    def generate_values_yaml(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate values.yaml with component configuration.
        
        Delegates to HelmValuesGenerator.
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            values.yaml content as dictionary
        """
        return self.values_generator.generate_values_yaml(component, environment, config)
    
    def generate_templates(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any],
        chart_dir: Path
    ) -> list:
        """
        Generate Kubernetes resource templates.
        
        Delegates to HelmTemplateGenerator.
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            chart_dir: Path to chart directory
            
        Returns:
            List of generated template file paths
        """
        return self.template_generator.generate_templates(component, environment, config, chart_dir)
    
    def _write_yaml_file(self, file_path: Path, content: Dict[str, Any]) -> None:
        """
        Write YAML content to file.
        
        Args:
            file_path: Path to output file
            content: Dictionary to write as YAML
        """
        with open(file_path, 'w') as f:
            yaml.dump(
                content,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                width=120,
                allow_unicode=True
            )
