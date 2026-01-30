"""
Kubernetes resource management for GitLab CI/CD Migration system.

This module handles creation and management of Kubernetes resources including
ConfigMaps, Secrets, and Namespaces.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logging_config import get_logger, OperationLogger
from utils.exceptions import DeploymentError

logger = get_logger(__name__)


class KubernetesResourceManager:
    """
    Manager for Kubernetes resources (ConfigMaps, Secrets, Namespaces).
    
    This class handles:
    - ConfigMap creation from files
    - SSL secret creation with auto-discovery
    - Namespace management
    
    Responsibilities:
    - Create ConfigMaps using kubectl create configmap --from-file
    - Auto-discover and create SSL secrets
    - Create namespaces if they don't exist
    """
    
    def __init__(self):
        """Initialize Kubernetes resource manager."""
        logger.debug("KubernetesResourceManager initialized")
    
    def create_configmaps(
        self,
        configmaps: List[Dict[str, Any]],
        namespace: str,
        context: Optional[str] = None
    ) -> None:
        """
        Create ConfigMaps from file paths.
        
        Creates Kubernetes ConfigMaps using kubectl create configmap --from-file.
        Supports multiple files per ConfigMap.
        Logs warnings for missing files and continues.
        
        Args:
            configmaps: List of ConfigMap configurations, each containing:
                - name: ConfigMap name
                - files: List of file configurations with:
                    - path: File path relative to component directory
                    - key: Optional key name in ConfigMap (defaults to filename)
            namespace: Target namespace
            context: Optional Kubernetes context
            
        Raises:
            DeploymentError: If kubectl command fails
            
        Examples:
            >>> manager = KubernetesResourceManager()
            >>> configmaps = [
            ...     {
            ...         'name': 'nginx-config',
            ...         'files': [
            ...             {'path': 'conf/nginx.conf', 'key': 'nginx.conf'}
            ...         ]
            ...     }
            ... ]
            >>> manager.create_configmaps(configmaps, "my-namespace")
        """
        with OperationLogger(
            logger,
            f"create {len(configmaps)} ConfigMap(s)",
            namespace=namespace
        ):
            for cm_config in configmaps:
                cm_name = cm_config.get('name')
                files = cm_config.get('files', [])
                
                if not cm_name:
                    logger.warning("ConfigMap configuration missing 'name', skipping")
                    continue
                
                if not files:
                    logger.warning(
                        f"ConfigMap '{cm_name}' has no files configured, skipping"
                    )
                    continue
                
                # Build kubectl command
                cmd = ['kubectl', 'create', 'configmap', cm_name]
                
                # Add namespace
                cmd.extend(['-n', namespace])
                
                # Add context if specified
                if context:
                    cmd.extend(['--context', context])
                
                # Add --from-file for each file
                files_found = False
                for file_config in files:
                    file_path = file_config.get('path')
                    file_key = file_config.get('key')
                    
                    if not file_path:
                        logger.warning(
                            f"File configuration in ConfigMap '{cm_name}' "
                            f"missing 'path', skipping"
                        )
                        continue
                    
                    # Check if file exists
                    if not os.path.exists(file_path):
                        logger.warning(
                            f"ConfigMap file not found: {file_path}, skipping"
                        )
                        continue
                    
                    files_found = True
                    
                    # Add --from-file with optional key
                    if file_key:
                        cmd.append(f"--from-file={file_key}={file_path}")
                    else:
                        cmd.append(f"--from-file={file_path}")
                
                if not files_found:
                    logger.warning(
                        f"No valid files found for ConfigMap '{cm_name}', skipping"
                    )
                    continue
                
                # Add --dry-run=client and -o yaml to check if ConfigMap exists
                check_cmd = cmd + ['--dry-run=client', '-o', 'yaml']
                
                try:
                    # Delete existing ConfigMap if present
                    delete_cmd = [
                        'kubectl', 'delete', 'configmap', cm_name,
                        '-n', namespace,
                        '--ignore-not-found=true'
                    ]
                    if context:
                        delete_cmd.extend(['--context', context])
                    
                    logger.debug(f"Deleting existing ConfigMap: {' '.join(delete_cmd)}")
                    subprocess.run(
                        delete_cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Create ConfigMap
                    logger.debug(f"Creating ConfigMap: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    logger.info(f"Created ConfigMap: {cm_name}")
                    if result.stdout:
                        logger.debug(f"kubectl output: {result.stdout}")
                    
                except subprocess.CalledProcessError as e:
                    error_msg = f"Failed to create ConfigMap '{cm_name}': {e.stderr}"
                    logger.error(error_msg)
                    raise DeploymentError(
                        error_msg,
                        resource_type='ConfigMap',
                        resource_name=cm_name,
                        namespace=namespace,
                        context=context,
                        kubectl_error=e.stderr
                    )
    
    def create_ssl_secret(
        self,
        ssl_dir: str,
        secret_name: str,
        namespace: str,
        context: Optional[str] = None
    ) -> None:
        """
        Create TLS secret from SSL directory with auto-discovery.
        
        Auto-discovers certificate and key files in the SSL directory:
        - Certificate files: .crt, .pem
        - Key files: .key
        
        Creates a Kubernetes TLS secret using kubectl create secret tls.
        
        Args:
            ssl_dir: Directory containing SSL certificate and key files
            secret_name: Name for the TLS secret
            namespace: Target namespace
            context: Optional Kubernetes context
            
        Raises:
            DeploymentError: If SSL files not found or kubectl command fails
            
        Examples:
            >>> manager = KubernetesResourceManager()
            >>> manager.create_ssl_secret(
            ...     "frontend/ssl",
            ...     "frontend-tls",
            ...     "my-namespace"
            ... )
        """
        with OperationLogger(
            logger,
            f"create SSL secret '{secret_name}'",
            namespace=namespace
        ):
            # Check if SSL directory exists
            if not os.path.exists(ssl_dir):
                logger.warning(
                    f"SSL directory not found: {ssl_dir}, skipping secret creation"
                )
                return
            
            if not os.path.isdir(ssl_dir):
                logger.warning(
                    f"SSL path is not a directory: {ssl_dir}, skipping secret creation"
                )
                return
            
            # Auto-discover certificate file
            cert_file = None
            cert_extensions = ['.crt', '.pem']
            
            for filename in os.listdir(ssl_dir):
                file_path = os.path.join(ssl_dir, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in cert_extensions:
                        cert_file = file_path
                        logger.debug(f"Found certificate file: {cert_file}")
                        break
            
            if not cert_file:
                logger.warning(
                    f"No certificate file (.crt, .pem) found in {ssl_dir}, "
                    f"skipping secret creation"
                )
                return
            
            # Auto-discover key file
            key_file = None
            key_extension = '.key'
            
            for filename in os.listdir(ssl_dir):
                file_path = os.path.join(ssl_dir, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() == key_extension:
                        key_file = file_path
                        logger.debug(f"Found key file: {key_file}")
                        break
            
            if not key_file:
                logger.warning(
                    f"No key file (.key) found in {ssl_dir}, "
                    f"skipping secret creation"
                )
                return
            
            # Build kubectl command
            cmd = [
                'kubectl', 'create', 'secret', 'tls', secret_name,
                '--cert', cert_file,
                '--key', key_file,
                '-n', namespace
            ]
            
            # Add context if specified
            if context:
                cmd.extend(['--context', context])
            
            try:
                # Delete existing secret if present
                delete_cmd = [
                    'kubectl', 'delete', 'secret', secret_name,
                    '-n', namespace,
                    '--ignore-not-found=true'
                ]
                if context:
                    delete_cmd.extend(['--context', context])
                
                logger.debug(f"Deleting existing secret: {' '.join(delete_cmd)}")
                subprocess.run(
                    delete_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Create TLS secret
                logger.debug(f"Creating TLS secret: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(
                    f"Created TLS secret: {secret_name} "
                    f"(cert: {os.path.basename(cert_file)}, "
                    f"key: {os.path.basename(key_file)})"
                )
                if result.stdout:
                    logger.debug(f"kubectl output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create TLS secret '{secret_name}': {e.stderr}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    resource_type='Secret',
                    resource_name=secret_name,
                    namespace=namespace,
                    context=context,
                    kubectl_error=e.stderr
                )
    
    def ensure_namespace_exists(
        self,
        namespace: str,
        context: Optional[str] = None
    ) -> None:
        """
        Ensure Kubernetes namespace exists, create if it doesn't.
        
        Checks if namespace exists and creates it if not found.
        This operation is idempotent - safe to call multiple times.
        
        Args:
            namespace: Namespace name
            context: Optional Kubernetes context
            
        Raises:
            DeploymentError: If namespace creation fails
        """
        with OperationLogger(logger, f"ensure namespace '{namespace}' exists"):
            # Check if namespace exists
            check_cmd = ['kubectl', 'get', 'namespace', namespace]
            if context:
                check_cmd.extend(['--context', context])
            
            logger.debug(f"Checking namespace: {' '.join(check_cmd)}")
            
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.debug(f"Namespace '{namespace}' already exists")
                return
            
            # Namespace doesn't exist, create it
            create_cmd = ['kubectl', 'create', 'namespace', namespace]
            if context:
                create_cmd.extend(['--context', context])
            
            logger.debug(f"Creating namespace: {' '.join(create_cmd)}")
            
            try:
                result = subprocess.run(
                    create_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Created namespace: {namespace}")
                if result.stdout:
                    logger.debug(f"kubectl output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create namespace '{namespace}': {e.stderr}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    resource_type='Namespace',
                    resource_name=namespace,
                    context=context,
                    kubectl_error=e.stderr
                )
