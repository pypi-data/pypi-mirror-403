"""
Parser package for GitLab CI/CD Migration system.

This package contains components for parsing, validating, and processing
ci-config.yaml configuration files.
"""

from parser.config_parser import ConfigParser
from parser.interpolator import Interpolator
from parser.merger import Merger, MergeStrategy
from parser.validator import Validator
from parser.server_resolver import ServerResolver

__version__ = "1.0.0"

__all__ = [
    'ConfigParser',
    'Interpolator',
    'Merger',
    'MergeStrategy',
    'Validator',
    'ServerResolver',
]
