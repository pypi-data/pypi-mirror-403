"""
Configuration package for GitLab CI/CD Migration system.

This package contains default configurations, configuration templates,
and utilities for branch matching and environment resolution.
"""

from config.branch_matcher import BranchMatcher
from config.environment_resolver import EnvironmentResolver

__version__ = "1.0.0"

__all__ = [
    'BranchMatcher',
    'EnvironmentResolver',
]
