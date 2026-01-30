"""
Build and publish exception classes for GitLab CI/CD Migration system.

These exceptions handle errors related to building, publishing, and artifact management.
"""

from typing import Optional, Dict, Any, List

from utils.exceptions_base import CICDMigrationError


class BuildError(CICDMigrationError):
    """Exception raised when build command fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        working_directory: Optional[str] = None,
    ):
        """
        Initialize build error.
        
        Args:
            message: Error message
            component: Component name that failed to build
            command: Command that was executed
            exit_code: Exit code from command
            stdout: Standard output from command
            stderr: Standard error from command
            working_directory: Directory where command was executed
        """
        details = {}
        if component:
            details["component"] = component
        if command:
            details["command"] = command
        if exit_code is not None:
            details["exit_code"] = exit_code
        if working_directory:
            details["working_directory"] = working_directory
        if stdout:
            details["stdout"] = stdout[:1000]  # Limit output length
        if stderr:
            details["stderr"] = stderr[:1000]
        
        super().__init__(message, details)
        self.component = component
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.working_directory = working_directory
    
    def __str__(self) -> str:
        """Format build error with full command output."""
        parts = [self.message]
        
        if self.component:
            parts.append(f"  Component: {self.component}")
        
        if self.working_directory:
            parts.append(f"  Working directory: {self.working_directory}")
        
        if self.command:
            parts.append(f"  Command: {self.command}")
        
        if self.exit_code is not None:
            parts.append(f"  Exit code: {self.exit_code}")
        
        if self.stderr:
            parts.append("  Error output:")
            for line in self.stderr.split('\n')[:20]:  # Show first 20 lines
                if line.strip():
                    parts.append(f"    {line}")
        
        if self.stdout:
            parts.append("  Standard output:")
            for line in self.stdout.split('\n')[:20]:  # Show first 20 lines
                if line.strip():
                    parts.append(f"    {line}")
        
        parts.append("  Suggested fix: Check the command syntax and build configuration")
        
        return "\n".join(parts)


class PublishError(CICDMigrationError):
    """Exception raised when registry publish fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        registry_url: Optional[str] = None,
        image_name: Optional[str] = None,
        image_tag: Optional[str] = None,
        auth_method: Optional[str] = None,
        registry_error: Optional[str] = None,
    ):
        """
        Initialize publish error.
        
        Args:
            message: Error message
            component: Component name
            registry_url: Registry URL
            image_name: Image name
            image_tag: Image tag
            auth_method: Authentication method used
            registry_error: Error message from registry
        """
        details = {}
        if component:
            details["component"] = component
        if registry_url:
            details["registry_url"] = registry_url
        if image_name:
            details["image_name"] = image_name
        if image_tag:
            details["image_tag"] = image_tag
        if auth_method:
            details["auth_method"] = auth_method
        if registry_error:
            details["registry_error"] = registry_error
        
        super().__init__(message, details)
        self.component = component
        self.registry_url = registry_url
        self.image_name = image_name
        self.image_tag = image_tag
        self.auth_method = auth_method
        self.registry_error = registry_error
    
    def __str__(self) -> str:
        """Format publish error with registry details."""
        parts = [self.message]
        
        if self.component:
            parts.append(f"  Component: {self.component}")
        
        if self.registry_url:
            parts.append(f"  Registry: {self.registry_url}")
        
        if self.image_name and self.image_tag:
            parts.append(f"  Image: {self.image_name}:{self.image_tag}")
        elif self.image_name:
            parts.append(f"  Image: {self.image_name}")
        
        if self.auth_method:
            parts.append(f"  Authentication method: {self.auth_method}")
        
        if self.registry_error:
            parts.append(f"  Registry error: {self.registry_error}")
        
        # Provide context-specific suggestions
        if "unauthorized" in self.message.lower() or "authentication" in self.message.lower():
            parts.append("  Suggested fix: Check registry credentials and authentication configuration")
        elif "not found" in self.message.lower():
            parts.append("  Suggested fix: Verify the registry URL and image name are correct")
        elif "network" in self.message.lower() or "timeout" in self.message.lower():
            parts.append("  Suggested fix: Check network connectivity to the registry")
        else:
            parts.append("  Suggested fix: Verify registry configuration and credentials")
        
        return "\n".join(parts)


class ArtifactNotFoundError(CICDMigrationError):
    """Exception raised when artifact cannot be found for reuse."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        environment: Optional[str] = None,
        registry_url: Optional[str] = None,
        searched_tags: Optional[List[str]] = None,
    ):
        """
        Initialize artifact not found error.
        
        Args:
            message: Error message
            component: Component name
            environment: Environment name
            registry_url: Registry URL that was searched
            searched_tags: List of tags that were searched
        """
        details = {}
        if component:
            details["component"] = component
        if environment:
            details["environment"] = environment
        if registry_url:
            details["registry_url"] = registry_url
        if searched_tags:
            details["searched_tags"] = searched_tags
        
        super().__init__(message, details)
        self.component = component
        self.environment = environment
        self.registry_url = registry_url
        self.searched_tags = searched_tags or []
    
    def __str__(self) -> str:
        """Format artifact not found error with search details."""
        parts = [self.message]
        
        if self.component:
            parts.append(f"  Component: {self.component}")
        
        if self.environment:
            parts.append(f"  Environment: {self.environment}")
        
        if self.registry_url:
            parts.append(f"  Registry: {self.registry_url}")
        
        if self.searched_tags:
            parts.append("  Searched tags:")
            for tag in self.searched_tags:
                parts.append(f"    - {tag}")
        
        parts.append("  Suggested fix: Build the component first or check if the artifact exists in the registry")
        
        return "\n".join(parts)


class VersionCheckError(CICDMigrationError):
    """Exception raised when CLI version check fails."""
    
    def __init__(
        self,
        message: str,
        registry_url: Optional[str] = None,
        package_name: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        Initialize version check error.
        
        Args:
            message: Error message
            registry_url: Registry URL that was queried
            package_name: Package name that was checked
            error_type: Type of error (network, auth, parse)
        """
        details = {}
        if registry_url:
            details["registry_url"] = registry_url
        if package_name:
            details["package_name"] = package_name
        if error_type:
            details["error_type"] = error_type
        
        super().__init__(message, details)
        self.registry_url = registry_url
        self.package_name = package_name
        self.error_type = error_type
    
    def __str__(self) -> str:
        """Format version check error with registry details."""
        parts = [self.message]
        
        if self.package_name:
            parts.append(f"  Package: {self.package_name}")
        
        if self.registry_url:
            parts.append(f"  Registry: {self.registry_url}")
        
        if self.error_type:
            parts.append(f"  Error type: {self.error_type}")
        
        # Provide context-specific suggestions
        if "Authentication failed" in self.message:
            parts.append("  Suggested fix: Check registry credentials in ~/.geocicd/config.yaml")
        elif "not found" in self.message.lower():
            parts.append("  Suggested fix: Verify the package name and registry URL are correct")
        elif "Network error" in self.message:
            parts.append("  Suggested fix: Check network connectivity to the registry")
        else:
            parts.append("  Suggested fix: Verify registry configuration and connectivity")
        
        return "\n".join(parts)
