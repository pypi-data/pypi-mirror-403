"""
Helm Chart Manager module.

This module handles Helm chart structure creation and base chart management.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from utils.logging_config import get_logger, OperationLogger

logger = get_logger(__name__)


class HelmChartManager:
    """
    Manager for Helm chart structure and base chart operations.
    
    Responsibilities:
    - Create chart directory structure
    - Clone and setup base charts
    - Generate Chart.yaml metadata
    - Generate .helmignore file
    - Generate _helpers.tpl template
    """
    
    def get_chart_directory(self, component_name: str, environment: str) -> Path:
        """
        Determine chart directory path.
        
        Args:
            component_name: Component name
            environment: Environment name
            
        Returns:
            Path to chart directory
        """
        chart_dir = Path(f"/tmp/helm-{component_name}-{environment}")
        return chart_dir
    
    def create_chart_structure(self, chart_dir: Path) -> None:
        """
        Create Helm chart directory structure.
        
        Creates:
        - chart_dir/
        - chart_dir/templates/
        
        Args:
            chart_dir: Path to chart directory
            
        Raises:
            OSError: If directories cannot be created
        """
        chart_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = chart_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        logger.debug(f"Created chart structure at {chart_dir}")
    
    def setup_base_chart(
        self,
        chart_dir: Path,
        base_chart_config: Dict[str, Any],
        config: Dict[str, Any]
    ) -> None:
        """
        Clone base chart repository and copy templates to project chart.
        
        This method:
        1. Clones the base chart repository
        2. Copies all template files and helpers to project chart
        3. Preserves all template files unchanged
        4. Only values.yaml will be updated with project-specific values
        
        Args:
            chart_dir: Path to project chart directory
            base_chart_config: Base chart configuration
            config: Full configuration
            
        Raises:
            RuntimeError: If git clone fails
            OSError: If file operations fail
        """
        with OperationLogger(logger, "setup base Helm chart"):
            repo_url = base_chart_config.get('repository')
            branch = base_chart_config.get('branch', 'main')
            chart_path = base_chart_config.get('chartPath', '.')
            
            if not repo_url:
                raise ValueError("Base chart repository URL is required")
            
            # Create temporary directory for cloning
            temp_dir = Path(f"/tmp/base-chart-{os.getpid()}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Clone base chart repository
                logger.info(f"Cloning base chart from {repo_url} (branch: {branch})")
                clone_cmd = ['git', 'clone', '--depth', '1', '--branch', branch, repo_url, str(temp_dir)]
                
                result = subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to clone base chart repository: {result.stderr}")
                
                logger.debug(f"Base chart cloned to {temp_dir}")
                
                # Determine source chart directory
                source_chart_dir = temp_dir / chart_path
                if not source_chart_dir.exists():
                    raise ValueError(f"Chart path {chart_path} not found in base chart repository")
                
                # Create project chart directory
                chart_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy all files from base chart to project chart
                logger.info(f"Copying base chart templates to {chart_dir}")
                
                # Copy templates directory
                source_templates = source_chart_dir / "templates"
                if source_templates.exists():
                    dest_templates = chart_dir / "templates"
                    if dest_templates.exists():
                        shutil.rmtree(dest_templates)
                    shutil.copytree(source_templates, dest_templates)
                    logger.debug(f"Copied templates directory")
                
                # Copy Chart.yaml if exists (will be overwritten with project-specific values)
                source_chart_yaml = source_chart_dir / "Chart.yaml"
                if source_chart_yaml.exists():
                    shutil.copy2(source_chart_yaml, chart_dir / "Chart.yaml")
                    logger.debug(f"Copied Chart.yaml")
                
                # Copy .helmignore if exists
                source_helmignore = source_chart_dir / ".helmignore"
                if source_helmignore.exists():
                    shutil.copy2(source_helmignore, chart_dir / ".helmignore")
                    logger.debug(f"Copied .helmignore")
                
                # Copy any other files (charts/, crds/, etc.)
                for item in source_chart_dir.iterdir():
                    if item.name not in ['templates', 'Chart.yaml', 'values.yaml', '.helmignore']:
                        dest_item = chart_dir / item.name
                        if item.is_dir():
                            if dest_item.exists():
                                shutil.rmtree(dest_item)
                            shutil.copytree(item, dest_item)
                            logger.debug(f"Copied directory: {item.name}")
                        else:
                            shutil.copy2(item, dest_item)
                            logger.debug(f"Copied file: {item.name}")
                
                logger.info(f"Base chart setup complete")
                
            finally:
                # Clean up temporary directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
    
    def generate_chart_yaml(self, component: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Chart.yaml metadata.
        
        Creates Helm chart metadata including:
        - apiVersion (v2 for Helm 3)
        - name (component name)
        - description (from component or project)
        - type (application)
        - version (chart version)
        - appVersion (application version)
        
        Args:
            component: Component configuration
            config: Full configuration dictionary
            
        Returns:
            Chart.yaml content as dictionary
        """
        component_name = component.get('name')
        project = config.get('project', {})
        
        # Get kubernetes configuration
        k8s_config = component.get('kubernetes', {})
        helm_config = k8s_config.get('helm', {})
        
        # Extract version information
        chart_version = helm_config.get('chartVersion', project.get('version', '1.0.0'))
        app_version = project.get('version', '1.0.0')
        
        # Build Chart.yaml
        chart_yaml = {
            'apiVersion': 'v2',
            'name': helm_config.get('chartName', component_name),
            'description': component.get('description', f"Helm chart for {component_name}"),
            'type': 'application',
            'version': chart_version,
            'appVersion': app_version,
        }
        
        # Add optional fields if present
        if project.get('organization'):
            chart_yaml['maintainers'] = [
                {
                    'name': project.get('organization'),
                }
            ]
        
        logger.debug(f"Generated Chart.yaml: {chart_yaml}")
        return chart_yaml
    
    def generate_helmignore(self, chart_dir: Path) -> None:
        """
        Generate .helmignore file.
        
        Creates a .helmignore file with common patterns to exclude.
        
        Args:
            chart_dir: Path to chart directory
        """
        helmignore_content = """# Patterns to ignore when building packages.
# This supports shell glob matching, relative path matching, and
# negation (prefixed with !). Only one pattern per line.
.DS_Store
.git/
.gitignore
.bzr/
.bzrignore
.hg/
.hgignore
.svn/
*.swp
*.bak
*.tmp
*.orig
*~
.project
.idea/
*.tmproj
.vscode/
"""
        helmignore_path = chart_dir / ".helmignore"
        helmignore_path.write_text(helmignore_content)
        logger.debug(f"Generated .helmignore at {helmignore_path}")
    
    def generate_helpers_template(self, chart_dir: Path, component: Dict[str, Any]) -> None:
        """
        Generate _helpers.tpl file with Helm template helpers.
        
        This file contains reusable template definitions used across all templates.
        
        Args:
            chart_dir: Path to chart directory
            component: Component configuration
        """
        component_name = component.get('name')
        
        helpers_content = f'''{{/*
Expand the name of the chart.
*/}}
{{{{- define "chart.name" -}}}}
{{{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{/*
Create a default fully qualified app name.
*/}}
{{{{- define "chart.fullname" -}}}}
{{{{- if .Values.fullnameOverride }}}}
{{{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- $name := default .Chart.Name .Values.nameOverride }}}}
{{{{- if contains $name .Release.Name }}}}
{{{{- .Release.Name | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}
{{{{- end }}}}
{{{{- end }}}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{{{- define "chart.chart" -}}}}
{{{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{/*
Common labels
*/}}
{{{{- define "chart.labels" -}}}}
helm.sh/chart: {{{{ include "chart.chart" . }}}}
{{{{ include "chart.selectorLabels" . }}}}
{{{{- if .Chart.AppVersion }}}}
app.kubernetes.io/version: {{{{ .Chart.AppVersion | quote }}}}
{{{{- end }}}}
app.kubernetes.io/managed-by: {{{{ .Release.Service }}}}
{{{{- end }}}}

{{/*
Selector labels
*/}}
{{{{- define "chart.selectorLabels" -}}}}
app.kubernetes.io/name: {{{{ include "chart.name" . }}}}
app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}
'''
        
        helpers_path = chart_dir / "templates" / "_helpers.tpl"
        helpers_path.write_text(helpers_content)
        logger.debug(f"Generated _helpers.tpl at {helpers_path}")
