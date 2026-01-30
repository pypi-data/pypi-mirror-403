"""
Pattern matching utility for file path matching.

Provides glob pattern matching for change detection, supporting include
and exclude pattern lists.
"""

import logging
from typing import List, Optional
from fnmatch import fnmatch
from pathlib import Path

from utils.logging_config import get_logger


logger = get_logger(__name__)


class PatternMatcher:
    """
    Utility class for matching file paths against glob patterns.
    
    Supports:
    - Include patterns (files must match at least one)
    - Exclude patterns (files must not match any)
    - Standard glob patterns (*, **, ?, [abc])
    
    Examples:
        >>> matcher = PatternMatcher(
        ...     include_patterns=["src/**/*.py", "tests/**/*.py"],
        ...     exclude_patterns=["**/__pycache__/**", "**/*.pyc"]
        ... )
        >>> matcher.matches("src/main.py")  # True
        >>> matcher.matches("src/__pycache__/main.pyc")  # False
    """
    
    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize PatternMatcher with include and exclude patterns.
        
        Args:
            include_patterns: List of glob patterns to include.
                             If None or empty, all files are included by default.
            exclude_patterns: List of glob patterns to exclude.
                             If None or empty, no files are excluded.
        
        Examples:
            >>> # Match all Python files except in __pycache__
            >>> matcher = PatternMatcher(
            ...     include_patterns=["**/*.py"],
            ...     exclude_patterns=["**/__pycache__/**"]
            ... )
            
            >>> # Match all files in frontend/ except node_modules
            >>> matcher = PatternMatcher(
            ...     include_patterns=["frontend/**"],
            ...     exclude_patterns=["frontend/node_modules/**"]
            ... )
        """
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        
        logger.debug(
            f"Initialized PatternMatcher with {len(self.include_patterns)} "
            f"include patterns and {len(self.exclude_patterns)} exclude patterns"
        )
    
    def matches(self, file_path: str) -> bool:
        """
        Check if a file path matches the configured patterns.
        
        A file matches if:
        1. It matches at least one include pattern (or no include patterns are specified)
        2. AND it does not match any exclude pattern
        
        Args:
            file_path: File path to check (relative or absolute)
        
        Returns:
            True if file matches patterns, False otherwise
        
        Examples:
            >>> matcher = PatternMatcher(
            ...     include_patterns=["src/**/*.py"],
            ...     exclude_patterns=["**/*_test.py"]
            ... )
            >>> matcher.matches("src/main.py")  # True
            >>> matcher.matches("src/main_test.py")  # False
            >>> matcher.matches("docs/readme.md")  # False (doesn't match include)
        """
        # Normalize path separators to forward slashes for consistent matching
        normalized_path = str(Path(file_path)).replace('\\', '/')
        
        # Check exclude patterns first (more efficient to reject early)
        if self._matches_any_pattern(normalized_path, self.exclude_patterns):
            logger.debug(f"File '{file_path}' excluded by exclude patterns")
            return False
        
        # If no include patterns specified, include all files (that aren't excluded)
        if not self.include_patterns:
            logger.debug(f"File '{file_path}' included (no include patterns specified)")
            return True
        
        # Check if file matches at least one include pattern
        if self._matches_any_pattern(normalized_path, self.include_patterns):
            logger.debug(f"File '{file_path}' included by include patterns")
            return True
        
        logger.debug(f"File '{file_path}' does not match any include pattern")
        return False
    
    def _matches_any_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """
        Check if file path matches any pattern in the list.
        
        Args:
            file_path: Normalized file path
            patterns: List of glob patterns
        
        Returns:
            True if file matches at least one pattern, False otherwise
        """
        for pattern in patterns:
            # Normalize pattern separators
            normalized_pattern = pattern.replace('\\', '/')
            
            # Use fnmatch for glob pattern matching
            if fnmatch(file_path, normalized_pattern):
                logger.debug(f"File '{file_path}' matches pattern '{pattern}'")
                return True
        
        return False
    
    def filter_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter a list of file paths, returning only those that match patterns.
        
        Args:
            file_paths: List of file paths to filter
        
        Returns:
            List of file paths that match the patterns
        
        Examples:
            >>> matcher = PatternMatcher(include_patterns=["**/*.py"])
            >>> files = ["main.py", "test.js", "utils.py"]
            >>> matcher.filter_files(files)
            ['main.py', 'utils.py']
        """
        matched_files = [path for path in file_paths if self.matches(path)]
        
        logger.debug(
            f"Filtered {len(file_paths)} files to {len(matched_files)} "
            f"matching files"
        )
        
        return matched_files
    
    def get_include_patterns(self) -> List[str]:
        """
        Get the list of include patterns.
        
        Returns:
            List of include patterns
        """
        return self.include_patterns.copy()
    
    def get_exclude_patterns(self) -> List[str]:
        """
        Get the list of exclude patterns.
        
        Returns:
            List of exclude patterns
        """
        return self.exclude_patterns.copy()
    
    def add_include_pattern(self, pattern: str) -> None:
        """
        Add an include pattern to the matcher.
        
        Args:
            pattern: Glob pattern to add
        
        Examples:
            >>> matcher = PatternMatcher()
            >>> matcher.add_include_pattern("**/*.py")
        """
        if pattern not in self.include_patterns:
            self.include_patterns.append(pattern)
            logger.debug(f"Added include pattern: {pattern}")
    
    def add_exclude_pattern(self, pattern: str) -> None:
        """
        Add an exclude pattern to the matcher.
        
        Args:
            pattern: Glob pattern to add
        
        Examples:
            >>> matcher = PatternMatcher()
            >>> matcher.add_exclude_pattern("**/__pycache__/**")
        """
        if pattern not in self.exclude_patterns:
            self.exclude_patterns.append(pattern)
            logger.debug(f"Added exclude pattern: {pattern}")
    
    def remove_include_pattern(self, pattern: str) -> bool:
        """
        Remove an include pattern from the matcher.
        
        Args:
            pattern: Glob pattern to remove
        
        Returns:
            True if pattern was removed, False if it wasn't in the list
        
        Examples:
            >>> matcher = PatternMatcher(include_patterns=["**/*.py"])
            >>> matcher.remove_include_pattern("**/*.py")
            True
        """
        if pattern in self.include_patterns:
            self.include_patterns.remove(pattern)
            logger.debug(f"Removed include pattern: {pattern}")
            return True
        return False
    
    def remove_exclude_pattern(self, pattern: str) -> bool:
        """
        Remove an exclude pattern from the matcher.
        
        Args:
            pattern: Glob pattern to remove
        
        Returns:
            True if pattern was removed, False if it wasn't in the list
        
        Examples:
            >>> matcher = PatternMatcher(exclude_patterns=["**/*.pyc"])
            >>> matcher.remove_exclude_pattern("**/*.pyc")
            True
        """
        if pattern in self.exclude_patterns:
            self.exclude_patterns.remove(pattern)
            logger.debug(f"Removed exclude pattern: {pattern}")
            return True
        return False
    
    def clear_patterns(self) -> None:
        """
        Clear all include and exclude patterns.
        
        Examples:
            >>> matcher = PatternMatcher(
            ...     include_patterns=["**/*.py"],
            ...     exclude_patterns=["**/*.pyc"]
            ... )
            >>> matcher.clear_patterns()
            >>> matcher.get_include_patterns()
            []
        """
        self.include_patterns.clear()
        self.exclude_patterns.clear()
        logger.debug("Cleared all patterns")
    
    def __repr__(self) -> str:
        """String representation of PatternMatcher."""
        return (
            f"PatternMatcher("
            f"include_patterns={self.include_patterns}, "
            f"exclude_patterns={self.exclude_patterns})"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        include_str = f"{len(self.include_patterns)} include patterns"
        exclude_str = f"{len(self.exclude_patterns)} exclude patterns"
        return f"PatternMatcher with {include_str} and {exclude_str}"
