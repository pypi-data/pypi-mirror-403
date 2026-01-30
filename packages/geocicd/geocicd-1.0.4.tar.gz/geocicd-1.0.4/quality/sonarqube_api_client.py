"""
SonarQube API client for GitLab CI/CD Migration system.

This module provides API interaction with SonarQube server for querying
metrics and analysis results.
"""

import logging
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from utils.exceptions_base import CICDMigrationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SonarQubeAnalysisError(CICDMigrationError):
    """Exception raised when SonarQube analysis execution fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        """
        Initialize SonarQube analysis error.
        
        Args:
            message: Error message
            component: Component name
            command: Command that was executed
            exit_code: Exit code from command
            stdout: Standard output from command
            stderr: Standard error from command
        """
        details = {}
        if component:
            details["component"] = component
        if command:
            details["command"] = command
        if exit_code is not None:
            details["exit_code"] = exit_code
        if stdout:
            details["stdout"] = stdout[:1000]
        if stderr:
            details["stderr"] = stderr[:1000]
        
        super().__init__(message, details)
        self.component = component
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class SonarQubeAPIClient:
    """
    Client for SonarQube API interactions.
    
    This class handles:
    - Querying project metrics
    - Retrieving analysis results
    - API authentication
    
    Responsibilities:
    - Query SonarQube measures API
    - Handle API authentication
    - Parse and return metric data
    """
    
    def __init__(self):
        """Initialize SonarQube API client."""
        logger.debug("SonarQubeAPIClient initialized")
    
    def query_metrics(
        self,
        project_key: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query SonarQube API for project metrics.
        
        This method queries the SonarQube measures API to retrieve metric values
        for the analyzed project.
        
        Args:
            project_key: SonarQube project key
            config: Full configuration with SonarQube settings
            
        Returns:
            Dictionary of metric names to values
            
        Raises:
            SonarQubeAnalysisError: If API query fails
        """
        sonarqube_config = config.get('sonarqube', {})
        server_url = sonarqube_config.get('server', '').rstrip('/')
        token = sonarqube_config.get('token', '')
        
        if not server_url:
            logger.warning("SonarQube server URL not configured, cannot query metrics")
            return {}
        
        # Define metrics to retrieve
        metric_keys = [
            'bugs',
            'vulnerabilities',
            'code_smells',
            'coverage',
            'duplicated_lines_density',
            'ncloc',
            'sqale_rating',
            'reliability_rating',
            'security_rating',
            'security_hotspots',
            'new_bugs',
            'new_vulnerabilities',
            'new_code_smells',
            'new_coverage',
            'new_duplicated_lines_density'
        ]
        
        # Build API URL
        url = f"{server_url}/api/measures/component"
        params = {
            'component': project_key,
            'metricKeys': ','.join(metric_keys)
        }
        
        # Set up authentication
        auth = HTTPBasicAuth(token, '') if token else None
        
        try:
            logger.debug(f"Querying SonarQube metrics for {project_key}")
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            component = data.get('component', {})
            measures = component.get('measures', [])
            
            # Convert to dictionary
            metrics = {}
            for measure in measures:
                metric_key = measure.get('metric')
                value = measure.get('value')
                if metric_key and value is not None:
                    metrics[metric_key] = value
            
            logger.debug(f"Retrieved {len(metrics)} metrics from SonarQube")
            
            return metrics
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Project {project_key} not found in SonarQube")
                return {}
            else:
                logger.error(f"Failed to query SonarQube metrics: {e}")
                raise SonarQubeAnalysisError(
                    f"Failed to query SonarQube API for project {project_key}: {e}",
                    component=project_key
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to SonarQube: {e}")
            raise SonarQubeAnalysisError(
                f"Failed to connect to SonarQube server at {server_url}: {e}",
                component=project_key
            )
    
    def get_project_key(self, component: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Get SonarQube project key for component.
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            Project key string
        """
        sonarqube_config = config.get('sonarqube', {})
        component_name = component.get('name', 'unknown')
        
        # Get project key (use component-specific or default)
        project_key = sonarqube_config.get('projectKey', '')
        if not project_key:
            # Generate project key from project name and component name
            project_name = config.get('project', {}).get('name', 'unknown')
            project_key = f"{project_name}-{component_name}"
        else:
            # Append component name to project key for multi-component projects
            project_key = f"{project_key}-{component_name}"
        
        return project_key
