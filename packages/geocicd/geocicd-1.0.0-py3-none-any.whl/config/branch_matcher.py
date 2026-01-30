"""
Branch pattern matching for GitLab CI/CD pipeline generation.

This module provides the BranchMatcher class for matching Git branch names
against configured patterns. Supports exact matching, wildcard matching,
and path-based matching.

Requirements addressed:
- 2.1: Determine target environment by matching branch name against patterns
- 2.4: Support exact branch matching (e.g., "develop")
- 2.5: Support wildcard matching (e.g., "develop-*")
- 2.6: Support path-based matching (e.g., "release/*")
"""

import fnmatch
import re
from typing import List, Optional, Dict
from utils.logging_config import get_logger

logger = get_logger(__name__)


class BranchMatcher:
    """
    Matches Git branch names against configured patterns.
    
    Supports three types of patterns:
    1. Exact match: "develop" matches only "develop"
    2. Wildcard match: "develop-*" matches "develop-feature", "develop-bugfix", etc.
    3. Path match: "release/*" matches "release/1.0", "release/2.0", etc.
    
    Pattern matching is case-sensitive and uses fnmatch for glob-style patterns.
    """
    
    def __init__(self):
        """Initialize the BranchMatcher with an empty pattern cache."""
        self._pattern_cache: Dict[str, re.Pattern] = {}
        logger.debug("BranchMatcher initialized")
    
    def match(self, branch_name: str, pattern: str) -> bool:
        """
        Check if a branch name matches a pattern.
        
        Args:
            branch_name: The Git branch name to match (e.g., "develop", "feature/login")
            pattern: The pattern to match against (e.g., "develop", "feature/*", "release-*")
        
        Returns:
            True if the branch name matches the pattern, False otherwise
        
        Examples:
            >>> matcher = BranchMatcher()
            >>> matcher.match("develop", "develop")
            True
            >>> matcher.match("develop-feature", "develop-*")
            True
            >>> matcher.match("release/1.0", "release/*")
            True
            >>> matcher.match("main", "develop")
            False
        """
        if not branch_name or not pattern:
            logger.warning(f"Empty branch_name or pattern: branch='{branch_name}', pattern='{pattern}'")
            return False
        
        # Use fnmatch for glob-style pattern matching
        # This handles exact matches, wildcards (*), and path patterns
        result = fnmatch.fnmatch(branch_name, pattern)
        
        logger.debug(f"Branch match: '{branch_name}' vs pattern '{pattern}' = {result}")
        return result
    
    def match_any(self, branch_name: str, patterns: List[str]) -> bool:
        """
        Check if a branch name matches any of the provided patterns.
        
        Args:
            branch_name: The Git branch name to match
            patterns: List of patterns to match against
        
        Returns:
            True if the branch name matches at least one pattern, False otherwise
        
        Examples:
            >>> matcher = BranchMatcher()
            >>> matcher.match_any("develop", ["develop", "main"])
            True
            >>> matcher.match_any("feature/login", ["feature/*", "bugfix/*"])
            True
            >>> matcher.match_any("hotfix/urgent", ["feature/*", "bugfix/*"])
            False
        """
        if not branch_name:
            logger.warning("Empty branch_name provided to match_any")
            return False
        
        if not patterns:
            logger.warning(f"Empty patterns list for branch '{branch_name}'")
            return False
        
        for pattern in patterns:
            if self.match(branch_name, pattern):
                logger.debug(f"Branch '{branch_name}' matched pattern '{pattern}'")
                return True
        
        logger.debug(f"Branch '{branch_name}' did not match any of {len(patterns)} patterns")
        return False
    
    def find_first_match(self, branch_name: str, pattern_groups: List[Dict[str, any]]) -> Optional[Dict[str, any]]:
        """
        Find the first pattern group that matches the branch name.
        
        This implements the first-match precedence logic required by the specification.
        When multiple environments match a branch pattern, the first matching environment
        in configuration order is selected.
        
        Args:
            branch_name: The Git branch name to match
            pattern_groups: List of dictionaries containing 'patterns' key and other metadata
                           Each dict should have: {'patterns': List[str], ...other fields}
        
        Returns:
            The first matching pattern group dictionary, or None if no match found
        
        Examples:
            >>> matcher = BranchMatcher()
            >>> groups = [
            ...     {'name': 'dev', 'patterns': ['develop', 'develop-*']},
            ...     {'name': 'stg', 'patterns': ['staging', 'stage/*']},
            ... ]
            >>> result = matcher.find_first_match("develop", groups)
            >>> result['name']
            'dev'
        """
        if not branch_name:
            logger.warning("Empty branch_name provided to find_first_match")
            return None
        
        if not pattern_groups:
            logger.warning(f"Empty pattern_groups for branch '{branch_name}'")
            return None
        
        for group in pattern_groups:
            patterns = group.get('patterns', [])
            if not patterns:
                logger.warning(f"Pattern group missing 'patterns' key or has empty patterns: {group}")
                continue
            
            if self.match_any(branch_name, patterns):
                logger.info(f"Branch '{branch_name}' matched first group: {group.get('name', 'unnamed')}")
                return group
        
        logger.info(f"Branch '{branch_name}' did not match any of {len(pattern_groups)} pattern groups")
        return None
    
    def compile_pattern(self, pattern: str) -> re.Pattern:
        """
        Compile a glob pattern into a regular expression for caching.
        
        This method is used internally for performance optimization when
        the same patterns are matched repeatedly.
        
        Args:
            pattern: The glob pattern to compile
        
        Returns:
            Compiled regular expression pattern
        """
        if pattern in self._pattern_cache:
            return self._pattern_cache[pattern]
        
        # Convert fnmatch pattern to regex
        regex_pattern = fnmatch.translate(pattern)
        compiled = re.compile(regex_pattern)
        self._pattern_cache[pattern] = compiled
        
        logger.debug(f"Compiled and cached pattern: '{pattern}'")
        return compiled
    
    def clear_cache(self):
        """
        Clear the pattern cache.
        
        This can be useful in testing or when pattern definitions change dynamically.
        """
        cache_size = len(self._pattern_cache)
        self._pattern_cache.clear()
        logger.debug(f"Cleared pattern cache ({cache_size} entries)")
