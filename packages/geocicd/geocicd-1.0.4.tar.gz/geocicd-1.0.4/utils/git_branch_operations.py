"""
Git branch and tag operations for GitLab CI/CD Migration system.

Provides Git operations for branch management, tag listing, and repository status.
"""

import logging
from typing import List, Optional

from git import Repo, GitCommandError

from utils.exceptions_base import CICDMigrationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GitUtilsError(CICDMigrationError):
    """Exception raised when Git operations fail."""
    
    def __init__(
        self,
        message: str,
        repository_path: Optional[str] = None,
        git_error: Optional[str] = None,
    ):
        """
        Initialize Git utils error.
        
        Args:
            message: Error message
            repository_path: Path to Git repository
            git_error: Error message from Git command
        """
        details = {}
        if repository_path:
            details["repository_path"] = repository_path
        if git_error:
            details["git_error"] = git_error
        
        super().__init__(message, details)
        self.repository_path = repository_path
        self.git_error = git_error


class GitBranchOperations:
    """
    Git branch and tag operations.
    
    Provides methods for:
    - Checking branch existence
    - Listing remote and local branches
    - Getting commit metadata (message, author)
    - Checking repository status
    - Listing tags
    """
    
    def __init__(self, repo: Repo, repository_path: str):
        """
        Initialize GitBranchOperations.
        
        Args:
            repo: GitPython Repo object
            repository_path: Path to Git repository
        """
        self.repo = repo
        self.repository_path = repository_path
    
    def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists in the repository.
        
        Args:
            branch_name: Name of the branch to check (e.g., "develop", "origin/main")
            
        Returns:
            True if branch exists, False otherwise
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> if ops.branch_exists("origin/develop"):
            ...     print("Branch exists")
        """
        try:
            self.repo.commit(branch_name)
            return True
        except (GitCommandError, ValueError):
            return False
    
    def get_remote_branches(self) -> List[str]:
        """
        Get list of all remote branches.
        
        Returns:
            List of remote branch names (e.g., ["origin/main", "origin/develop"])
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> remotes = ops.get_remote_branches()
            >>> print(f"Remote branches: {remotes}")
        """
        try:
            remote_refs = self.repo.remote().refs
            branch_names = [ref.name for ref in remote_refs if not ref.name.endswith('/HEAD')]
            logger.debug(f"Found {len(branch_names)} remote branches")
            return sorted(branch_names)
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get remote branches: {str(e)}",
                repository_path=self.repository_path,
                git_error=str(e),
            )
    
    def get_local_branches(self) -> List[str]:
        """
        Get list of all local branches.
        
        Returns:
            List of local branch names (e.g., ["main", "develop", "feature/new"])
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> locals = ops.get_local_branches()
            >>> print(f"Local branches: {locals}")
        """
        try:
            branch_names = [head.name for head in self.repo.heads]
            logger.debug(f"Found {len(branch_names)} local branches")
            return sorted(branch_names)
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get local branches: {str(e)}",
                repository_path=self.repository_path,
                git_error=str(e),
            )
    
    def get_commit_message(self, commit_ref: Optional[str] = None) -> str:
        """
        Get the commit message for a specific commit or HEAD.
        
        Args:
            commit_ref: Commit reference (SHA, branch name, etc.). Default: HEAD
            
        Returns:
            Commit message as string
            
        Raises:
            GitUtilsError: If commit not found or Git operation fails
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> message = ops.get_commit_message()
            >>> print(f"Last commit: {message}")
        """
        try:
            if commit_ref is None:
                commit = self.repo.head.commit
            else:
                commit = self.repo.commit(commit_ref)
            
            return commit.message.strip()
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get commit message: {str(e)}",
                repository_path=self.repository_path,
                git_error=str(e),
            )
    
    def get_commit_author(self, commit_ref: Optional[str] = None) -> str:
        """
        Get the author of a specific commit or HEAD.
        
        Args:
            commit_ref: Commit reference (SHA, branch name, etc.). Default: HEAD
            
        Returns:
            Author name and email as string (e.g., "John Doe <john@example.com>")
            
        Raises:
            GitUtilsError: If commit not found or Git operation fails
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> author = ops.get_commit_author()
            >>> print(f"Author: {author}")
        """
        try:
            if commit_ref is None:
                commit = self.repo.head.commit
            else:
                commit = self.repo.commit(commit_ref)
            
            return f"{commit.author.name} <{commit.author.email}>"
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get commit author: {str(e)}",
                repository_path=self.repository_path,
                git_error=str(e),
            )
    
    def is_dirty(self) -> bool:
        """
        Check if the repository has uncommitted changes.
        
        Returns:
            True if there are uncommitted changes, False otherwise
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> if ops.is_dirty():
            ...     print("Warning: uncommitted changes detected")
        """
        return self.repo.is_dirty()
    
    def get_tags(self) -> List[str]:
        """
        Get list of all tags in the repository.
        
        Returns:
            List of tag names sorted alphabetically
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> ops = GitBranchOperations(repo, "/path/to/repo")
            >>> tags = ops.get_tags()
            >>> print(f"Tags: {tags}")
        """
        try:
            tag_names = [tag.name for tag in self.repo.tags]
            return sorted(tag_names)
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get tags: {str(e)}",
                repository_path=self.repository_path,
                git_error=str(e),
            )
