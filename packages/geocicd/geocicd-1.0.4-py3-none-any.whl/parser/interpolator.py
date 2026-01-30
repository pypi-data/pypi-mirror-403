"""
Interpolator module for GitLab CI/CD Migration system.

This module provides variable interpolation and resolution for configuration files.
Supports {{ variable.path }} expressions with nested references and context building.
"""

import logging
import re
from typing import Any, Dict, List, Set

from utils.exceptions import InterpolationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Interpolator:
    """
    Resolves {{ variable }} expressions in configuration.
    
    This class provides recursive interpolation with support for:
    - Dot notation: {{ project.name }}
    - Nested references: {{ defaults.{{ env }}.value }}
    - Array indexing: {{ components[0].name }}
    - Multiple expressions in single string: "{{ prefix }}-{{ suffix }}"
    """
    
    # Pattern to match {{ expression }}
    INTERPOLATION_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    # Maximum recursion depth to prevent infinite loops
    MAX_RECURSION_DEPTH = 10
    
    def __init__(self):
        """Initialize interpolator."""
        self._recursion_depth = 0
        self._resolving_stack: List[str] = []
    
    def resolve(self, obj: Any, context: Dict[str, Any]) -> Any:
        """
        Recursively resolve interpolation expressions in an object.
        
        Args:
            obj: Object to interpolate (dict, list, str, or primitive)
            context: Variable context for resolution
            
        Returns:
            Object with all interpolations resolved
            
        Raises:
            InterpolationError: If variable not found or circular reference detected
        """
        # Reset recursion tracking for top-level call
        if self._recursion_depth == 0:
            self._resolving_stack = []
        
        # Check recursion depth
        self._recursion_depth += 1
        if self._recursion_depth > self.MAX_RECURSION_DEPTH:
            self._recursion_depth = 0
            raise InterpolationError(
                f"Maximum recursion depth ({self.MAX_RECURSION_DEPTH}) exceeded",
                circular_references=self._resolving_stack
            )
        
        try:
            result = self._resolve_recursive(obj, context)
            self._recursion_depth -= 1
            return result
        except Exception:
            self._recursion_depth = 0
            raise
    
    def _resolve_recursive(self, obj: Any, context: Dict[str, Any]) -> Any:
        """
        Internal recursive resolution method.
        
        Args:
            obj: Object to interpolate
            context: Variable context
            
        Returns:
            Resolved object
        """
        if isinstance(obj, dict):
            # Resolve all values in dictionary
            return {
                key: self._resolve_recursive(value, context)
                for key, value in obj.items()
            }
        
        elif isinstance(obj, list):
            # Resolve all items in list
            return [
                self._resolve_recursive(item, context)
                for item in obj
            ]
        
        elif isinstance(obj, str):
            # Resolve string interpolations
            return self._resolve_string(obj, context)
        
        else:
            # Return primitives as-is (int, float, bool, None)
            return obj
    
    def _resolve_string(self, text: str, context: Dict[str, Any]) -> Any:
        """
        Resolve interpolation expressions in a string.
        
        Args:
            text: String potentially containing {{ expressions }}
            context: Variable context
            
        Returns:
            Resolved value (string or other type if single expression)
        """
        # Find all interpolation expressions
        matches = list(self.INTERPOLATION_PATTERN.finditer(text))
        
        if not matches:
            # No interpolations, return as-is
            return text
        
        # Check if entire string is a single expression
        if len(matches) == 1 and matches[0].group(0) == text:
            # Single expression - return resolved value with original type
            expression = matches[0].group(1).strip()
            return self.resolve_expression(expression, context)
        
        # Multiple expressions or mixed text - build string
        result = text
        for match in reversed(matches):  # Process in reverse to maintain positions
            expression = match.group(1).strip()
            value = self.resolve_expression(expression, context)
            
            # Convert value to string for substitution
            str_value = self._value_to_string(value)
            
            # Replace the {{ expression }} with resolved value
            result = result[:match.start()] + str_value + result[match.end():]
        
        return result
    
    def resolve_expression(self, expr: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a single {{ expression }}.
        
        Supports:
        - Simple variables: project.name
        - Nested references: defaults.{{ env }}.value
        - Array indexing: components[0].name
        
        Args:
            expr: Expression like "project.name" (without {{ }})
            context: Variable context
            
        Returns:
            Resolved value
            
        Raises:
            InterpolationError: If variable not found in context
        """
        # Check for circular references
        if expr in self._resolving_stack:
            raise InterpolationError(
                f"Circular reference detected: {expr}",
                expression=expr,
                circular_references=self._resolving_stack + [expr]
            )
        
        # Add to resolution stack
        self._resolving_stack.append(expr)
        
        try:
            # First, resolve any nested {{ }} in the expression itself
            if '{{' in expr:
                expr = self._resolve_string(expr, context)
            
            # Now resolve the path
            value = self._resolve_path(expr, context)
            
            # Remove from resolution stack
            self._resolving_stack.pop()
            
            return value
        
        except InterpolationError:
            # Re-raise interpolation errors
            raise
        except Exception as e:
            # Remove from resolution stack on error
            if self._resolving_stack and self._resolving_stack[-1] == expr:
                self._resolving_stack.pop()
            raise InterpolationError(
                f"Failed to resolve expression: {expr}",
                expression=expr,
                missing_variables=[expr]
            )
    
    def _resolve_path(self, path: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a dot-notation path in the context.
        
        Args:
            path: Dot-notation path like "project.name" or "components[0].name"
            context: Variable context
            
        Returns:
            Value at the path
            
        Raises:
            InterpolationError: If path not found
        """
        # Split path by dots, handling array indexing
        parts = self._split_path(path)
        
        # Navigate through the context
        current = context
        resolved_path = []
        
        for part in parts:
            resolved_path.append(part)
            
            # Check for array indexing
            if '[' in part and part.endswith(']'):
                # Extract array name and index
                array_name, index_str = part[:-1].split('[', 1)
                
                try:
                    index = int(index_str)
                except ValueError:
                    raise InterpolationError(
                        f"Invalid array index: {index_str}",
                        expression=path,
                        missing_variables=['.'.join(resolved_path)]
                    )
                
                # Get array
                if not isinstance(current, dict) or array_name not in current:
                    raise InterpolationError(
                        f"Variable not found: {'.'.join(resolved_path)}",
                        expression=path,
                        missing_variables=['.'.join(resolved_path)]
                    )
                
                current = current[array_name]
                
                # Get indexed item
                if not isinstance(current, list) or index >= len(current):
                    raise InterpolationError(
                        f"Array index out of bounds: {index}",
                        expression=path,
                        missing_variables=['.'.join(resolved_path)]
                    )
                
                current = current[index]
            
            else:
                # Regular property access
                if isinstance(current, dict):
                    if part not in current:
                        raise InterpolationError(
                            f"Variable not found: {'.'.join(resolved_path)}",
                            expression=path,
                            missing_variables=['.'.join(resolved_path)]
                        )
                    current = current[part]
                else:
                    raise InterpolationError(
                        f"Cannot access property '{part}' on non-dict value",
                        expression=path,
                        missing_variables=['.'.join(resolved_path)]
                    )
        
        return current
    
    def _split_path(self, path: str) -> List[str]:
        """
        Split a path into parts, handling array indexing.
        
        Args:
            path: Path like "project.name" or "components[0].name"
            
        Returns:
            List of path parts
        """
        # Split by dots, but keep array indexing together
        parts = []
        current = ""
        
        for char in path:
            if char == '.':
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def _value_to_string(self, value: Any) -> str:
        """
        Convert a value to string for interpolation.
        
        Args:
            value: Value to convert
            
        Returns:
            String representation
        """
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (list, dict)):
            # For complex types, use JSON-like representation
            import json
            return json.dumps(value)
        else:
            return str(value)
    
    def build_context(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build interpolation context from configuration.
        
        The context includes:
        - All top-level configuration keys
        - Environment variables (if available)
        - Special variables (CI_*, etc.)
        
        Args:
            config: Parsed configuration
            
        Returns:
            Context dictionary for interpolation
        """
        import os
        
        # Start with the configuration itself
        context = dict(config)
        
        # Add environment variables under 'env' key
        context['env'] = dict(os.environ)
        
        # Add special CI variables if available
        ci_vars = {}
        for key, value in os.environ.items():
            if key.startswith('CI_') or key.startswith('GITLAB_'):
                ci_vars[key] = value
        
        if ci_vars:
            context['ci'] = ci_vars
        
        logger.debug(f"Built interpolation context with {len(context)} top-level keys")
        
        return context
    
    def find_undefined_variables(self, obj: Any, context: Dict[str, Any]) -> List[str]:
        """
        Find all undefined variables in an object without resolving.
        
        This is useful for validation - finding all missing variables
        before attempting resolution.
        
        Args:
            obj: Object to scan for variables
            context: Variable context
            
        Returns:
            List of undefined variable expressions
        """
        undefined = []
        
        def scan(item: Any):
            """Recursively scan for undefined variables."""
            if isinstance(item, dict):
                for value in item.values():
                    scan(value)
            elif isinstance(item, list):
                for element in item:
                    scan(element)
            elif isinstance(item, str):
                # Find all interpolation expressions
                matches = self.INTERPOLATION_PATTERN.findall(item)
                for expr in matches:
                    expr = expr.strip()
                    try:
                        # Try to resolve - if it fails, it's undefined
                        self._resolve_path(expr, context)
                    except InterpolationError:
                        if expr not in undefined:
                            undefined.append(expr)
        
        scan(obj)
        return undefined
    
    def has_interpolations(self, obj: Any) -> bool:
        """
        Check if an object contains any interpolation expressions.
        
        Args:
            obj: Object to check
            
        Returns:
            True if object contains {{ }} expressions, False otherwise
        """
        def check(item: Any) -> bool:
            """Recursively check for interpolations."""
            if isinstance(item, dict):
                return any(check(value) for value in item.values())
            elif isinstance(item, list):
                return any(check(element) for element in item)
            elif isinstance(item, str):
                return bool(self.INTERPOLATION_PATTERN.search(item))
            return False
        
        return check(obj)
