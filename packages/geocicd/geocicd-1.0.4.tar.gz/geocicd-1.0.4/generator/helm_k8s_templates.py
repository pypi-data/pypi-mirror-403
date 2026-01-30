"""
Helm Kubernetes Templates module.

This module handles generation of core Kubernetes resource templates.
"""

import logging
from typing import Any, Dict

from utils.logging_config import get_logger

logger = get_logger(__name__)


class HelmK8sTemplates:
    """
    Generator for core Kubernetes resource templates.
    
    Responsibilities:
    - Generate Deployment templates
    - Generate Service templates
    - Generate Ingress templates
    - Generate HPA templates
    """
    
    def generate_deployment_template(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Deployment template.
        
        Args:
            component: Component configuration
            environment: Environment name
            config: Full configuration
            
        Returns:
            Deployment template dictionary
        """
        component_name = component.get('name')
        deploy_config = component.get('deploy', {})
        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': '{{ include "chart.fullname" . }}',
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                    'app.kubernetes.io/version': '{{ .Chart.AppVersion }}',
                    'app.kubernetes.io/managed-by': '{{ .Release.Service }}',
                }
            },
            'spec': {
                'replicas': '{{ .Values.replicaCount }}',
                'selector': {
                    'matchLabels': {
                        'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                        'app.kubernetes.io/instance': '{{ .Release.Name }}',
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                            'app.kubernetes.io/instance': '{{ .Release.Name }}',
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': component_name,
                                'image': '{{ .Values.image.repository }}:{{ .Values.image.tag }}',
                                'imagePullPolicy': '{{ .Values.image.pullPolicy }}',
                                'ports': [
                                    {
                                        'name': 'http',
                                        'containerPort': deploy_config.get('service', {}).get('targetPort', 80),
                                        'protocol': 'TCP',
                                    }
                                ],
                            }
                        ]
                    }
                }
            }
        }
        
        container = deployment['spec']['template']['spec']['containers'][0]
        
        # Add resources if defined
        if 'resources' in deploy_config:
            container['resources'] = '{{ toYaml .Values.resources | nindent 12 }}'
        
        # Add liveness probe if defined
        probes_config = deploy_config.get('probes', {})
        if probes_config.get('liveness', {}).get('enabled', False):
            container['livenessProbe'] = '{{ toYaml .Values.livenessProbe | nindent 12 }}'
        
        # Add readiness probe if defined
        if probes_config.get('readiness', {}).get('enabled', False):
            container['readinessProbe'] = '{{ toYaml .Values.readinessProbe | nindent 12 }}'
        
        # Add environment variables if defined
        if 'env' in deploy_config:
            container['env'] = '{{ toYaml .Values.env | nindent 12 }}'
        
        return deployment
    
    def generate_service_template(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Service template.
        
        Args:
            component: Component configuration
            
        Returns:
            Service template dictionary
        """
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': '{{ include "chart.fullname" . }}',
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                }
            },
            'spec': {
                'type': '{{ .Values.service.type }}',
                'ports': [
                    {
                        'port': '{{ .Values.service.port }}',
                        'targetPort': 'http',
                        'protocol': 'TCP',
                        'name': 'http',
                    }
                ],
                'selector': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                }
            }
        }
        
        return service
    
    def generate_ingress_template(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Ingress template.
        
        Args:
            component: Component configuration
            
        Returns:
            Ingress template dictionary
        """
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': '{{ include "chart.fullname" . }}',
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                },
                'annotations': '{{ toYaml .Values.ingress.annotations | nindent 4 }}',
            },
            'spec': {
                'ingressClassName': '{{ .Values.ingress.className }}',
                'rules': [
                    {
                        'host': '{{ .host }}',
                        'http': {
                            'paths': [
                                {
                                    'path': '{{ .path }}',
                                    'pathType': '{{ .pathType }}',
                                    'backend': {
                                        'service': {
                                            'name': '{{ include "chart.fullname" $ }}',
                                            'port': {
                                                'number': '{{ $.Values.service.port }}',
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ],
            }
        }
        
        return ingress
    
    def generate_hpa_template(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate HorizontalPodAutoscaler template.
        
        Args:
            component: Component configuration
            
        Returns:
            HPA template dictionary
        """
        hpa = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': '{{ include "chart.fullname" . }}',
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                }
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': '{{ include "chart.fullname" . }}',
                },
                'minReplicas': '{{ .Values.autoscaling.minReplicas }}',
                'maxReplicas': '{{ .Values.autoscaling.maxReplicas }}',
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': '{{ .Values.autoscaling.targetCPUUtilizationPercentage }}',
                            }
                        }
                    }
                ]
            }
        }
        
        return hpa
    
    def generate_configmap_template(
        self,
        component: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate ConfigMap template.
        
        Args:
            component: Component configuration
            resource: Resource configuration
            
        Returns:
            ConfigMap template dictionary
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': resource.get('name', '{{ include "chart.fullname" . }}-config'),
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                }
            },
            'data': {}
        }
        
        return configmap
    
    def generate_secret_template(
        self,
        component: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Secret template.
        
        Args:
            component: Component configuration
            resource: Resource configuration
            
        Returns:
            Secret template dictionary
        """
        secret_type = resource.get('secretType', 'Opaque')
        
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': resource.get('name', '{{ include "chart.fullname" . }}-secret'),
                'labels': {
                    'app.kubernetes.io/name': '{{ include "chart.name" . }}',
                    'app.kubernetes.io/instance': '{{ .Release.Name }}',
                }
            },
            'type': secret_type,
            'data': {}
        }
        
        return secret
