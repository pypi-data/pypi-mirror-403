"""
Helm Values Generator module.

This module handles generation of values.yaml for Helm charts.
"""

import logging
from typing import Any, Dict

from utils.logging_config import get_logger

logger = get_logger(__name__)


class HelmValuesGenerator:
    """
    Generator for Helm values.yaml files.
    
    Responsibilities:
    - Generate complete values.yaml structure
    - Generate image configuration
    - Generate service configuration
    - Generate ingress configuration
    - Generate autoscaling configuration
    - Generate probe configuration
    - Merge values overrides
    """
    
    def generate_values_yaml(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate values.yaml with component configuration.
        
        Creates Helm values including:
        - replicaCount
        - image (repository, tag, pullPolicy)
        - service configuration
        - ingress configuration
        - resources (requests/limits)
        - autoscaling configuration
        - probes (liveness/readiness)
        - environment variables
        
        Merges with valuesOverride if specified.
        
        Args:
            component: Component configuration
            environment: Target environment name
            config: Full configuration dictionary
            
        Returns:
            values.yaml content as dictionary
        """
        component_name = component.get('name')
        deploy_config = component.get('deploy', {})
        k8s_config = component.get('kubernetes', {})
        
        # Get environment-specific configuration
        env_config = config.get('environments', {}).get(environment, {})
        
        # Build base values
        values = {}
        
        # Replica count
        values['replicaCount'] = deploy_config.get('replicas', 1)
        
        # Image configuration
        values['image'] = self.generate_image_values(component, environment, config)
        
        # Service configuration
        if deploy_config.get('service', {}).get('enabled', True):
            values['service'] = self.generate_service_values(deploy_config)
        
        # Ingress configuration
        if deploy_config.get('ingress', {}).get('enabled', False):
            values['ingress'] = self.generate_ingress_values(deploy_config)
        
        # Resources configuration
        if 'resources' in deploy_config:
            values['resources'] = deploy_config['resources']
        
        # Autoscaling configuration
        if deploy_config.get('autoscaling', {}).get('enabled', False):
            values['autoscaling'] = self.generate_autoscaling_values(deploy_config)
        
        # Probes configuration
        probes_config = deploy_config.get('probes', {})
        if probes_config.get('liveness', {}).get('enabled', False):
            values['livenessProbe'] = self.generate_probe_values(probes_config['liveness'])
        if probes_config.get('readiness', {}).get('enabled', False):
            values['readinessProbe'] = self.generate_probe_values(probes_config['readiness'])
        
        # Environment variables
        if 'env' in deploy_config:
            values['env'] = deploy_config['env']
        
        # Merge with valuesOverride if specified
        values_override = k8s_config.get('values', {})
        if values_override:
            values = self.deep_merge(values, values_override)
            logger.debug(f"Merged valuesOverride for {component_name}")
        
        logger.debug(f"Generated values.yaml with {len(values)} top-level keys")
        return values
    
    def generate_image_values(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate image values for values.yaml.
        
        Args:
            component: Component configuration
            environment: Environment name
            config: Full configuration
            
        Returns:
            Image values dictionary
        """
        from utils.output_resolver import OutputResolver
        output_resolver = OutputResolver()
        
        build_config = component.get('build', {})
        outputs = build_config.get('outputs', [])
        
        # Get docker server configuration for this environment
        registry_url = ''
        image_name = component.get('name')
        
        if 'docker' in outputs:
            try:
                server_config = output_resolver.resolve_output(
                    output_type='docker',
                    component=component,
                    environment=environment,
                    config=config
                )
                # Use pullUrl for image repository
                registry_url = server_config.get('pullUrl', '')
            except Exception as e:
                logger.warning(f"Failed to resolve docker output for {image_name}: {e}")
        
        image_values = {
            'repository': f"{registry_url}/{image_name}".strip('/'),
            'pullPolicy': 'IfNotPresent',
            'tag': '{{ .Chart.AppVersion }}',
        }
        
        return image_values
    
    def generate_service_values(self, deploy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate service values for values.yaml.
        
        Args:
            deploy_config: Deploy configuration
            
        Returns:
            Service values dictionary
        """
        service_config = deploy_config.get('service', {})
        
        service_values = {
            'type': service_config.get('type', 'ClusterIP'),
            'port': service_config.get('port', 80),
            'targetPort': service_config.get('targetPort', 80),
        }
        
        return service_values
    
    def generate_ingress_values(self, deploy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate ingress values for values.yaml.
        
        Args:
            deploy_config: Deploy configuration
            
        Returns:
            Ingress values dictionary
        """
        ingress_config = deploy_config.get('ingress', {})
        
        ingress_values = {
            'enabled': True,
            'className': ingress_config.get('className', 'nginx'),
            'annotations': ingress_config.get('annotations', {}),
            'hosts': [
                {
                    'host': ingress_config.get('host', 'example.local'),
                    'paths': [
                        {
                            'path': ingress_config.get('path', '/'),
                            'pathType': ingress_config.get('pathType', 'Prefix'),
                        }
                    ]
                }
            ],
        }
        
        # Add TLS if enabled
        tls_config = ingress_config.get('tls', {})
        if tls_config.get('enabled', False):
            ingress_values['tls'] = [
                {
                    'secretName': tls_config.get('secretName', 'tls-secret'),
                    'hosts': [ingress_config.get('host', 'example.local')]
                }
            ]
        
        return ingress_values
    
    def generate_autoscaling_values(self, deploy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate autoscaling values for values.yaml.
        
        Args:
            deploy_config: Deploy configuration
            
        Returns:
            Autoscaling values dictionary
        """
        autoscaling_config = deploy_config.get('autoscaling', {})
        
        autoscaling_values = {
            'enabled': True,
            'minReplicas': autoscaling_config.get('minReplicas', 1),
            'maxReplicas': autoscaling_config.get('maxReplicas', 10),
            'targetCPUUtilizationPercentage': autoscaling_config.get('targetCPUUtilizationPercentage', 80),
        }
        
        return autoscaling_values
    
    def generate_probe_values(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate probe values for values.yaml.
        
        Args:
            probe_config: Probe configuration
            
        Returns:
            Probe values dictionary
        """
        probe_type = probe_config.get('type', 'http')
        
        probe_values = {
            'initialDelaySeconds': probe_config.get('initialDelaySeconds', 30),
            'periodSeconds': probe_config.get('periodSeconds', 10),
            'timeoutSeconds': probe_config.get('timeoutSeconds', 5),
            'successThreshold': probe_config.get('successThreshold', 1),
            'failureThreshold': probe_config.get('failureThreshold', 3),
        }
        
        if probe_type == 'http':
            probe_values['httpGet'] = {
                'path': probe_config.get('path', '/'),
                'port': probe_config.get('port', 80),
            }
        elif probe_type == 'tcp':
            probe_values['tcpSocket'] = {
                'port': probe_config.get('port', 80),
            }
        elif probe_type == 'exec':
            probe_values['exec'] = {
                'command': probe_config.get('command', ['/bin/sh', '-c', 'exit 0']),
            }
        
        return probe_values
    
    def deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
