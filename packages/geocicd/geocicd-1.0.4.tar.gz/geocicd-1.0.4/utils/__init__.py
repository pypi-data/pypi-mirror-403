"""
Utils package for GitLab CI/CD Migration system.

This package contains utility components for Git operations, logging,
file operations, and other common functionality.
"""

from utils.git_utils import GitUtils, GitUtilsError
from utils.pattern_matcher import PatternMatcher
from utils.change_detector import ChangeDetector, ChangeDetectorError
from utils.artifact_resolver import (
    ArtifactResolver,
    ArtifactResolverError,
    RegistryClient,
    DockerRegistryClient,
    ECRRegistryClient,
    DockerHubRegistryClient,
)
from utils.managed_file_handler import ManagedFileHandler
from utils.version_extractor import VersionExtractor
from utils.artifact_tagger import ArtifactTagger
from utils.artifact_metadata import ArtifactMetadata
from utils.exceptions import (
    CICDMigrationError,
    ValidationError,
    InterpolationError,
    ImportError,
    BuildError,
    PublishError,
    DeploymentError,
    QualityGateError,
    ArtifactNotFoundError,
)
from utils.logging_config import (
    setup_logging,
    get_logger,
    OperationLogger,
    ChangeDetectionLogger,
)

__version__ = "1.0.0"

__all__ = [
    # Git utilities
    "GitUtils",
    "GitUtilsError",
    # Pattern matching
    "PatternMatcher",
    # Change detection
    "ChangeDetector",
    "ChangeDetectorError",
    # Artifact resolution
    "ArtifactResolver",
    "ArtifactResolverError",
    "RegistryClient",
    "DockerRegistryClient",
    "ECRRegistryClient",
    "DockerHubRegistryClient",
    # Managed files
    "ManagedFileHandler",
    # Version extraction
    "VersionExtractor",
    # Artifact tagging
    "ArtifactTagger",
    # Artifact metadata
    "ArtifactMetadata",
    # Exceptions
    "CICDMigrationError",
    "ValidationError",
    "InterpolationError",
    "ImportError",
    "BuildError",
    "PublishError",
    "DeploymentError",
    "QualityGateError",
    "ArtifactNotFoundError",
    # Logging
    "setup_logging",
    "get_logger",
    "OperationLogger",
    "ChangeDetectionLogger",
]
