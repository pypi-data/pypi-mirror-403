"""
SonarQube quality gate validation for GitLab CI/CD Migration system.

This module validates SonarQube metrics against configured quality gates
and determines acceptable vs critical failures.
"""

import logging
from typing import Any, Dict, List

from utils.logging_config import get_logger

logger = get_logger(__name__)


class SonarQubeQualityValidator:
    """
    Validator for SonarQube quality gates.
    
    This class handles:
    - Quality gate validation against thresholds
    - Environment-specific quality gate configuration
    - Acceptable vs critical failure determination
    
    Responsibilities:
    - Compare metrics against configured thresholds
    - Support environment-specific quality gates
    - Determine which failures are acceptable
    - Provide detailed validation results
    """
    
    def __init__(self):
        """Initialize SonarQube quality validator."""
        logger.debug("SonarQubeQualityValidator initialized")
    
    def validate_quality_gates(
        self,
        metrics: Dict[str, Any],
        gates: Dict[str, Dict[str, Any]],
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate metrics against configured quality gates.
        
        This method compares actual metric values against configured thresholds
        and determines which failures are acceptable vs critical.
        Supports environment-specific quality gate thresholds and acceptableFailures.
        
        Args:
            metrics: SonarQube metrics from API
            gates: Quality gate configuration with thresholds
            environment: Target environment
            config: Full configuration with acceptableFailures
            
        Returns:
            Validation results dictionary with:
            - failures: List of all failed quality gates
            - critical_failures: List of critical failures (not acceptable)
            - failed_metrics: Dictionary of failed metrics with details
            
        Requirements: 7.2, 7.3, 7.4, 7.6, 7.7
        """
        sonarqube_config = config.get('sonarqube', {})
        
        # Get environment-specific quality gates if available, otherwise use global
        env_gates = sonarqube_config.get('qualityGatesByEnvironment', {}).get(environment, {})
        if env_gates:
            logger.debug(f"Using environment-specific quality gates for {environment}")
            gates = env_gates
        else:
            logger.debug(f"Using global quality gates for {environment}")
        
        # Get environment-specific acceptableFailures if available, otherwise use global
        env_acceptable = sonarqube_config.get('acceptableFailuresByEnvironment', {}).get(environment)
        if env_acceptable is not None:
            logger.debug(f"Using environment-specific acceptableFailures for {environment}")
            acceptable_failures = env_acceptable
        else:
            logger.debug(f"Using global acceptableFailures for {environment}")
            acceptable_failures = sonarqube_config.get('acceptableFailures', [])
        
        failures = []
        critical_failures = []
        failed_metrics = {}
        
        logger.debug(f"Validating {len(gates)} quality gates")
        
        for metric_name, gate_config in gates.items():
            # Skip if gate is disabled
            if not gate_config.get('enabled', True):
                logger.debug(f"Quality gate {metric_name} is disabled, skipping")
                continue
            
            # Get threshold and operator
            threshold = gate_config.get('threshold')
            operator = gate_config.get('operator', 'GT')
            
            if threshold is None:
                logger.warning(f"No threshold configured for {metric_name}, skipping")
                continue
            
            # Get actual metric value
            actual_value = metrics.get(metric_name)
            
            if actual_value is None:
                logger.warning(f"Metric {metric_name} not found in SonarQube results")
                continue
            
            # Convert to float for comparison
            try:
                actual_float = float(actual_value)
                threshold_float = float(threshold)
            except (ValueError, TypeError):
                logger.warning(f"Cannot compare {metric_name}: actual={actual_value}, threshold={threshold}")
                continue
            
            # Perform comparison based on operator
            failed = False
            
            if operator == 'GT':
                failed = actual_float > threshold_float
            elif operator == 'LT':
                failed = actual_float < threshold_float
            elif operator == 'GTE':
                failed = actual_float >= threshold_float
            elif operator == 'LTE':
                failed = actual_float <= threshold_float
            elif operator == 'EQ':
                failed = actual_float == threshold_float
            else:
                logger.warning(f"Unknown operator {operator} for {metric_name}")
                continue
            
            if failed:
                failure_info = {
                    'metric': metric_name,
                    'actual': actual_value,
                    'threshold': threshold,
                    'operator': operator
                }
                
                failures.append(failure_info)
                failed_metrics[metric_name] = {
                    'actual': actual_value,
                    'threshold': threshold,
                    'operator': operator
                }
                
                # Check if this is an acceptable failure
                is_acceptable = metric_name in acceptable_failures
                
                if is_acceptable:
                    logger.warning(
                        f"Quality gate failed (acceptable): {metric_name} = {actual_value} "
                        f"(threshold: {operator} {threshold})"
                    )
                else:
                    logger.error(
                        f"Quality gate failed (critical): {metric_name} = {actual_value} "
                        f"(threshold: {operator} {threshold})"
                    )
                    critical_failures.append(failure_info)
            else:
                logger.debug(
                    f"Quality gate passed: {metric_name} = {actual_value} "
                    f"(threshold: {operator} {threshold})"
                )
        
        logger.info(
            f"Quality gate validation complete: {len(failures)} failures "
            f"({len(critical_failures)} critical)"
        )
        
        return {
            'failures': failures,
            'critical_failures': critical_failures,
            'failed_metrics': failed_metrics
        }
