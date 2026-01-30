"""
SonarQubeParameterBuilder module for GitLab CI/CD Migration system.

This module provides SonarQube command-line parameter generation based on
component type, ensuring centralized control and preventing user modifications.
"""

import logging
from typing import Any, Dict, List

from utils.logging_config import get_logger

logger = get_logger(__name__)


class SonarQubeParameterBuilder:
    """
    Builder for SonarQube command-line parameters.
    
    This class generates SonarQube parameters based on component type,
    ensuring all parameters are passed via CLI and cannot be modified by users.
    
    Responsibilities:
    - Build type-specific SonarQube parameters
    - Generate base parameters (projectKey, host.url, login)
    - Use predefined templates that cannot be customized
    - Support Maven, NPM, Vue, Gradle, and Python projects
    
    Requirements: 22.1-22.10
    """
    
    def __init__(self):
        """Initialize SonarQube parameter builder."""
        logger.debug("SonarQubeParameterBuilder initialized")
    
    def build_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build SonarQube parameters for component.
        
        This method determines the component type and generates the appropriate
        parameters using predefined templates. Users cannot override these parameters.
        
        Args:
            component: Component configuration with type and settings
            config: Full configuration with SonarQube settings
            
        Returns:
            List of -D parameters for sonar-scanner
            
        Requirements: 22.3, 22.8, 22.9
        """
        component_type = component.get('type', '').lower()
        component_name = component.get('name', 'unknown')
        
        logger.debug(f"Building SonarQube parameters for {component_name} (type: {component_type})")
        
        # Get base parameters (common to all types)
        parameters = self.get_base_parameters(component, config)
        
        # Add type-specific parameters
        if component_type == 'maven':
            parameters.extend(self.get_maven_parameters(component, config))
        elif component_type in ['npm', 'vue']:
            parameters.extend(self.get_npm_parameters(component, config))
        elif component_type == 'python':
            parameters.extend(self.get_python_parameters(component, config))
        elif component_type == 'gradle':
            parameters.extend(self.get_gradle_parameters(component, config))
        else:
            logger.warning(
                f"Unknown component type '{component_type}' for {component_name}, "
                f"using generic parameters"
            )
            # Use generic parameters for unknown types
            parameters.extend(self.get_generic_parameters(component, config))
        
        logger.debug(f"Generated {len(parameters)} SonarQube parameters for {component_name}")
        
        return parameters
    
    def get_base_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build base parameters common to all types.
        
        These parameters are mandatory for all SonarQube analyses:
        - sonar.projectKey: Unique project identifier
        - sonar.host.url: SonarQube server URL
        - sonar.login: Authentication token
        
        Args:
            component: Component configuration
            config: Full configuration with SonarQube settings
            
        Returns:
            Base parameters (projectKey, host.url, login)
            
        Requirements: 22.6
        """
        sonarqube_config = config.get('sonarqube', {})
        component_name = component.get('name', 'unknown')
        
        # Get SonarQube server URL
        server_url = sonarqube_config.get('server', '')
        if not server_url:
            logger.warning("SonarQube server URL not configured")
        
        # Get project key (use component-specific or default)
        project_key = sonarqube_config.get('projectKey', '')
        if not project_key:
            # Generate project key from project name and component name
            project_name = config.get('project', {}).get('name', 'unknown')
            project_key = f"{project_name}-{component_name}"
        else:
            # Append component name to project key for multi-component projects
            project_key = f"{project_key}-{component_name}"
        
        # Get authentication token (from config or environment variable)
        token = sonarqube_config.get('token', '')
        if not token:
            logger.warning("SonarQube token not configured")
        
        parameters = [
            f"-Dsonar.projectKey={project_key}",
            f"-Dsonar.host.url={server_url}",
        ]
        
        # Add token if available
        if token:
            parameters.append(f"-Dsonar.login={token}")
        
        return parameters
    
    def get_maven_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build parameters for Maven projects.
        
        Maven-specific parameters:
        - sonar.java.binaries: Compiled class files location
        - sonar.sources: Source code directory
        - sonar.tests: Test code directory
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            Maven-specific sonar parameters
            
        Requirements: 22.4, 22.7
        """
        component_path = component.get('path', '.')
        
        parameters = [
            "-Dsonar.java.binaries=target/classes",
            "-Dsonar.sources=src/main/java",
            "-Dsonar.tests=src/test/java",
        ]
        
        logger.debug(f"Generated Maven-specific parameters for component at {component_path}")
        
        return parameters
    
    def get_npm_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build parameters for NPM/Vue projects.
        
        NPM/Vue-specific parameters:
        - sonar.sources: Source code directory
        - sonar.exclusions: Excluded directories (node_modules, dist, build)
        - sonar.javascript.lcov.reportPaths: Code coverage report path
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            NPM-specific sonar parameters
            
        Requirements: 22.5, 22.7
        """
        component_path = component.get('path', '.')
        
        parameters = [
            "-Dsonar.sources=src",
            "-Dsonar.exclusions=node_modules/**,dist/**,build/**,coverage/**",
            "-Dsonar.javascript.lcov.reportPaths=coverage/lcov.info",
        ]
        
        logger.debug(f"Generated NPM/Vue-specific parameters for component at {component_path}")
        
        return parameters
    
    def get_python_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build parameters for Python projects.
        
        Python-specific parameters:
        - sonar.sources: Source code directory
        - sonar.python.version: Python version
        - sonar.exclusions: Excluded directories (venv, .venv, tests)
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            Python-specific sonar parameters
            
        Requirements: 22.7
        """
        component_path = component.get('path', '.')
        
        parameters = [
            "-Dsonar.sources=.",
            "-Dsonar.python.version=3.11",
            "-Dsonar.exclusions=venv/**,.venv/**,tests/**,__pycache__/**",
        ]
        
        logger.debug(f"Generated Python-specific parameters for component at {component_path}")
        
        return parameters
    
    def get_gradle_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build parameters for Gradle projects.
        
        Gradle-specific parameters:
        - sonar.java.binaries: Compiled class files location
        - sonar.sources: Source code directory
        - sonar.tests: Test code directory
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            Gradle-specific sonar parameters
            
        Requirements: 22.7
        """
        component_path = component.get('path', '.')
        
        parameters = [
            "-Dsonar.java.binaries=build/classes",
            "-Dsonar.sources=src/main",
            "-Dsonar.tests=src/test",
        ]
        
        logger.debug(f"Generated Gradle-specific parameters for component at {component_path}")
        
        return parameters
    
    def get_generic_parameters(self, component: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Build generic parameters for unknown component types.
        
        Generic parameters:
        - sonar.sources: Current directory
        
        Args:
            component: Component configuration
            config: Full configuration
            
        Returns:
            Generic sonar parameters
        """
        parameters = [
            "-Dsonar.sources=.",
        ]
        
        logger.debug("Generated generic SonarQube parameters")
        
        return parameters
    
    def get_command_for_type(self, component_type: str) -> List[str]:
        """
        Get the base command for running SonarQube analysis based on component type.
        
        Args:
            component_type: Component type (maven, npm, vue, gradle, python)
            
        Returns:
            Base command as list of strings
            
        Requirements: 22.4, 22.5
        """
        component_type = component_type.lower()
        
        if component_type == 'maven':
            # Maven uses mvn sonar:sonar
            return ['mvn', 'sonar:sonar']
        elif component_type in ['npm', 'vue', 'python', 'gradle']:
            # Other types use sonar-scanner
            return ['sonar-scanner']
        else:
            # Default to sonar-scanner for unknown types
            logger.warning(f"Unknown component type '{component_type}', using sonar-scanner")
            return ['sonar-scanner']
