"""
GitLabCIQualityBuilder module for quality and validation job generation.

This module handles the creation of validation and quality analysis jobs.
"""

import logging
from typing import Any, Dict, List

from utils.constants import (
    STAGE_VALIDATE,
    STAGE_CHANGE_DETECTION,
    STAGE_QUALITY,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GitLabCIQualityBuilder:
    """
    Builder for GitLab CI quality and validation jobs.
    
    This class generates validation and quality analysis jobs with:
    - Configuration validation
    - Change detection
    - SonarQube analysis
    """
    
    def __init__(self):
        """Initialize quality builder."""
        logger.debug("GitLabCIQualityBuilder initialized")
    
    def generate_validation_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate configuration validation job.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validation job definition
        """
        job = {
            'stage': STAGE_VALIDATE,
            'image': 'python:3.11-slim',
            'script': [
                'pip install -q pyyaml jsonschema',
                'python -m parser.validator ci-config.yaml',
            ],
            'only': {
                'refs': ['merge_requests']
            }
        }
        
        return job
    
    def generate_change_detection_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate change detection job.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Change detection job definition
        """
        job = {
            'stage': STAGE_CHANGE_DETECTION,
            'image': 'python:3.11-slim',
            'script': [
                'pip install -q pyyaml jsonschema gitpython',
                'python -m utils.change_detector --config ci-config.yaml --output changed-components.json',
            ],
            'artifacts': {
                'paths': ['changed-components.json'],
                'expire_in': '1 hour'
            },
            'needs': ['validate:config']
        }
        
        return job
    
    def generate_quality_jobs(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Generate SonarQube quality analysis jobs.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary of quality job definitions
        """
        logger.debug("Generating quality analysis jobs")
        
        quality_jobs = {}
        components = config.get('components', [])
        sonarqube_config = config.get('sonarqube', {})
        
        for component in components:
            component_name = component.get('name')
            if not component_name:
                continue
            
            job_name = f"quality:{component_name}"
            quality_jobs[job_name] = self.create_quality_job(
                component,
                sonarqube_config
            )
            logger.debug(f"Generated quality job: {job_name}")
        
        return quality_jobs
    
    def create_quality_job(
        self,
        component: Dict[str, Any],
        sonarqube_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create SonarQube analysis job for a component.
        
        Args:
            component: Component configuration
            sonarqube_config: SonarQube configuration
            
        Returns:
            Quality job definition
        """
        component_name = component.get('name')
        component_path = component.get('path', '.')
        
        server_url = sonarqube_config.get('server', '')
        project_key = sonarqube_config.get('projectKey', f'${{PROJECT_NAME}}-{component_name}')
        
        script = [
            f'cd {component_path}' if component_path != '.' else '# Running in root',
            f'sonar-scanner',
            f'  -Dsonar.projectKey={project_key}',
            f'  -Dsonar.sources=.',
            f'  -Dsonar.host.url={server_url}',
            f'  -Dsonar.login=$SONAR_TOKEN',
        ]
        
        job = {
            'stage': STAGE_QUALITY,
            'image': 'sonarsource/sonar-scanner-cli:5.0',
            'script': script,
            'needs': [f'build:{component_name}'],
            'allow_failure': True
        }
        
        return job
    
    def is_change_detection_enabled(self, config: Dict[str, Any]) -> bool:
        """
        Check if change detection is enabled globally.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if change detection is enabled
        """
        change_detection = config.get('changeDetection', {})
        return change_detection.get('enabled', False)
    
    def is_sonarqube_enabled(self, config: Dict[str, Any]) -> bool:
        """
        Check if SonarQube is enabled.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if SonarQube is enabled
        """
        sonarqube = config.get('sonarqube', {})
        return sonarqube.get('enabled', False)
