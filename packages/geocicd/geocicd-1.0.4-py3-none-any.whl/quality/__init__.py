"""
Quality analysis module for GitLab CI/CD Migration system.

This module provides SonarQube integration for code quality analysis
and quality gate validation.
"""

from quality.sonarqube_analyzer import SonarQubeAnalyzer
from quality.sonarqube_parameter_builder import SonarQubeParameterBuilder

__all__ = [
    'SonarQubeAnalyzer',
    'SonarQubeParameterBuilder',
]
