"""
Custom exception classes for GitLab CI/CD Migration system.

This module re-exports all exception classes from specialized modules
for backward compatibility and convenient imports.
"""

# Import base exceptions
from utils.exceptions_base import (
    CICDMigrationError,
    ValidationError,
    InterpolationError,
    ImportError,
)

# Import build and publish exceptions
from utils.exceptions_build import (
    BuildError,
    PublishError,
    ArtifactNotFoundError,
    VersionCheckError,
)

# Import deployment and quality exceptions
from utils.exceptions_deploy import (
    DeploymentError,
    QualityGateError,
)

# Re-export all exceptions for backward compatibility
__all__ = [
    'CICDMigrationError',
    'ValidationError',
    'InterpolationError',
    'ImportError',
    'BuildError',
    'PublishError',
    'DeploymentError',
    'QualityGateError',
    'ArtifactNotFoundError',
    'VersionCheckError',
]


# Legacy class definition for backward compatibility (deprecated)
class _LegacyValidationError(CICDMigrationError):
    """Deprecated: Use ValidationError from exceptions_base instead."""
    pass

