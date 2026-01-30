"""
ArgoCD repository management operations.

Handles cloning, copying charts, and committing to k8s-charts repository.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
import shutil

from utils.logging_config import get_logger, OperationLogger
from utils.exceptions import DeploymentError

logger = get_logger(__name__)


class ArgocdRepoManager:
    """Manager for k8s-charts repository operations."""
    
    def __init__(self):
        """Initialize repository manager."""
        logger.debug("ArgocdRepoManager initialized")
    
    def clone_charts_repository(
        self,
        repo_url: str,
        branch: str,
        credentials: Optional[Dict[str, Any]] = None,
        target_dir: Optional[str] = None
    ) -> str:
        """
        Clone k8s-charts repository.
        
        Args:
            repo_url: Git repository URL
            branch: Branch to clone
            credentials: Optional credentials dict
            target_dir: Optional target directory
            
        Returns:
            Path to cloned repository
            
        Raises:
            DeploymentError: If clone operation fails
        """
        with OperationLogger(logger, f"clone charts repository from {repo_url}"):
            # Create target directory
            if target_dir is None:
                target_dir = tempfile.mkdtemp(prefix="k8s-charts-")
            else:
                os.makedirs(target_dir, exist_ok=True)
            
            # Build authenticated URL if credentials provided
            clone_url = repo_url
            if credentials:
                username = credentials.get('username')
                password = credentials.get('password') or credentials.get('token')
                
                if username and password:
                    if '://' in repo_url:
                        protocol, rest = repo_url.split('://', 1)
                        clone_url = f"{protocol}://{username}:{password}@{rest}"
                    else:
                        logger.warning(
                            "Repository URL format not recognized for credential injection"
                        )
            
            # Execute git clone
            try:
                cmd = [
                    'git', 'clone',
                    '--branch', branch,
                    '--depth', '1',
                    clone_url,
                    target_dir
                ]
                
                safe_cmd = [
                    'git', 'clone',
                    '--branch', branch,
                    '--depth', '1',
                    repo_url,
                    target_dir
                ]
                logger.debug(f"Executing: {' '.join(safe_cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Cloned repository to: {target_dir}")
                return target_dir
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to clone repository: {e.stderr}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    details={
                        'repository': repo_url,
                        'branch': branch,
                        'exit_code': e.returncode,
                        'stderr': e.stderr
                    }
                )
    
    def copy_helm_chart(
        self,
        chart_path: str,
        repo_path: str,
        target_path: str
    ) -> str:
        """
        Copy Helm chart to k8s-charts repository.
        
        Args:
            chart_path: Path to generated Helm chart
            repo_path: Path to cloned k8s-charts repository
            target_path: Relative path within repository
            
        Returns:
            Full path to copied chart in repository
            
        Raises:
            DeploymentError: If copy operation fails
        """
        with OperationLogger(logger, f"copy Helm chart to {target_path}"):
            # Build full target path
            full_target_path = os.path.join(repo_path, target_path)
            
            # Create parent directories
            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
            
            # Remove existing chart if present
            if os.path.exists(full_target_path):
                logger.debug(f"Removing existing chart at {full_target_path}")
                shutil.rmtree(full_target_path)
            
            # Copy chart directory
            try:
                shutil.copytree(chart_path, full_target_path)
                logger.info(f"Copied chart to: {full_target_path}")
                return full_target_path
                
            except Exception as e:
                error_msg = f"Failed to copy Helm chart: {str(e)}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    details={
                        'source': chart_path,
                        'destination': full_target_path,
                        'error': str(e)
                    }
                )
    
    def commit_and_push_chart(
        self,
        repo_path: str,
        component_name: str,
        environment: str,
        commit_message: Optional[str] = None
    ) -> None:
        """
        Commit and push Helm chart changes to repository.
        
        Args:
            repo_path: Path to k8s-charts repository
            component_name: Component name
            environment: Environment name
            commit_message: Optional custom commit message
            
        Raises:
            DeploymentError: If git operations fail
        """
        with OperationLogger(logger, f"commit and push chart for {component_name}"):
            # Build commit message
            if commit_message is None:
                commit_message = f"Update {component_name} chart for {environment} environment"
            
            try:
                # Configure git user if not set
                self._configure_git_user(repo_path)
                
                # Stage all changes
                self._run_git_command(
                    ['git', 'add', '-A'],
                    cwd=repo_path,
                    description="stage changes"
                )
                
                # Check if there are changes to commit
                result = subprocess.run(
                    ['git', 'diff', '--cached', '--quiet'],
                    cwd=repo_path,
                    capture_output=True
                )
                
                if result.returncode == 0:
                    logger.info("No changes to commit")
                    return
                
                # Commit changes
                self._run_git_command(
                    ['git', 'commit', '-m', commit_message],
                    cwd=repo_path,
                    description="commit changes"
                )
                
                # Push to remote
                self._run_git_command(
                    ['git', 'push'],
                    cwd=repo_path,
                    description="push changes"
                )
                
                logger.info(f"Successfully pushed chart changes for {component_name}")
                
            except DeploymentError:
                raise
            except Exception as e:
                error_msg = f"Failed to commit and push chart: {str(e)}"
                logger.error(error_msg)
                raise DeploymentError(
                    error_msg,
                    details={
                        'repository': repo_path,
                        'component': component_name,
                        'environment': environment,
                        'error': str(e)
                    }
                )
    
    def _configure_git_user(self, repo_path: str) -> None:
        """Configure git user for commits if not already set."""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                subprocess.run(
                    ['git', 'config', 'user.name', 'GitLab CI/CD'],
                    cwd=repo_path,
                    check=True
                )
                logger.debug("Configured git user.name")
            
            result = subprocess.run(
                ['git', 'config', 'user.email'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                subprocess.run(
                    ['git', 'config', 'user.email', 'ci-cd@gitlab.com'],
                    cwd=repo_path,
                    check=True
                )
                logger.debug("Configured git user.email")
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to configure git user: {e}")
    
    def _run_git_command(
        self,
        cmd: list,
        cwd: str,
        description: str
    ) -> str:
        """Run a git command and handle errors."""
        logger.debug(f"Executing git command to {description}: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to {description}: {e.stderr}"
            logger.error(error_msg)
            raise DeploymentError(
                error_msg,
                details={
                    'command': ' '.join(cmd),
                    'exit_code': e.returncode,
                    'stderr': e.stderr,
                    'stdout': e.stdout
                }
            )
