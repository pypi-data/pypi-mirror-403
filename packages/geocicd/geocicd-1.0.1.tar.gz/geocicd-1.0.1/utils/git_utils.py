"""
Git utility functions for GitLab CI/CD Migration system.

Provides Git operations for change detection, versioning, and branch management.
"""

import logging
from typing import List, Optional
from pathlib import Path

from git import Repo, GitCommandError, InvalidGitRepositoryError
from git.exc import NoSuchPathError

from utils.exceptions_base import CICDMigrationError
from utils.git_branch_operations import GitBranchOperations, GitUtilsError
from utils.logging_config import get_logger


logger = get_logger(__name__)


class GitUtils:
    """
    Utility class for Git operations.
    
    Provides methods for:
    - Getting changed files between branches
    - Determining current branch
    - Getting commit information for versioning
    """
    
    def __init__(self, repository_path: str = "."):
        """
        Initialize GitUtils with repository path.
        
        Args:
            repository_path: Path to Git repository (default: current directory)
            
        Raises:
            GitUtilsError: If path is not a valid Git repository
        """
        self.repository_path = Path(repository_path).resolve()
        
        try:
            self.repo = Repo(self.repository_path)
        except InvalidGitRepositoryError:
            raise GitUtilsError(
                f"Path is not a valid Git repository: {self.repository_path}",
                repository_path=str(self.repository_path),
            )
        except NoSuchPathError:
            raise GitUtilsError(
                f"Repository path does not exist: {self.repository_path}",
                repository_path=str(self.repository_path),
            )
        
        logger.debug(f"Initialized GitUtils for repository: {self.repository_path}")
        self.branch_ops = GitBranchOperations(self.repo, str(self.repository_path))
    
    def get_changed_files(
        self,
        base_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
    ) -> List[str]:
        """
        Get list of changed files between branches.
        
        If base_branch is None, returns all tracked files.
        If target_branch is None, uses current HEAD.
        
        Args:
            base_branch: Base branch to compare against (e.g., "develop", "origin/develop")
            target_branch: Target branch to compare (default: current HEAD)
            
        Returns:
            List of file paths relative to repository root
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> # Get files changed between develop and current branch
            >>> changed = git_utils.get_changed_files("origin/develop")
            >>> # Get all tracked files
            >>> all_files = git_utils.get_changed_files()
        """
        try:
            # If no base branch specified, return all tracked files
            if base_branch is None:
                logger.debug("No base branch specified, returning all tracked files")
                tracked_files = []
                for item in self.repo.tree().traverse():
                    if item.type == 'blob':  # Only files, not directories
                        tracked_files.append(item.path)
                logger.debug(f"Found {len(tracked_files)} tracked files")
                return tracked_files
            
            # Resolve target branch (default to HEAD)
            if target_branch is None:
                target_ref = self.repo.head.commit
                target_name = "HEAD"
            else:
                target_ref = self.repo.commit(target_branch)
                target_name = target_branch
            
            # Resolve base branch
            try:
                base_ref = self.repo.commit(base_branch)
            except GitCommandError as e:
                raise GitUtilsError(
                    f"Base branch not found: {base_branch}",
                    repository_path=str(self.repository_path),
                    git_error=str(e),
                )
            
            logger.debug(f"Comparing {base_branch} with {target_name}")
            
            # Get diff between commits
            diff_index = base_ref.diff(target_ref)
            
            # Extract changed file paths
            changed_files = []
            for diff_item in diff_index:
                # Include both added and modified files
                if diff_item.a_path:
                    changed_files.append(diff_item.a_path)
                if diff_item.b_path and diff_item.b_path != diff_item.a_path:
                    changed_files.append(diff_item.b_path)
            
            # Remove duplicates and sort
            changed_files = sorted(set(changed_files))
            
            logger.debug(
                f"Found {len(changed_files)} changed files between "
                f"{base_branch} and {target_name}"
            )
            
            return changed_files
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get changed files: {str(e)}",
                repository_path=str(self.repository_path),
                git_error=str(e),
            )
    
    def get_current_branch(self) -> str:
        """
        Get the name of the current active branch.
        
        Returns:
            Current branch name (e.g., "develop", "feature/new-feature")
            
        Raises:
            GitUtilsError: If not on a branch (detached HEAD) or Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> branch = git_utils.get_current_branch()
            >>> print(f"Current branch: {branch}")
        """
        try:
            if self.repo.head.is_detached:
                raise GitUtilsError(
                    "Repository is in detached HEAD state (not on any branch)",
                    repository_path=str(self.repository_path),
                )
            
            branch_name = self.repo.active_branch.name
            logger.debug(f"Current branch: {branch_name}")
            return branch_name
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get current branch: {str(e)}",
                repository_path=str(self.repository_path),
                git_error=str(e),
            )
    
    def get_commit_sha(self, short: bool = False) -> str:
        """
        Get the full or short commit SHA of the current HEAD.
        
        Args:
            short: If True, return short SHA (7 characters), otherwise full SHA
            
        Returns:
            Commit SHA as string
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> full_sha = git_utils.get_commit_sha()
            >>> short_sha = git_utils.get_commit_sha(short=True)
        """
        try:
            commit = self.repo.head.commit
            sha = commit.hexsha
            
            if short:
                sha = sha[:7]
            
            logger.debug(f"Current commit SHA: {sha}")
            return sha
            
        except GitCommandError as e:
            raise GitUtilsError(
                f"Failed to get commit SHA: {str(e)}",
                repository_path=str(self.repository_path),
                git_error=str(e),
            )
    
    def get_commit_short(self) -> str:
        """
        Get the short commit SHA (7 characters) of the current HEAD.
        
        This is a convenience method that calls get_commit_sha(short=True).
        
        Returns:
            Short commit SHA as string (7 characters)
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> short_sha = git_utils.get_commit_short()
            >>> print(f"Short SHA: {short_sha}")
        """
        return self.get_commit_sha(short=True)
    
    def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists in the repository.
        
        Args:
            branch_name: Name of the branch to check (e.g., "develop", "origin/main")
            
        Returns:
            True if branch exists, False otherwise
            
        Examples:
            >>> git_utils = GitUtils()
            >>> if git_utils.branch_exists("origin/develop"):
            ...     print("Branch exists")
        """
        return self.branch_ops.branch_exists(branch_name)
    
    def get_remote_branches(self) -> List[str]:
        """
        Get list of all remote branches.
        
        Returns:
            List of remote branch names (e.g., ["origin/main", "origin/develop"])
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> remotes = git_utils.get_remote_branches()
            >>> print(f"Remote branches: {remotes}")
        """
        return self.branch_ops.get_remote_branches()
    
    def get_local_branches(self) -> List[str]:
        """
        Get list of all local branches.
        
        Returns:
            List of local branch names (e.g., ["main", "develop", "feature/new"])
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> locals = git_utils.get_local_branches()
            >>> print(f"Local branches: {locals}")
        """
        return self.branch_ops.get_local_branches()
    
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
            >>> git_utils = GitUtils()
            >>> message = git_utils.get_commit_message()
            >>> print(f"Last commit: {message}")
        """
        return self.branch_ops.get_commit_message(commit_ref)
    
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
            >>> git_utils = GitUtils()
            >>> author = git_utils.get_commit_author()
            >>> print(f"Author: {author}")
        """
        return self.branch_ops.get_commit_author(commit_ref)
    
    def is_dirty(self) -> bool:
        """
        Check if the repository has uncommitted changes.
        
        Returns:
            True if there are uncommitted changes, False otherwise
            
        Examples:
            >>> git_utils = GitUtils()
            >>> if git_utils.is_dirty():
            ...     print("Warning: uncommitted changes detected")
        """
        return self.branch_ops.is_dirty()
    
    def get_tags(self) -> List[str]:
        """
        Get list of all tags in the repository.
        
        Returns:
            List of tag names sorted alphabetically
            
        Raises:
            GitUtilsError: If Git operation fails
            
        Examples:
            >>> git_utils = GitUtils()
            >>> tags = git_utils.get_tags()
            >>> print(f"Tags: {tags}")
        """
        return self.branch_ops.get_tags()
