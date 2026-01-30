"""
Environment resolution for GitLab CI/CD pipeline generation.

This module provides the EnvironmentResolver class for determining the target
deployment environment based on Git branch names and configured branch patterns.

Requirements addressed:
- 2.1: Determine target environment by matching branch name against patterns
- 2.2: Use first matching environment in configuration order
- 2.3: Skip deployment stages when no environment matches
- 2.7: Apply default patterns based on environment name
- 14.5: Determine environment from merge request target branch
"""

from typing import Dict, List, Optional
from config.branch_matcher import BranchMatcher
from utils.logging_config import get_logger

logger = get_logger(__name__)


class EnvironmentResolver:
    """
    Resolves Git branch names to deployment environments.
    
    This class determines which environment (dev, stg, ese) a branch should
    deploy to based on configured branch patterns. It implements first-match
    precedence and supports default pattern application.
    """
    
    # Default branch patterns for common environment names
    DEFAULT_PATTERNS = {
        'dev': ['develop', 'develop-*', 'dev', 'dev-*', 'development'],
        'stg': ['staging', 'stage', 'stage/*', 'staging/*', 'stg', 'stg-*'],
        'ese': ['main', 'master', 'production', 'prod'],
        'test': ['test', 'test-*', 'testing'],
        'uat': ['uat', 'uat-*', 'acceptance'],
        'preprod': ['preprod', 'preprod-*', 'pre-production'],
    }
    
    def __init__(self, branch_matcher: Optional[BranchMatcher] = None):
        """
        Initialize the EnvironmentResolver.
        
        Args:
            branch_matcher: Optional BranchMatcher instance. If not provided,
                          a new instance will be created.
        """
        self.branch_matcher = branch_matcher or BranchMatcher()
        logger.debug("EnvironmentResolver initialized")
    
    def resolve_environment(self, branch_name: str, environments: Dict[str, Dict]) -> Optional[str]:
        """
        Determine the target environment for a given branch name.
        
        This method implements the core environment resolution logic:
        1. Iterate through environments in configuration order
        2. For each environment, check if branch matches its patterns
        3. Return the first matching environment name
        4. Return None if no environment matches
        
        Args:
            branch_name: The Git branch name (e.g., "develop", "release/1.0")
            environments: Dictionary of environment configurations
                         Format: {'env_name': {'branches': [...], ...}, ...}
        
        Returns:
            The name of the first matching environment, or None if no match
        
        Examples:
            >>> resolver = EnvironmentResolver()
            >>> envs = {
            ...     'dev': {'branches': ['develop', 'develop-*']},
            ...     'stg': {'branches': ['staging']},
            ... }
            >>> resolver.resolve_environment("develop", envs)
            'dev'
            >>> resolver.resolve_environment("unknown", envs)
            None
        """
        if not branch_name:
            logger.warning("Empty branch_name provided to resolve_environment")
            return None
        
        if not environments:
            logger.warning(f"Empty environments configuration for branch '{branch_name}'")
            return None
        
        logger.info(f"Resolving environment for branch: '{branch_name}'")
        
        # Iterate through environments in order (Python 3.7+ preserves dict order)
        for env_name, env_config in environments.items():
            if not isinstance(env_config, dict):
                logger.warning(f"Invalid environment configuration for '{env_name}': not a dictionary")
                continue
            
            # Get branch patterns for this environment
            patterns = self._get_branch_patterns(env_name, env_config)
            
            if not patterns:
                logger.debug(f"Environment '{env_name}' has no branch patterns, skipping")
                continue
            
            # Check if branch matches any pattern for this environment
            if self.branch_matcher.match_any(branch_name, patterns):
                logger.info(f"Branch '{branch_name}' resolved to environment: '{env_name}'")
                return env_name
        
        logger.info(f"Branch '{branch_name}' did not match any environment")
        return None
    
    def _get_branch_patterns(self, env_name: str, env_config: Dict) -> List[str]:
        """
        Get branch patterns for an environment, applying defaults if needed.
        
        This method implements the default pattern application logic:
        - If 'branches' is explicitly configured, use those patterns
        - If 'branches' is not configured, apply default patterns based on env name
        - If env name is not in DEFAULT_PATTERNS, return empty list
        
        Args:
            env_name: The environment name (e.g., 'dev', 'stg', 'ese')
            env_config: The environment configuration dictionary
        
        Returns:
            List of branch patterns for this environment
        """
        # Check if branches are explicitly configured
        if 'branches' in env_config:
            patterns = env_config['branches']
            
            # Validate that branches is a list
            if not isinstance(patterns, list):
                logger.warning(f"Environment '{env_name}' has invalid 'branches' config: not a list")
                return []
            
            # Filter out empty strings
            patterns = [p for p in patterns if p]
            
            if patterns:
                logger.debug(f"Using explicit patterns for '{env_name}': {patterns}")
                return patterns
            else:
                logger.debug(f"Environment '{env_name}' has empty 'branches' list")
        
        # Apply default patterns based on environment name
        default_patterns = self.DEFAULT_PATTERNS.get(env_name.lower())
        
        if default_patterns:
            logger.debug(f"Applying default patterns for '{env_name}': {default_patterns}")
            return default_patterns
        else:
            logger.debug(f"No default patterns available for environment '{env_name}'")
            return []
    
    def get_all_matching_environments(self, branch_name: str, environments: Dict[str, Dict]) -> List[str]:
        """
        Get all environments that match a branch name.
        
        This is useful for debugging and validation to see which environments
        would match a given branch. Note that only the first match is used
        for actual deployment.
        
        Args:
            branch_name: The Git branch name
            environments: Dictionary of environment configurations
        
        Returns:
            List of all environment names that match the branch
        
        Examples:
            >>> resolver = EnvironmentResolver()
            >>> envs = {
            ...     'dev': {'branches': ['develop*']},
            ...     'test': {'branches': ['develop*']},
            ... }
            >>> resolver.get_all_matching_environments("develop", envs)
            ['dev', 'test']
        """
        if not branch_name or not environments:
            return []
        
        matching_envs = []
        
        for env_name, env_config in environments.items():
            if not isinstance(env_config, dict):
                continue
            
            patterns = self._get_branch_patterns(env_name, env_config)
            
            if patterns and self.branch_matcher.match_any(branch_name, patterns):
                matching_envs.append(env_name)
        
        if len(matching_envs) > 1:
            logger.warning(
                f"Branch '{branch_name}' matches multiple environments: {matching_envs}. "
                f"First match '{matching_envs[0]}' will be used."
            )
        
        return matching_envs
    
    def should_deploy(self, branch_name: str, environments: Dict[str, Dict]) -> bool:
        """
        Check if a branch should trigger deployment to any environment.
        
        Args:
            branch_name: The Git branch name
            environments: Dictionary of environment configurations
        
        Returns:
            True if the branch matches at least one environment, False otherwise
        """
        env = self.resolve_environment(branch_name, environments)
        return env is not None
    
    def get_environment_info(self, branch_name: str, environments: Dict[str, Dict]) -> Optional[Dict]:
        """
        Get complete environment information for a branch.
        
        This returns the full environment configuration for the resolved environment,
        which is useful for downstream processing (deployment, configuration, etc.).
        
        Args:
            branch_name: The Git branch name
            environments: Dictionary of environment configurations
        
        Returns:
            Dictionary containing environment name and full configuration, or None
            Format: {'name': 'dev', 'config': {...}}
        """
        env_name = self.resolve_environment(branch_name, environments)
        
        if env_name is None:
            return None
        
        return {
            'name': env_name,
            'config': environments[env_name]
        }
    
    def validate_environment_config(self, environments: Dict[str, Dict]) -> List[str]:
        """
        Validate environment configuration and return any warnings.
        
        This checks for common configuration issues:
        - Environments with no branch patterns (explicit or default)
        - Overlapping patterns that might cause confusion
        - Invalid pattern syntax
        
        Args:
            environments: Dictionary of environment configurations
        
        Returns:
            List of warning messages (empty if no issues found)
        """
        warnings = []
        
        if not environments:
            warnings.append("No environments configured")
            return warnings
        
        # Check each environment
        for env_name, env_config in environments.items():
            if not isinstance(env_config, dict):
                warnings.append(f"Environment '{env_name}' has invalid configuration: not a dictionary")
                continue
            
            patterns = self._get_branch_patterns(env_name, env_config)
            
            if not patterns:
                warnings.append(
                    f"Environment '{env_name}' has no branch patterns and no default patterns available"
                )
        
        # Check for overlapping patterns
        all_patterns = {}
        for env_name, env_config in environments.items():
            if not isinstance(env_config, dict):
                continue
            
            patterns = self._get_branch_patterns(env_name, env_config)
            for pattern in patterns:
                if pattern in all_patterns:
                    warnings.append(
                        f"Pattern '{pattern}' is used in both '{all_patterns[pattern]}' and '{env_name}'. "
                        f"First match ('{all_patterns[pattern]}') will take precedence."
                    )
                else:
                    all_patterns[pattern] = env_name
        
        return warnings
