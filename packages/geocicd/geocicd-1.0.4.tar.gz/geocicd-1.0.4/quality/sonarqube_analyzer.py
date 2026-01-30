"""
SonarQubeAnalyzer module for GitLab CI/CD Migration system.

This module provides SonarQube quality analysis execution and validation,
including quality gate checking and change-based skip logic.
"""

import logging
import subprocess
import time
from typing import Any, Dict

from quality.sonarqube_parameter_builder import SonarQubeParameterBuilder
from quality.sonarqube_api_client import SonarQubeAPIClient, SonarQubeAnalysisError
from quality.sonarqube_quality_validator import SonarQubeQualityValidator
from utils.exceptions_deploy import QualityGateError
from utils.logging_config import get_logger
from utils.change_detector import ChangeDetector

logger = get_logger(__name__)


class SonarQubeAnalyzer:
    """
    SonarQube quality analyzer for CI/CD pipelines.
    
    This class executes SonarQube analysis using sonar-scanner with CLI parameters,
    validates quality gates, and implements change-based skip logic.
    
    Responsibilities:
    - Execute sonar-scanner with CLI parameters (no sonar-project.properties)
    - Query SonarQube API for analysis results
    - Validate quality gates against configured thresholds
    - Support environment-specific quality gate thresholds and acceptable failures
    - Implement skip logic for unchanged components
    - Handle acceptable vs critical quality gate failures
    
    Requirements: 7.1, 7.2, 7.5, 7.6, 22.1-22.10
    """
    
    def __init__(self):
        """Initialize SonarQube analyzer."""
        self.parameter_builder = SonarQubeParameterBuilder()
        self.api_client = SonarQubeAPIClient()
        self.quality_validator = SonarQubeQualityValidator()
        self.change_detector = ChangeDetector()
        logger.debug("SonarQubeAnalyzer initialized")
    
    def analyze(
        self,
        component: Dict[str, Any],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run SonarQube analysis and validate quality gates.
        
        This method executes the complete SonarQube analysis workflow:
        1. Check if analysis should be skipped (change detection)
        2. Build CLI parameters using SonarQubeParameterBuilder
        3. Execute sonar-scanner with parameters
        4. Wait for analysis to complete
        5. Query SonarQube API for results
        6. Validate quality gates
        7. Return analysis results with pass/fail status
        
        Args:
            component: Component configuration with type, path, and settings
            environment: Target environment (dev, stg, ese)
            config: Full configuration with SonarQube settings
            
        Returns:
            Analysis results dictionary with:
            - status: 'passed' | 'failed' | 'skipped'
            - metrics: Dictionary of metric values
            - failures: List of failed quality gates
            - critical_failures: List of critical failures
            - quality_gate_url: URL to SonarQube quality gate
            
        Raises:
            QualityGateError: If critical quality gates fail
            SonarQubeAnalysisError: If analysis execution fails
            
        Requirements: 7.1, 7.2, 22.1-22.10
        """
        component_name = component.get('name', 'unknown')
        component_type = component.get('type', 'unknown')
        component_path = component.get('path', '.')
        
        logger.info(f"Starting SonarQube analysis for {component_name} in {environment}")
        
        # Check if analysis should be skipped
        if self.should_skip(component_name, environment, config):
            logger.info(f"Skipping SonarQube analysis for {component_name} (no changes detected)")
            return {
                'status': 'skipped',
                'reason': 'No changes detected',
                'metrics': {},
                'failures': [],
                'critical_failures': []
            }
        
        # Get SonarQube configuration
        sonarqube_config = config.get('sonarqube', {})
        if not sonarqube_config.get('enabled', False):
            logger.info(f"SonarQube is disabled, skipping analysis for {component_name}")
            return {
                'status': 'skipped',
                'reason': 'SonarQube disabled',
                'metrics': {},
                'failures': [],
                'critical_failures': []
            }
        
        # Build CLI parameters
        parameters = self.parameter_builder.build_parameters(component, config)
        
        # Get base command for component type
        base_command = self.parameter_builder.get_command_for_type(component_type)
        
        # Build full command
        command = base_command + parameters
        command_str = ' '.join(command)
        
        # Log command (excluding sensitive token)
        safe_command = command_str.replace(
            sonarqube_config.get('token', ''),
            '***TOKEN***'
        )
        logger.info(f"Executing SonarQube analysis: {safe_command}")
        
        # Execute sonar-scanner
        try:
            result = subprocess.run(
                command,
                cwd=component_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"SonarQube analysis failed for {component_name}")
                logger.error(f"Exit code: {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                
                raise SonarQubeAnalysisError(
                    f"SonarQube analysis failed for component {component_name}",
                    component=component_name,
                    command=command_str,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            logger.info(f"SonarQube analysis completed successfully for {component_name}")
            logger.debug(f"Analysis output: {result.stdout}")
            
        except subprocess.TimeoutExpired:
            logger.error(f"SonarQube analysis timed out for {component_name}")
            raise SonarQubeAnalysisError(
                f"SonarQube analysis timed out after 10 minutes for component {component_name}",
                component=component_name,
                command=command_str
            )
        except FileNotFoundError:
            logger.error(f"sonar-scanner command not found")
            raise SonarQubeAnalysisError(
                f"sonar-scanner command not found. Please ensure SonarQube scanner is installed.",
                component=component_name,
                command=command_str
            )
        
        # Wait for analysis to be processed by SonarQube server
        logger.info(f"Waiting for SonarQube server to process analysis...")
        time.sleep(5)  # Give server time to process
        
        # Query SonarQube API for results
        project_key = self.api_client.get_project_key(component, config)
        metrics = self.api_client.query_metrics(project_key, config)
        
        # Validate quality gates
        quality_gates = sonarqube_config.get('qualityGates', {})
        validation_result = self.quality_validator.validate_quality_gates(
            metrics, quality_gates, environment, config
        )
        
        # Validate quality gates
        quality_gates = sonarqube_config.get('qualityGates', {})
        validation_result = self.validate_quality_gates(metrics, quality_gates, environment, config)
        
        # Build quality gate URL
        server_url = sonarqube_config.get('server', '').rstrip('/')
        quality_gate_url = f"{server_url}/dashboard?id={project_key}"
        
        # Determine if analysis passed or failed
        has_critical_failures = len(validation_result['critical_failures']) > 0
        
        if has_critical_failures:
            # Check if failure is allowed for this environment
            on_failure_config = sonarqube_config.get('onFailure', {}).get(environment, {})
            allow_failure = on_failure_config.get('allowFailure', False)
            
            if not allow_failure:
                logger.error(f"Critical quality gate failures for {component_name}")
                raise QualityGateError(
                    f"Quality gate failed for component {component_name}",
                    component=component_name,
                    environment=environment,
                    project_key=project_key,
                    failed_metrics=validation_result['failed_metrics'],
                    quality_gate_url=quality_gate_url
                )
            else:
                logger.warning(f"Quality gate failed for {component_name}, but failure is allowed")
        
        result = {
            'status': 'failed' if has_critical_failures else 'passed',
            'metrics': metrics,
            'failures': validation_result['failures'],
            'critical_failures': validation_result['critical_failures'],
            'quality_gate_url': quality_gate_url
        }
        
        logger.info(f"SonarQube analysis result for {component_name}: {result['status']}")
        
        return result
    
    def should_skip(
        self,
        component: str,
        environment: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Determine if analysis should be skipped based on change detection.
        
        This method checks if skipIfNoChanges is enabled for the environment
        and whether the component has changes compared to the comparison branch.
        
        Args:
            component: Component name
            environment: Environment name (dev, stg, ese)
            config: Full configuration with SonarQube and change detection settings
            
        Returns:
            True if should skip analysis, False otherwise
            
        Requirements: 7.5
        """
        sonarqube_config = config.get('sonarqube', {})
        strategy = sonarqube_config.get('strategy', {}).get(environment, {})
        
        # Check if skip is enabled for this environment
        skip_if_no_changes = strategy.get('skipIfNoChanges', False)
        
        if not skip_if_no_changes:
            logger.debug(f"skipIfNoChanges is disabled for {environment}, will not skip")
            return False
        
        # Check if component has changes
        try:
            changed_components = self.change_detector.get_changed_components(environment, config)
            has_changes = component in changed_components
            
            if has_changes:
                logger.debug(f"Component {component} has changes, will not skip")
                return False
            else:
                logger.info(f"Component {component} has no changes, will skip analysis")
                return True
                
        except Exception as e:
            logger.warning(f"Error checking changes for {component}: {e}")
            logger.warning("Will proceed with analysis to be safe")
            return False

