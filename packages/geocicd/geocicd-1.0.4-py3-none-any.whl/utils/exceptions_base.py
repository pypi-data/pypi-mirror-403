"""
Base exception classes for GitLab CI/CD Migration system.

These exceptions provide structured error handling with detailed context
for different types of failures.
"""

from typing import Optional, Dict, Any, List


class CICDMigrationError(Exception):
    """Base exception for all GitLab CI/CD Migration errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Format exception as string with details."""
        if self.details:
            details_str = "\n".join(f"  {k}: {v}" for k, v in self.details.items())
            return f"{self.message}\nDetails:\n{details_str}"
        return self.message


class ValidationError(CICDMigrationError):
    """Exception raised when configuration validation fails."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        violations: Optional[List[str]] = None,
        suggested_fix: Optional[str] = None,
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            file_path: Path to configuration file
            line_number: Line number where error occurred
            column_number: Column number where error occurred
            violations: List of validation violations
            suggested_fix: Suggested fix for the error
        """
        details = {}
        if file_path:
            details["file"] = file_path
        if line_number:
            details["line"] = line_number
        if column_number:
            details["column"] = column_number
        if violations:
            details["violations"] = violations
        if suggested_fix:
            details["suggested_fix"] = suggested_fix
        
        super().__init__(message, details)
        self.file_path = file_path
        self.line_number = line_number
        self.column_number = column_number
        self.violations = violations or []
        self.suggested_fix = suggested_fix
    
    def __str__(self) -> str:
        """Format validation error with location and suggested fix."""
        parts = [self.message]
        
        # Add location information
        if self.file_path:
            location = f"  File: {self.file_path}"
            if self.line_number:
                location += f", line {self.line_number}"
                if self.column_number:
                    location += f", column {self.column_number}"
            parts.append(location)
        
        # Add violations
        if self.violations:
            parts.append("  Violations:")
            for violation in self.violations:
                parts.append(f"    - {violation}")
        
        # Add suggested fix
        if self.suggested_fix:
            parts.append(f"  Suggested fix: {self.suggested_fix}")
        
        return "\n".join(parts)


class InterpolationError(CICDMigrationError):
    """Exception raised when variable interpolation fails."""
    
    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        missing_variables: Optional[List[str]] = None,
        circular_references: Optional[List[str]] = None,
    ):
        """
        Initialize interpolation error.
        
        Args:
            message: Error message
            expression: The interpolation expression that failed
            missing_variables: List of undefined variables
            circular_references: List of circular reference chains
        """
        details = {}
        if expression:
            details["expression"] = expression
        if missing_variables:
            details["missing_variables"] = missing_variables
        if circular_references:
            details["circular_references"] = circular_references
        
        super().__init__(message, details)
        self.expression = expression
        self.missing_variables = missing_variables or []
        self.circular_references = circular_references or []
    
    def __str__(self) -> str:
        """Format interpolation error with missing variables and circular references."""
        parts = [self.message]
        
        if self.expression:
            parts.append(f"  Expression: {self.expression}")
        
        if self.missing_variables:
            parts.append("  Missing variables:")
            for var in self.missing_variables:
                parts.append(f"    - {var}")
            parts.append("  Suggested fix: Define these variables in the configuration or defaults")
        
        if self.circular_references:
            parts.append("  Circular reference chain:")
            for ref in self.circular_references:
                parts.append(f"    - {ref}")
            parts.append("  Suggested fix: Remove circular dependencies between variables")
        
        return "\n".join(parts)


class ImportError(CICDMigrationError):
    """Exception raised when configuration import fails."""
    
    def __init__(
        self,
        message: str,
        import_path: Optional[str] = None,
        referenced_from: Optional[str] = None,
        import_chain: Optional[List[str]] = None,
    ):
        """
        Initialize import error.
        
        Args:
            message: Error message
            import_path: Path to import file that failed
            referenced_from: File that referenced the import
            import_chain: Chain of imports leading to circular reference
        """
        details = {}
        if import_path:
            details["import_path"] = import_path
        if referenced_from:
            details["referenced_from"] = referenced_from
        if import_chain:
            details["import_chain"] = " -> ".join(import_chain)
        
        super().__init__(message, details)
        self.import_path = import_path
        self.referenced_from = referenced_from
        self.import_chain = import_chain or []
    
    def __str__(self) -> str:
        """Format import error with import chain."""
        parts = [self.message]
        
        if self.import_path:
            parts.append(f"  Import path: {self.import_path}")
        
        if self.referenced_from:
            parts.append(f"  Referenced from: {self.referenced_from}")
        
        if self.import_chain:
            parts.append("  Import chain:")
            parts.append(f"    {' -> '.join(self.import_chain)}")
            parts.append("  Suggested fix: Remove circular import or reorganize configuration files")
        
        return "\n".join(parts)
