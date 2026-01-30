"""
GitLabCIGenerator module for GitLab CI/CD Migration system.

This module provides the main generator for creating .gitlab-ci.yml files
from parsed configuration.
"""

import logging
from typing import Any, Dict, List

import yaml

from utils.constants import (
    STAGE_VALIDATE,
    STAGE_CHANGE_DETECTION,
    STAGE_BUILD,
    STAGE_PUBLISH,
    STAGE_QUALITY,
    STAGE_DEPLOY,
)
from utils.logging_config import get_logger, OperationLogger
from generator.gitlab_ci_jobs_builder import GitLabCIJobsBuilder
from generator.gitlab_ci_deploy_builder import GitLabCIDeployBuilder
from generator.gitlab_ci_quality_builder import GitLabCIQualityBuilder

logger = get_logger(__name__)


class GitLabCIGenerator:
    """
    Generator for GitLab CI/CD pipeline files.
    
    This class generates complete .gitlab-ci.yml files from parsed configuration,
    including workflow rules, build jobs, publish jobs, quality jobs, and deploy jobs.
    
    Responsibilities:
    - Generate complete .gitlab-ci.yml structure
    - Format YAML with proper indentation
    - Generate workflow rules for MR-merged-only triggering
    - Orchestrate job generation through specialized builders
    - Apply proper job dependencies and stage ordering
    """
    
    def __init__(self):
        """Initialize GitLab CI generator."""
        self.jobs_builder = GitLabCIJobsBuilder()
        self.deploy_builder = GitLabCIDeployBuilder()
        self.quality_builder = GitLabCIQualityBuilder()
        logger.debug("GitLabCIGenerator initialized")
    
    def generate(self, config: Dict[str, Any]) -> str:
        """
        Generate complete .gitlab-ci.yml file from configuration.
        
        This method orchestrates the generation of all pipeline sections:
        1. Workflow rules (MR-merged-only trigger)
        2. Stages definition
        3. Global variables
        4. Validation jobs
        5. Change detection jobs
        6. Build jobs for each component
        7. Publish jobs for each component destination
        8. Quality analysis jobs
        9. Deploy jobs for each environment
        
        Args:
            config: Validated configuration dictionary
            
        Returns:
            Complete .gitlab-ci.yml content as YAML string
            
        Raises:
            ValueError: If configuration is missing required fields
        """
        with OperationLogger(logger, "generate GitLab CI pipeline"):
            # Validate required configuration sections
            self._validate_config(config)
            
            # Build pipeline structure
            pipeline = {}
            
            # Add workflow rules
            pipeline['workflow'] = self.generate_workflow_rules(config)
            
            # Add stages
            pipeline['stages'] = self._generate_stages(config)
            
            # Add global variables
            pipeline['variables'] = self._generate_global_variables(config)
            
            # Add validation job
            validation_job = self.quality_builder.generate_validation_job(config)
            pipeline['validate:config'] = validation_job
            
            # Add change detection job if enabled
            if self.quality_builder.is_change_detection_enabled(config):
                change_detection_job = self.quality_builder.generate_change_detection_job(config)
                pipeline['detect:changes'] = change_detection_job
            
            # Add build jobs
            build_jobs = self.jobs_builder.generate_build_jobs(config.get('components', []))
            pipeline.update(build_jobs)
            
            # Add publish jobs for each environment
            environments = config.get('environments', {})
            for env_name in environments.keys():
                publish_jobs = self.jobs_builder.generate_publish_jobs(
                    config.get('components', []),
                    env_name,
                    config
                )
                pipeline.update(publish_jobs)
            
            # Add quality analysis jobs if SonarQube is enabled
            if self.quality_builder.is_sonarqube_enabled(config):
                quality_jobs = self.quality_builder.generate_quality_jobs(config)
                pipeline.update(quality_jobs)
            
            # Add deploy jobs
            deploy_jobs = self.deploy_builder.generate_deploy_jobs(
                config.get('environments', {}),
                config.get('components', [])
            )
            pipeline.update(deploy_jobs)
            
            # Convert to YAML with proper formatting
            yaml_content = self._format_yaml(pipeline)
            
            logger.info("GitLab CI pipeline generated successfully")
            return yaml_content
    
    def generate_workflow_rules(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate workflow rules for MR-merged-only triggering.
        
        The workflow ensures pipelines only run when merge requests are merged,
        not on every commit or when MRs are opened.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Workflow rules configuration
        """
        logger.debug("Generating workflow rules")
        
        workflow = {
            'rules': [
                {
                    'if': '$CI_PIPELINE_SOURCE == "merge_request_event" && $CI_MERGE_REQUEST_EVENT_TYPE == "merged"',
                    'when': 'always'
                },
                {
                    'when': 'never'
                }
            ]
        }
        
        return workflow
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate that configuration has required fields.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        if 'project' not in config:
            raise ValueError("Configuration missing 'project' section")
        
        if 'components' not in config or not config['components']:
            raise ValueError("Configuration must have at least one component")
        
        if 'environments' not in config or not config['environments']:
            raise ValueError("Configuration must have at least one environment")
    
    def _generate_stages(self, config: Dict[str, Any]) -> List[str]:
        """
        Generate list of pipeline stages.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of stage names in execution order
        """
        stages = [STAGE_VALIDATE]
        
        # Add change detection stage if enabled
        if self.quality_builder.is_change_detection_enabled(config):
            stages.append(STAGE_CHANGE_DETECTION)
        
        stages.extend([
            STAGE_BUILD,
            STAGE_PUBLISH,
        ])
        
        # Add quality stage if SonarQube is enabled
        if self.quality_builder.is_sonarqube_enabled(config):
            stages.append(STAGE_QUALITY)
        
        stages.append(STAGE_DEPLOY)
        
        return stages
    
    def _generate_global_variables(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate global pipeline variables.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary of global variables
        """
        project = config.get('project', {})
        
        variables = {
            'PROJECT_NAME': project.get('name', 'unknown'),
            'PROJECT_VERSION': project.get('version', '1.0.0'),
            'ORGANIZATION': project.get('organization', 'default'),
            'DOCKER_DRIVER': 'overlay2',
            'DOCKER_TLS_CERTDIR': '/certs',
        }
        
        return variables
    
    def _format_yaml(self, pipeline: Dict[str, Any]) -> str:
        """
        Format pipeline dictionary as YAML with proper indentation.
        
        Uses PyYAML with custom formatting options:
        - 2-space indentation
        - No flow style (always use block style)
        - Preserve key order
        - Add header comment
        
        Args:
            pipeline: Pipeline dictionary
            
        Returns:
            Formatted YAML string
        """
        # Add header comment
        header = (
            "# GitLab CI/CD Pipeline\n"
            "# Generated by GitLab CI/CD Migration Tool\n"
            "# DO NOT EDIT MANUALLY - Changes will be overwritten\n\n"
        )
        
        # Convert to YAML with proper formatting
        yaml_content = yaml.dump(
            pipeline,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            width=120,
            allow_unicode=True
        )
        
        return header + yaml_content
