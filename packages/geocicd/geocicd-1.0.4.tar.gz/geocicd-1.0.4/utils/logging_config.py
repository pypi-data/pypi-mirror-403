"""
Logging configuration for GitLab CI/CD Migration system.

Provides structured logging with timestamps, log levels, and context information.
"""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color if supported."""
        # Add color to level name
        if sys.stdout.isatty():
            levelname = record.levelname
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        format_string: Optional custom format string
        
    Returns:
        Configured root logger
    """
    # Default format string with timestamp, level, module, and message
    if format_string is None:
        format_string = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class OperationLogger:
    """Context manager for logging operation start, end, and status."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        """
        Initialize operation logger.
        
        Args:
            logger: Logger instance to use
            operation: Operation name (e.g., "build", "deploy")
            **context: Additional context information (component, environment, etc.)
        """
        self.logger = logger
        self.operation = operation
        self.context = context
        self.success = False
    
    def __enter__(self):
        """Log operation start."""
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        self.logger.info(f"Starting {self.operation} ({context_str})")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation end and status."""
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation} successfully ({context_str})")
            self.success = True
        else:
            self.logger.error(
                f"Failed {self.operation} ({context_str}): {exc_type.__name__}: {exc_val}"
            )
            self.success = False
        
        # Don't suppress exceptions
        return False


class ChangeDetectionLogger:
    """Helper class for logging change detection results."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize change detection logger.
        
        Args:
            logger: Logger instance to use
        """
        self.logger = logger
    
    def log_comparison_branch(self, environment: str, branch: str):
        """
        Log the comparison branch being used for change detection.
        
        Args:
            environment: Target environment name
            branch: Branch name being compared against
        """
        self.logger.info(f"Change detection for {environment}: comparing against branch '{branch}'")
    
    def log_changed_components(self, changed: list, unchanged: list):
        """
        Log which components are changed vs unchanged.
        
        Args:
            changed: List of changed component names
            unchanged: List of unchanged component names
        """
        if changed:
            self.logger.info(f"Changed components ({len(changed)}): {', '.join(changed)}")
        else:
            self.logger.info("No components have changed")
        
        if unchanged:
            self.logger.info(f"Unchanged components ({len(unchanged)}): {', '.join(unchanged)}")
    
    def log_artifact_reuse(self, component: str, artifact_tag: str):
        """
        Log that an artifact is being reused for an unchanged component.
        
        Args:
            component: Component name
            artifact_tag: Full artifact tag being reused (registry/image:tag)
        """
        self.logger.info(f"Reusing artifact for {component}: {artifact_tag}")
    
    def log_build_required(self, component: str, reason: str):
        """
        Log that a component requires building.
        
        Args:
            component: Component name
            reason: Reason why build is required
        """
        self.logger.info(f"Building {component}: {reason}")
    
    def log_change_detection_summary(
        self,
        environment: str,
        comparison_branch: str,
        total_components: int,
        changed_count: int,
        unchanged_count: int,
        reused_count: int
    ):
        """
        Log a summary of change detection results.
        
        Args:
            environment: Target environment
            comparison_branch: Branch compared against
            total_components: Total number of components
            changed_count: Number of changed components
            unchanged_count: Number of unchanged components
            reused_count: Number of artifacts reused
        """
        self.logger.info("=" * 60)
        self.logger.info("Change Detection Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Environment: {environment}")
        self.logger.info(f"Comparison branch: {comparison_branch}")
        self.logger.info(f"Total components: {total_components}")
        self.logger.info(f"Changed: {changed_count}")
        self.logger.info(f"Unchanged: {unchanged_count}")
        self.logger.info(f"Artifacts reused: {reused_count}")
        self.logger.info("=" * 60)
