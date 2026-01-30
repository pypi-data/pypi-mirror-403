"""
Docker registry authentication module for GitLab CI/CD Migration system.

This module provides authentication functionality for different registry types
including standard Docker registries, AWS ECR, and DockerHub.
"""

import logging
import os
import subprocess
from typing import Optional

from utils.exceptions_build import PublishError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DockerRegistryAuth:
    """
    Authentication handler for Docker registries.
    
    This class handles authentication with:
    - Standard Docker registries (username/password)
    - AWS ECR (AWS CLI authentication)
    - DockerHub (username/password)
    
    Responsibilities:
    - Authenticate with Docker registries
    - Handle different authentication methods
    - Extract AWS region from ECR URLs
    - Manage AWS credentials
    """
    
    @staticmethod
    def login(
        registry_url: str,
        credentials_name: Optional[str] = None,
        dest_type: str = 'dockerRegistry'
    ) -> None:
        """
        Authenticate with Docker registry.
        
        Supports:
        - Username/password authentication (Nexus, DockerHub)
        - AWS ECR authentication with aws ecr get-login-password
        
        Args:
            registry_url: Registry URL (e.g., "nexus.example.com:8083")
            credentials_name: Name of credentials (environment variable prefix)
            dest_type: Destination type (dockerRegistry, awsEcr)
            
        Raises:
            PublishError: If authentication fails
        """
        logger.debug(f"Authenticating with registry: {registry_url}")
        
        try:
            if dest_type == 'awsEcr':
                DockerRegistryAuth._login_ecr(registry_url, credentials_name)
            else:
                DockerRegistryAuth._login_standard(registry_url, credentials_name)
            
            logger.info(f"Successfully authenticated with {registry_url}")
            
        except PublishError:
            raise
        except Exception as e:
            raise PublishError(
                f"Unexpected error during registry authentication: {e}",
                registry=registry_url,
                error=str(e)
            )
    
    @staticmethod
    def _login_standard(
        registry_url: str,
        credentials_name: Optional[str]
    ) -> None:
        """
        Login to standard Docker registry with username/password.
        
        Args:
            registry_url: Registry URL
            credentials_name: Credentials environment variable prefix
            
        Raises:
            PublishError: If login fails
        """
        if not credentials_name:
            raise PublishError(
                f"No credentials specified for registry {registry_url}",
                registry=registry_url,
                suggested_fix="Add 'credentials' field to destination configuration"
            )
        
        # Get credentials from environment variables
        username_var = f"{credentials_name}_USERNAME"
        password_var = f"{credentials_name}_PASSWORD"
        
        username = os.environ.get(username_var)
        password = os.environ.get(password_var)
        
        if not username or not password:
            raise PublishError(
                f"Registry credentials not found in environment",
                registry=registry_url,
                credentials=credentials_name,
                missing_vars=[
                    v for v in [username_var, password_var]
                    if not os.environ.get(v)
                ],
                suggested_fix=f"Set {username_var} and {password_var} environment variables"
            )
        
        # Execute docker login
        cmd = ['docker', 'login', registry_url, '-u', username, '--password-stdin']
        
        try:
            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise PublishError(
                    f"Docker login failed for {registry_url}",
                    registry=registry_url,
                    exit_code=result.returncode,
                    command=' '.join(cmd[:-2] + ['***']),  # Hide password
                    error=result.stderr,
                    suggested_fix="Verify credentials and registry URL"
                )
                
        except FileNotFoundError:
            raise PublishError(
                "Docker command not found",
                suggested_fix="Ensure Docker is installed and in PATH"
            )
    
    @staticmethod
    def _login_ecr(
        registry_url: str,
        credentials_name: Optional[str]
    ) -> None:
        """
        Login to AWS ECR using AWS CLI.
        
        Args:
            registry_url: ECR registry URL (e.g., "123456789012.dkr.ecr.eu-west-1.amazonaws.com")
            credentials_name: AWS credentials environment variable prefix
            
        Raises:
            PublishError: If login fails
        """
        # Extract region from ECR URL
        region = DockerRegistryAuth._extract_ecr_region(registry_url)
        
        # Get AWS credentials if specified
        if credentials_name:
            access_key_var = f"{credentials_name}_ACCESS_KEY_ID"
            secret_key_var = f"{credentials_name}_SECRET_ACCESS_KEY"
            
            access_key = os.environ.get(access_key_var)
            secret_key = os.environ.get(secret_key_var)
            
            if access_key and secret_key:
                os.environ['AWS_ACCESS_KEY_ID'] = access_key
                os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        
        # Get ECR login password
        try:
            result = subprocess.run(
                ['aws', 'ecr', 'get-login-password', '--region', region],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise PublishError(
                    f"Failed to get ECR login password",
                    registry=registry_url,
                    region=region,
                    exit_code=result.returncode,
                    error=result.stderr,
                    suggested_fix="Verify AWS credentials and region"
                )
            
            password = result.stdout.strip()
            
        except FileNotFoundError:
            raise PublishError(
                "AWS CLI not found",
                suggested_fix="Ensure AWS CLI is installed and in PATH"
            )
        
        # Login to ECR
        cmd = ['docker', 'login', registry_url, '-u', 'AWS', '--password-stdin']
        
        try:
            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise PublishError(
                    f"Docker login to ECR failed",
                    registry=registry_url,
                    exit_code=result.returncode,
                    error=result.stderr,
                    suggested_fix="Verify AWS credentials and ECR permissions"
                )
                
        except FileNotFoundError:
            raise PublishError(
                "Docker command not found",
                suggested_fix="Ensure Docker is installed and in PATH"
            )
    
    @staticmethod
    def _extract_ecr_region(registry_url: str) -> str:
        """
        Extract AWS region from ECR registry URL.
        
        Args:
            registry_url: ECR registry URL
            
        Returns:
            AWS region string
            
        Raises:
            PublishError: If URL format is invalid
        """
        # Format: <account-id>.dkr.ecr.<region>.amazonaws.com
        parts = registry_url.split('.')
        if len(parts) >= 4 and 'ecr' in parts:
            return parts[3]
        else:
            raise PublishError(
                f"Invalid ECR registry URL format: {registry_url}",
                registry=registry_url,
                suggested_fix="ECR URL should be in format: <account>.dkr.ecr.<region>.amazonaws.com"
            )
