"""
VersionExtractor module for GitLab CI/CD Migration system.

This module provides version extraction from project files.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class VersionExtractor:
    """
    Extractor for version information from project files.
    
    This class extracts version information from:
    - package.json for NPM/Node.js projects
    - pom.xml for Maven projects
    - Configuration files
    - Git tags
    
    Responsibilities:
    - Extract version from package.json
    - Extract version from pom.xml
    - Support explicit version in configuration
    - Provide fallback version strategies
    """
    
    def __init__(self):
        """Initialize version extractor."""
        logger.debug("VersionExtractor initialized")
    
    def extract_version(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any],
        fallback: str = "1.0.0"
    ) -> str:
        """
        Extract version from component configuration or project files.
        
        Extraction order:
        1. Explicit version in component configuration
        2. Explicit version in project configuration
        3. Version from package.json (for NPM/Vue components)
        4. Version from pom.xml (for Maven components)
        5. Fallback version
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
            fallback: Fallback version if no version found
        
        Returns:
            Version string (e.g., "1.2.3")
        """
        with OperationLogger(logger, f"extract version for {component.get('name')}"):
            component_name = component.get('name')
            component_type = component.get('type', '')
            component_path = component.get('path', '.')
            
            # 1. Check explicit version in component
            if 'version' in component:
                version = component['version']
                logger.info(f"Using explicit version from component: {version}")
                return version
            
            # 2. Check explicit version in project
            project = config.get('project', {})
            if 'version' in project:
                version = project['version']
                logger.info(f"Using version from project configuration: {version}")
                return version
            
            # 3. Extract from package.json for NPM/Vue components
            if component_type in ['npm', 'vue', 'node']:
                version = self.extract_from_package_json(component_path)
                if version:
                    logger.info(f"Extracted version from package.json: {version}")
                    return version
            
            # 4. Extract from pom.xml for Maven components
            if component_type == 'maven':
                version = self.extract_from_pom_xml(component_path)
                if version:
                    logger.info(f"Extracted version from pom.xml: {version}")
                    return version
            
            # 5. Use fallback
            logger.warning(f"No version found for {component_name}, using fallback: {fallback}")
            return fallback
    
    def extract_from_package_json(self, component_path: str) -> Optional[str]:
        """
        Extract version from package.json file.
        
        Args:
            component_path: Path to component directory
        
        Returns:
            Version string or None if not found
        """
        package_json_path = Path(component_path) / "package.json"
        
        if not package_json_path.exists():
            logger.debug(f"package.json not found at {package_json_path}")
            return None
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            version = package_data.get('version')
            if version:
                logger.debug(f"Found version in package.json: {version}")
                return version
            else:
                logger.debug("No version field in package.json")
                return None
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse package.json: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading package.json: {e}")
            return None
    
    def extract_from_pom_xml(self, component_path: str) -> Optional[str]:
        """
        Extract version from pom.xml file.
        
        Args:
            component_path: Path to component directory
        
        Returns:
            Version string or None if not found
        """
        pom_xml_path = Path(component_path) / "pom.xml"
        
        if not pom_xml_path.exists():
            logger.debug(f"pom.xml not found at {pom_xml_path}")
            return None
        
        try:
            tree = ET.parse(pom_xml_path)
            root = tree.getroot()
            
            # Handle XML namespace
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            # Try with namespace
            version_elem = root.find('maven:version', namespace)
            if version_elem is not None and version_elem.text:
                version = version_elem.text.strip()
                logger.debug(f"Found version in pom.xml: {version}")
                return version
            
            # Try without namespace (for POMs without namespace)
            version_elem = root.find('version')
            if version_elem is not None and version_elem.text:
                version = version_elem.text.strip()
                logger.debug(f"Found version in pom.xml: {version}")
                return version
            
            # Try parent version
            parent_elem = root.find('maven:parent', namespace)
            if parent_elem is not None:
                parent_version = parent_elem.find('maven:version', namespace)
                if parent_version is not None and parent_version.text:
                    version = parent_version.text.strip()
                    logger.debug(f"Found parent version in pom.xml: {version}")
                    return version
            
            # Try parent without namespace
            parent_elem = root.find('parent')
            if parent_elem is not None:
                parent_version = parent_elem.find('version')
                if parent_version is not None and parent_version.text:
                    version = parent_version.text.strip()
                    logger.debug(f"Found parent version in pom.xml: {version}")
                    return version
            
            logger.debug("No version found in pom.xml")
            return None
        
        except ET.ParseError as e:
            logger.error(f"Failed to parse pom.xml: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading pom.xml: {e}")
            return None
    
    def normalize_version(self, version: str) -> str:
        """
        Normalize version string to semantic versioning format.
        
        Removes prefixes like 'v' and ensures format is X.Y.Z
        
        Args:
            version: Raw version string
        
        Returns:
            Normalized version string
        """
        # Remove 'v' prefix if present
        if version.startswith('v'):
            version = version[1:]
        
        # Remove any whitespace
        version = version.strip()
        
        # Ensure at least major.minor.patch format
        parts = version.split('.')
        while len(parts) < 3:
            parts.append('0')
        
        # Take only first 3 parts for semantic versioning
        version = '.'.join(parts[:3])
        
        logger.debug(f"Normalized version: {version}")
        return version
    
    def is_valid_semver(self, version: str) -> bool:
        """
        Check if version string is valid semantic versioning.
        
        Args:
            version: Version string to validate
        
        Returns:
            True if valid semver, False otherwise
        """
        # Semantic versioning pattern: X.Y.Z where X, Y, Z are integers
        semver_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
        return bool(re.match(semver_pattern, version))
