"""
Deployment and quality exception classes for GitLab CI/CD Migration system.

These exceptions handle errors related to deployment, quality gates, and SonarQube analysis.
"""

from typing import Optional, Dict, Any

from utils.exceptions_base import CICDMigrationError


class DeploymentError(CICDMigrationError):
    """Exception raised when Kubernetes deployment fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        environment: Optional[str] = None,
        namespace: Optional[str] = None,
        context: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        kubectl_error: Optional[str] = None,
        helm_error: Optional[str] = None,
    ):
        """
        Initialize deployment error.
        
        Args:
            message: Error message
            component: Component name
            environment: Target environment
            namespace: Kubernetes namespace
            context: Kubernetes context
            resource_type: Type of resource that failed
            resource_name: Name of resource that failed
            kubectl_error: Error from kubectl
            helm_error: Error from helm
        """
        details = {}
        if component:
            details["component"] = component
        if environment:
            details["environment"] = environment
        if namespace:
            details["namespace"] = namespace
        if context:
            details["context"] = context
        if resource_type:
            details["resource_type"] = resource_type
        if resource_name:
            details["resource_name"] = resource_name
        if kubectl_error:
            details["kubectl_error"] = kubectl_error
        if helm_error:
            details["helm_error"] = helm_error
        
        super().__init__(message, details)
        self.component = component
        self.environment = environment
        self.namespace = namespace
        self.context = context
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.kubectl_error = kubectl_error
        self.helm_error = helm_error
    
    def __str__(self) -> str:
        """Format deployment error with kubectl/helm errors."""
        parts = [self.message]
        
        if self.component:
            parts.append(f"  Component: {self.component}")
        
        if self.environment:
            parts.append(f"  Environment: {self.environment}")
        
        if self.namespace:
            parts.append(f"  Namespace: {self.namespace}")
        
        if self.context:
            parts.append(f"  Context: {self.context}")
        
        if self.resource_type and self.resource_name:
            parts.append(f"  Resource: {self.resource_type}/{self.resource_name}")
        elif self.resource_type:
            parts.append(f"  Resource type: {self.resource_type}")
        
        if self.kubectl_error:
            parts.append("  kubectl error:")
            for line in self.kubectl_error.split('\n')[:15]:
                if line.strip():
                    parts.append(f"    {line}")
        
        if self.helm_error:
            parts.append("  Helm error:")
            for line in self.helm_error.split('\n')[:15]:
                if line.strip():
                    parts.append(f"    {line}")
        
        # Provide context-specific suggestions
        if "not found" in self.message.lower():
            parts.append("  Suggested fix: Verify the resource exists and the namespace is correct")
        elif "forbidden" in self.message.lower() or "unauthorized" in self.message.lower():
            parts.append("  Suggested fix: Check RBAC permissions and service account configuration")
        elif "invalid" in self.message.lower():
            parts.append("  Suggested fix: Validate the resource manifest syntax and required fields")
        else:
            parts.append("  Suggested fix: Check Kubernetes cluster connectivity and resource configuration")
        
        return "\n".join(parts)


class QualityGateError(CICDMigrationError):
    """Exception raised when SonarQube quality gate fails."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        environment: Optional[str] = None,
        project_key: Optional[str] = None,
        failed_metrics: Optional[Dict[str, Dict[str, Any]]] = None,
        quality_gate_url: Optional[str] = None,
    ):
        """
        Initialize quality gate error.
        
        Args:
            message: Error message
            component: Component name
            environment: Target environment
            project_key: SonarQube project key
            failed_metrics: Dictionary of failed metrics with actual vs threshold
            quality_gate_url: URL to quality gate in SonarQube
        """
        details = {}
        if component:
            details["component"] = component
        if environment:
            details["environment"] = environment
        if project_key:
            details["project_key"] = project_key
        if failed_metrics:
            details["failed_metrics"] = failed_metrics
        if quality_gate_url:
            details["quality_gate_url"] = quality_gate_url
        
        super().__init__(message, details)
        self.component = component
        self.environment = environment
        self.project_key = project_key
        self.failed_metrics = failed_metrics or {}
        self.quality_gate_url = quality_gate_url
    
    def __str__(self) -> str:
        """Format quality gate error with metric details."""
        parts = [self.message]
        
        if self.component:
            parts.append(f"  Component: {self.component}")
        
        if self.environment:
            parts.append(f"  Environment: {self.environment}")
        
        if self.project_key:
            parts.append(f"  Project key: {self.project_key}")
        
        if self.failed_metrics:
            parts.append("  Failed metrics:")
            for metric_name, metric_data in self.failed_metrics.items():
                actual = metric_data.get('actual', 'N/A')
                threshold = metric_data.get('threshold', 'N/A')
                operator = metric_data.get('operator', 'N/A')
                parts.append(f"    - {metric_name}: {actual} (threshold: {operator} {threshold})")
        
        if self.quality_gate_url:
            parts.append(f"  Quality gate URL: {self.quality_gate_url}")
        
        parts.append("  Suggested fix: Review and fix the code quality issues in SonarQube")
        
        return "\n".join(parts)
