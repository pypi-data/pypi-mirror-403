"""
Helm Template Generator module.

This module handles generation of Kubernetes resource templates for Helm charts.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from generator.helm_k8s_templates import HelmK8sTemplates
from utils.logging_config import get_logger

logger = get_logger(__name__)


class HelmTemplateGenerator:
    """
    Generator for Kubernetes resource templates in Helm charts.
    
    Responsibilities:
    - Orchestrate template generation
    - Write template files to disk
    - Coordinate with HelmK8sTemplates for resource generation
    """
    
    def __init__(self):
        """Initialize template generator with K8s templates module."""
        self.k8s_templates = HelmK8sTemplates()
    
    def generate_templates(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any],
        chart_dir: Path
    ) -> List[str]:
        """
        Generate Kubernetes resource templates.
        
        Creates template files for:
        - Deployment
        - Service
        - Ingress
        - ConfigMap
        - Secret
        - HorizontalPodAutoscaler
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            chart_dir: Path to chart directory
            
        Returns:
            List of generated template file paths
        """
        templates_dir = chart_dir / "templates"
        templates_created = []
        
        component_name = component.get('name')
        deploy_config = component.get('deploy', {})
        k8s_config = component.get('kubernetes', {})
        
        # Generate Deployment
        deployment_template = self.k8s_templates.generate_deployment_template(component, environment, config)
        deployment_path = templates_dir / "deployment.yaml"
        self._write_yaml_file(deployment_path, deployment_template)
        templates_created.append(str(deployment_path))
        logger.debug(f"Generated deployment template for {component_name}")
        
        # Generate Service if enabled
        if deploy_config.get('service', {}).get('enabled', True):
            service_template = self.k8s_templates.generate_service_template(component)
            service_path = templates_dir / "service.yaml"
            self._write_yaml_file(service_path, service_template)
            templates_created.append(str(service_path))
            logger.debug(f"Generated service template for {component_name}")
        
        # Generate Ingress if enabled
        if deploy_config.get('ingress', {}).get('enabled', False):
            ingress_template = self.k8s_templates.generate_ingress_template(component)
            ingress_path = templates_dir / "ingress.yaml"
            self._write_yaml_file(ingress_path, ingress_template)
            templates_created.append(str(ingress_path))
            logger.debug(f"Generated ingress template for {component_name}")
        
        # Generate HorizontalPodAutoscaler if autoscaling enabled
        if deploy_config.get('autoscaling', {}).get('enabled', False):
            hpa_template = self.k8s_templates.generate_hpa_template(component)
            hpa_path = templates_dir / "hpa.yaml"
            self._write_yaml_file(hpa_path, hpa_template)
            templates_created.append(str(hpa_path))
            logger.debug(f"Generated HPA template for {component_name}")
        
        # Generate ConfigMaps from kubernetes.resources
        resources = k8s_config.get('resources', [])
        for idx, resource in enumerate(resources):
            if resource.get('type') == 'configmap':
                cm_template = self.k8s_templates.generate_configmap_template(component, resource)
                cm_path = templates_dir / f"configmap-{resource.get('name', idx)}.yaml"
                self._write_yaml_file(cm_path, cm_template)
                templates_created.append(str(cm_path))
                logger.debug(f"Generated configmap template: {resource.get('name')}")
        
        # Generate Secrets from kubernetes.resources
        for idx, resource in enumerate(resources):
            if resource.get('type') == 'secret':
                secret_template = self.k8s_templates.generate_secret_template(component, resource)
                secret_path = templates_dir / f"secret-{resource.get('name', idx)}.yaml"
                self._write_yaml_file(secret_path, secret_template)
                templates_created.append(str(secret_path))
                logger.debug(f"Generated secret template: {resource.get('name')}")
        
        return templates_created
    
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
